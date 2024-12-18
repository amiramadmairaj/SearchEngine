from math import log10, sqrt
import json
from nltk.stem import PorterStemmer
import csv
import ast
import sys
import time
from collections import deque
import mmap

csv.field_size_limit(sys.maxsize)
N = 0
index_of_index = {}
start_time = 0
end_time = 0

def load_index():
    global index_of_index, N
    with open('index_of_index.json', 'r') as ioi_file:
        index_of_index = json.load(ioi_file)

    with open('inverted_index.csv', 'r') as f:
        q = deque(f, 1)
    q = q[0]
    number_of_files = q.split(',')[1].split('\n')[0].strip()
    N = number_of_files

    with open('inverted_index.csv', 'r') as file:
        return file


def main():
    global index_of_index, N, start_time, end_time

    print("_+_+_+_+_+_Please wait until the search engine has warmed up..._+_+_+_+_+_")
    load_index()
    print("_+_+_+_+_+_!!Search Engine Ready!!_+_+_+_+_+_")

    while True:
        query_string = input("Enter Search (type 'q' to quit): ").lower()
        if query_string == 'q':
            quit()
        else:
            result = search(query_string)
            elapsed_time = end_time - start_time
            print(elapsed_time)
            if len(result) == 0:
                print("Sorry, this search returned no results.")
            else:
                try:
                    for result, confidence in result[:5]:
                        print("URL: ", result, "Relevance Score: ", confidence)
                except:
                    # less than 5 results
                    for result, confidence in result:
                        print("URL: ", result, "Relevance Score: ", confidence)

def search(query):
    global index_of_index, N, start_time, end_time
    resp = {}
    splitted_query = query.split()
    ps = PorterStemmer()

    for word in splitted_query:
        stemmed_word = ps.stem(word)
        try:
            start_time = time.time()
            seek_value = index_of_index[stemmed_word]  # url hash, word freq
            print("WORD",stemmed_word)
            print("FOUND HERE", index_of_index[stemmed_word])
            filename = 'inverted_index.csv'
            with open(filename, 'r') as file:
                with mmap.mmap(file.fileno(), 0, access = mmap.ACCESS_READ) as mapped_file:
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
        except Exception as e:
            print(e)
            return []

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

    sorted_by_idf = sorted(resp.items(), key=lambda x: x[1], reverse=True)  # sort by value
    return sorted_by_idf

def word_scoring(tf, df, N):
    idf = tf * log10(N / df)
    return idf

main()
