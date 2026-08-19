import os
from dotenv import load_dotenv

# Load variables from .env into the environment
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found. Please create a .env file in the project "
        "root with: GROQ_API_KEY=your_key_here"
    )

GROQ_MODEL_NAME = "openai/gpt-oss-120b"