# Template for loading environment variables
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Get Gemini API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not set in .env file. Please add your API key to the .env file."
    )

# Configure Gemini with the API key
genai.configure(api_key=GEMINI_API_KEY)

# Example usage:
# model = genai.GenerativeModel("gemini-2.5-pro")
# response = model.generate_content("Your prompt here")
