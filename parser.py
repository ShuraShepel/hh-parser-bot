import requests
from bs4 import BeautifulSoup

def parse_hh_vacancy(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Описание вакансии
    description_block = soup.find('div', {'data-qa': 'vacancy-description'})
    description = description_block.get_text(strip=True, separator="\n") if description_block else None

    # Название вакансии
    title_block = soup.find('h1', {'data-qa': 'vacancy-title'})
    title = title_block.get_text(strip=True) if title_block else None

    return description, title