import os
import json
import math
import re
from collections import Counter
import pymorphy2

TASK1_DIR = '../task1'
TASK3_DIR = '../task3'
TASK4_DIR = '../task4'

ALL_DOCS_PATH = os.path.join(TASK3_DIR, 'all_docs.json')
INDEX_PATH = os.path.join(TASK1_DIR, 'index.txt')
TFIDF_OUTPUT_DIR = os.path.join(TASK4_DIR, 'task4_output')
LEMMAS_TFIDF_FILENAME = 'lemmas_tf_idf.txt'
morph = pymorphy2.MorphAnalyzer()


def load_all_docs(filepath):
    # загрузка id из all_docs.json
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось декодировать JSON из файла {filepath}")
        return None


def load_index(filepath):
    # index.txt для отображения ссылок
    index_map = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(' ', 1)
                if len(parts) == 2:
                    doc_num_str, url = parts
                    doc_id = f"выкачка{doc_num_str}"
                    index_map[doc_id] = url
                else:
                    print(f"Предупреждение: Неверный формат строки в {filepath}: {line.strip()}")

    except FileNotFoundError:
        print(f"Ошибка: Файл не найден {filepath}")
        return None
    return index_map


def load_tfidf_vectors_and_idf(tfidf_dir, doc_ids):
    # загрузка  TF-IDF для лемм из соотв. lemmas_tf_idf + IDF
    doc_vectors = {}
    idf_values = {}
    # все уникальные леммы
    vocabulary = set()

    for doc_id in doc_ids:
        vector_path = os.path.join(tfidf_dir, doc_id, LEMMAS_TFIDF_FILENAME)
        # словарь lemmaN: tfidfN
        doc_vec = {}
        try:
            with open(vector_path, 'r', encoding='utf-8') as f:
                # парсим
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 3:
                        lemma, tfidf_str, idf_str = parts
                        try:
                            tfidf = float(tfidf_str)
                            idf = float(idf_str)
                            doc_vec[lemma] = tfidf
                            vocabulary.add(lemma)
                            # IDF для уникальных лемм
                            if lemma not in idf_values:
                                idf_values[lemma] = idf
                        except ValueError:
                            print(
                                f"Предупреждение: Не удалось преобразовать числа в строке: {line.strip()} в файле {vector_path}")
                    else:
                        print(f"Предупреждение: Неверный формат строки: {line.strip()} в файле {vector_path}")
            if doc_vec:
                doc_vectors[doc_id] = doc_vec

        except FileNotFoundError:
            print(f"Предупреждение: Файл TF-IDF не найден для документа {doc_id} по пути {vector_path}")
        except Exception as e:
            print(f"Ошибка при обработке файла {vector_path}: {e}")

    print(f"Загружено {len(doc_vectors)} векторов документов.")
    print(f"Размер словаря (уникальных лемм): {len(vocabulary)}")
    print(f"Загружено {len(idf_values)} IDF значений.")
    return doc_vectors, idf_values, vocabulary


def preprocess_query(query_text):
    # извлечение токенов из запроса
    tokens = re.findall(r'[а-яёa-z0-9]+', query_text.lower())
    # итоговые леммы запроса
    lemmas = []
    for token in tokens:
        parsed = morph.parse(token)
        # лемматизация токена
        if parsed:
            lemmas.append(parsed[0].normal_form)
    return lemmas


def create_query_vector(query_lemmas, idf_values, vocabulary):
    # список лемм из запроса -> TF-IDF вектор
    query_vector = {}
    if not query_lemmas:
        return query_vector

    # подсчет частоты элементов в списке
    term_counts = Counter(query_lemmas)
    for lemma, count in term_counts.items():
        if lemma in vocabulary and lemma in idf_values:
            # tf частота леммы из запроса * idf глобальный idf леммы = вес леммы для запроса
            tf = count
            idf = idf_values[lemma]
            query_vector[lemma] = tf * idf
    return query_vector


def calculate_vector_len(vector):
    # длина вектора для вычисления косинусного сходства
    if not vector:
        return 0.0
    sum_of_squares = sum(val ** 2 for val in vector.values())
    return math.sqrt(sum_of_squares)


# косинусное сходство
def cosine_similarity(vec1, vec2, len1, len2):
    if len1 == 0 or len2 == 0:
        return 0.0
    dot_product = 0.0
    smaller_vec, larger_vec = (vec1, vec2) if len(vec1) < len(vec2) else (vec2, vec1)

    # скалярное произведение векторов (только по общим леммам, начиная с меньшего вектора)
    for lemma, val1 in smaller_vec.items():
        if lemma in larger_vec:
            dot_product += val1 * larger_vec[lemma]

    return dot_product / (len1 * len2)


def vector_search(query, doc_vectors, idf_values, vocabulary, index_map, top_n=10):
    query_lemmas = preprocess_query(query)
    if not query_lemmas:
        print("Запрос не содержит известных лемм.")
        return []

    print(f"Леммы запроса: {query_lemmas}")
    query_vector = create_query_vector(query_lemmas, idf_values, vocabulary)
    print(
        f"Вектор запроса (TF-IDF): { {k: round(v, 4) for k, v in query_vector.items()} }")  # Округление для читаемости

    if not query_vector:
        print("Не удалось построить вектор")
        return []

    query_lens = calculate_vector_len(query_vector)
    if query_lens == 0:
        print("Длина вектора запроса равна нулю.")
        return []

    results = []
    doc_lens = {doc_id: calculate_vector_len(vec) for doc_id, vec in doc_vectors.items()}

    for doc_id, doc_vec in doc_vectors.items():
        doc_len = doc_lens[doc_id]
        similarity = cosine_similarity(query_vector, doc_vec, query_lens, doc_len)
        if similarity > 0:  # Добавляем только если сходство положительное
            results.append((similarity, doc_id))

    results.sort(key=lambda item: item[0], reverse=True)

    print("Результаты поиска:")
    output = []
    for i, (sim, doc_id) in enumerate(results[:top_n]):
        url = index_map.get(doc_id, "URL не найден")
        print(f"{i + 1}. Документ: {doc_id}, Сходство: {sim:.4f}, URL: {url}")
        output.append({"doc_id": doc_id, "similarity": sim, "url": url})

    if not results:
        print("Документы, соответствующие запросу, не найдены.")

    return output


if __name__ == "__main__":
    all_docs = load_all_docs(ALL_DOCS_PATH)
    doc_index_map = load_index(INDEX_PATH)

    if all_docs is None or doc_index_map is None:
        print("Не удалось загрузить данные.\n Выход.")
        exit()

    document_vectors, idf, vocab = load_tfidf_vectors_and_idf(TFIDF_OUTPUT_DIR, all_docs)

    if not document_vectors or not idf:
        print("Не удалось загрузить векторы TF-IDF или IDF значения. \nВыход.")
        exit()

    # 2. Цикл обработки запросов
    print("\nВведите запрос или 'quit' для выхода.")
    while True:
        user_query = input("Запрос> ")
        if user_query.lower() in ['quit', 'exit']:
            break
        if not user_query.strip():
            continue

        search_results = vector_search(user_query, document_vectors, idf, vocab, doc_index_map)
        print("-" * 20)
