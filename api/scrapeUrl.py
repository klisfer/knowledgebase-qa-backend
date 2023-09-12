from bs4 import BeautifulSoup
import requests
import os
from serpapi import GoogleSearch

def google_search_results(query):
    params = {
        "api_key": "6145e3a7bf290c43902f3056e6606140e624ee5566c66203ecbcd2212d749356",
        "engine": "google",
        "q": f"{query}",
        "location": "Austin, Texas, United States",
        "google_domain": "google.com",
        "gl": "us",
        "hl": "en"
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    return results

def scrape_url(url):
    base_url = "http://api.scraperapi.com"
    params = {
        "api_key": os.environ['SCRAPER_API_KEY'],
        "url": url,
        "render": True
    }
    
    
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        content = soup.get_text()
        content = content.strip()
        content = ' '.join(content.split())
       
        return {"text": content, "html" : response.text}
    else:
        print(f"Request failed with status code {response.status_code}")
