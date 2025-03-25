import os
import re
from collections import defaultdict
import pymorphy2

current_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(current_dir, "../task1/выкачка")

OUTPUT_DIR = "task2/task2_output"

# стоп-слова
STOP_WORDS = {
    "и", "в", "во", "не", "на", "но", "а", "по", "к", "о",
    "с", "у", "за", "для", "так", "то", "ли", "же", "бы",
    "либо", "или", "если", "чтобы", "также", "еще"
}

# регулярное выражение для поиска слов
WORD_REGEX = re.compile(r"[a-zA-Zа-яА-ЯёЁ]+")
# регулярное выражения для проверки, что слово состоит только из английских букв
ENGLISH_REGEX = re.compile(r"^[a-zA-Z]+$")

morph = pymorphy2.MorphAnalyzer()


def lemmatize(token: str) -> str:
    return morph.parse(token)[0].normal_form


# чтение файла, токенизация, фильтрация, создание двух файлов lemmas.txt и tokens.txt
def process_file(filepath: str, out_subdir: str):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"Ошибка чтения файла {filepath}: {e}")
        return

    tokens_set = set()
    for word in WORD_REGEX.findall(text):
        word_lower = word.lower()
        if len(word_lower) <= 1 or word_lower in STOP_WORDS or ENGLISH_REGEX.fullmatch(word_lower):
            continue
        tokens_set.add(word_lower)
    tokens = sorted(tokens_set)

    # запись токенов в файл tokens.txt
    tokens_file = os.path.join(out_subdir, "tokens.txt")
    try:
        with open(tokens_file, "w", encoding="utf-8") as f:
            for token in tokens:
                f.write(token + "\n")
    except Exception as e:
        print(f"Ошибка записи файла {tokens_file}: {e}")
        return

    # группировка токенов по лемме
    lemma_groups = defaultdict(set)
    for token in tokens:
        lemma = lemmatize(token)
        lemma_groups[lemma].add(token)

    # запись лемм и соответствующих токенов в файл lemmas.txt
    lemmas_file = os.path.join(out_subdir, "lemmas.txt")
    try:
        with open(lemmas_file, "w", encoding="utf-8") as f:
            for lemma in sorted(lemma_groups.keys()):
                tokens_list = sorted(lemma_groups[lemma])
                line = f"{lemma}: " + ", ".join(tokens_list) + "\n"
                f.write(line)
    except Exception as e:
        print(f"Ошибка записи файла {lemmas_file}: {e}")
        return

    print(f"Обработан файл {filepath} -> {tokens_file}, {lemmas_file}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
        txt_files = [os.path.join(INPUT_DIR, file)
                     for file in os.listdir(INPUT_DIR)
                     if file.endswith(".txt")]
    except Exception as e:
        print(f"Ошибка чтения директории {INPUT_DIR}: {e}")
        return

    for idx, filepath in enumerate(txt_files, start=1):
        subdir_name = f"выкачка{idx}"
        out_subdir = os.path.join(OUTPUT_DIR, subdir_name)
        os.makedirs(out_subdir, exist_ok=True)
        process_file(filepath, out_subdir)

    print("Готово. Все файлы обработаны.")


if __name__ == "__main__":
    main()
