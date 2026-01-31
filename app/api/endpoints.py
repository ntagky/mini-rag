from typing import List
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal
from ..config.logger import get_logger
from ..orchestrator.pipeline import post_query
from ..model.chat_client import LlmModel, ChatMessage, ChatContent, DEFAULT_LLM_MODEL

logger = get_logger("mini-rag." + __name__)

router = APIRouter()


class QueryRequestMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class QueryRequest(BaseModel):
    messages: List[QueryRequestMessage]
    model: str


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/api/v1/models")
def get_models():
    return [model.value for model in LlmModel]


@router.post("/api/v1/chat")
async def query(request: QueryRequest):
    model = LlmModel(request.model) if LlmModel.has_value(request.model) else DEFAULT_LLM_MODEL
    if len(request.messages) == 1:
        question = request.messages[0].content
        response = post_query(question=question, messages=[], top_k=-1, model=model)
    else:
        messages = [ChatMessage(role=message.role, content=[ChatContent(text=message.content)]) for message in request.messages]
        response = post_query(question=request.messages[-1].content, messages=messages, top_k=-1, model=model)

    return {"response": response}
