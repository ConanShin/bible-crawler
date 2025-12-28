import requests
import json
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Tuple
from tqdm import tqdm
import re
import argparse

# Configuration
API_BASE_URL = "https://goodtvbible.goodtv.co.kr/api/onlinebible/bibleread/read-all"
OUTPUT_DIR = "output"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "goodtv_crawler.log")

# Version Mapping
# Korean: 0: krv, 20: snkv, 3: ncv, 1: ksv, 2: kcb
# English: 6: kjv, 13: nasb, 5: niv, 14: esv
VERSIONS = {
    "krv": {"id": "0", "lang": "ko"},
    "snkv": {"id": "20", "lang": "ko"},
    "ncv": {"id": "3", "lang": "ko"},
    "ksv": {"id": "1", "lang": "ko"},
    "kcb": {"id": "2", "lang": "ko"},
    "kjv": {"id": "6", "lang": "en"},
    "nasb": {"id": "13", "lang": "en"},
    "niv": {"id": "5", "lang": "en"},
    "esv": {"id": "14", "lang": "en"}
}

# Book Abbreviation Mapping (for fallbacks if API doesn't return bookname_abb)
BOOK_ABBR_MAP = {
    "누": "눅",
    "계": "계",
}

# Import standard book metadata
try:
    from books_data import BOOKS, BOOK_ORDER
except ImportError:
    BOOKS = {} 
    BOOK_ORDER = []

# Setup Logging
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class GoodTVBibleCrawler:
    def __init__(self, version_name: str, version_id: str, lang: str):
        self.version_name = version_name
        self.version_id = version_id
        self.lang = lang
        self.results: Dict[str, str] = {}
        self.session = requests.Session()
        self.output_file = os.path.join(OUTPUT_DIR, f"bible_{version_name}_{lang}.json")
        
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Remove "○" and extra whitespace
        text = text.replace("○", "")
        return " ".join(text.split()).strip()

    def fetch_chapter(self, bible_code: int, chapter: int) -> Tuple[List[Dict[str, Any]], str]:
        params = {
            'version1': self.version_id,
            'version2': '',
            'version3': '',
            'bible_code': bible_code,
            'jang': chapter
        }
        try:
            response = self.session.get(API_BASE_URL, params=params, timeout=15)
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
                                # The requirement is bookname_abb + jang + ":" + jul
                                # For English versions, API still returns "창", "출" etc.
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

def crawl_version(v_name):
    v_info = VERSIONS[v_name]
    crawler = GoodTVBibleCrawler(v_name, v_info["id"], v_info["lang"])
    crawler.crawl()
    return v_name, len(crawler.results)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", help="Specific version to crawl (krv, kjv, etc.)")
    parser.add_argument("--all", action="store_true", help="Crawl all versions")
    parser.add_argument("--lang", help="Crawl all versions of a specific language (ko, en)")
    args = parser.parse_args()

    target_versions = []
    if args.version:
        if args.version in VERSIONS:
            target_versions.append(args.version)
        else:
            print(f"Unknown version: {args.version}")
            return
    elif args.lang:
        target_versions = [name for name, info in VERSIONS.items() if info["lang"] == args.lang]
    elif args.all:
        target_versions = list(VERSIONS.keys())
    else:
        print("Please specify --version, --lang, or --all")
        return

    if not target_versions:
        print("No versions to crawl.")
        return

    # Parallel crawl target versions
    results = []
    # Use fewer workers for versions to avoid overwhelming the server
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_v = {executor.submit(crawl_version, name): name for name in target_versions}
        for future in as_completed(future_to_v):
            try:
                v_name, count = future.result()
                results.append((v_name, count))
            except Exception as e:
                print(f"Error crawling {future_to_v[future]}: {e}")
    
    print("\nCrawl Summary:")
    for v_name, count in results:
        print(f"- {v_name}: {count} verses")
    
    # Verify counts within same language
    lang_results = {}
    for v_name, count in results:
        lang = VERSIONS[v_name]["lang"]
        if lang not in lang_results: lang_results[lang] = []
        lang_results[lang].append(count)
    
    for lang, counts in lang_results.items():
        if len(set(counts)) == 1:
            print(f"\n✅ All {lang} versions have the same number of verses ({counts[0]}).")
        else:
            print(f"\n⚠️ Warning: Verse counts differ between {lang} versions!")
            for v_name, count in results:
                if VERSIONS[v_name]["lang"] == lang:
                    print(f"  {v_name}: {count}")

if __name__ == "__main__":
    main()
