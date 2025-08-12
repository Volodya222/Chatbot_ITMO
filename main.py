# main.py
# pip install python-dotenv openai
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

MODEL = "gpt-4o"
BASE_URL = "https://api.proxyapi.ru/openai/v1"
SYSTEM_LOG = "system_log.txt"

FILES = {
    "AI — страница": "ai.txt",
    "AI — учебный план": "ai_plan.txt",
    "AI Product — страница": "ai_product.txt",
    "AI Product — учебный план": "ai_product_plan.txt",
}

INSTRUCTION = (
    "Ты — помощник абитуриента по ДВУМ магистерским программам ИТМО: "
    "«Искусственный интеллект» и «Управление AI-продуктами». "
    "Отвечай вежливо и только по вопросам поступления/обучения на этих двух программах: "
    "программа, треки, дисциплины, семестры, практики, ГИА, нагрузки, контакты, сроки, формат. "
    "Если вопрос вне этой темы — отвечай кратко: «Я помогаю только с поступлением и обучением "
    "на двух магистратурах ИТМО: AI и AI Product» и предложи задать релевантный вопрос. "
    "Если чего-то нет в данных ниже — честно скажи, что в материалах это не указано."
)

def read_text(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"[ФАЙЛ НЕ НАЙДЕН: {path}]"
    return p.read_text(encoding="utf-8", errors="ignore")

def build_system_content(history_text: str) -> str:
    parts = [f"# Инструкция\n{INSTRUCTION}\n"]
    for title, fname in FILES.items():
        parts.append(f"\n# {title}\n" + read_text(fname))
    if history_text:
        parts.append("\n# История диалога (для контекста)\n" + history_text)
    return "\n".join(parts)

def append_system_log(system_content: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SYSTEM_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n\n===== SYSTEM @ {ts} =====\n")
        f.write(system_content)

def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Не найден OPENAI_API_KEY в .env")
        return

    client = OpenAI(api_key=api_key, base_url=BASE_URL)

    history_pairs = []  # [(user, assistant), ...]
    print("Консольный чат. Введите вопрос. Выход: /exit")

    while True:
        try:
            user_input = input("\nвы: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            break

        if user_input.lower() in {"/exit", "exit", "quit", "/q"}:
            print("Пока!")
            break
        if not user_input:
            continue

        # соберём историю в плоский текст для системки
        hist_lines = []
        for u, a in history_pairs:
            hist_lines.append(f"Пользователь: {u}")
            hist_lines.append(f"Ассистент: {a}")
        hist_lines.append(f"Пользователь: {user_input}")
        history_text = "\n".join(hist_lines)

        system_content = build_system_content(history_text)
        append_system_log(system_content)

        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_content},
                    # отдельно дублировать историю в messages не требуем — мы уже запихнули её в system
                    {"role": "user", "content": user_input},
                ],
                temperature=0.2,
            )
            answer = (resp.choices[0].message.content or "").strip()
        except Exception as e:
            answer = f"Ошибка при обращении к модели: {e}"

        print(f"бот: {answer}")
        history_pairs.append((user_input, answer))

if __name__ == "__main__":
    main()
