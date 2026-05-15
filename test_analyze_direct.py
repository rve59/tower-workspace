import os
from google import genai
from dotenv import load_dotenv

load_dotenv(".env")
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_TOKEN_KEY")
client = genai.Client(api_key=api_key)
try:
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents="Hello"
    )
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {e}")
