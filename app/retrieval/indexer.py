from typing import List
from dataclasses import dataclass, asdict
from elasticsearch import Elasticsearch
from ..config.logger import get_logger
from ..config.configer import MIN_SCORE_THRESHOLD

logger = get_logger("mini-rag." + __name__)


@dataclass(frozen=True)
class ChunkMetadata:
    document_id: str
    page: str
    chunk_index: int
    source: str
    embedding_version: str = "v1"

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "ChunkMetadata":
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
        Initialize the Elasticsearch client and ensure the index exists.

        Args:
            embedding_dim (int): Dimension of embedding vectors.
            index_name (str, optional): Name of the Elasticsearch index.

        Returns:
            None
        """
        self.client = Elasticsearch("http://localhost:9200")
        self.index_name = index_name
        self.embedding_dim = embedding_dim

        if not self.client.indices.exists(index=index_name):
            self.create_index()
        else:
            logger.debug(f"[ElasticDB] Loaded existing index '{index_name}'")

    def create_index(self):
        """
        Create a new Elasticsearch index with the appropriate mapping for document chunks.
        """
        mapping = {
            "mappings": {
                "properties": {
                    "text": {"type": "text"},
                    "document_id": {"type": "keyword"},
                    "page": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                    "source": {"type": "keyword"},
                    "embedding_version": {"type": "keyword"},
                    "embedding": {"type": "dense_vector", "dims": self.embedding_dim},
                }
            }
        }
        self.client.indices.create(index=self.index_name, body=mapping)
        logger.debug(f"[ElasticDB] Created index '{self.index_name}'")

    def add_items(self, document_entries: List[DocumentChunk]):
        """
        Add multiple document chunks to the Elasticsearch index.

        Args:
            document_entries (List[DocumentChunk]): List of chunks to index.
        """
        for entry in document_entries:
            doc = {
                "text": entry.text,
                "embedding": entry.embedding,
                **entry.metadata.to_dict(),
            }
            self.client.index(index=self.index_name, id=entry.id, document=doc)
        self.client.indices.refresh(index=self.index_name)
        logger.debug(f"[ElasticDB] Added {len(document_entries)} items")

    def similarity_search(
        self, query_embedding, top_k: int = 3, threshold: float = MIN_SCORE_THRESHOLD
    ) -> List[DocumentChunkDistant]:
        """
        Perform a similarity search over the indexed chunks using a query embedding.

        Args:
            query_embedding: Embedding vector to search for similar chunks.
            top_k (int, optional): Number of top results to return. Defaults to 3.
            threshold (float, optional): Minimum score threshold to include results. Defaults to MIN_SCORE_THRESHOLD.

        Returns:
            List[DocumentChunkDistant]: Ranked list of similar chunks with scores.
        """
        query = {"field": "embedding", "query_vector": query_embedding, "k": top_k}

        res = self.client.search(index=self.index_name, knn=query)
        results = []
        for hit in res["hits"]["hits"]:
            if hit["_score"] > threshold:
                metadata_dict = {
                    k: v
                    for k, v in hit["_source"].items()
                    if k not in ["text", "embedding"]
                }
                chunk_metadata = ChunkMetadata.from_dict(metadata_dict)
                results.append(
                    DocumentChunkDistant(
                        id=hit["_id"],
                        text=hit["_source"]["text"],
                        embedding=[],
                        metadata=chunk_metadata,
                        score=hit["_score"],
                        source="Elastic",
                    )
                )

        return results

    def delete(self, ids: List[str]):
        """
        Delete specific document chunks from the Elasticsearch index.

        Args:
            ids (List[str]): List of document IDs to delete.
        """
        for doc_id in ids:
            self.client.delete(index=self.index_name, id=doc_id, ignore=[404])
        logger.debug(f"[ElasticDB] Deleted {len(ids)} items")

    def reset(self):
        """
        Delete and recreate the Elasticsearch index, effectively clearing all stored data.
        """
        self.client.indices.delete(index=self.index_name, ignore=[400, 404])
        logger.debug(f"[ElasticDB] Reset index '{self.index_name}'")
        self.create_index()

    def retrieve_all(self) -> List[DocumentChunk]:
        """
        Retrieve all document chunks from the Elasticsearch index.

        Returns:
            List[DocumentChunk]: All stored document chunks.
        """
        res = self.client.search(
            index=self.index_name, query={"match_all": {}}, size=1000
        )
        results = []
        for hit in res["hits"]["hits"]:
            metadata_dict = {
                k: v
                for k, v in hit["_source"].items()
                if k not in ["text", "embedding"]
            }
            chunk_metadata = ChunkMetadata.from_dict(metadata_dict)
            results.append(
                DocumentChunk(
                    id=hit["_id"],
                    text=hit["_source"]["text"],
                    embedding=[],
                    metadata=chunk_metadata,
                )
            )
        return results
