from app.config.configer import WELCOMING_MESSAGE_LOGO
from app.orchestrator.pipeline import ingest_corpus, post_query
from app.config.logger import setup_logging, get_logger

setup_logging()
logger = get_logger("mini-rag." + __name__)


def runner():
    logger.info(WELCOMING_MESSAGE_LOGO)
    logger.info("")
    logger.info("Commands:")
    logger.info("  ingest [--reset] → scan and ingest corpus")
    logger.info("  query <your question> [--top-k N] → ask a question over corpus")
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
                logger.info(f"Ingesting corpus{' after erasing current data' if reset else ''}...")
                ingest_corpus(reset=reset)
                continue

            # Parse /query command
            if user_input.startswith("query"):
                # Split on space after command
                parts = user_input.split()
                if len(parts) < 2:
                    logger.info("Error: query requires a question.")
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
                logger.debug(f"Running query: {question} with top_k={top_k}...")
                post_query(question=question, top_k=top_k)
                continue

            # Unknown command
            logger.info("Unknown command. Available: ingest, query, exit")

        except KeyboardInterrupt:
            logger.warning("\nInterrupted! Type exit to exit.")
        except Exception as e:
            logger.error(f"Error: {e}")
