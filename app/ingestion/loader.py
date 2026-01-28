import PyPDF2
from pathlib import Path
from pydantic import BaseModel
from docling_core.types import DoclingDocument
from .hasher import hash_content
from .converter import PdfToMarkdownConverter


class CorpusFile(BaseModel):
    filename: str
    path: str
    pages: int
    hash: str


class CorpusLoader:
    def __init__(self, corpus_dir: Path = "data/corpus/unprocessed", markdown_dir: Path = "data/markdowns"):
        self.corpus_dir = Path(corpus_dir)
        self.markdown_dir = Path(markdown_dir)
        self.markdown_dir.mkdir(parents=True, exist_ok=True)
        self.converter = PdfToMarkdownConverter(markdown_dir=self.markdown_dir)

    def scan_corpus_dir(self) -> list[CorpusFile]:
        corpus_files = []
        pdf_files = list(self.corpus_dir.glob("*.pdf"))
        for pdf_file in pdf_files:
            file = open(pdf_file, 'rb')
            pdf_reader = PyPDF2.PdfReader(file)

            text = ''
            for i in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[i]
                text += page.extract_text()
            hashed_content = hash_content(text)

            corpus_files.append(CorpusFile(
                filename=pdf_file.name,
                path=str(self.corpus_dir),
                pages=len(pdf_reader.pages),
                hash=hashed_content
            ))
        return corpus_files

    def load_files(self, files: set[str]) -> list[DoclingDocument]:
        return self.converter.convert_files(files)
