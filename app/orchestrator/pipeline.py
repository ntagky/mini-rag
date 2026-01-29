import uuid

from pathlib import Path
from ..config.configer import TMP_DIR, SYSTEM_PROMPT_SINGLE_RESPONSE_DESCRIBER
from ..ingestion.chunker import Chunker
from ..ingestion.loader import CorpusLoader, CorpusFile
from ..retrieval.embedder import Embedder
from ..retrieval.vector_storage import ChromaDB, ChunkMetadata
from ..retrieval.sql_storage import IngestionDB, IngestedFile
from ..model.chat_client import ChatClient
from ..config.logger import get_logger

logger = get_logger("mini-rag." + __name__)

chunker = Chunker()
embedder = Embedder()
chat_client = ChatClient("gpt-4.1-mini")
loader = CorpusLoader(chat_client)
vector_db = ChromaDB()
sql_db = IngestionDB()


def ingest_corpus(reset: bool = False):
    if reset:
        vector_db.reset()
        sql_db.reset()
        loader.reset()

    ingested_files = sql_db.read_all_files()
    corpus_files = loader.scan_corpus_dir()

    unprocessed = loader.get_unprocessed_files(corpus_files, ingested_files)

    if len(unprocessed):
        logger.debug(f"Found {len(unprocessed)} unprocessed file{'s' if len(unprocessed) > 1 else ''}..")
        documents = loader.load_files(set(unprocessed))

        output_dir = Path(TMP_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        for corpus_file, document in zip(corpus_files, documents):
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
        logger.info("Corpus files are up to date.")


def post_query(question: str, top_k):
    embedding = embedder.embed([question])
    chunks = vector_db.similarity_search(embedding, top_k)[0]

    # for item in chunks:
    #     print(f"ID: {item['id']}, Text: {item['text']}, Distance: {item['distance']:.4f}")

    user_prompt = _build_user_prompt(question, chunks)
    _ = chat_client.chat([
        {
            "role": "system",
            "content": [{"text": SYSTEM_PROMPT_SINGLE_RESPONSE_DESCRIBER}],
        },
        {
            "role": "user",
            "content": [{"text": user_prompt}]
        }
    ], stream=True)


def _build_user_prompt(question: str, chunks: list[dict]) -> str:
    context_blocks = []

    for chunk in chunks:
        metadata = chunk["metadata"]
        context_blocks.append(
            f"[file:{metadata['document_id']} | chunk_index:{metadata['chunk_index']}]\n{chunk['text']}"
        )

    context = "\n\n---\n\n".join(context_blocks)

    prompt = f"Context:\n{context}\n\nQuestion:\n{question}"
    return prompt
