from docling_core.types import DoclingDocument
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.base import BaseTokenizer
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer
from app.config.configer import SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH
from ..config.logger import get_logger

logger = get_logger("mini-rag." + __name__)


class Chunker:
    def __init__(self):
        tokenizer = AutoTokenizer.from_pretrained(SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH)
        max_tokens = tokenizer.model_max_length
        base_tokenizer: BaseTokenizer = HuggingFaceTokenizer(tokenizer=tokenizer, max_tokens=max_tokens)
        self.chunker = HybridChunker(tokenizer=base_tokenizer, max_tokens=max_tokens)

    def chunk(self, doc: DoclingDocument) -> [str]:
        chunks = []
        chunk_iter = self.chunker.chunk(dl_doc=doc)
        for i, chunk in enumerate(chunk_iter):
            enriched_text = self.chunker.contextualize(chunk=chunk)
            logger.debug(f"chunker.contextualize(chunk):\n{f'{enriched_text}'!r}\n")
            chunks.append(enriched_text)
        return chunks
