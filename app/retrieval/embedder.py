from enum import Enum
from typing import List
from abc import ABC, abstractmethod
from sentence_transformers import SentenceTransformer
from app.model.chat_client import OpenAILLM
from app.config.configer import (
    OFFLINE_SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH,
    OPENAI_EMBEDDING_MODEL,
)


class EmbedderModel(Enum):
    OPENAI = "openai"
    MINILM = "minilm"


DEFAULT_EMBEDDER_MODEL = EmbedderModel.OPENAI


class BaseEmbedder(ABC):
    @abstractmethod
    def embed(self, texts: list[str]):
        pass


class Embedder:
    embedder: BaseEmbedder

    def __init__(self, model: EmbedderModel):
        """
        Select and initialize the embedding backend based on the provided model.

        Args:
            model (EmbedderModel): Embedding provider to use.
        """
        if model == EmbedderModel.OPENAI:
            self.embedder = OpenAIEmbedder()
        else:
            self.embedder = OfflineEmbedder()

    def embed(self, texts: list[str]) -> List[List[float]]:
        """
        Generate vector embeddings for the provided texts using the configured embedder backend.

        Args:
            texts (list[str]): List of input strings to embed.

        Returns:
            List[List[float]]: Numerical vector representations for each input text.
        """
        return self.embedder.embed(texts)


class OfflineEmbedder(BaseEmbedder):
    def __init__(self, model: str = OFFLINE_SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH):
        """
        Load a local SentenceTransformer model for offline embedding generation.

        Args:
            model (str, optional): Filesystem path to the local embedding model.
        """
        self.model_name = model
        self.model = SentenceTransformer(
            self.model_name,
            tokenizer_kwargs={"padding_side": "left"},
        )

    def embed(self, texts: list[str]) -> List[List[float]]:
        """
        Encode texts into embeddings using the locally loaded SentenceTransformer model.

        Args:
            texts (list[str]): List of input strings to embed.

        Returns:
            List[List[float]]: Embedding vectors for the input texts.
        """
        query_embeddings = self.model.encode_query(texts, prompt_name="query")
        return query_embeddings.flatten().tolist()


class OpenAIEmbedder(BaseEmbedder):
    def __init__(self, model: str = OPENAI_EMBEDDING_MODEL):
        """
        Initialize the OpenAI embedding client with the configured model.

        Args:
            model (str, optional): Name of the OpenAI embedding model.
        """
        self.model_name = model
        self.chat_client = OpenAILLM()

    def embed(self, texts: list[str]) -> List[List[float]]:
        """
        Request embeddings from the OpenAI API for the provided texts.

        Args:
            texts (list[str]): List of input strings to embed.

        Returns:
            List[List[float]]: Embedding vectors returned by the OpenAI service.
        """
        query_embeddings = self.chat_client.embed(texts)
        return query_embeddings
