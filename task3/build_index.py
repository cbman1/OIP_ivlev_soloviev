import os
import glob
import json
from collections import defaultdict
import re

TASK2_OUTPUT_DIR = '../task2/task2_output'
INDEX_FILE = 'inverted_index.json'
ALL_DOCS_FILE = 'all_docs.json'


def build_inverted_index(input_dir):
    inverted_index = defaultdict(set)
    all_doc_ids = set()

    #ищем леммы
    abs_input_dir = os.path.abspath(input_dir)
    lemma_files = glob.glob(os.path.join(abs_input_dir, 'выкачка*', 'lemmas.txt'))

    if not lemma_files:
        print("леммы не найдены ")
        return {}, set()

    print(f" найдено {len(lemma_files)} файлов lemmas.txt для индексации")

    for filepath in lemma_files:
        try:
            #извлечение айди (в данном случае выкачкаN)
            doc_id = os.path.basename(os.path.dirname(filepath))
            all_doc_ids.add(doc_id)

            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    # РЕЗНЯ ЛЕММ
                    parts = line.strip().split(':', 1)
                    if len(parts) == 2:
                        lemma = parts[0].strip()
                        if lemma:
                            inverted_index[lemma].add(doc_id)
        except Exception as e:
            print(f"Ошибка в файле {filepath} \n{e}")

    print(f"индекс построен: {len(inverted_index)} уникальных лемм в {len(all_doc_ids)} документах.")
    return dict(inverted_index), all_doc_ids


def save_index(index, all_docs, index_filename, docs_filename):
    #сохранение индекса и список всех Id документов в JSON
    try:
        #  set --> list для JSON сериализации
        serializable_index = {k: list(v) for k, v in index.items()}
        serializable_docs = list(all_docs)

        for k in serializable_index:
            try:
                #сортировка по числовой части (ID)
                serializable_index[k] = sorted(serializable_index[k], key=lambda x: int(re.search(r'\d+', x).group()))
            except:
                #сортируем как строки, если не извлеклось число
                serializable_index[k] = sorted(serializable_index[k])
        try:
            serializable_docs = sorted(serializable_docs, key=lambda x: int(re.search(r'\d+', x).group()))
        except:
            serializable_docs = sorted(serializable_docs)

        #запись в JSON
        with open(index_filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_index, f, ensure_ascii=False, indent=4)
        with open(docs_filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_docs, f, ensure_ascii=False, indent=4)
        print(f"Индекс сохранен: {index_filename} \nсписок документов сохранен: {docs_filename}")
    except Exception as e:
        print(f"ошибка: {e}")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    task2_dir_abs = os.path.join(script_dir, TASK2_OUTPUT_DIR)

    # строим индекс
    inverted_index, all_doc_ids = build_inverted_index(task2_dir_abs)

    if inverted_index and all_doc_ids:
        index_file_path = os.path.join(script_dir, INDEX_FILE)
        docs_file_path = os.path.join(script_dir, ALL_DOCS_FILE)
        save_index(inverted_index, all_doc_ids, index_file_path, docs_file_path)
    else:
        print("не удалось построить индекс. Проверьте наличие и содержимое файлов lemmas.txt.")

    print("Построение индекса завершено!!!")
