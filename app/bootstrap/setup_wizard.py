import os
from pathlib import Path
from getpass import getpass
from dotenv import load_dotenv
from app.config.logger import get_logger

logger = get_logger("mini-rag." + __name__)

load_dotenv()
ENV_FILE = Path(".env")


def prompt_with_default(prompt: str, default: str | None):
    if default:
        user_input = input(f"{prompt} [{default}] (press Enter to keep): ").strip()

        return user_input if user_input else default

    return input(f"{prompt}: ").strip()


def prompt_secret(prompt: str, default: str | None):
    """
    Do not echo secrets to the terminal.
    """
    if default:
        print(f"{prompt} [EXISTS] (press Enter to keep)", end="", flush=True)
        user_input = getpass(": ").strip()

        return user_input if user_input else default

    return getpass(f"{prompt}: ").strip()


def run_setup():
    logger.info("🔧 MiniRAG Environment Setup\n")

    existing_env = dict(os.environ)

    openai_key = prompt_secret(
        "OPENAI_API_KEY",
        existing_env.get("OPENAI_API_KEY"),
    )

    es_url = prompt_with_default(
        "ELASTICSEARCH_URL",
        existing_env.get("ELASTICSEARCH_URL"),
    )

    ollama_url = prompt_with_default(
        "OLLAMA_URL",
        existing_env.get("OLLAMA_URL"),
    )

    # Preserve unknown keys
    required_env = dict()
    required_env["OPENAI_API_KEY"] = openai_key
    required_env["ELASTICSEARCH_URL"] = es_url
    required_env["OLLAMA_URL"] = ollama_url

    content = "\n".join(f"{k}={v}" for k, v in required_env.items())

    ENV_FILE.write_text(content + "\n")

    load_dotenv()
