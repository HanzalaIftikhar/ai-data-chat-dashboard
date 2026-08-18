import os
from dotenv import load_dotenv

# Load variables from .env into the environment
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. Please create a .env file in the project "
        "root with: GEMINI_API_KEY=your_key_here"
    )

GEMINI_MODEL_NAME = "gemini-flash-latest"