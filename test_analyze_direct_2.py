import os
import time
from google import genai
from dotenv import load_dotenv

load_dotenv(".env")
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_TOKEN_KEY")
client = genai.Client(api_key=api_key)
for model in ["gemini-3.1-flash-lite-preview", "gemini-2.0-flash-lite-preview-02-05", "gemini-2.5-flash"]:
    try:
        t0 = time.time()
        print(f"Testing {model}...")
        response = client.models.generate_content(
            model=model,
            contents="Hello",
            config={"max_output_tokens": 10}
        )
        print(f"SUCCESS {model} in {time.time()-t0:.2f}s")
    except Exception as e:
        print(f"ERROR {model}: {e}")
