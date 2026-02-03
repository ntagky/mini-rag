from docling_core.types import DoclingDocument
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer
from typing import List, Tuple
from app.config.configer import OFFLINE_SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH
from ..config.logger import get_logger

logger = get_logger("mini-rag." + __name__)


class Chunker:
    def __init__(self):
        """
        Initialize the HybridChunker with a locally stored Hugging Face tokenizer.
        """
        tokenizer = AutoTokenizer.from_pretrained(
            OFFLINE_SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH
        )
        max_tokens = tokenizer.model_max_length
        base_tokenizer = HuggingFaceTokenizer(
            tokenizer=tokenizer, max_tokens=max_tokens
        )
        self.chunker = HybridChunker(tokenizer=base_tokenizer, max_tokens=max_tokens)

    def chunk(self, doc: DoclingDocument) -> Tuple[List[str], List[str]]:
        """
        Split a DoclingDocument into contextualized text chunks and map them to their source pages.

        Args:
            doc (DoclingDocument): Parsed document to be chunked.

        Returns:
            Tuple[List[str], List[str]]: A tuple containing the generated text chunks and their corresponding page identifiers.
        """
        chunks: List[str] = []
        pages: List[str] = []
        chunk_iter = self.chunker.chunk(dl_doc=doc)
        for i, chunk in enumerate(chunk_iter):
            page_nos = sorted(
                {p.page_no for item in chunk.meta.doc_items for p in item.prov}
            )
            page_str = f"{','.join(map(str, page_nos))}" if page_nos else "N/A"
            enriched_text = self.chunker.contextualize(chunk=chunk)
            logger.debug(f"chunker.contextualize(chunk):\n{f'{enriched_text}'!r}\n")
            chunks.append(enriched_text)
            pages.append(page_str)
        return chunks, pages
