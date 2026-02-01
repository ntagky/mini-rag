from enum import Enum
from typing import List
from abc import ABC, abstractmethod
from sentence_transformers import SentenceTransformer
from ..model.chat_client import OpenAILLM
from ..config.configer import (
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
        if model == EmbedderModel.OPENAI:
            self.embedder = OpenAIEmbedder()
        else:
            self.embedder = OfflineEmbedder()

    def embed(self, texts: list[str]) -> List[List[float]]:
        return self.embedder.embed(texts)


class OfflineEmbedder(BaseEmbedder):
    def __init__(self, model: str = OFFLINE_SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH):
        self.model_name = model
        self.model = SentenceTransformer(
            self.model_name,
            tokenizer_kwargs={"padding_side": "left"},
        )

    def embed(self, texts: list[str]) -> List[List[float]]:
        query_embeddings = self.model.encode_query(texts, prompt_name="query")
        return query_embeddings.flatten().tolist()


class OpenAIEmbedder(BaseEmbedder):
    def __init__(self, model: str = OPENAI_EMBEDDING_MODEL):
        self.model_name = model
        self.chat_client = OpenAILLM()

    def embed(self, texts: list[str]) -> List[List[float]]:
        query_embeddings = self.chat_client.embed(texts)
        return query_embeddings
