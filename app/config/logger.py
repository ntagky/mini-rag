import os
import sys
import uuid
import json
import socket
import logging
from pathlib import Path
from datetime import datetime
from platform import platform, python_version
from .configer import LOG_DIR


_RUN_ID = str(uuid.uuid4())


def get_run_id() -> str:
    return _RUN_ID


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "run_id": _RUN_ID,
            "service": "rag-cli",
            "hostname": socket.gethostname(),
            "pid": os.getpid(),
            "python_version": python_version(),
            "platform": platform(),
            "pathname": record.pathname,
            "module": record.module,
            "class": record.filename,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra"):
            log.update(record.extra)

        return json.dumps(log)


def setup_logging(log_dir: Path = LOG_DIR) -> None:
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(
        log_dir, f"rag_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)

    root = logging.getLogger("mini-rag")
    root.setLevel(logging.DEBUG)
    root.propagate = False

    # Console configuration
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    # File configuration - JSON
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JsonFormatter())

    root.addHandler(console_handler)
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
