from app.config.configer import WELCOMING_MESSAGE_LOGO


def runner():
    print(WELCOMING_MESSAGE_LOGO)
    print()
    print("Commands:")
    print("  /ingest [--rescan]   → scan and ingest corpus")
    print("  /query <your question> [--top-k N] → ask a question over corpus")
    print("  /bye → quit session")

    while True:
        try:
            user_input = input("\n> ").strip()
            if not user_input:
                continue

            # Exit condition
            if user_input.lower() == "/bye":
                print("Goodbye!")
                break

            # Parse /ingest command
            if user_input.startswith("/ingest"):
                rescan = "--rescan" in user_input
                print(f"Ingesting corpus (rescan={rescan})...")
                # ingest_corpus(rescan=rescan)
                continue

            # Parse /query command
            if user_input.startswith("/query"):
                # Split on space after command
                parts = user_input.split()
                if len(parts) < 2:
                    print("Error: /query requires a question.")
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
                        print("Error: --top-k requires an integer")
                        continue

                question = " ".join(parts[1:])
                print(f"Running query: {question} (top_k={top_k})...")
                # run_query(question=question, top_k=top_k)
                continue

            # Unknown command
            print("Unknown command. Available: /ingest, /query, /bye")

        except KeyboardInterrupt:
            print("\nInterrupted! Type /bye to exit.")
        except Exception as e:
            print(f"Error: {e}")
