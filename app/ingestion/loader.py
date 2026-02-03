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
from ..config.configer import CORPUS_DIR, TMP_DOCUMENTS_DIR

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
        markdown_dir: Path = TMP_DOCUMENTS_DIR,
    ):
        """
        Initialize the corpus loader with paths and a PDF-to-Markdown converter.

        Args:
            chat_client (ChatClient): Language model client for processing documents.
            corpus_dir (Path, optional): Directory containing PDF files. Defaults to CORPUS_DIR.
            markdown_dir (Path, optional): Directory to store converted markdown files. Defaults to TMP_DOCUMENTS_DIR.
        """
        self.chat_client = chat_client
        self.corpus_dir = Path(corpus_dir)
        self.markdown_dir = Path(markdown_dir)
        self.markdown_dir.mkdir(parents=True, exist_ok=True)
        self.converter = PdfToMarkdownConverter(
            chat_client=chat_client, markdown_dir=self.markdown_dir
        )

    def scan_corpus_dir(self) -> List[CorpusFile]:
        """
        Scan the corpus directory for PDF files, compute their page count and content hash.

        Returns:
            List[CorpusFile]: List of discovered corpus files with metadata.
        """
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
        """
        Determine which corpus files have not yet been ingested by comparing hashes with existing database records.

        Args:
            corpus_files (List[CorpusFile]): List of scanned corpus files.
            ingested_files (List[File]): List of files already ingested.

        Returns:
            List[str]: Paths of unprocessed files.
        """
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
        """
        Convert a set of PDF files to DoclingDocument objects via the PDF-to-Markdown converter.

        Args:
            files (set[str]): File paths to convert.

        Returns:
            list[DoclingDocument]: Converted document objects ready for chunking.
        """
        return self.converter.convert_files(files)

    @staticmethod
    def reset():
        """
        Delete all markdown files in the temporary documents directory.
        """
        directory = TMP_DOCUMENTS_DIR

        for file_path in directory.glob("*.md"):
            if file_path.is_file():
                file_path.unlink()
        logger.debug("Deleted all markdown files")
