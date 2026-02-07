from pathlib import Path
from dotenv import dotenv_values

REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",
    "ELASTICSEARCH_URL",
]


def validate_env() -> tuple[bool, list[str]]:
    """
    Validates that the .env file exists and contains required variables.
    Returns:
        (is_valid, missing_vars)
    """
    env_path = Path(".env")

    if not env_path.exists():
        return False, REQUIRED_ENV_VARS

    env_vars = dotenv_values(env_path)

    missing = [var for var in REQUIRED_ENV_VARS if not env_vars.get(var)]

    return len(missing) == 0, missing
