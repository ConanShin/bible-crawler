import requests
from bs4 import BeautifulSoup
from config import READ_PAGE_URL

def check_jonah():
    # Jonah
    params = {
        'version': 'GAE',
        'book': 'jon', 
        'chap': 1,
        'range': 'all'
    }
    
    print(f"Fetching {READ_PAGE_URL} with params {params}")
    resp = requests.get(READ_PAGE_URL, params=params)
    resp.encoding = 'utf-8'
    
    soup = BeautifulSoup(resp.text, 'lxml')
    text = soup.get_text()
    
    clean_text = ' '.join(text.split())
    print("\n--- Extracted Text Preview (First 1000 chars) ---")
    print(clean_text[:1000])
    
    # Check for patterns
    print("\n--- Pattern Checks ---")
    print(f"'제 1 장' in text: {'제 1 장' in clean_text}")
    print(f"'요나' in text: {'요나' in clean_text}")

if __name__ == "__main__":
    check_jonah()
