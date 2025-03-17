import re
import requests
from bs4 import BeautifulSoup

#есть статьи не на русском языке, фильтр:
def is_russian(text: str) -> bool:
    all_letters = re.findall(r'[a-zA-Zа-яА-ЯёЁ]', text)
    if not all_letters:
        return False
    rus_letters = re.findall(r'[а-яА-ЯёЁ]', text)

    ratio = len(rus_letters) / len(all_letters)
    return ratio >= 0.8


def scrape(output_file='links.txt'):
    base_url = "https://sibac.info/arhive-article"
    total_pages = 134

    with open(output_file, 'w', encoding='utf-8') as f:
        for page_num in range(total_pages + 1):
            params = {
                'page': page_num,
                'science': '352'
            }
            response = requests.get(base_url, params=params)

            if response.status_code != 200:
                print(f"ошибка на странице {page_num}, \n {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.select('#archive-wrapp .item p a')

            for link in items:
                title = link.get_text(strip=True)
                href = link.get('href')
                if href and is_russian(title):
                    full_link = "https://sibac.info" + href
                    f.write(full_link + "\n")

            print(f"страница {page_num + 1} / {total_pages + 1}")


if __name__ == "__main__":
    scrape("links.txt")
