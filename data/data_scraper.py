# data_scraper.py

import requests
from bs4 import BeautifulSoup

# Function to scrape data from the DSV website
def scrape_dsv(URL):
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")

    return soup