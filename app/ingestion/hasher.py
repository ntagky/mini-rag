import hashlib


def hash_content(content: str):
    hasher = hashlib.sha256()
    hasher.update(content.encode())
    return hasher.hexdigest()
