from server import app
from typing import Optional
from pydantic import BaseModel
from fastapi import HTTPException


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5


class IngestRequest(BaseModel):
    rescan: Optional[bool] = False


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query")
def query_endpoint(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        # Call the same run_query pipeline as CLI
        # result = run_query(
        #     question=request.question,
        #     top_k=request.top_k
        # )
        return {"answer": "result"}  # result can include text + citations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest")
def ingest_endpoint(request: IngestRequest):
    try:
        # ingest_corpus(rescan=request.rescan)
        return {"status": "ingestion completed", "rescan": request.rescan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
