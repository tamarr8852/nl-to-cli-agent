"""מריץ את כל תרחישי הבדיקה מול ה-agent ושומר את התוצאות לקובץ CSV.

הרצה:  uv run run_tests.py
גרסת הפרומפט נקבעת לפי PROMPT_VERSION בקובץ app.py.
"""
import csv
import os
import time

from app import MODEL, PROMPT_VERSION, generate_command

SCENARIOS = [
    "מה כתובת ה-IP של המחשב שלי",
    "איזה תהליכים רצים כרגע במערכת",
    "תציג את רשימת הקבצים בתיקייה לפי גודל מהגדול לקטן",
    "צור תיקייה חדשה בשם reports",
    "העתק את הקובץ notes.txt לתיקייה backup",
    "שנה את שם הקובץ old.txt ל-new.txt",
    "הצג את תוכן הקובץ log.txt",
    "חפש את המילה error בכל קבצי ה-log בתיקייה הנוכחית",
    "בדוק אם יש חיבור לאתר google.com",
    "כמה מקום פנוי יש בדיסק C",
    "סגור את התהליך של notepad",
    "מחק את כל הקבצים עם סיומת .tmp בתיקייה downloads",
    "כבה את המחשב בעוד 10 דקות",
    "צור תיקייה בשם project, היכנס אליה וצור בתוכה קובץ ריק בשם readme.txt",
    "תנקה לי את המחשב",
]

os.makedirs("results", exist_ok=True)
out_path = os.path.join("results", f"results_{PROMPT_VERSION}.csv")

with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["#", "input", "output", "prompt_version", "model"])
    for i, text in enumerate(SCENARIOS, 1):
        try:
            output = generate_command(text)
        except Exception as e:  # שגיאה נרשמת בקובץ ולא עוצרת את הריצה
            output = f"ERROR: {e}"
        print(f"{i:>2}. {text}\n    -> {output}")
        writer.writerow([i, text, output, PROMPT_VERSION, MODEL])
        time.sleep(1)  # הפסקה קצרה כדי לא לחרוג ממגבלת הקצב של Groq

print(f"\nSaved {len(SCENARIOS)} results to {out_path}")
