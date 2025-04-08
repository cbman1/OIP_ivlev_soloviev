import os
import json
import math
import re
from collections import Counter
import pymorphy2
from flask import Flask, render_template, request

app = Flask(__name__)
morph = pymorphy2.MorphAnalyzer()

DATA_DIR = './app_data'
DOCS_DATA_PATH = os.path.join(DATA_DIR, 'docs_data.json')
IDF_VALUES_PATH = os.path.join(DATA_DIR, 'idf_values.json')

DOCUMENTS_DATA = []
IDF_VALUES = {}
VOCABULARY = set()


def load_data():
    global DOCUMENTS_DATA, IDF_VALUES, VOCABULARY
    if not os.path.exists(DATA_DIR):
        print(f"директория не найдена: {DATA_DIR}")
        return
    try:
        with open(DOCS_DATA_PATH, 'r', encoding='utf-8') as f:
            DOCUMENTS_DATA = json.load(f)
        print(f"Загружено {len(DOCUMENTS_DATA)} документов.")

        with open(IDF_VALUES_PATH, 'r', encoding='utf-8') as f:
            IDF_VALUES = json.load(f)
        VOCABULARY = set(IDF_VALUES.keys())
        print(f"Загружено {len(IDF_VALUES)} IDF значений.")

    except FileNotFoundError as e:
        print(f"Не найден файл данных: {e}, \n{DATA_DIR}")
        DOCUMENTS_DATA = []
        IDF_VALUES = {}
    except json.JSONDecodeError as e:
        print(f"Не удалось декодировать JSON файл: {e}")
        DOCUMENTS_DATA = []
        IDF_VALUES = {}
    except Exception as e:
        print(f"ошибка при загрузке данных: {e}")
        DOCUMENTS_DATA = []
        IDF_VALUES = {}


def preprocess_query(query_text):
    tokens = re.findall(r'[а-яёa-z0-9]+', query_text.lower())
    lemmas = []
    for token in tokens:
        parsed = morph.parse(token)
        if parsed:
            lemmas.append(parsed[0].normal_form)
    return lemmas


def create_query_vector(query_lemmas):
    query_vector = {}
    if not query_lemmas:
        return query_vector

    term_counts = Counter(query_lemmas)
    for lemma, count in term_counts.items():
        if lemma in IDF_VALUES:
            tf = count
            idf = IDF_VALUES[lemma]
            query_vector[lemma] = tf * idf
    return query_vector


def calculate_len(vector):
    if not vector: return 0.0
    return math.sqrt(sum(val ** 2 for val in vector.values()))


def cosine_similarity(vec1, vec2, len1, len2):
    if len1 == 0 or len2 == 0: return 0.0
    dot_product = 0.0
    smaller_vec, larger_vec = (vec1, vec2) if len(vec1) < len(vec2) else (vec2, vec1)
    for lemma, val1 in smaller_vec.items():
        if lemma in larger_vec:
            dot_product += val1 * larger_vec[lemma]
    denominator = (len1 * len2)
    return dot_product / denominator if denominator != 0 else 0.0


def search(query_text, top_n=10):
    if not DOCUMENTS_DATA or not IDF_VALUES:
        return [], "Ошибка сервера: Данные для поиска не загружены."

    query_lemmas = preprocess_query(query_text)
    if not query_lemmas:
        return [], "Запрос не содержит распознанных слов."

    query_vector = create_query_vector(query_lemmas)
    if not query_vector:
        return [], "Ни одно слово из запроса не найдено в базе данных."

    query_len = calculate_len(query_vector)
    if query_len == 0:
        return [], "Не удалось рассчитать вектор запроса (нулевая магнитуда)."

    results = []
    for doc_data in DOCUMENTS_DATA:
        doc_len = doc_data.get('len', 0)
        doc_vector = doc_data.get('vector', {})

        similarity = cosine_similarity(query_vector, doc_vector, query_len, doc_len)
        if similarity > 0.0001:
            results.append({
                'id': doc_data.get('id', 'N/A'),
                'title': doc_data.get('title', 'Без заголовка'),
                'url': doc_data.get('url', '#'),
                'similarity': similarity
            })

    results.sort(key=lambda item: item['similarity'], reverse=True)
    print(f"найдено {len(results)} результатов до отсечения top_n ")
    return results[:top_n], None


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', query="", results=[], error=None)


@app.route('/search', methods=['GET'])
def search_results():
    query = request.args.get('query', '').strip()
    results, error = [], None
    print(f"Получен запрос: '{query}'")
    if query:
        results, error = search(query)
    elif request.args:
        error = "введите поисковый запрос"

    return render_template('index.html', query=query, results=results, error=error)


load_data()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
