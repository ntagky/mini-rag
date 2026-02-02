from app.model.chat_client import ChatClient, LlmModel, ChatMessage, ChatContent
from app.agent.rag_agent import RAGAgent
from app.retrieval.embedder import Embedder, EmbedderModel
from app.retrieval.indexer import ElasticsearchIndex
from app.retrieval.ranker import TfidfRetriever
from app.config.configer import OPENAI_EMBEDDING_DIMENSIONS
from app.orchestrator.pipeline import Orchestrator

embedder = Embedder(EmbedderModel.OPENAI)
elastic_index = ElasticsearchIndex(embedding_dim=OPENAI_EMBEDDING_DIMENSIONS)
tfidf_retriever = TfidfRetriever()
chat_client = ChatClient(LlmModel.OPENAI)


def test_agent_quicker():
    agent = RAGAgent(
        embedder=embedder,
        retriever=elastic_index,
        fallback_retriever=tfidf_retriever,
        chat_client=chat_client,
        is_cli=True,
    )
    question = "hello"
    messages = [ChatMessage(role="user", content=[ChatContent(text=question)])]
    response = agent.run(question, messages, 3)
    assert response.citations == []


def test_agent_cite_1():
    agent = RAGAgent(
        embedder=embedder,
        retriever=elastic_index,
        fallback_retriever=tfidf_retriever,
        chat_client=chat_client,
        is_cli=True,
    )
    question = "In what specific clinical scenarios is a randomized withdrawal study design most effective for determining long-term efficacy and treatment duration?"
    messages = [ChatMessage(role="user", content=[ChatContent(text=question)])]
    response = agent.run(question, messages, 3)
    assert any([cite.startswith("E10") for cite in response.citations])


def test_agent_cite_2():
    agent = RAGAgent(
        embedder=embedder,
        retriever=elastic_index,
        fallback_retriever=tfidf_retriever,
        chat_client=chat_client,
        is_cli=True,
    )
    question = "Who must be listed as contacts in the consent document, and why does the FDA recommend a separate contact for questions regarding subjects rights?"
    messages = [ChatMessage(role="user", content=[ChatContent(text=question)])]
    response = agent.run(question, messages, 3)
    assert any([cite.startswith("ICD") for cite in response.citations])


def test_agent_chat():
    agent = RAGAgent(
        embedder=embedder,
        retriever=elastic_index,
        fallback_retriever=tfidf_retriever,
        chat_client=chat_client,
        is_cli=True,
    )
    question = "Okay, thank you. Bye!"
    messages = [
        ChatMessage(role="user", content=[ChatContent(text="Hello")]),
        ChatMessage(
            role="assistant", content=[ChatContent(text="Hi, how can I help you?")]
        ),
        ChatMessage(
            role="user",
            content=[
                ChatContent(
                    text="Who should I contact if I cannot identify the appropriate FDA staff?"
                )
            ],
        ),
        ChatMessage(
            role="assistant",
            content=[
                ChatContent(
                    text="If you cannot identify the appropriate FDA staff, call the appropriate number listed on the title page of the guidance. Contact numbers include: - Office of Communications Division of Drug Information, CDER"
                )
            ],
        ),
        ChatMessage(role="user", content=[ChatContent(text=question)]),
    ]
    response = agent.run(question, messages, 3)
    assert response.citations == []


def test_orchestrator_ingestor():
    orchestrator = Orchestrator()
    ingest_files = orchestrator.ingest_corpus(reset=True)
    assert ingest_files > 0
