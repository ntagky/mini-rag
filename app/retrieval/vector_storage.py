import uuid
import chromadb
from typing import List
from typing import Dict, Any
from chromadb.config import Settings
from dataclasses import dataclass, asdict
from ..config.logger import get_logger

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
    metadata: ChunkMetadata


class ChromaDB:
    def __init__(self, path: str = ".chroma_db", collection_name: str = "default"):
        """
        Initialize a persistent ChromaDB client.
        The database will be created (if needed) and persisted to `path`.
        """
        # Persistent client
        self.client = chromadb.PersistentClient(path=path, settings=Settings())
        self.collection_name = collection_name

        # Safe get-or-create for collection
        existing_collections = [c.name for c in self.client.list_collections()]
        if collection_name in existing_collections:
            self.collection = self.client.get_collection(name=collection_name)
            logger.debug(f"[ChromaDB] Loaded existing collection '{collection_name}'")
        else:
            self.collection = self.client.create_collection(name=collection_name)
            logger.debug(f"[ChromaDB] Created new collection '{collection_name}'")

    def add_items(
            self,
            embeddings: List[List[float]],
            texts: List[str],
            metadatas: List[Dict[str, Any]] = None
    ):
        """
        Add vectors with associated text and optional metadata.
        All lists must be the same length.
        """
        if metadatas is None:
            metadatas = [{} for _ in texts]

        ids = [str(uuid.uuid4()) for i in range(len(texts))]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        print(f"[ChromaDB] Added {len(texts)} items")

    def similarity_search(
            self,
            query_embeddings: List[List[float]],
            n_results: int = 5,
            where: Dict[str, Any] = None
    ) -> List[List[dict]]:
        """
        Search for similar vectors.
        Returns a structured list of results for each query.
        """
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where
        )

        # Format results
        formatted = []
        for i in range(len(query_embeddings)):
            items = []
            for j in range(len(results["ids"][i])):
                items.append({
                    "id": results["ids"][i][j],
                    "text": results["documents"][i][j],
                    "metadata": results["metadatas"][i][j],
                    "distance": results["distances"][i][j]
                })
            formatted.append(items)
        return formatted

    def delete(self, ids: List[str]):
        """
        Delete items from the collection by ID.
        """
        self.collection.delete(ids=ids)
        print(f"[ChromaDB] Deleted {len(ids)} items")

    def reset(self):
        self.client.delete_collection(self.collection_name)
        print(f"[ChromaDB] Deleted all items")
        self.collection = self.client.create_collection(name=self.collection_name)
