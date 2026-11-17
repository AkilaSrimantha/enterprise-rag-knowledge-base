import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

from google import genai

client = genai.Client(api_key=api_key)

print("Scanning all working generation models for your account...")

results = []
try:
    for m in client.models.list():
        # Get clean model name
        m_name = m.name.replace("models/", "")
        
        # Test generation with 1 token
        try:
            resp = client.models.generate_content(
                model=m_name,
                contents="OK"
            )
            txt = resp.text.strip() if resp and resp.text else "Empty"
            print(f"[WORKING] -> '{m_name}': {txt}")
            results.append(m_name)
        except Exception as e:
            err = str(e)
            if "503" in err:
                print(f"[503 Overloaded] -> '{m_name}'")
            elif "404" in err:
                pass # skip obsolete
            else:
                print(f"[Failed] -> '{m_name}': {err[:60]}")
except Exception as e:
    print(f"Error listing models: {e}")

print(f"\nSummary of WORKING models: {results}")
