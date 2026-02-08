import os
from dotenv import load_dotenv

load_dotenv()

REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",
    "ELASTICSEARCH_URL",
    "OLLAMA_URL",
]


def validate_env() -> tuple[bool, list[str]]:
    """
    Validates that the .env file exists and contains required variables.
    Returns:
        (is_valid, missing_vars)
    """
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]

    return len(missing) == 0, missing
