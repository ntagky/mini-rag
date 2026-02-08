import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

# APP METADATA
APP_NAME = "MiniRAG"
with open(".assets/logo.txt", "r", encoding="utf-8") as file:
    text = file.read()
WELCOMING_MESSAGE_LOGO = text if text else APP_NAME

# STORAGE ATTRIBUTES
CORPUS_DIR = Path("documents/")
TMP_DOCUMENTS_DIR = Path(".tmp/documents")
os.makedirs(TMP_DOCUMENTS_DIR, exist_ok=True)
TMP_IMAGES_DIR = Path(".tmp/images")
os.makedirs(TMP_IMAGES_DIR, exist_ok=True)
LOG_DIR = Path(".logs")
os.makedirs(LOG_DIR, exist_ok=True)

# DATABASE STORAGE
DB_DIR = Path(".db")
os.makedirs(DB_DIR, exist_ok=True)
SQLITE_DIR = Path(".db/sqlite")
TFIDF_DIR = Path(".db/tfidf")

# MODELS
SENTENCE_TRANSFORMER_MODEL_NAME = "BAAI/bge-base-en-v1.5"
SENTENCE_TRANSFORMER_DIMENSIONS = 384
OFFLINE_SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH = ".models/BAAI/bge-base-en-v1.5"
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
If the answer is not in the context, ask the user for the specific information or clarification needed to answer accurately.

Rules:
- No introductions
- No explanations outside the answer
- Always include file citations, using only this format: cite=[filename+3,4,10 | filename+66,98,99].
If one source has multiple page references, combine to one entry placing pages next to each other next to the '+' sign.
- Be concise and factual
"""

SYSTEM_PROMPT_PLANNER = """
You are a reasoning agent planner for a RAG system.
Your job is to generate a JSON object containing all the configurable plan options for answering a user's question.
Do not add explanations, text, or comments.
Only output valid JSON.
"""

SYSTEM_PROMPT_REWRITER = """
You are a query rewriting assistant for a retrieval system.
Given the user's current question and up to three previous user questions, decide whether rewriting is necessary.
If the current question is already clear and self-contained, return it unchanged.
If context from previous questions is required, rewrite the question into a single, clear, self-contained query optimized for semantic search.
Rules:
- Use only relevant prior questions.
- Do NOT add new information.
- Do NOT explain your reasoning.
- Output only the rewritten question as plain text.
"""

USER_PROMPT_PLANNER = """
You are a planner for a Retrieval-Augmented Generation (RAG) agent.

Generate ONLY a valid JSON object describing the execution plan.
Do not include explanations, markdown, comments, or any text outside the JSON.

Use ONLY the step names and fields defined below.
Never invent new step names or fields.
Prefer the minimum number of steps required to answer the question.

SPECIAL RULE:
If the question is a greeting, gratitude, or capability question,
return ONLY the "answer" step and do not include any other steps.

REWRITE RULES:
Only include the rewrite step when the question:
- depends on prior conversation
- is ambiguous
- is too short
- would benefit from semantic expansion for better embedding retrieval

Otherwise, skip rewriting.

RETRIEVAL RULES:
Include the retrieve step for knowledge-based questions.
Skip retrieval only when the answer is trivial or conversational.

DRAFT RULES:
Include the draft step whenever retrieval is used.
Use:
- "concise" for direct factual answers
- "detailed" for complex or technical explanations
- "explain_reasoning" only when the user explicitly asks for reasoning

KEYWORDS:
Generate up to 3 short keywords for analytics.

Return a JSON object with this exact structure:

{
    "steps": [
        { "name": "answer", "response": "..." },
        { "name": "rewrite", "style": "standalone | expand | disambiguate" },
        {
            "name": "retrieve",
            "strategy": "vector_only | tfidf_fallback | vector+tfidf_fallback",
            "top_k": 1 | 3 | 5 | 10 | 20,
            "fallback_threshold": 0.0 | 0.1 | 0.25 | 0.5
        },
        { "name": "draft", "style": "concise | detailed | explain_reasoning" }
    ],
    "keywords": ["strings"]
}

Do not include trailing commas.

Question:
"""

# RETRIEVAL STRATEGY
MIN_SCORE_THRESHOLD = 0.5
