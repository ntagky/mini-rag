from fastapi import APIRouter, UploadFile, File, HTTPException
from app.api.dto import QueryRequest
from app.config.logger import get_logger
from app.config.configer import CORPUS_DIR
from app.retrieval.persistor import SqliteDb
from app.model.chat_client import ChatClient
from app.ingestion.loader import CorpusLoader
from app.orchestrator.pipeline import Orchestrator
from app.bootstrap.health_checks import full_environment_validation
from app.model.chat_client import LlmModel, ChatMessage, ChatContent, DEFAULT_LLM_MODEL

logger = get_logger("mini-rag." + __name__)

router = APIRouter()
orchestrator = Orchestrator()


@router.get("/health")
def health():
    """
    Health check endpoint to verify that the API and its external dependencies are running.

    Returns:
        dict: Status of the service, e.g., {"status": "ok"}.
    """

    is_valid, results = full_environment_validation()
    return results


@router.get("/api/v1/models")
def get_models():
    """
    Retrieve a list of available LLM models.

    Returns:
        List[str]: List of model names as strings.
    """
    return [model.value for model in LlmModel]


@router.get("/api/v1/documents")
def get_documents():
    """
    Get documents from corpus

    Returns:
        dict: Ingested files with metadata and a list of unprocessed filenames
    """
    sqldb = SqliteDb()
    ingested_files = sqldb.read_all_files()
    loader = CorpusLoader(ChatClient())
    corpus_files = loader.scan_corpus_dir()
    unprocessed_files = loader.get_unprocessed_files(corpus_files, ingested_files)
    return {
        "ingested_files": ingested_files,
        "unprocessed_filenames": [file.filename for file in unprocessed_files],
    }


@router.post("/api/v1/ingest")
def ingest_files(reset: bool = False):
    """
    Ingests unprocessed corpus.

    Returns:
        int: Number of new documents ingested.
    """
    return orchestrator.ingest_corpus(reset=reset)


@router.get("/api/v1/ingestion-status")
def get_ingestion_status():
    """
    Get ingestion status with a boolean attribute.

    Returns:
        bool: Whether ingestion has finished or not
    """
    sqldb = SqliteDb()
    return sqldb.read_ingestion_control()


@router.post("/api/v1/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    file_path = CORPUS_DIR / file.filename

    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"filename": file.filename}


@router.post("/api/v1/chat")
async def query(request: QueryRequest):
    """
    Handle a chat query request via POST, routing it to the orchestrator.

    Args:
        request (QueryRequest): The request payload containing messages and the model.

    Returns:
        dict: Contains the LLM response text and any citations, e.g. {"content": "<response>", "citations": [...]}
    """
    model = (
        LlmModel(request.model)
        if LlmModel.has_value(request.model)
        else DEFAULT_LLM_MODEL
    )
    if len(request.messages) == 1:
        question = request.messages[0].content
        response, citations = orchestrator.post_query(question=question, model=model)
    else:
        messages = [
            ChatMessage(role=message.role, content=[ChatContent(text=message.content)])
            for message in request.messages
        ]
        response, citations = orchestrator.post_query(
            question=request.messages[-1].content,
            messages=messages,
            model=model,
        )

    return {"content": response, "citations": citations}
