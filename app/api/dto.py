from pydantic import BaseModel
from typing import Literal, List


class QueryRequestMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class QueryRequest(BaseModel):
    messages: List[QueryRequestMessage]
    model: str
