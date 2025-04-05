import os
import re
import math


def process_document(doc_num):
    doc_id = f"выкачка{doc_num}"
    text_path = os.path.join("..", "task1", "выкачка", f"{doc_id}.txt")
    tokens_dir = os.path.join("..", "task2", "task2_output", doc_id)
    tokens_path = os.path.join(tokens_dir, "tokens.txt")
    lemmas_path = os.path.join(tokens_dir, "lemmas.txt")

    # чтение списка терминов (tokens)
    with open(tokens_path, "r", encoding="utf-8") as f:
        tokens = [line.strip() for line in f if line.strip()]

    # чтение списка лемм"
    lemma_map = {}
    lemmas_order = []  # сохранение порядка лемм
    with open(lemmas_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(":")
            if len(parts) < 2:
                continue
            lemma = parts[0].strip()
            variants = [v.strip() for v in parts[1].split(",") if v.strip()]
            lemma_map[lemma] = variants
            lemmas_order.append(lemma)

    with open(text_path, "r", encoding="utf-8") as f:
        html = f.read()

    text = re.sub(r'<[^>]+>', ' ', html)
    words = re.findall(r'[^\W\d_]+', text.lower(), re.UNICODE)
    total_words = len(words)

    # подсчет частот терминов (TF = raw count, т.е. просто количество вхождений)
    token_counts = {}
    for token in tokens:
        token_lower = token.lower()
        count = sum(1 for w in words if w == token_lower)
        token_counts[token] = count

    # подсчет частот лемм (суммируя частоты всех вариантов)
    lemma_counts = {}
    for lemma, variants in lemma_map.items():
        count = 0
        for variant in variants:
            variant_lower = variant.lower()
            count += sum(1 for w in words if w == variant_lower)
        lemma_counts[lemma] = count

    # определение присутствия термина/леммы в документе (для расчета df)
    token_presence = {token for token, cnt in token_counts.items() if cnt > 0}
    lemma_presence = {lemma for lemma, cnt in lemma_counts.items() if cnt > 0}

    return {
        "doc_id": doc_id,
        "total_words": total_words,
        "tokens": tokens,
        "token_counts": token_counts,
        "lemmas_order": lemmas_order,
        "lemma_map": lemma_map,
        "lemma_counts": lemma_counts,
        "token_presence": token_presence,
        "lemma_presence": lemma_presence
    }


def main():
    num_docs = 100
    docs = []

    # обработка документов
    for i in range(1, num_docs + 1):
        try:
            doc_data = process_document(i)
            docs.append(doc_data)
        except Exception as e:
            print(f"Ошибка при обработке документа выкачка{i}: {e}")

    N = len(docs)
    if N == 0:
        print("Нет обработанных документов.")
        return

    # глобальный подсчет document frequency (df) для терминов и лемм
    global_token_df = {}
    global_lemma_df = {}

    for doc in docs:
        for token in doc["tokens"]:
            if token not in global_token_df:
                global_token_df[token] = 0
            if token in doc["token_presence"]:
                global_token_df[token] += 1
        for lemma in doc["lemmas_order"]:
            if lemma not in global_lemma_df:
                global_lemma_df[lemma] = 0
            if lemma in doc["lemma_presence"]:
                global_lemma_df[lemma] += 1

    # вычисление IDF: IDF(t) = ln(N / df)
    token_idf = {}
    for token, df in global_token_df.items():
        token_idf[token] = math.log(N / df) if df > 0 else 0.0

    lemma_idf = {}
    for lemma, df in global_lemma_df.items():
        lemma_idf[lemma] = math.log(N / df) if df > 0 else 0.0

    # сохранение результатов TF-IDF для каждого документа
    for doc in docs:
        doc_id = doc["doc_id"]
        output_dir = os.path.join("task4_output", doc_id)
        os.makedirs(output_dir, exist_ok=True)

        # запись TF-IDF для терминов (TF = raw count)
        tokens_output_path = os.path.join(output_dir, "tokens_tf_idf.txt")
        with open(tokens_output_path, "w", encoding="utf-8") as fout:
            for token in doc["tokens"]:
                count = doc["token_counts"].get(token, 0)
                tf = count  # raw term frequency (количество вхождений)
                idf_val = token_idf.get(token, 0.0)
                tf_idf = tf * idf_val
                fout.write(f"{token} {idf_val:.6f} {tf_idf:.6f}\n")

        # запись TF-IDF для лемм (TF = raw count)
        lemmas_output_path = os.path.join(output_dir, "lemmas_tf_idf.txt")
        with open(lemmas_output_path, "w", encoding="utf-8") as fout:
            for lemma in doc["lemmas_order"]:
                count = doc["lemma_counts"].get(lemma, 0)
                tf = count  # raw term frequency (количество вхождений)
                idf_val = lemma_idf.get(lemma, 0.0)
                tf_idf = tf * idf_val
                fout.write(f"{lemma} {idf_val:.6f} {tf_idf:.6f}\n")


if __name__ == "__main__":
    main()
