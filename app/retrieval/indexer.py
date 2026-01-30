from typing import List
from dataclasses import dataclass, asdict
from elasticsearch import Elasticsearch
from ..config.logger import get_logger
from ..config.configer import MIN_SCORE_THRESHOLD

logger = get_logger("mini-rag." + __name__)


@dataclass(frozen=True)
class ChunkMetadata:
    document_id: str
    chunk_index: int
    source: str
    embedding_version: str = "v1"

    def to_dict(self) -> dict:
        """
        Convert to a Chroma-compatible metadata dict.
        """
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "ChunkMetadata":
        """
        Reconstruct metadata from Chroma.
        """
        return ChunkMetadata(**data)


@dataclass
class DocumentChunk:
    id: str
    text: str
    embedding: List[float]
    metadata: ChunkMetadata


@dataclass
class DocumentChunkDistant(DocumentChunk):
    score: float
    source: str


class ElasticsearchIndex:
    def __init__(self, embedding_dim: int, index_name: str = "document_chunks"):
        """
        Initialize Elasticsearch client and create index if it doesn't exist.
        """
        self.client = Elasticsearch("http://localhost:9200")
        self.index_name = index_name
        self.embedding_dim = embedding_dim

        if not self.client.indices.exists(index=index_name):
            self.create_index()
        else:
            logger.debug(f"[ElasticDB] Loaded existing index '{index_name}'")

    def create_index(self):
        mapping = {
            "mappings": {
                "properties": {
                    "text": {"type": "text"},
                    "document_id": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                    "source": {"type": "keyword"},
                    "embedding_version": {"type": "keyword"},
                    "embedding": {"type": "dense_vector", "dims": self.embedding_dim}
                }
            }
        }
        self.client.indices.create(index=self.index_name, body=mapping)
        logger.debug(f"[ElasticDB] Created index '{self.index_name}'")

    def add_items(self, document_entries: List[DocumentChunk]):
        """
        Add DocumentChunk objects with their embeddings.
        """
        for entry in document_entries:
            doc = {
                "text": entry.text,
                "embedding": entry.embedding,
                **entry.metadata.to_dict()
            }
            self.client.index(index=self.index_name, id=entry.id, document=doc)
        self.client.indices.refresh(index=self.index_name)
        logger.debug(f"[ElasticDB] Added {len(document_entries)} items")

    def similarity_search(
            self, query_embedding, top_k: int = 3, threshold: float = MIN_SCORE_THRESHOLD
    ) -> List[DocumentChunkDistant]:
        """
        Return top n DocumentChunk objects similar to query_embedding.
        """
        query = {
            "field": 'embedding',
            "query_vector": query_embedding,
            "k": top_k
        }

        res = self.client.search(index=self.index_name, knn=query)
        results = []
        for hit in res["hits"]["hits"]:
            if hit["_score"] > threshold:
                metadata_dict = {k: v for k, v in hit["_source"].items() if k not in ["text", "embedding"]}
                chunk_metadata = ChunkMetadata.from_dict(metadata_dict)
                results.append(
                    DocumentChunkDistant(
                        id=hit["_id"],
                        text=hit["_source"]["text"],
                        embedding=[],
                        metadata=chunk_metadata,
                        score=hit["_score"],
                        source="Elastic"
                    )
                )

        return results

    def delete(self, ids: List[str]):
        """
        Delete documents by their IDs.
        """
        for doc_id in ids:
            self.client.delete(index=self.index_name, id=doc_id, ignore=[404])
        logger.debug(f"[ElasticDB] Deleted {len(ids)} items")

    def reset(self):
        """
        Delete all documents by deleting and recreating the index.
        """
        self.client.indices.delete(index=self.index_name, ignore=[400, 404])
        logger.debug(f"[ElasticDB] Reset index '{self.index_name}'")
        self.create_index()

    def retrieve_all(self) -> List[DocumentChunk]:
        """
        Retrieve all documents in the index as DocumentChunk objects.
        """
        res = self.client.search(index=self.index_name, query={"match_all": {}}, size=1000)
        results = []
        for hit in res["hits"]["hits"]:
            metadata_dict = {k: v for k, v in hit["_source"].items() if k not in ["text", "embedding"]}
            chunk_metadata = ChunkMetadata.from_dict(metadata_dict)
            results.append(DocumentChunk(id=hit["_id"], text=hit["_source"]["text"], embedding=[], metadata=chunk_metadata))
        return results
