This is a Search Engine I created to parse data on UCI ICS subdomains. There is a functioanlity to connect with the OpenAI API for search summaries, but this feature has been removed for the sake of not having a current API Key. 

Here is how to get started:
(1). First you must run the file entitled M3Indexer.py, this creates an Inverted Index in the CWD for the actual search engine to use. This is a large file so it is saved as a CSV file so that it is stored in main memory and not RAM. NOTE: This file does take quite a while to run, this is so searching itself can be fast. 
(2). You can now run either the command line interface of the web scraper or the GUI (file names SearchEngineNoGUI.py, and SearchEngineWithGUI.py respectively). 
Once run, you can enter search terms such as "Machine Learning" and see what the most recommended result is. This recommendation is NOT simply just the count of the frequency of the Term, but instead, all potential matches to the term are scored and the most relevant results are returned only.



<img width="985" alt="webscraper copy" src="https://github.com/amiramadmairaj/SearchEngine/assets/75645123/2f24a73e-701a-4285-a83e-deecb2cd87d4">
