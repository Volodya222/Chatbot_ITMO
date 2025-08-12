# save as extract_pdf_text.py
# pip install pymupdf
import os
import re
import sys
import fitz  # PyMuPDF

# укажи свои имена PDF тут (лежат в корне проекта)
PDF_FILES = ["10033-abit.pdf", "10130-abit.pdf"]

# соответствие PDF -> итоговый .txt (правь при необходимости)
OUTPUT_MAP = {
    "10033-abit.pdf": "ai_plan.txt",
    "10130-abit.pdf": "ai_product_plan.txt",
}

def extract_pdf_text(path: str) -> str:
    """Достаёт текст из PDF (по страницам) и приводит к читабельному виду."""
    doc = fitz.open(path)
    pages = []
    for i, page in enumerate(doc, start=1):
        txt = page.get_text("text")  # потоковый текст
        pages.append(txt)
    doc.close()
    raw = "\n".join(pages)
    return clean_text(raw)

def clean_text(s: str) -> str:
    """Мини-очистка под LLM: склейка переносов по дефисам, вырезка мусора, нормализация пробелов."""
    s = s.replace("\r", "")
    s = s.replace("\u00ad", "")  # мягкие дефисы
    # склейка слов, разорванных переносом с дефисом
    s = re.sub(r"(\w)-\n(\w)", r"\1\2", s)
    # нормализация длинных тире/прочего
    s = s.replace("—", "-").replace("–", "-")

    # построчная фильтрация
    lines = [ln.strip() for ln in s.split("\n")]

    keep = []
    for ln in lines:
        if not ln:
            continue
        # отбрасываем явные футеры/маркеры страниц
        if re.fullmatch(r"\d+\s*/\s*\d+", ln):
            continue
        if re.fullmatch(r"(стр\.?|страница)\s*\d+(\s*из\s*\d+)?", ln.lower()):
            continue
        if ln.lower().startswith("лист"):
            continue
        keep.append(ln)

    s = "\n".join(keep)
    # схлопываем лишние пустые строки
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    return s

def main(files):
    for pdf in files:
        if not os.path.exists(pdf):
            print(f"Skip: {pdf} (not found)")
            continue
        text = extract_pdf_text(pdf)
        out_name = OUTPUT_MAP.get(os.path.basename(pdf),
                                  os.path.splitext(os.path.basename(pdf))[0] + ".txt")
        with open(out_name, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved: {out_name} ({len(text)} chars)")

if __name__ == "__main__":
    # можно передать файлы как аргументы: python extract_pdf_text.py 10033-abit.pdf 10130-abit.pdf
    pdfs = sys.argv[1:] or PDF_FILES
    main(pdfs)
