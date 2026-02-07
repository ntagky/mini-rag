import uuid
from typing import List
from pathlib import Path
from app.config.configer import TMP_IMAGES_DIR, OPENAI_EMBEDDING_DIMENSIONS
from app.agent.rag_agent import RAGAgent, AgentResult
from app.ingestion.chunker import Chunker
from app.ingestion.loader import CorpusLoader
from app.retrieval.embedder import Embedder, EmbedderModel
from app.retrieval.indexer import ElasticsearchIndex, ChunkMetadata, DocumentChunk
from app.retrieval.persistor import SqliteDb, File
from app.model.chat_client import (
    ChatClient,
    LlmModel,
    ChatMessage,
    ChatContent,
    DEFAULT_LLM_MODEL,
)
from app.config.logger import get_logger
from app.retrieval.ranker import TfidfRank, TfidfRetriever
from app.config.model_loader import load_embedding_model


logger = get_logger("mini-rag." + __name__)


class Orchestrator:
    load_embedding_model()
    chunker = Chunker()
    embedder = Embedder(EmbedderModel.OPENAI)
    elastic_index = ElasticsearchIndex(embedding_dim=OPENAI_EMBEDDING_DIMENSIONS)
    sql_db = SqliteDb()
    tfidf_rank = TfidfRank()
    chat_client = {
        LlmModel.OPENAI.value: ChatClient(LlmModel.OPENAI),
        LlmModel.OLLAMA.value: ChatClient(LlmModel.OLLAMA),
    }
    loader = CorpusLoader(chat_client[LlmModel.OPENAI.value])

    def ingest_corpus(self, reset: bool = False) -> int:
        """
        Ingest corpus files into the retrieval system.

        Args:
            reset (bool): If True, clears existing indexes, database records, and cached data before ingestion.

        Returns:
            int: Number of newly ingested files.
        """
        if reset:
            self.elastic_index.reset()
            self.sql_db.reset()
            self.loader.reset()

        ingested_files = self.sql_db.read_all_files()
        corpus_files = self.loader.scan_corpus_dir()

        unprocessed = self.loader.get_unprocessed_files(corpus_files, ingested_files)

        if len(unprocessed):
            logger.debug(
                f"Found {len(unprocessed)} unprocessed file{'s' if len(unprocessed) > 1 else ''}.."
            )
            documents = self.loader.load_files(set(unprocessed))

            output_dir = Path(TMP_IMAGES_DIR)
            output_dir.mkdir(parents=True, exist_ok=True)
            for corpus_file, document in zip(corpus_files, documents):
                chunks, pages = self.chunker.chunk(document)
                embeddings = self.embedder.embed(chunks)

                document_entries = [
                    DocumentChunk(
                        str(uuid.uuid4()),
                        chunks[i],
                        embeddings[i],
                        ChunkMetadata(
                            document_id=document.origin.filename,
                            page=pages[i],
                            chunk_index=i,
                            source="markdown",
                        ),
                    )
                    for i in range(len(chunks))
                ]

                self.sql_db.create_file(
                    File(
                        id=uuid.uuid4(),
                        filename=corpus_file.filename,
                        path=corpus_file.path,
                        hash=corpus_file.hash,
                        page_count=corpus_file.pages,
                        chunk_count=len(chunks),
                    )
                )
                self.elastic_index.add_items(document_entries)

            # Recompute TF-IDF matrix
            chunked_data = self.elastic_index.retrieve_all()
            self.tfidf_rank.build(chunked_data)
            return len(unprocessed)
        else:
            logger.info("Corpus files are up to date.")
            return 0

    def post_query(
        self,
        question: str,
        messages: List[ChatMessage] = [],
        top_k: int = -1,
        model: LlmModel = DEFAULT_LLM_MODEL,
        is_cli: bool = False,
    ):
        """
        Run a RAG query using the specified language model and retrieval strategy.

        Args:
            question (str): User question to be answered.
            messages (List[ChatMessage], optional): Conversation history for contextual responses.
            top_k (int, optional): Number of top retrieval results to consider. Defaults to -1.
            model (LlmModel, optional): Language model used for generation.
            is_cli (bool, optional): Whether the request originates from the CLI.

        Returns:
            Tuple[str, List]: Generated answer and its associated citations.
        """
        # Create a message chain if its empty
        if len(messages) == 0:
            messages = [ChatMessage(role="user", content=[ChatContent(text=question)])]

        # Setup agent with dependency injection and trigger it
        agent = RAGAgent(
            self.embedder,
            self.elastic_index,
            TfidfRetriever(),
            self.chat_client[model.value],
            is_cli,
        )
        result: AgentResult = agent.run(question, messages, top_k)

        return result.answer, result.citations
