import requests
from bs4 import BeautifulSoup
from config import READ_PAGE_URL

def check_one_chapter_book():
    # Obadiah
    params = {
        'version': 'GAE',
        'book': 'oba', 
        'chap': 1,
        'range': 'all'
    }
    
    print(f"Fetching {READ_PAGE_URL} with params {params}")
    resp = requests.get(READ_PAGE_URL, params=params)
    resp.encoding = 'utf-8'
    
    soup = BeautifulSoup(resp.text, 'lxml')
    text = soup.get_text()
    
    clean_text = ' '.join(text.split())
    print("\n--- Extracted Text Preview (First 2000 chars) ---")
    print(clean_text[:2000])
    
    # Try to find where verse 1 starts
    marker = " 1 "
    if marker in clean_text:
        pos = clean_text.find(marker)
        print(f"\n--- Context around '{marker}' (pos {pos}) ---")
        print(clean_text[pos-50:pos+200])
    
    # Check for patterns
    print("\n--- Pattern Checks ---")
    print(f"'제 1 장' in text: {'제 1 장' in clean_text}")
    print(f"'오바댜' in text: {'오바댜' in clean_text}")

if __name__ == "__main__":
    check_one_chapter_book()
