import uuid
from pathlib import Path
from ..config.configer import TMP_DIR, OPENAI_EMBEDDING_DIMENSIONS
from ..agent.rag_agent import RAGAgent
from ..ingestion.chunker import Chunker
from ..ingestion.loader import CorpusLoader
from ..retrieval.embedder import Embedder, EmbedderModel
from ..retrieval.indexer import ElasticsearchIndex, ChunkMetadata, DocumentChunk, DocumentChunkDistant
from ..retrieval.persistor import SqliteDb, File
from ..model.chat_client import ChatClient, LlmModel, ChatMessage, ChatContent, DEFAULT_LLM_MODEL
from ..config.logger import get_logger
from ..retrieval.ranker import TfidfRank, TfidfRetriever


logger = get_logger("mini-rag." + __name__)

chunker = Chunker()
embedder = Embedder(EmbedderModel.OPENAI)
elastic_index = ElasticsearchIndex(embedding_dim=OPENAI_EMBEDDING_DIMENSIONS)
sql_db = SqliteDb()
tfidf_rank = TfidfRank()
tfidf_retriever = TfidfRetriever()
chat_client = ChatClient(LlmModel.OPENAI)
loader = CorpusLoader(chat_client)


def ingest_corpus(reset: bool = False):
    if reset:
        elastic_index.reset()
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

            document_entries = [DocumentChunk(
                str(uuid.uuid4()),
                chunks[i],
                embeddings[i],
                ChunkMetadata(
                    document_id=document.origin.filename,
                    chunk_index=i,
                    source="markdown"
                )
            ) for i in range(len(chunks))]

            sql_db.create_file(File(
                id=uuid.uuid4(),
                filename=corpus_file.filename,
                path=corpus_file.path,
                hash=corpus_file.hash,
                page_count=corpus_file.pages,
                chunk_count=len(chunks)
            ))
            elastic_index.add_items(document_entries)

        # Recompute TF-IDF matrix
        chunked_data = elastic_index.retrieve_all()
        tfidf_rank.build(chunked_data)
    else:
        logger.info("Corpus files are up to date.")


def post_query(question: str, messages: list[ChatMessage], top_k: int, model: LlmModel = DEFAULT_LLM_MODEL, is_cli: bool = False):
    if model != DEFAULT_LLM_MODEL:
        current_chat_client = ChatClient(model.value)
    else:
        current_chat_client = chat_client

    if len(messages) == 0:
        messages = [ChatMessage(role="user", content=[ChatContent(text=question)])]

    agent = RAGAgent(embedder, elastic_index, tfidf_retriever, current_chat_client)
    plan = agent.generate_plan(question, top_k)
    if "quick_answer" in plan and plan["quick_answer"]:
        return plan["quick_answer"]
    if "query_rewriting" in plan and plan["query_rewriting"]:
        question = agent.rewrite_question(messages[:-6:-2])
    chunks = agent.retrieve_chunks(question, plan)
    last_messages = messages[-6:]
    response = agent.draft_response(last_messages, question, chunks, plan, is_cli=is_cli)
    return response
