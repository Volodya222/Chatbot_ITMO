# save as scrape_text.py
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from pathlib import Path

urls = [
    "https://abit.itmo.ru/program/master/ai",
    "https://abit.itmo.ru/program/master/ai_product",
]

def extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # убираем служебные теги
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # получаем текст
    text = soup.get_text(separator="\n")

    # чистим пустые строки/пробелы
    text = re.sub(r"\r", "", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    return text

def filename_from_url(u: str) -> str:
    # последний сегмент пути — имя файла
    path = urlparse(u).path.rstrip("/")
    name = path.split("/")[-1] or "page"
    return f"{name}.txt"

def main():
    # outdir = Path(".")
    # outdir.mkdir(exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/124.0 Safari/537.36"
    }

    for url in urls:
        print(f"Fetching: {url}")
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        # на всякий — доверимся auto-detected encoding
        if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
            resp.encoding = resp.apparent_encoding

        text = extract_visible_text(resp.text)
        out_path = (Path(".") / filename_from_url(url))
        out_path.write_text(text, encoding="utf-8")
        print(f"Saved: {out_path} ({len(text)} chars)")

if __name__ == "__main__":
    main()
