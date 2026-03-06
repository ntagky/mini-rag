from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from app.config.logger import get_logger

logger = get_logger("mini-rag." + __name__)


class CleanURLMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, frontend_path: Path):
        super().__init__(app)
        self.frontend_path = frontend_path

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Check if the request is for a URL with no extension
        if request.method in ["GET", "HEAD"] and "." not in path.split("/")[-1]:
            relative_path = path.lstrip("/")
            if relative_path:
                full_path = self.frontend_path / f"{relative_path}.html"
                if full_path.is_file():
                    return FileResponse(full_path)

        return await call_next(request)


def setup_ui(app: FastAPI, directory: str = "frontend/out"):
    frontend_path = Path(directory)

    if not frontend_path.exists():
        logger.warning(f"Frontend directory '{directory}' not found.")
        return

    # Add the middleware to handle .html aliasing
    app.add_middleware(CleanURLMiddleware, frontend_path=frontend_path)

    # Mount the static files
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="ui")
