from app.config.configer import WELCOMING_MESSAGE_LOGO
from app.orchestrator.pipeline import ingest_corpus, post_query
from app.config.logger import setup_logging, get_logger
from app.model.chat_client import LlmModel, DEFAULT_LLM_MODEL

setup_logging()
logger = get_logger("mini-rag." + __name__)


def runner():
    logger.info(WELCOMING_MESSAGE_LOGO)
    logger.info("")
    logger.info("Commands:")
    logger.info(f"  ingest [--reset] → scan and ingest corpus")
    logger.info(f"  query <your question> [--top-k N] [--model {'|'.join([e.value for e in LlmModel])}] → ask a question over corpus")
    logger.info("  exit → quit session")

    while True:
        try:
            user_input = input("\n> ").strip()
            if not user_input:
                continue

            # Exit condition
            if user_input.lower() == "exit":
                break

            # Parse /ingest command
            if user_input.startswith("ingest"):
                reset = "--reset" in user_input
                logger.debug(f"Ingesting corpus{' after erasing current data' if reset else ''}...")
                ingest_corpus(reset=reset)
                continue

            # Parse /query command
            if user_input.startswith("query"):
                # Split on space after command
                parts = user_input.split()
                if len(parts) < 2:
                    logger.info("Error: query requires a question.")
                    continue

                # Extract model if specified
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
                        logger.debug("Error: --model does not exist, moving with default")
                        continue

                # Extract top-k if specified
                top_k = 5  # default
                if "--top-k" in parts:
                    idx = parts.index("--top-k")
                    try:
                        top_k = int(parts[idx + 1])
                        # Remove from parts
                        parts.pop(idx)
                        parts.pop(idx)  # remove the number too
                    except (IndexError, ValueError):
                        logger.info("Error: --top-k requires an integer")
                        continue

                # Post question
                question = " ".join(parts[1:])
                logger.debug(f"Running query: '{question}' with top_k={top_k} and model={model.value}...")
                post_query(question=question, top_k=top_k, model=model)
                continue

            # Unknown command
            logger.info("Unknown command. Available: ingest, query, exit")

        except KeyboardInterrupt:
            logger.warning("\nInterrupted! Type exit to exit.")
        except Exception as e:
            logger.error(f"Error: {e}")
