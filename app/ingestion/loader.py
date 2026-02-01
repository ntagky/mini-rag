import PyPDF2
from typing import List
from pathlib import Path
from pydantic import BaseModel
from docling_core.types import DoclingDocument
from .hasher import hash_content
from .converter import PdfToMarkdownConverter
from ..config.logger import get_logger
from ..retrieval.persistor import File
from ..model.chat_client import ChatClient
from ..config.configer import CORPUS_DIR, MARKDOWN_DIR

logger = get_logger("mini-rag." + __name__)


class CorpusFile(BaseModel):
    filename: str
    path: str
    pages: int
    hash: str


class CorpusLoader:
    def __init__(
        self,
        chat_client: ChatClient,
        corpus_dir: Path = CORPUS_DIR,
        markdown_dir: Path = MARKDOWN_DIR,
    ):
        self.chat_client = chat_client
        self.corpus_dir = Path(corpus_dir)
        self.markdown_dir = Path(markdown_dir)
        self.markdown_dir.mkdir(parents=True, exist_ok=True)
        self.converter = PdfToMarkdownConverter(
            chat_client=chat_client, markdown_dir=self.markdown_dir
        )

    def scan_corpus_dir(self) -> List[CorpusFile]:
        corpus_files = []
        pdf_files = list(self.corpus_dir.glob("*.pdf"))
        for pdf_file in pdf_files:
            file = open(pdf_file, "rb")
            pdf_reader = PyPDF2.PdfReader(file)

            text = ""
            for i in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[i]
                text += page.extract_text()
            hashed_content = hash_content(text)

            corpus_files.append(
                CorpusFile(
                    filename=pdf_file.name,
                    path=str(self.corpus_dir),
                    pages=len(pdf_reader.pages),
                    hash=hashed_content,
                )
            )
        return corpus_files

    @staticmethod
    def get_unprocessed_files(
        corpus_files: List[CorpusFile], ingested_files: List[File]
    ) -> List[str]:
        unprocessed = []
        for corpus_file in corpus_files:
            found = False
            for ingested_file in ingested_files:
                if (
                    corpus_file.filename == ingested_file.filename
                    and corpus_file.hash == ingested_file.hash
                ):
                    found = True
                    break

            if not found:
                unprocessed.append("/".join([corpus_file.path, corpus_file.filename]))

        return unprocessed

    def load_files(self, files: set[str]) -> list[DoclingDocument]:
        return self.converter.convert_files(files)

    @staticmethod
    def reset():
        directory = MARKDOWN_DIR

        for file_path in directory.glob("*.md"):
            if file_path.is_file():
                file_path.unlink()
        logger.debug("Deleted all markdown files")
