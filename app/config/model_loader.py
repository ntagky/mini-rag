from pathlib import Path
from .configer import (
    SENTENCE_TRANSFORMER_MODEL_NAME,
    OFFLINE_SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH,
)
from sentence_transformers import SentenceTransformer
from ..config.logger import get_logger

logger = get_logger("mini-rag." + __name__)


def load_embedding_model():
    """
    Ensure the sentence transformer embedding model is available locally; download and persist it if missing.
    """
    if Path(OFFLINE_SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH).exists():
        logger.debug(
            f"Sentence transformer model found locally at path: {OFFLINE_SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH}"
        )
    else:
        logger.info(
            f"Sentence transformer model not found locally. Downloading: {SENTENCE_TRANSFORMER_MODEL_NAME}.."
        )
        tokenizer = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL_NAME)
        Path(OFFLINE_SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH).mkdir(
            parents=True, exist_ok=True
        )
        tokenizer.save(OFFLINE_SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH)
        logger.info(
            f"Downloaded and saved locally to: {OFFLINE_SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH}"
        )
