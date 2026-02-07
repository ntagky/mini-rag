import os
from openai import OpenAI
from typing import Tuple, Dict
from elasticsearch import Elasticsearch
from app.bootstrap.env_validator import validate_env
from openai import AuthenticationError, APIConnectionError
from elastic_transport import ConnectionError as ESConnectionError


def validate_openai() -> tuple[bool, str]:
    """
    Perform a real ping to OpenAI using a minimal token request.
    """

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        client.models.list()

        return True, "OpenAI connectivity OK"

    except AuthenticationError:
        return False, "Invalid OPENAI_API_KEY"

    except APIConnectionError:
        return False, "Cannot reach OpenAI API (network issue?)"

    except Exception as e:
        return False, f"OpenAI error: {str(e)}"


def validate_elasticsearch() -> tuple[bool, str]:
    """
    Ping Elasticsearch without creating indices.
    """

    try:
        es = Elasticsearch(os.getenv("ELASTICSEARCH_URL"))

        if es.ping():
            return True, "Elasticsearch reachable"

        return False, "Elasticsearch did not respond to ping"

    except ESConnectionError:
        return False, "Cannot connect to Elasticsearch"

    except Exception as e:
        return False, f"Elasticsearch error: {str(e)}"


def full_environment_validation() -> Tuple[bool, Dict]:
    """
    Perform full environment validation:
    - .env existence
    - required variables
    - OpenAI connectivity
    - Elasticsearch connectivity
    """

    ok, missing = validate_env()

    if not ok:
        return False, {
            "type": "env",
            "missing": missing,
        }

    checks = []

    openai_ok, openai_msg = validate_openai()
    checks.append({"service": "OpenAI", "status": openai_ok, "message": openai_msg})

    es_ok, es_msg = validate_elasticsearch()
    checks.append({"service": "Elasticsearch", "status": es_ok, "message": es_msg})

    all_ok = all(ok for _, ok, _ in checks)

    return all_ok, {
        "status": all_ok,
        "checks": checks,
    }
