import base64
import uuid
from typing import List
from pathlib import Path
from docling_core.types.doc.document import PictureItem, TextItem, DocItemLabel
from .chunker import Chunker
from .loader import CorpusLoader, CorpusFile
from ..config.configer import SYSTEM_PROMPT_IMAGE_DESCRIBER, USER_PROMPT_IMAGE_DESCRIBER
from ..retrieval.embedder import Embedder
from ..retrieval.vector_storage import ChromaDB, ChunkMetadata
from ..retrieval.sql_storage import IngestionDB, IngestedFile
from ..model.llm_client import LLMClient


def ingest_corpus():
    loader = CorpusLoader()
    chunker = Chunker()
    embedder = Embedder()
    llm_client = LLMClient()
    vector_db = ChromaDB()
    sql_db = IngestionDB()

    ingested_files = sql_db.read_all_files()
    corpus_files = loader.scan_corpus_dir()

    unprocessed = _get_unprocessed_files(corpus_files, ingested_files)
    # corpus_files = ["data/corpus/singular/E3 Structure - Document 2.pdf"]
    # unprocessed = ["data/corpus/singular/E3 Structure - Document 2.pdf"]

    if len(unprocessed):
        print(f"Found {len(unprocessed)} unprocessed file{'s' if len(unprocessed) > 1 else ''}..")
        documents = loader.load_files(set(unprocessed))
        print(documents)

        output_dir = Path(".tmp")
        output_dir.mkdir(parents=True, exist_ok=True)
        for corpus_file, document in zip(corpus_files, documents):

            replacements = []
            for item, _ in document.iterate_items():
                if isinstance(item, PictureItem):
                    # Get image and prompt it to LLM
                    picture_uri = str(item.image.uri)
                    if picture_uri.startswith("data:image/png;base64,"):
                        element_image_filename = (output_dir / f"{document.origin.filename}-image-{len(replacements)+1}.png")
                        data = picture_uri.split(",")[1]
                        decoded_bytes = base64.b64decode(data)
                        with open(element_image_filename, "wb") as f:
                            f.write(decoded_bytes)

                        # print("Calling agent to describe image..")
                        # result = llm_client.generate_multimodal(
                        #     SYSTEM_PROMPT_IMAGE_DESCRIBER,
                        #     USER_PROMPT_IMAGE_DESCRIBER,
                        #     [element_image_filename]
                        # )
                        # print(result["text"])

                        # extracted_text = result["text"]
                        extracted_text = 'result["text"]'
                        new_text = document.add_text(
                            label=DocItemLabel.TEXT,
                            text=extracted_text
                        )
                        replacements.append((item, new_text))

            for old_item, new_item in replacements:
                document.replace_item(new_item=new_item, old_item=old_item)

            chunks = chunker.chunk(document)

            embeddings = embedder.embed(chunks)
            metadatas = [ChunkMetadata(
                document_id=document.origin.filename,
                chunk_index=i,
                source="markdown"
            ).to_dict() for i in range(len(chunks))]

            sql_db.create_file(IngestedFile(
                id=uuid.uuid4(),
                filename=corpus_file.filename,
                path=corpus_file.path,
                hash=corpus_file.hash,
                page_count=corpus_file.pages,
                chunk_count=len(chunks)
            ))
            vector_db.add_items(embeddings=embeddings, texts=chunks, metadatas=metadatas)
    else:
        print("All corpus files have been processed.")


def _get_unprocessed_files(corpus_files, ingested_files) -> List[str]:
    unprocessed = []
    for corpus_file in corpus_files:
        found = False
        for ingested_file in ingested_files:
            if corpus_file.filename == ingested_file.filename and corpus_file.hash == ingested_file.hash:
                found = True
                break

        if not found:
            unprocessed.append("/".join([corpus_file.path, corpus_file.filename]))

    return unprocessed
