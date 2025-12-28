import requests
from bs4 import BeautifulSoup
import time
import json
import os
import logging
from typing import Dict, Optional, List
from tqdm import tqdm
from fake_useragent import UserAgent
import re

from config import (
    BIBLE_COM_BASE_URL, BIBLE_COM_VERSION_IDS, VERSION, REQUEST_TIMEOUT, 
    REQUEST_DELAY, MAX_RETRIES, RETRY_BACKOFF, OUTPUT_FILE, LOG_FILE, ENCODING,
    TOTAL_VERSES_EXPECTED
)
from books_data import BOOKS, BOOK_ORDER

# Setup Logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class BibleComCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.results: Dict[str, str] = {}
        
    def _get_headers(self) -> Dict[str, str]:
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

    def fetch_chapter(self, book_abbr: str, chapter: int) -> Dict[str, str]:
        """
        Fetches all verses for a given book and chapter from Bible.com
        Example URL: https://www.bible.com/bible/111/GEN.1.NIV
        """
        version_id = BIBLE_COM_VERSION_IDS.get(VERSION)
        if not version_id:
            logging.error(f"Version ID for {VERSION} not found.")
            return {}

        book_url_abbr = BOOKS[book_abbr]['url_abbr'].upper()
        url = f"{BIBLE_COM_BASE_URL}/{version_id}/{book_url_abbr}.{chapter}.{VERSION}"
        
        retries = 0
        while retries <= MAX_RETRIES:
            try:
                response = self.session.get(
                    url, 
                    headers=self._get_headers(), 
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                return self._parse_verses(book_abbr, chapter, response.text)
            except Exception as e:
                retries += 1
                wait_time = RETRY_BACKOFF ** retries
                logging.error(f"Error fetching {book_abbr} {chapter}: {e}. Retry {retries}/{MAX_RETRIES} in {wait_time}s")
                if retries > MAX_RETRIES:
                    logging.critical(f"Failed to fetch {book_abbr} {chapter} after {MAX_RETRIES} retries.")
                    return {}
                time.sleep(wait_time)
        return {}

    def _parse_verses(self, book_abbr: str, chapter: int, html_content: str) -> Dict[str, str]:
        """
        Parses Bible.com HTML structure.
        Verses are typically structured with span classes like 'verse v1', then 'label' for number and 'content' for text.
        """
        soup = BeautifulSoup(html_content, 'lxml')
        chapter_verses = {}
        
        # Bible.com classes as of 2025/12
        # Container class: starts with "ChapterContent_verse"
        # Label class: starts with "ChapterContent_label"
        # Content class: starts with "ChapterContent_content"
        verse_spans = soup.find_all('span', class_=re.compile(r'ChapterContent_verse'))
        
        current_verse_num = None
        current_verse_text = []

        for span in verse_spans:
            # Extract verse number if present
            label_span = span.find('span', class_=re.compile(r'ChapterContent_label'))
            if label_span:
                # If we were collecting text for a previous verse, save it
                if current_verse_num is not None and current_verse_text:
                    key = f"{book_abbr}{chapter}:{current_verse_num}"
                    chapter_verses[key] = ''.join(current_verse_text).strip()
                
                try:
                    current_verse_num = int(label_span.get_text().strip())
                except ValueError:
                    # Might be sub-verse marker or verse letter
                    pass
                current_verse_text = []

            # Extract content text
            content_spans = span.find_all('span', class_=re.compile(r'ChapterContent_content'))
            for content in content_spans:
                text = content.get_text() # Get full text including space
                if text:
                    current_verse_text.append(text)

        # Save the last verse collected
        if current_verse_num is not None and current_verse_text:
            key = f"{book_abbr}{chapter}:{current_verse_num}"
            chapter_verses[key] = ' '.join(current_verse_text).strip()

        return chapter_verses

    def crawl_all(self):
        logging.info(f"Starting crawl for {VERSION} from Bible.com")
        
        with tqdm(total=TOTAL_VERSES_EXPECTED, desc=f"Progress {VERSION}") as pbar:
            for book_abbr in BOOK_ORDER:
                book_info = BOOKS[book_abbr]
                for chapter in range(1, book_info['chapters'] + 1):
                    chapter_data = self.fetch_chapter(book_abbr, chapter)
                    if chapter_data:
                        self.results.update(chapter_data)
                        pbar.update(len(chapter_data))
                    time.sleep(REQUEST_DELAY)
                    
        self.save_to_json()

    def save_to_json(self):
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 JSON saved: {OUTPUT_FILE}")
            print(f"📊 Total verses: {len(self.results):,} items")
        except Exception as e:
            logging.error(f"Error saving JSON: {e}")

if __name__ == "__main__":
    # Test for Genesis 1 NIV
    import os
    os.environ["BIBLE_VERSION"] = "NIV"
    crawler = BibleComCrawler()
    print(crawler.fetch_chapter("창", 1))
