from pathlib import Path
from .configer import SENTENCE_TRANSFORMER_MODEL_NAME, SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH
from sentence_transformers import SentenceTransformer
from ..config.logger import get_logger

logger = get_logger("mini-rag." + __name__)


def load_embedding_model() -> None:
    if Path(SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH).exists():
        logger.debug(f"Sentence transformer model found locally at path: {SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH}")
    else:
        logger.info(f"Sentence transformer model not found locally. Downloading: {SENTENCE_TRANSFORMER_MODEL_NAME}")
        tokenizer = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL_NAME)
        Path(SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH).mkdir(parents=True, exist_ok=True)
        tokenizer.save(SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH)
        logger.info(f"Sentence transformer model saved locally to: {SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH}")
