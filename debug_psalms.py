import requests
from bs4 import BeautifulSoup
from config import READ_PAGE_URL, VERSION
from books_data import BOOKS

def check_psalms():
    url = READ_PAGE_URL
    params = {
        'version': VERSION,
        'book': 'psa', # Psalms
        'chap': 1,
        'range': 'all'
    }
    
    print(f"Fetching {url} with params {params}")
    resp = requests.get(url, params=params)
    resp.encoding = 'utf-8'
    
    soup = BeautifulSoup(resp.text, 'lxml')
    text = soup.get_text()
    
    # Normalize whitespace for easier reading
    clean_text = ' '.join(text.split())
    print("\n--- Extracted Text Preview (First 500 chars) ---")
    print(clean_text[:500])
    
    # Check for "제 1 장" vs "제 1 편"
    if "제 1 장" in clean_text or "제1장" in clean_text:
        print("\nFound '제 1 장'")
    elif "제 1 편" in clean_text or "제1편" in clean_text:
        print("\nFound '제 1 편'")
    else:
        print("\nCould not find Chapter/Psalm heading.")

if __name__ == "__main__":
    check_psalms()
