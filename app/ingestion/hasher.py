import hashlib


def hash_content(content: str) -> str:
    """
    Compute the SHA-256 hash of a given string.

    Args:
        content (str): Input text to hash.

    Returns:
        str: Hexadecimal digest of the hash.
    """
    hasher = hashlib.sha256()
    hasher.update(content.encode())
    return hasher.hexdigest()
