from sentence_transformers import SentenceTransformer
from ..config.configer import SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH


class Embedder:
    def __init__(self, model_name: str = SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH):
        self.model_name = model_name
        self.model = SentenceTransformer(
            self.model_name,
            tokenizer_kwargs={"padding_side": "left"},
        )

    def embed(self, texts: list[str]):
        query_embeddings = self.model.encode_query(texts, prompt_name="query")
        print(query_embeddings)
        return query_embeddings
