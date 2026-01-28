from pathlib import Path
from .configer import SENTENCE_TRANSFORMER_MODEL_NAME, SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH
from sentence_transformers import SentenceTransformer


def load_embedding_model() -> None:
    if Path(SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH).exists():
        print(f"✅ Loading sentence transformer model from local path: {SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH}")
    else:
        print(f"⬇️ Sentence transformer model not found locally. Downloading: {SENTENCE_TRANSFORMER_MODEL_NAME}")
        tokenizer = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL_NAME)
        Path(SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH).mkdir(parents=True, exist_ok=True)
        tokenizer.save(SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH)
        print(f"💾 Sentence transformer model saved to: {SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH}")
