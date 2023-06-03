from flask import Flask, render_template, request
import json
from math import log10, sqrt
from nltk.stem import PorterStemmer
import csv
import ast
import sys
import time
import mmap
from collections import deque

app = Flask(__name__)

csv.field_size_limit(sys.maxsize)
N = 0
index_of_index = {}
start_time = 0
end_time = 0
cache = {}



def load_index():
    global index_of_index, N
    with open('index_of_index.json', 'r') as ioi_file:
        index_of_index = json.load(ioi_file)

    with open('inverted_index.csv', 'r') as f:
        q = deque(f, 1)
    q = q[0]
    number_of_files = q.split(',')[1].split('\n')[0].strip()
    N = number_of_files


def load_data():
    global index_of_index, N
    print("_+_+_+_+_+_Please wait until the search engine has warmed up..._+_+_+_+_+_")
    load_index()
    print("_+_+_+_+_+_!!Search Engine Ready!!_+_+_+_+_+_")


@app.before_request
def setup():
    load_data()


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/search', methods=['POST'])
def search():
    query_string = request.form['query']
    result = execute_search(query_string)
    elapsed_time = end_time - start_time
    print(elapsed_time)
    elapsed_time = "{:.10f}".format(elapsed_time)
    if len(result) == 0:
        return render_template("index.html", no_results=True)
    else:
        results = []
        for url, confidence in result:
            results.append({'url': url, 'confidence': confidence, 'time': elapsed_time})
        return render_template("index.html", results=results, query=query_string, elapsed_time=elapsed_time)


def word_scoring(tf, df, N):
    idf = tf * log10(N / df)
    return idf


def execute_search(query):
    global index_of_index, N, start_time, end_time, cache
    resp = {}
    splitted_query = query.lower().split()
    ps = PorterStemmer()
    start_time = time.time()
    for word in splitted_query:
        print(word)
        stemmed_word = ps.stem(word)
        try:
            seek_value = index_of_index[stemmed_word]  # url hash, word freq
            if len(splitted_query) == 1 and stemmed_word in cache.keys():
                end_time = time.time()
                print("its cached", cache)
                return cache[stemmed_word]

        except:
            return []
        filename = 'inverted_index.csv'
        with open(filename, 'r') as file:
            with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as mapped_file:
                current_line_number = 0
                line_start = 0
                while current_line_number < seek_value:
                    line_start = mapped_file.find(b'\n', line_start) + 1
                    current_line_number += 1
                mapped_file.seek(line_start)
                doc = mapped_file.readline().decode()
                split_result = doc.split(',', 1)
                _, modified_string = split_result
                docs_as_str = ast.literal_eval(modified_string)
                remove_brackets = docs_as_str[1:-1]
                list_of_docs = ast.literal_eval(remove_brackets)
                docs = list_of_docs

        end_time = time.time()

        df = len(docs)  # number of documents containing stemmed_word
        query_term_freq = splitted_query.count(word)
        query_vector_length = sqrt(sum(query_term_freq * query_term_freq for _ in splitted_query))
        for d in docs:
            tf, url = d[0], d[1]
            score = word_scoring(int(tf), int(df), int(N))
            doc_vector_length = sqrt(sum(int(tf) * int(tf) for tf, _ in docs))
            dot_product = query_term_freq * int(tf)
            cosine_similarity = dot_product / (query_vector_length * doc_vector_length)
            try:
                resp[url] += score * cosine_similarity
            except:
                resp[url] = score * cosine_similarity

    sorted_by_idf = sorted(resp.items(), key=lambda x: x[1], reverse=True)[:5]  # sort by value
    cache[stemmed_word] = sorted_by_idf
    return sorted_by_idf

# #Implement the summarization of the resulting pages using the OpenAI API and show the short summaries in the web GUI.
# def gpt_summary(query_string):
#
#     openai.api_key = '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'
#
#     result = openai.Completion.create(
#         engine='text-davinci-003',
#         prompt=f" As best as you can, give me a brief summary of this users search query: {query_string}",
#         max_tokens=1000,
#         temperature=0.3,
#         top_p=1.0,
#         frequency_penalty=0.0,
#         presence_penalty=0.0
#     )
#
#     summary = result.choices[0].text.strip()
#     return summary


if __name__ == '__main__':
    app.run(debug=True)
