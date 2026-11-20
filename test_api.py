"""בדיקת חיבור ל-Groq: מריצים עם  uv run test_api.py  ומדביקים את הפלט."""
import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
key = os.environ.get("GROQ_API_KEY")
print("GROQ_API_KEY loaded:", bool(key))

client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1", timeout=20)

available = sorted(m.id for m in client.models.list().data)
print("\nModels available to this key:")
for m in available:
    print("  ", m)

preferred = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "openai/gpt-oss-20b", "llama-3.1-8b-instant"]
candidates = [m for m in preferred if m in available] or available

for model in candidates:
    print(f"\n--- trying {model} ---")
    start = time.time()
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Return ONLY a Windows CMD command."},
                {"role": "user", "content": "מה כתובת ה-IP של המחשב שלי"},
            ],
            temperature=0.0,
        )
        print(f"SUCCESS in {time.time() - start:.1f}s ->", (r.choices[0].message.content or "").strip())
        break
    except Exception as e:
        print("FAILED:", e)
