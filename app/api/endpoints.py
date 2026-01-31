from typing import List
from pydantic import BaseModel
from fastapi import HTTPException, APIRouter
from ..config.logger import get_logger
from ..orchestrator.pipeline import post_query
from ..model.chat_client import LlmModel, DEFAULT_LLM_MODEL

logger = get_logger("mini-rag." + __name__)

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class QueryRequest(BaseModel):
    messages: List[Message]
    model: str


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/api/v1/models")
def get_models():
    return [model.value for model in LlmModel]


@router.post("/api/v1/chat")
async def query(request: QueryRequest):
    # 'request.messages' is now a list of objects you can iterate through
    # 'request.model' tells you which model the user selected

    # Example logic:
    model = LlmModel(request.model).name if LlmModel.has_value(request.model) else DEFAULT_LLM_MODEL
    print(f"Using model: {request.model}")
    question = request.messages[-1].content

    post_query(question=question, top_k=-1, )

    ai_response = f"I am {request.model}. You said: {last_user_message}"

    return {"response": ai_response}