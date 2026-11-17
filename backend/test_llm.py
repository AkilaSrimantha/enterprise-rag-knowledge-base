import os
import time
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

from google import genai

client = genai.Client(api_key=api_key)

print("Testing 'gemini-3.1-flash-lite'...")
t0 = time.time()
try:
    resp = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents="You are an assistant. Question: What is the company name? Context: Founded in 2020, CodeXpress IT Solution is based in Sri Lanka."
    )
    print(f"-> SUCCESS in {time.time()-t0:.2f}s!\nResponse: {resp.text.strip()}")
except Exception as e:
    print(f"-> FAILED: {e}")
