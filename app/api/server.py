from fastapi import FastAPI
from .endpoints import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MiniRAG", version="1.0")

app.include_router(router)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
