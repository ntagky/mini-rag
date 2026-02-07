from app.config.configer import WELCOMING_MESSAGE_LOGO
from app.orchestrator.pipeline import Orchestrator
from app.config.logger import get_logger
from app.bootstrap.health_checks import full_environment_validation
from app.model.chat_client import LlmModel, DEFAULT_LLM_MODEL, ChatMessage, ChatContent

logger = get_logger("mini-rag." + __name__)


def runner():
    """
    Start the interactive CLI loop, display available commands, and route ingest, query, and chat requests.
    """
    logger.info(WELCOMING_MESSAGE_LOGO)
    logger.info("")
    logger.info("Commands:")
    logger.info("  doctor → health checks to external services")
    logger.info("  ingest [--reset] → scan and ingest corpus")
    logger.info(
        f"  query <your question> [--top-k N] [--model {'|'.join([e.value for e in LlmModel])}] → ask a question over corpus"
    )
    logger.info(
        f"  chat [--model {'|'.join([e.value for e in LlmModel])}] → initialize a conversation and chat with history"
    )
    logger.info("  exit → quit session")

    orchestrator = Orchestrator()

    while True:
        try:
            user_input = input("\n> ").strip()
            if not user_input:
                continue

            if user_input.lower() == "exit":
                break

            if user_input.startswith("doctor"):
                is_valid, results = full_environment_validation()
                logger.info(
                    f"Overall status {'healthy' if is_valid else 'unhealthy'}.\nServices:"
                )
                for check in results["checks"]:
                    logger.info(
                        f"  - {check['service']} [{'healthy' if check['status'] else 'unhealthy'}]: {check['message']}"
                    )
                continue

            # Parse /ingest command
            if user_input.startswith("ingest"):
                reset = "--reset" in user_input
                logger.debug(
                    f"Ingesting corpus{' after erasing current data' if reset else ''}..."
                )
                _ = orchestrator.ingest_corpus(reset=reset)
                continue

            # Parse /query command
            if user_input.startswith("query"):
                parts = user_input.split()
                if len(parts) < 2:
                    logger.info("Error: query requires a question.")
                    continue

                # Extract model, if specified
                model = DEFAULT_LLM_MODEL
                if "--model" in parts:
                    idx = parts.index("--model")
                    try:
                        option = parts[idx + 1]
                        if option == LlmModel.OLLAMA.value:
                            model = LlmModel.OLLAMA
                            # Remove from parts
                        parts.pop(idx)
                        parts.pop(idx)
                    except (IndexError, ValueError):
                        logger.debug(
                            "Error: --model does not exist, moving with default"
                        )
                        continue

                # Extract top-k, if specified
                top_k = 5
                if "--top-k" in parts:
                    idx = parts.index("--top-k")
                    try:
                        top_k = int(parts[idx + 1])
                        # Remove from parts
                        parts.pop(idx)
                        parts.pop(idx)
                    except (IndexError, ValueError):
                        logger.info("Error: --top-k requires an integer")

                question = " ".join(parts[1:])
                logger.debug(
                    f"Running query: '{question}' with top_k={top_k} and model={model.value}..."
                )
                orchestrator.post_query(
                    question=question,
                    top_k=top_k,
                    model=model,
                    is_cli=True,
                )
                continue

            # Parse /chat command
            if user_input.startswith("chat"):
                parts = user_input.split()

                # Extract model, if specified
                model = DEFAULT_LLM_MODEL
                if "--model" in parts:
                    idx = parts.index("--model")
                    try:
                        option = parts[idx + 1]
                        if option == LlmModel.OLLAMA.value:
                            model = LlmModel.OLLAMA
                    except (IndexError, ValueError):
                        logger.debug(
                            "Error: --model does not exist, moving with default"
                        )

                print(
                    "Chat mode activated... Type 'exit' or 'back' to return to main menu."
                )
                messages = []
                while True:
                    try:
                        user_input = input("chat|user> ").strip()
                        if not user_input:
                            continue
                        if user_input.lower() == "exit" or user_input.lower() == "back":
                            break

                        question = user_input
                        messages.append(
                            ChatMessage(
                                role="user", content=[ChatContent(text=question)]
                            )
                        )
                        logger.debug(
                            f"Running chat query: '{question}' with and model={model.value}..."
                        )
                        print("chat|assistant>", end=" ", flush=True)
                        response, _ = orchestrator.post_query(
                            question=question,
                            messages=messages,
                            top_k=-1,
                            model=model,
                            is_cli=True,
                        )
                        messages.append(
                            ChatMessage(
                                role="assistant", content=[ChatContent(text=response)]
                            )
                        )
                    except KeyboardInterrupt:
                        break
                continue

            # Unknown command
            logger.info("Unknown command. Available: ingest, query, exit")
        except KeyboardInterrupt:
            print()
            break
        except Exception as e:
            logger.error(f"Error: {e}")
