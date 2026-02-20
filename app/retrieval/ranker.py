import json
import joblib
from pathlib import Path
from typing import List, Dict
from scipy.sparse import save_npz, load_npz
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

from ..config.configer import TFIDF_DIR
from .indexer import DocumentChunk, DocumentChunkDistant


class TfidfRank:
    def __init__(self, base_path: Path = TFIDF_DIR):
        """
        Initialize the TF-IDF ranker and set up paths for storing vectorizer, matrix, and chunk metadata.

        Args:
            base_path (Path, optional): Directory to store TF-IDF data. Defaults to TFIDF_DIR.
        """
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.vectorizer_path = self.base_path / "vectorizer.joblib"
        self.matrix_path = self.base_path / "matrix.npz"
        self.chunks_path = self.base_path / "chunks.json"

        self.vectorizer: TfidfVectorizer | None = None
        self.matrix = None
        self.chunks: List[DocumentChunk] = []

    def build(self, chunks: List[DocumentChunk]):
        """
        Compute TF-IDF vectors for the given document chunks and save the vectorizer, matrix, and chunk metadata to disk.

        Args:
            chunks (List[DocumentChunk]): List of document chunks to index.
        """
        texts = [c.text for c in chunks]

        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_df=0.5,
            min_df=2,
        )

        self.matrix = self.vectorizer.fit_transform(texts)
        self.chunks = chunks

        joblib.dump(self.vectorizer, self.vectorizer_path)
        save_npz(self.matrix_path, self.matrix)

        with open(self.chunks_path, "w", encoding="utf-8") as f:
            json.dump(
                [
                    {"id": c.id, "text": c.text, "metadata": c.metadata.to_dict()}
                    for c in chunks
                ],
                f,
                ensure_ascii=False,
                indent=4,
            )

    def exists(self) -> bool:
        """
        Check if the TF-IDF vectorizer, matrix, and chunk metadata files exist on disk.

        Returns:
            bool: True if all files exist, False otherwise.
        """
        return (
            self.vectorizer_path.exists()
            and self.matrix_path.exists()
            and self.chunks_path.exists()
        )


class TfidfRetriever:
    REQUIRED_FILES = ["vectorizer.joblib", "matrix.npz", "chunks.json"]

    @classmethod
    def exists(cls, base_path: Path = TFIDF_DIR) -> bool:
        """
        Return True if all required TF-IDF files exist.
        """
        return all((base_path / f).exists() for f in cls.REQUIRED_FILES)

    def __init__(self, base_path: Path = TFIDF_DIR):
        """
        Load the TF-IDF vectorizer, matrix, and chunk metadata from disk for retrieval.

        Args:
            base_path (Path, optional): Directory containing TF-IDF data. Defaults to TFIDF_DIR.
        """
        self.base = base_path

        self.vectorizer = joblib.load(self.base / "vectorizer.joblib")
        self.matrix = load_npz(self.base / "matrix.npz")

        with open(self.base / "chunks.json", encoding="utf-8") as f:
            self.chunks: List[Dict] = json.load(f)

    def retrieve(self, query: str, top_k: int = 5) -> List[DocumentChunkDistant]:
        """
        Retrieve the top-k most similar document chunks to a query using TF-IDF cosine similarity.

        Args:
            query (str): Input query string.
            top_k (int, optional): Number of top results to return. Defaults to 5.

        Returns:
            List[DocumentChunkDistant]: Ranked list of matching document chunks with scores.
        """
        query_vec = self.vectorizer.transform([query])

        scores = cosine_similarity(query_vec, self.matrix)[0]
        top_indices = scores.argsort()[::-1][:top_k]

        results = []
        for idx in top_indices:
            chunk = self.chunks[idx]
            results.append(
                DocumentChunkDistant(
                    id=chunk["id"],
                    text=chunk["text"],
                    embedding=[],
                    metadata=chunk["metadata"],
                    score=float(scores[idx]),
                    source="TF-IDF",
                )
            )

        return results
