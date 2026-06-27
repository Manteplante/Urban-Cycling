from bs4 import BeautifulSoup
import requests
import time  # Import time module for delays

def parse_html(html):
    print("Parsing HTML content ...")
    soup = BeautifulSoup(html, 'html.parser')
    return soup

def fetch_html(url):
    print(f"Fetching HTML content from: {url}")
    time.sleep(5)  # Wait 1 second before making request to be considerate
    response = requests.get(url)
    return response.text

def get_next_url(next_url):
    time.sleep(5)  # Add delay before processing next URL
    return next_url
