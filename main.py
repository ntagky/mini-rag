import argparse
from app.cli.console import runner
from app.api.server import app
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Mini-RAG: choose interface mode")
    parser.add_argument(
        "mode",
        choices=["cli", "api"],
        help="Interface mode: CLI REPL or FastAPI server",
    )
    args = parser.parse_args()

    if args.mode == "cli":
        runner()
    elif args.mode == "api":
        uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
