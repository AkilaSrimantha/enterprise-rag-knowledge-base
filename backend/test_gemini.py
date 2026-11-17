import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print(f"Testing GEMINI_API_KEY: {api_key[:10]}...{api_key[-5:] if api_key else ''}\n")

if not api_key:
    print("ERROR: GEMINI_API_KEY is not set in backend/.env!")
    exit(1)

genai.configure(api_key=api_key)

print("1. Fetching available models for this key...")
try:
    models = list(genai.list_models())
    print(f"-> Total models found: {len(models)}\n")

    embed_models = [m.name for m in models if "embedContent" in m.supported_generation_methods]
    print("2. Models supporting 'embedContent' (Embeddings):")
    if embed_models:
        for m in embed_models:
            print(f"   * {m}")
    else:
        print("   [NONE FOUND! Your key or project does not have Generative Language API embedding access]")

    print("\n3. Models supporting 'generateContent' (Chat / LLM):")
    gen_models = [m.name for m in models if "generateContent" in m.supported_generation_methods]
    for m in gen_models[:5]:
        print(f"   * {m}")

    if embed_models:
        chosen = embed_models[0]
        print(f"\n4. Testing embedding generation with '{chosen}'...")
        res = genai.embed_content(model=chosen, content="Test embedding")
        print(f"-> SUCCESS! Generated vector with dimension: {len(res['embedding'])}")
    else:
        print("\n4. Cannot test embedding because no embedding model is enabled for this API key.")

except Exception as exc:
    print(f"\nERROR from Google Gemini API:\n{exc}")
