from fastapi import APIRouter
from app.api.dto import QueryRequest
from app.config.logger import get_logger
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


@router.post("/api/v1/ingest")
def ingest_files(reset: bool = False):
    """
    Ingests unprocessed corpus.

    Returns:
        int: Number of new documents ingested.
    """
    return orchestrator.ingest_corpus(reset=reset)


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
