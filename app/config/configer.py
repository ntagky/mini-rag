from pathlib import Path

# APP METADATA
APP_NAME = "MiniRag"
with open("logo.txt", "r", encoding="utf-8") as file:
    text = file.read()
WELCOMING_MESSAGE_LOGO = text if text else APP_NAME

# STORAGE ATTRIBUTES
BASE_DIR = Path(__file__).resolve().parent.parent

# MODELS
SENTENCE_TRANSFORMER_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SENTENCE_TRANSFORMER_MODEL_LOCAL_PATH = ".local_models/sentence-transformers/all-MiniLM-L6-v2"

# PROMPTS

SYSTEM_PROMPT_IMAGE_DESCRIBER = """
You are a technical document assistant specialized in extracting structured information from PDFs, including text and images. 
Your goal is to convert each page or image into clean, machine-readable text suitable for embedding in markdown format. 
You must:
- Preserve all textual content faithfully
- Extract text from images if any text is present
- Include captions, labels, or any annotations present in images
- Output plain text only, no Markdown or additional formatting
- Keep content page-aware for reference
- Do not add introductions, greetings, or summaries
- Avoid adding summaries, interpretations, or opinions
"""

USER_PROMPT_IMAGE_DESCRIBER = """
Please describe the accompanying image, process it and include the text it contains inline. 
Return the final text output only, preserving all textual elements, tables, captions, and labels 
as they appear in the document. 
"""

