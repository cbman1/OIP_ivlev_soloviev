import os
import re
import json
import pymorphy2
from collections import deque

INDEX_FILE = 'inverted_index.json'
ALL_DOCS_FILE = 'all_docs.json'
URL_INDEX_FILE = os.path.join('..', 'task1', 'index.txt')

morph = pymorphy2.MorphAnalyzer()


def load_data(index_f, docs_f, url_f):
    inverted_index, all_docs, doc_id_to_url = None, None, {}
    #загрузка инвертированного индекса и списка всех документов
    try:
        if not os.path.exists(index_f) or not os.path.exists(docs_f):
            print(f"ошибка: '{index_f}' или '{docs_f}' не найдены. \n python build_index.py.")
            return None, None, None

        with open(index_f, 'r', encoding='utf-8') as f:
            serializable_index = json.load(f)
        with open(docs_f, 'r', encoding='utf-8') as f:
            serializable_docs = json.load(f)

        inverted_index = {k: set(v) for k, v in serializable_index.items()}
        all_docs = set(serializable_docs)

    except Exception as e:
        print(f"ошибка загрузки инв. индекса: {e}")
        return None, None, None

    #загрузка URL маппинга
    abs_url_filepath = os.path.abspath(url_f)
    if os.path.exists(abs_url_filepath):
        with open(abs_url_filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                parts = line.strip().split(' ', 1)
                if len(parts) == 2:
                    try:
                        doc_num = int(parts[0])
                        doc_id = f"выкачка{doc_num}"
                        doc_id_to_url[doc_id] = parts[1].strip()
                    except ValueError:
                        print(f"неверны номер в строке {i + 1}. url: {line.strip()}")

    return inverted_index, all_docs, doc_id_to_url


def token_sorting(tokens):
    # преобразование в RPN
    # (A + B) * C -> A B + C *
    output_queue, operator_stack = deque(), []
    precedence = {'NOT': 3, 'AND': 2, 'OR': 1}
    associativity = {'NOT': 'RIGHT', 'AND': 'LEFT', 'OR': 'LEFT'}
    for token in tokens:
        if isinstance(token, str) and token not in precedence and token not in ['(', ')']:
            output_queue.append(token)
        elif token == '(':
            operator_stack.append(token)
        elif token == ')':
            while operator_stack and operator_stack[-1] != '(': output_queue.append(operator_stack.pop())
            if not operator_stack or operator_stack[-1] != '(': raise ValueError("Скобки не согласованы.")
            operator_stack.pop()
        elif token in precedence:
            while (operator_stack and operator_stack[-1] != '(' and
                   ((associativity[token] == 'LEFT' and precedence.get(operator_stack[-1], 0) >= precedence[token]) or
                    (associativity[token] == 'RIGHT' and precedence.get(operator_stack[-1], 0) > precedence[token]))):
                output_queue.append(operator_stack.pop())
            operator_stack.append(token)
        else:
            raise ValueError(f"неизвестный токен: {token}")
    while operator_stack:
        if operator_stack[-1] == '(': raise ValueError("ошибка со скобками")
        output_queue.append(operator_stack.pop())
    return list(output_queue)


def evaluate_rpn(rpn_tokens, index, all_docs):
    # для хранения промежуточных результатов (множеств ID документов)
    eval_stack = []
    ops = {
        'AND': lambda l, r: l.intersection(r),
        'OR': lambda l, r: l.union(r),
        'NOT': lambda op: all_docs.difference(op)
    }
    for token in rpn_tokens:
        try:
            if token in ('AND', 'OR'):
                #right,left - мн-ва соотв слева или справа от конкретного токена
                right, left = eval_stack.pop(), eval_stack.pop()
                #вместо двух исходных множеств - результат соотв фунуции (из ops) над множествами
                eval_stack.append(ops[token](left, right))
            #not - cнимаем со стека один верхний элемент, функция, кладем обратно
            elif token == 'NOT':
                operand = eval_stack.pop()
                eval_stack.append(ops[token](operand))
            else:
                # исходный токен - терм
                #по умолчанию лемма - это терм в нижнем регистре
                term = token
                lemma = term.lower()
                if term.isalpha():
                    parsed = morph.parse(term)
                    if parsed:
                        lemma = parsed[0].normal_form
                # Получаем ID документов для леммы. если нет, вернется просто пустой сет
                postings = index.get(lemma, set())
                eval_stack.append(postings)
        except IndexError:
            raise ValueError(f"стек пуст для {token}.")
    if len(eval_stack) != 1: raise ValueError("ошибка вычисления RPN")
    return eval_stack[0]


def tokenize_query(query):
    #токенизация запроса по регекс
    query = query.replace('(', ' ( ').replace(')', ' ) ')
    tokens = re.findall(r'\(|\)|\bAND\b|\bOR\b|\bNOT\b|\w+', query, re.IGNORECASE)
    return [t.upper() if t.upper() in ('AND', 'OR', 'NOT', '(', ')') else t
            for t in tokens if t.isalnum() or t in ('(', ')')]


def perform_search(query, index, all_docs):
    if not query or not index or not all_docs: return set()
    try:
        tokens = tokenize_query(query)
        if not tokens: return set()
        rpn = token_sorting(tokens)
        return evaluate_rpn(rpn, index, all_docs)
    except ValueError as e:
        print(f"Ошибка в запросе: {e}")
    except Exception as e:
        print(f"Ошибка поиска: {e}")
    return set()



if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    index_file_path = os.path.join(script_dir, INDEX_FILE)
    docs_file_path = os.path.join(script_dir, ALL_DOCS_FILE)
    url_index_file_path = os.path.join(script_dir, URL_INDEX_FILE)

    inverted_index, all_doc_ids, doc_id_to_url = load_data(
        index_file_path, docs_file_path, url_index_file_path
    )
    if inverted_index is None: exit(1)

    print("\n--- Булев поиск ---")
    print("Введите запрос (или 'quit'/'exit' для выхода):")
    while True:
        try:
            user_query = input("Запрос> ").strip()
            if user_query.lower() in ['quit', 'exit']: break
            if not user_query: continue

            results = perform_search(user_query, inverted_index, all_doc_ids)

            if results:
                print(f"Найдено документов: {len(results)}")
                try:
                    sorted_ids = sorted(list(results), key=lambda x: int(re.search(r'\d+', x).group()))
                except:
                    sorted_ids = sorted(list(results))
                for doc_id in sorted_ids:
                    print(f"- {doc_id}: {doc_id_to_url.get(doc_id, 'URL не найден')}")
            else:
                print("Документы не найдены.")
            print("-" * 60)
        except KeyboardInterrupt:
            print("\nВыход."); break
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
