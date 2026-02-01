from time import sleep


def stream_print(text: str, delay=0.05):
    for word in text.split(" "):
        print(word, end=" ", flush=True)
        sleep(delay)
    print()
