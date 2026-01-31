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

# DATABASE STORAGE
SQLITE_DIR = Path(".db/sqlite")
TFIDF_DIR = Path(".db/tfidf")

# MODELS
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OLLAMA_BASE_URL = "http://localhost:11434"
SENTENCE_TRANSFORMER_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SENTENCE_TRANSFORMER_DIMENSIONS = 384
OFFLINE_SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH = ".models/sentence-transformers/all-MiniLM-L6-v2"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_EMBEDDING_DIMENSIONS = 512
OPENAI_COMPLETION_MODEL = "gpt-4.1-mini"
OLLAMA_CHAT_MODEL = "llava:7b"

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

SYSTEM_PROMPT_PLANNER = """
You are a reasoning agent planner for a RAG system. 
Your job is to generate a JSON object containing all the configurable plan options for answering a user's question. 
Do not add explanations, text, or comments. 
Only output valid JSON.
"""

USER_PROMPT_PLANNER = """
Generate a JSON object containing all available plan options for a RAG agent. 
Each option should have an array of possible values. 
Only output JSON. 
Do not include explanations, descriptions, or any text outside the JSON.

Pick one value from this JSON based on the following question and return the corresponding JSON:
{
  "retrieval_strategy": ["vector_only", "tfidf_fallback", "vector+tfidf_fallback"],
  "top_k": [1, 3, 5, 10, 20],
  "include_images": [true, false],
  "draft_style": ["concise", "detailed", "explain_reasoning"],
  "citation_style": ["inline", "footnotes"],
  "fallback_threshold": [0.0, 0.1, 0.25, 0.5],
  "query_rewriting": [true, false],
  "confidence_tagging": [true, false]
}
Do not include trailing commas or extra newlines.

Question: 
"""

# RETRIEVAL STRATEGY
MIN_SCORE_THRESHOLD = 0.5
