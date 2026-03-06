import argparse
from app.config.logger import setup_logging, get_logger
from app.bootstrap.env_validator import validate_env
from app.bootstrap.setup_wizard import run_setup


setup_logging()
logger = get_logger("mini-rag." + __name__)


def main():
    """
    Parse the interface mode argument and start either the CLI runner or the FastAPI server.
    """
    parser = argparse.ArgumentParser(description="MiniRAG: choose interface mode")
    parser.add_argument(
        "mode",
        choices=["cli", "api", "setup"],
        help="Interface mode: CLI REPL or FastAPI server",
    )
    args = parser.parse_args()

    if args.mode == "setup":
        run_setup()
    else:
        is_valid, _ = validate_env()
        if not is_valid:
            run_setup()

    if args.mode == "cli":
        from app.cli.console import runner

        runner()
    elif args.mode == "api":
        from app.api.server import app
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
