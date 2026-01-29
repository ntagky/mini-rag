import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# APP METADATA
APP_NAME = "MiniRag"
with open("logo.txt", "r", encoding="utf-8") as file:
    text = file.read()
WELCOMING_MESSAGE_LOGO = text if text else APP_NAME

# STORAGE ATTRIBUTES
BASE_DIR = Path(__file__).resolve().parent.parent
CORPUS_DIR = Path("data/corpus/unprocessed")
MARKDOWN_DIR = Path("data/markdowns")
TMP_DIR = Path(".tmp")
LOG_DIR = Path(".logs")

# MODELS
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OLLAMA_BASE_URL = "http://localhost:11434"
SENTENCE_TRANSFORMER_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH = ".local_models/sentence-transformers/all-MiniLM-L6-v2"

# PROMPTS

SYSTEM_PROMPT_IMAGE_DESCRIBER = """
You are a technical vision model.
Your task is to describe what is visually present in the image.
Rules:
- Describe the image contents directly, as if transcribing what is visible
- Include labels, captions, tables, and any text visible in the image inline
- In case of diagram, explain also the flow
- Do NOT add introductions, conclusions, section headers, or separators
- Do NOT explain what you are doing
- Do NOT say phrases like: "The image shows", "This image depicts", "Text extracted from the image", "End of extracted text"
- Do NOT add summaries, interpretations, assumptions, or commentary
- Do NOT add greetings or sign-offs
- Output plain text only
"""

USER_PROMPT_IMAGE_DESCRIBER = """
Describe the image with words.
"""

SYSTEM_PROMPT_SINGLE_RESPONSE_DESCRIBER = """
You are a retrieval-augmented question answering assistant.
Answer ONLY using the provided context.
If the answer is not in the context, say "I don't know".

Rules:
- No introductions
- No explanations outside the answer
- Cite sources using [file:page:chunk_id]
- Be concise and factual
"""
