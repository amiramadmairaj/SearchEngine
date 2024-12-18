import os
import json
import string
import sys
import csv
import re
from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer
from collections import Counter, defaultdict
from urllib.parse import urldefrag

inverted_index = defaultdict(list)
num_documents = 0
alphabet = list(string.ascii_lowercase)
track_visited_urls = set()


"""
Main function to initiate the indexing process.
This function sets the file_path and calls the `process` function.
"""
def main():
    file_path = '/Users/amirmairaj/Desktop/DEV'
    process(file_path)
    print("==============================\nALL DOCUMENTS INDEXED SUCCESSFULLY\n==============================")


"""
Dump the inverted index to separate JSON files based on the first letter of each word.
Parameters:
    - ii (defaultdict): The inverted index to be dumped.
"""
def dump(ii):
    global alphabet
    if not os.path.exists('jsoninvertedindex'):
        os.makedirs('jsoninvertedindex')

    for letter in alphabet:
        holdinglist = []
        for word in ii.keys():
            if word[0] == letter:
                holdinglist.append(word)
        json_filename = f'jsoninvertedindex/{letter}.json'
        data_dict = defaultdict(list)
        if os.path.exists(json_filename):
            with open(json_filename, 'r') as f:
                data_dict = json.load(f)
        for word in holdinglist:
            try:
                data_dict[word] += ii[word]
            except KeyError:
                data_dict[word] = ii[word]
        with open(json_filename, 'w') as f:
            json.dump(data_dict, f)
        for deletethis in holdinglist:
            del ii[deletethis]

    json_filename = f'jsoninvertedindex/other.json'
    data_dict = defaultdict(list)
    if os.path.exists(json_filename):
        with open(json_filename, 'r') as f:
            data_dict = json.load(f)
    for word in ii.keys():
        try:
            data_dict[word] += ii[word]
        except KeyError:
            data_dict[word] = ii[word]
    with open(json_filename, 'w') as f:
        json.dump(data_dict, f)

    ii.clear()  # Clear the remaining values


"""
Convert a JSON string to a defaultdict object.
Parameters:
    - json_str (str): The JSON string to be converted.
Returns:
    - defaultdict: The converted defaultdict object.
"""
def json_to_defaultdict(json_str):
    def defaultdict_hook(pairs):
        result = defaultdict(list)
        result.clear()
        for key, value in pairs:
            result[key].append(value)
        return result

    return json.loads(json_str, object_pairs_hook=defaultdict_hook)


"""
Convert the inverted index from JSON files to a CSV file.
"""
def invertedindex_into_csv():
    directory_name = 'jsoninvertedindex'
    output_filename = 'inverted_index.csv'
    print("STARTING JSON TO CSV CONVERSION")
    with open(output_filename, 'w', newline='') as output_file:
        writer = csv.writer(output_file, escapechar='\\')
        # Iterate over all JSON files in the specified directory
        for filename in os.listdir(directory_name):
            if filename.endswith('.json'):
                file_path = os.path.join(directory_name, filename)
                with open(file_path, 'r') as input_file:
                    json_str = input_file.read()
                    dict = json_to_defaultdict(json_str)
                    for key, value in dict.items():
                        writer.writerow((key, value))
        writer.writerow(("Total Number of URLs Indexed", len(track_visited_urls)))

    print(f"Data merged and saved to {output_filename}")
    generate_index_of_index()


"""
Generate the index of index file (index_of_index.json).
This file contains the word and its corresponding line number in the CSV file for quick search.
"""
def generate_index_of_index(): #Enhance the index with word positions and use them for retrieval
    csv.field_size_limit(sys.maxsize)
    print("CREATING INDEX OF INDEX")
    index_of_index = {}  # {word: line in csv file}, able to use seek(line_no) -> instant search (hopefully)
    with open("inverted_index.csv", 'r') as input_file:
        reader = csv.reader(input_file)
        try:
            for index, word in enumerate(reader):
                index_of_index[word[0]] = index
        except csv.Error as e:
            print(f"Error reading CSV: {str(e)}")
    with open('index_of_index.json', 'w') as json_file:
        json.dump(index_of_index, json_file)


"""
Process the files in the given directory path.
This function iterates over the files, extracts tokens and URLs, and builds the inverted index.
Parameters:
    - file_path (str): The path to the directory containing the files to be processed.
"""
def process(file_path):
    global num_documents, track_visited_urls
    ps = PorterStemmer()
    for root, _, files in os.walk(file_path):
        print("CURRENT DIRECTORY:", root)
        for i in files:
            if os.path.splitext(i)[-1] != ".json":  # skip non-json files
                continue
            else:
                path = root + os.sep + i
                print(f"====================================\nCURRENT PATH: {path}\n======================================")
                get_tokens_and_url = tokenize_large_html_file(path)

                try:
                    token = get_tokens_and_url[0]
                    url = get_tokens_and_url[1]
                    defragmented_url, fragment = urldefrag(url)
                    urlhash = hash(defragmented_url)
                    if urlhash in track_visited_urls: #Detect and eliminate duplicate pages
                        continue
                    else:
                        track_visited_urls.add(defragmented_url)

                    num_documents += 1
                    print(f"FILE {i}")
                    print(f"DOCUMENT # {num_documents}")

                    stemmed = [ps.stem(t) for t in token]
                    word_freq = Counter(stemmed)

                    for word, freq in word_freq.items():
                        inverted_index[word].extend([(freq, defragmented_url)])

                except Exception as e:
                    return e
        print("******** COMPLETED INDEXING DIRECTORY, NOW DUMPING ********")
        dump(inverted_index)
    invertedindex_into_csv()


"""
Tokenize a large HTML file and extract tokens and the URL.
Parameters:
    - file_path (str): The path to the HTML file to be tokenized.
Returns:
    - tuple: A tuple containing the tokens (list) and the URL (str).
"""
def tokenize_large_html_file(file_path):
    with open(file_path, 'r') as file:
        try:
            data = json.load(file)
            soup = BeautifulSoup(data['content'], features='html.parser')
            words = soup.get_text()
            tokens = re.findall(r"\b[A-Za-z0-9]+\b", words.lower())
            return (tokens, data['url'])
        except Exception as E:
            print("Something went wrong", E)
            return


main()
