import os
import requests
from bs4 import BeautifulSoup

#фильтры html кода для выделения блоков с текстом
def clean_content(content_div):
    if not content_div:
        return
    banner = content_div.find("div", class_="node-banner ga_send_event_load")
    if banner:
        banner.decompose()

    body_div = content_div.find("div", class_="field field-name-body field-type-text-with-summary field-label-hidden")
    if not body_div:
        return

    field_item_even = body_div.find("div", class_="field-item even")
    if not field_item_even:
        return

    p_tags = field_item_even.find_all("p", recursive=True)
    if p_tags:
        p_tags[0].decompose()

    for p_tag in field_item_even.find_all("p", align="right"):
        p_tag.decompose()

    abstract_p = None
    for p_tag in field_item_even.find_all("p"):
        strong_tag = p_tag.find("strong")
        if strong_tag and strong_tag.get_text(strip=True).upper() == "ABSTRACT":
            abstract_p = p_tag
            break
    if abstract_p:
        abstract_p.decompose()
        next_p = abstract_p.find_next_sibling("p")
        if next_p:
            next_p.decompose()

    for p_tag in field_item_even.find_all("p"):
        strong_tag = p_tag.find("strong")
        if strong_tag and strong_tag.get_text(strip=True).upper() == "KEYWORDS":
            p_tag.decompose()
            break


def main():
    with open("links.txt", "r", encoding="utf-8") as f:
        links = [line.strip() for line in f if line.strip()]

    with open("выкачка_общая.txt", "w", encoding="utf-8") as _:
        pass
    with open("index.txt", "w", encoding="utf-8") as _:
        pass

    for i, url in enumerate(links, start=1):
        try:
            response = requests.get(url, timeout=15)
            response.encoding = response.apparent_encoding
            if response.status_code != 200:
                print(response.status_code, "\n", url)
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            title_tag = soup.find("h1", class_="page_title")
            authors_div = soup.find("div", class_="authors")
            content_div = soup.find("div", class_="content clearfix")
            clean_content(content_div)

            final_html = ""
            if title_tag:
                final_html += str(title_tag)
            if authors_div:
                final_html += str(authors_div)
            if content_div:
                final_html += str(content_div)

            out_filename = f"выкачка{i}.txt"
            with open(out_filename, "w", encoding="utf-8") as out_f:
                out_f.write(final_html)
            with open("выкачка_общая.txt", "a", encoding="utf-8") as out_common:
                out_common.write("-------------------\n")
                out_common.write(f"НАЧАЛО ФАЙЛА выкачка{i}.txt \n")
                out_common.write("-------------------\n")
                out_common.write(final_html + "\n\n")

            with open("index.txt", "a", encoding="utf-8") as idx_f:
                idx_f.write(f"{i} {url}\n")

            print(f"{i} обработано по ссылке -  {url}")

        except Exception as e:
            print(f"{i} {url} \n {e}")


if __name__ == "__main__":
    main()
