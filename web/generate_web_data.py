import os
import sys
import json
import math
import re
from collections import Counter

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

TASK1_DIR = os.path.join(PROJECT_ROOT, 'task1')
TASK3_DIR = os.path.join(PROJECT_ROOT, 'task3')
TASK4_DIR = os.path.join(PROJECT_ROOT, 'task4')
OUTPUT_DATA_DIR = os.path.join(os.path.dirname(__file__), 'app_data')

ALL_DOCS_PATH = os.path.join(TASK3_DIR, 'all_docs.json')
INDEX_PATH = os.path.join(TASK1_DIR, 'index.txt')
RAW_DOCS_DIR = os.path.join(TASK1_DIR, 'выкачка')
TFIDF_OUTPUT_DIR = os.path.join(TASK4_DIR, 'task4_output')
LEMMAS_TFIDF_FILENAME = 'lemmas_tf_idf.txt'

def load_all_docs(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)
    except Exception: return None

def load_index(filepath):
    index_map = {}; doc_id_prefix="выкачка"
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(' ', 1)
                if len(parts) == 2: index_map[f"{doc_id_prefix}{parts[0]}"] = parts[1]
    except Exception: return None
    return index_map

def extract_title(filepath):
    title = "Заголовок не найден"
    try:
        with open(filepath, 'r', encoding='utf-8') as f: content = f.read()
        match = re.search(r'<h1 class="page_title">(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
        if match: title = match.group(1).strip()
        else:
            match_h1 = re.search(r'<h1.*?>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
            if match_h1: title = match_h1.group(1).strip()
        title = re.sub(r'<.*?>', '', title).replace('\n', ' ').replace('\r', '').strip()
    except Exception: pass
    return title

def calculate_vector_len(vector):
    if not vector: return 0.0
    return math.sqrt(sum(val**2 for val in vector.values()))

def load_data_for_web(doc_ids, index_map, raw_docs_dir, tfidf_dir):
    docs_data = []; idf_values = {}; vocabulary = set(); processed_count = 0; skipped_count = 0
    if not doc_ids: return [], {}, []

    for doc_id in doc_ids:
        vector_path = os.path.join(tfidf_dir, doc_id, LEMMAS_TFIDF_FILENAME)
        raw_doc_path = os.path.join(raw_docs_dir, f"{doc_id}.txt")
        doc_vector = {}; doc_has_valid_data = False
        try:
            with open(vector_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split();
                    if len(parts) == 3:
                        lemma, tfidf_str, idf_str = parts
                        try:
                            tfidf=float(tfidf_str); idf=float(idf_str); doc_vector[lemma]=tfidf
                            vocabulary.add(lemma);
                            if lemma not in idf_values: idf_values[lemma]=idf
                            doc_has_valid_data=True
                        except ValueError: continue
            if doc_has_valid_data and doc_vector:
                title = extract_title(raw_doc_path); url = index_map.get(doc_id, "#")
                vector_len = calculate_vector_len(doc_vector)
                docs_data.append({"id": doc_id, "title": title, "url": url, "vector": doc_vector, "len": vector_len})
                processed_count += 1
            else: skipped_count +=1
        except FileNotFoundError: skipped_count +=1; continue
        except Exception: skipped_count +=1; continue
    return docs_data, idf_values, list(vocabulary)

if __name__ == "__main__":
    all_document_ids = load_all_docs(ALL_DOCS_PATH)
    url_map = load_index(INDEX_PATH)
    if not all_document_ids or not url_map: exit("Ошибка загрузки данных")

    docs_export_data, idf_export_data, vocab_export_data = load_data_for_web(
        all_document_ids, url_map, RAW_DOCS_DIR, TFIDF_OUTPUT_DIR
    )
    if not docs_export_data or not idf_export_data: exit("")

    try:
        os.makedirs(OUTPUT_DATA_DIR, exist_ok=True)
        docs_json_path = os.path.join(OUTPUT_DATA_DIR, 'docs_data.json')
        with open(docs_json_path, 'w', encoding='utf-8') as f: json.dump(docs_export_data, f, ensure_ascii=False, separators=(',', ':'))
        idf_json_path = os.path.join(OUTPUT_DATA_DIR, 'idf_values.json')
        with open(idf_json_path, 'w', encoding='utf-8') as f: json.dump(idf_export_data, f, ensure_ascii=False, separators=(',', ':'))
    except Exception as e: print(f"ошибка записи: {e}")