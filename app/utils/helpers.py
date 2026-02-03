from time import sleep


def stream_print(text: str, delay=0.05):
    """
    Print text word by word with a small delay to simulate streaming output.

    Args:
        text (str): Text to print.
        delay (float, optional): Time in seconds to wait between words. Defaults to 0.05.
    """
    for word in text.split(" "):
        print(word, end=" ", flush=True)
        sleep(delay)
    print()
