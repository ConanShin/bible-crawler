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
    READ_PAGE_URL, VERSION, REQUEST_TIMEOUT, REQUEST_DELAY,
    MAX_RETRIES, RETRY_BACKOFF, OUTPUT_FILE, LOG_FILE, ENCODING,
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

class BibleCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.results: Dict[str, str] = {}
        
    def _get_headers(self) -> Dict[str, str]:
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
        }

    def fetch_chapter(self, book_abbr: str, chapter: int) -> Dict[str, str]:
        """
        Fetches all verses for a given book and chapter.
        Returns a dictionary of { "AbbrChapter:Verse": "Text" }
        """
        url = READ_PAGE_URL
        params = {
            'version': VERSION,
            'book': BOOKS[book_abbr]['url_abbr'],
            'chap': chapter,
            'range': 'all'
        }
        
        retries = 0
        while retries <= MAX_RETRIES:
            try:
                response = self.session.get(
                    url, 
                    params=params, 
                    headers=self._get_headers(), 
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                response.encoding = ENCODING
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
        Parses HTML content to extract verses.
        The BSKorea site returns verses as plain text in format: "1 verse_text 2 verse_text..."
        """
        soup = BeautifulSoup(html_content, 'lxml')
        chapter_verses = {}
        
        # Get all text from the page
        full_text = soup.get_text()
        
        # Find the chapter heading to locate where verses start
        # Pattern: "제 N 장" (Chapter N) or "제 N 편" (Psalm N)
        # For 1-chapter books, the header "제 1 장" is often missing.
        chapter_pattern = rf'제\s*{chapter}\s*[장편]'
        chapter_match = re.search(chapter_pattern, full_text)
        
        if not chapter_match:
            # Fallback for 1-chapter books: BookName + Chapter
            book_name = BOOKS[book_abbr]['name']
            fallback_pattern = rf'{book_name}\s*{chapter}'
            chapter_match = re.search(fallback_pattern, full_text)
            
            if not chapter_match:
                logging.warning(f"Could not find chapter {chapter} heading for {book_abbr}")
                return {}
        
        # Extract text after the chapter heading
        text_after_chapter = full_text[chapter_match.end():]
        
        # Find verse pattern: number followed by Korean text
        # Pattern: digit(s) followed by spaces and Korean characters
        # We need to match: "1   태초에 하나님이..." "2   땅이..."
        # But stop at footnote markers like "1)" or before next chapter/section
        
        # Split by verse numbers (look ahead to preserve the number)
        # Match: one or more digits followed by whitespace and Korean text
        verse_pattern = r'(\d+)\s+([가-힣])'
        
        verses_raw = re.split(verse_pattern, text_after_chapter)
        
        # Process the split results
        # Format after split: ['', '1', '태', '초에...', '2', '땅', '이...', ...]
        i = 1  # Start from first verse number
        while i < len(verses_raw) - 2:
            try:
                verse_num = int(verses_raw[i])
                first_char = verses_raw[i + 1]
                verse_text_part = verses_raw[i + 2]
                
                # Combine first char with the rest
                verse_text = first_char + verse_text_part
                
                # Clean up the text
                # Remove footnote markers like "1)", "2)" etc
                verse_text = re.sub(r'\d+\)', '', verse_text)
                
                # Remove extra whitespace
                verse_text = ' '.join(verse_text.split())
                # Stop at certain markers (next section, etc)
                # Take only until we hit certain patterns
                stop_patterns = [
                    r'제\s*\d+\s*[장편]',      # Next chapter/psalm
                    r'성경\s*단어',          # Bible word search
                    r'[A-Z]{2,}',           # All caps (likely section headers)
                ]
                for pattern in stop_patterns:
                    match = re.search(pattern, verse_text)
                    if match:
                        verse_text = verse_text[:match.start()]
                        break
                
                verse_text = verse_text.strip()
                
                if verse_text and len(verse_text) > 3:  # Reasonable verse length
                    key = f"{book_abbr}{chapter}:{verse_num}"
                    chapter_verses[key] = verse_text
                    
                i += 3
            except (ValueError, IndexError):
                i += 1
                continue
        
        return chapter_verses

    def crawl_all(self):
        """
        Main loop to crawl all 66 books.
        """
        logging.info("Starting crawl of all 66 books.")
        total_books = len(BOOK_ORDER)
        
        with tqdm(total=TOTAL_VERSES_EXPECTED, desc="Total Progress") as pbar:
            for book_abbr in BOOK_ORDER:
                book_info = BOOKS[book_abbr]
                logging.info(f"Crawling {book_info['name']} ({book_info['chapters']} chapters)")
                
                for chapter in range(1, book_info['chapters'] + 1):
                    chapter_data = self.fetch_chapter(book_abbr, chapter)
                    if chapter_data:
                        self.results.update(chapter_data)
                        pbar.update(len(chapter_data))
                    
                    time.sleep(REQUEST_DELAY)
                    
        self.save_to_json()

    def save_to_json(self):
        """
        Saves the results to output/bible_data.json
        """
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            
            file_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
            print(f"\n💾 JSON saved: {OUTPUT_FILE} ({file_size:.1f} MB)")
            print(f"📊 Total verses: {len(self.results):,} items")
        except Exception as e:
            logging.error(f"Error saving JSON: {e}")
            print(f"❌ Error saving JSON: {e}")

if __name__ == "__main__":
    crawler = BibleCrawler()
    # For quick test:
    # print(crawler.fetch_chapter("창", 1))
    crawler.crawl_all()
