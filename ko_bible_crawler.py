import requests
import json
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any
from tqdm import tqdm
import re
import argparse

# Configuration (Merging some from existing config.py logic)
API_BASE_URL = "https://goodtvbible.goodtv.co.kr/api/onlinebible/bibleread/read-all"
OUTPUT_DIR = "output"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "ko_crawler.log")

# Version Mapping
# 0: 개역개정 (krv), 20: 새번역 (snkv), 3: 표준새번역 (ncv), 1: 개역한글 (ksv), 2: 공동번역 (kcb)
VERSIONS = {
    "krv": "0",
    "snkv": "20",
    "ncv": "3",
    "ksv": "1",
    "kcb": "2"
}

# Book Abbreviation Mapping (for fallbacks if API doesn't return bookname_abb)
BOOK_ABBR_MAP = {
    "누": "눅",
    "계": "계",
    # Most match, but we can add more if needed
}

# Book metadata structure (simplified from books_data.py for internal use if needed)
# But we can import from existing books_data.py
try:
    from books_data import BOOKS, BOOK_ORDER
except ImportError:
    # Fallback if not in the same dir
    BOOKS = {} 
    BOOK_ORDER = []

# Setup Logging
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class KoBibleCrawler:
    def __init__(self, version_name: str, version_id: str):
        self.version_name = version_name
        self.version_id = version_id
        self.results: Dict[str, str] = {}
        self.session = requests.Session()
        self.output_file = os.path.join(OUTPUT_DIR, f"bible_{version_name}_ko.json")
        
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Remove "○" and extra whitespace
        text = text.replace("○", "")
        return " ".join(text.split()).strip()

    def fetch_chapter(self, bible_code: int, chapter: int) -> List[Dict[str, Any]]:
        params = {
            'version1': self.version_id,
            'version2': '',
            'version3': '',
            'bible_code': bible_code,
            'jang': chapter
        }
        try:
            response = self.session.get(API_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            # The structure is data.data.version1.content
            content = data.get("data", {}).get("data", {}).get("version1", {}).get("content", [])
            bookname_abb = data.get("data", {}).get("bookname_abb", "")
            return content, bookname_abb
        except Exception as e:
            logging.error(f"Error fetching version {self.version_name} code {bible_code} jang {chapter}: {e}")
            return [], ""

    def crawl(self):
        logging.info(f"Starting crawl for {self.version_name} (ID: {self.version_id})")
        
        # We'll store results in a structure that's easy to sort: (bible_code, chapter, jul)
        temp_results = {}

        tasks = []
        for i, book_abbr in enumerate(BOOK_ORDER):
            book_info = BOOKS[book_abbr]
            bible_code = i + 1
            for chapter in range(1, book_info['chapters'] + 1):
                tasks.append((bible_code, chapter, book_abbr))

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_task = {executor.submit(self.fetch_chapter, bc, ch): (bc, ch, abbr) for bc, ch, abbr in tasks}
            
            with tqdm(total=len(tasks), desc=f"Crawling {self.version_name}", unit="chap") as pbar:
                for future in as_completed(future_to_task):
                    bc, ch, abbr = future_to_task[future]
                    try:
                        content, bookname_abb = future.result()
                        if not bookname_abb:
                            # Use mapping or fallback
                            bookname_abb = BOOK_ABBR_MAP.get(abbr, abbr)
                            
                        for item in content:
                            jul = item.get("jul")
                            text = item.get("text")
                            if jul is not None and text:
                                cleaned_text = self.clean_text(text)
                                key = f"{bookname_abb}{ch}:{jul}"
                                temp_results[(bc, ch, jul)] = (key, cleaned_text)
                    except Exception as e:
                        logging.error(f"Task failed for {abbr} {ch}: {e}")
                    pbar.update(1)

        # Sort by bible_code, chapter, jul
        sorted_keys = sorted(temp_results.keys())
        for k in sorted_keys:
            json_key, text = temp_results[k]
            self.results[json_key] = text

        self.save()

    def save(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"Saved {self.version_name} to {self.output_file}")

def crawl_version(v_name, v_id):
    crawler = KoBibleCrawler(v_name, v_id)
    crawler.crawl()
    return v_name, len(crawler.results)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", help="Specific version to crawl (krv, snkv, etc.)")
    args = parser.parse_args()

    if args.version:
        if args.version in VERSIONS:
            crawl_version(args.version, VERSIONS[args.version])
        else:
            print(f"Unknown version: {args.version}")
    else:
        # Parallel crawl all versions
        results = []
        with ThreadPoolExecutor(max_workers=len(VERSIONS)) as executor:
            future_to_v = {executor.submit(crawl_version, name, vid): name for name, vid in VERSIONS.items()}
            for future in as_completed(future_to_v):
                v_name, count = future.result()
                results.append((v_name, count))
        
        print("\nCrawl Summary:")
        for v_name, count in results:
            print(f"- {v_name}: {count} verses")
        
        # Verify counts
        counts = [r[1] for r in results]
        if len(set(counts)) == 1:
            print("\n✅ All versions have the same number of verses.")
        else:
            print("\n⚠️ Warning: Verse counts differ between versions!")
            for v_name, count in results:
                print(f"  {v_name}: {count}")

if __name__ == "__main__":
    main()
