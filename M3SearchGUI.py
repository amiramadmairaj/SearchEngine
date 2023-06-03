from flask import Flask, render_template, request
import json
from math import log10, sqrt
from nltk.stem import PorterStemmer
import csv
from itertools import islice
import pandas as pd
import ast
import sys
import time
import openai

app = Flask(__name__)

"""EC: Implement a Web or local GUI interface instead of using the console. We used Tutorials Point to help write this file: https://www.tutorialspoint.com/flask/index.html"""

"""
Load the necessary data before handling any request.
This function reads the index_of_index.json and inverted_index.csv files,
and initializes global variables index_of_index and N.
"""
@app.before_request
def load_data():
    global index_of_index, N

    print("_+_+_+_+_+_Please wait until the search engine has warmed up..._+_+_+_+_+_")
    ioi = open('index_of_index.json', 'r')
    index_of_index = json.load(ioi)
    df = pd.read_csv('inverted_index.csv')
    N = df.iloc[-1][1]  # get number of documents indexed (N)
    print("_+_+_+_+_+_!!Search Engine Ready!!_+_+_+_+_+_")


"""
Render the index.html template for the home page.
"""
@app.route('/')
def index():
    return render_template("index.html")


"""
Handle the search request.
Extracts the query from the form data, executes the search using `execute_search` function,
and renders the index.html template with the search results.
"""
@app.route('/search', methods=['POST'])
def search():
    query_string = request.form['query']
    result = execute_search(query_string)
    if len(result) == 0:
        return render_template("index.html", no_results = True)
    else:
        results = []
        for url, confidence in result[:5]:
            elapsed_time = end_time - start_time
            print(elapsed_time)
            #summary = gpt_summary(query_string)
            results.append({'url': url, 'confidence': confidence})#, 'summary': summary})
        return render_template("index.html", results=results)

"""
Calculate the IDF (Inverse Document Frequency) score for a given word in the search query.
Parameters:
    - tf (int): Term frequency (how many times the word appears in a document)
    - df (int): Document frequency (number of documents containing the word)
    - N (int): Total number of documents indexed
Returns:
    - idf (float): IDF score for the word
"""
def word_scoring(tf,df,N):
    idf = tf * log10( N / df)
    return idf


"""
Execute the search query.
Parameters:
    - query (str): The search query entered by the user
Returns:
    - sorted_by_idf (list): List of tuples containing the URLs and their relevance scores,
                           sorted in descending order of relevance.
"""
def execute_search(query):
    global index_of_index, N, start_time, end_time
    resp = {}
    splitted_query = query.lower().split()
    ps = PorterStemmer()
    start_time = time.time()
    for word in splitted_query:
        print(word)
        stemmed_word = ps.stem(word)
        try:
            seek_value = index_of_index[stemmed_word]  # url hash, word freq
        except:
            return []
        with open('inverted_index.csv', 'r') as csvfile:
            csv.field_size_limit(sys.maxsize)
            reader = csv.reader(csvfile)

            docs = next(islice(reader, seek_value, seek_value + 1))[1]
            docs, = ast.literal_eval(docs)
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
    end_time = time.time()
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