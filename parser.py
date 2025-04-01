# parser.py

import requests
from bs4 import BeautifulSoup

def parse_hh_vacancy(url: str) -> str:
    if "hh.ru" not in url:
        return "Ссылка должна вести на hh.ru"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        title_tag = soup.find("h1")
        description_tag = soup.find("div", {"data-qa": "vacancy-description"})

        title = title_tag.get_text(strip=True) if title_tag else "Без названия"
        description = description_tag.get_text(strip=True, separator="\n") if description_tag else "Описание не найдено"

        return f"{title}\n\n{description}"
    
    except Exception as e:
        return f"Ошибка при парсинге: {e}"