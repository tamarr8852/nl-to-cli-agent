import os
import time

# הבדיקה הפנימית של Gradio מול localhost לא צריכה לעבור דרך ה-proxy של הרשת
os.environ["NO_PROXY"] = ",".join(
    filter(None, [os.environ.get("NO_PROXY"), "localhost", "127.0.0.1", "0.0.0.0"])
)
os.environ["no_proxy"] = os.environ["NO_PROXY"]

import gradio as gr
from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, OpenAI

# טעינת מפתח ה-API של Groq מקובץ .env
load_dotenv()
client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",  # Groq תואם ל-API של OpenAI
    timeout=30,
)
# מודלים מועדפים לפי הסדר; בעלייה נבחר הראשון שזמין בחשבון (אפשר לקבוע ידנית עם GROQ_MODEL ב-.env)
PREFERRED_MODELS = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "llama-3.1-8b-instant",
]


def pick_model():
    if os.environ.get("GROQ_MODEL"):
        return os.environ["GROQ_MODEL"]
    available = [m.id for m in client.models.list().data]
    for name in PREFERRED_MODELS:
        if name in available:
            return name
    raise RuntimeError(f"None of the preferred models is available. Available: {available}")


MODEL = pick_model()
print(f"Using Groq model: {MODEL}")
MAX_ATTEMPTS = 4

# כל גרסאות הפרומפט נשמרות כאן לצורך תיעוד האיטרציות
PROMPTS = {
    # v1 - איטרציה 1: גרסת MVP ראשונית
    "v1": """
You are a CLI command generator agent. 
The user will give you a natural language instruction. 
Your job is to translate it into a valid terminal command (Windows CMD / PowerShell).
Return ONLY the command itself, with no extra explanations or markdown formatting.
""",
    # v2 - איטרציה 2: סימון פקודות מסוכנות ובקשת הבהרה כשההוראה לא ברורה
    "v2": """
You are a CLI command generator agent. 
The user will give you a natural language instruction. 
Your job is to translate it into a valid terminal command (Windows CMD / PowerShell).
Return ONLY the command itself, with no extra explanations or markdown formatting.
When a request is dangerous, you must mark the command as dangerous.
If the instruction is not clear to you, you must ask for clarification.
To mark a dangerous command, start the line with "[DANGEROUS] " followed by the command.
To ask for clarification, write one line that starts with "[CLARIFY] " followed by your question.
These two prefixes are the only text allowed besides the command.
""",
    # v3 - איטרציה 3: עבודה ב-CMD בלבד, בלי דגלים או הרחבות שהמשתמש לא ביקש
    "v3": """
You are a CLI command generator agent. 
The user will give you a natural language instruction. 
Your job is to translate it into a valid terminal command (Windows CMD).
Return ONLY the command itself, with no extra explanations or markdown formatting.
When a request is dangerous, you must mark the command as dangerous.
If the instruction is not clear to you, you must ask for clarification.
To mark a dangerous command, start the line with "[DANGEROUS] " followed by the command.
To ask for clarification, write one line that starts with "[CLARIFY] " followed by your question.
These two prefixes are the only text allowed besides the command.
You must always work in CMD.
You must not add flags that the user did not ask for.
You must not expand the request, you must not add to it, and you must not change it.
""",
}

PROMPT_VERSION = "v3"
SYSTEM_PROMPT = PROMPTS[PROMPT_VERSION]
print(f"Using prompt version: {PROMPT_VERSION}")


def generate_command(user_input):
    # אם השרת עמוס או מגביל קצב (429/5xx) מחכים קצת ומנסים שוב
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_input},
                ],
                temperature=0.0,
            )
            return (response.choices[0].message.content or "").strip()
        except APIStatusError as e:
            print(f"[attempt {attempt}/{MAX_ATTEMPTS}] Groq error {e.status_code}: {e.message}")
            if e.status_code not in (429, 500, 502, 503) or attempt == MAX_ATTEMPTS:
                raise gr.Error(f"Groq error {e.status_code}: {e.message}")
        except APIConnectionError as e:
            print(f"[attempt {attempt}/{MAX_ATTEMPTS}] connection error: {e}")
            if attempt == MAX_ATTEMPTS:
                raise gr.Error(f"Connection error: {e}")
        time.sleep(3 * attempt)


# יצירת ממשק Gradio פשוט
demo = gr.Interface(
    fn=generate_command,
    inputs=gr.Textbox(label="הוראה בשפה טבעית (לדוגמה: מצא את כל קבצי ה-tmp)"),
    outputs=gr.Textbox(label="פקודת CLI (תוצאה)"),
    title="Natural Language to CLI Agent (MVP)",
)

if __name__ == "__main__":
    demo.launch()
