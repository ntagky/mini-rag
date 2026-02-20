from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router
from app.api.ui_handler import setup_ui

app = FastAPI(title="MiniRAG", version="1.0")

app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# UI serving with middleware and static files
setup_ui(app)
