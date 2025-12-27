import json
import os
import logging
import re
from typing import Dict, List, Tuple
from config import OUTPUT_FILE, TOTAL_VERSES_EXPECTED
from books_data import BOOKS, BOOK_ORDER

# Setup minimal logging for validation
logging.basicConfig(level=logging.INFO, format='%(message)s')

class BibleValidator:
    def __init__(self, json_path: str = OUTPUT_FILE):
        self.json_path = json_path
        self.data: Dict[str, str] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def load_data(self) -> bool:
        if not os.path.exists(self.json_path):
            self.errors.append(f"File not found: {self.json_path}")
            return False
        
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return True
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON format: {e}")
            return False

    def validate_structure(self):
        """Validates that keys follow the pattern 'BookAbbrChapter:Verse'"""
        # Pattern: Korean/English chars + Digits + : + Digits
        pattern = r'^[가-힣A-Za-z0-9]+[0-9]+:[0-9]+$'
        for key, value in self.data.items():
            if not re.match(pattern, key):
                self.errors.append(f"Invalid key format: {key}")
            
            if not isinstance(value, str) or not value.strip():
                self.errors.append(f"Invalid value for {key}: {value}")

    def validate_completeness(self):
        """Checks if all books and chapters are present (heuristically)"""
        # Group by book
        book_counts = {abbr: 0 for abbr in BOOK_ORDER}
        
        for key in self.data.keys():
            # Extract book abbr (this is a bit tricky without a delimiter, 
            # but our abbrs are English letters and chapters are numbers)
            match = re.match(r'^([A-Za-z]+)([0-9]+):([0-9]+)$', key)
            if match:
                abbr = match.group(1)
                # chapter = int(match.group(2))
                if abbr in book_counts:
                    book_counts[abbr] += 1
                else:
                    self.errors.append(f"Unknown book abbreviation in key: {key}")

        # Check against expected counts (if we had exact verse counts per book, we'd check that.
        # For now, just check if we have > 0 verses for expected books)
        for abbr, count in book_counts.items():
            if count == 0:
                self.warnings.append(f"Missing data for book: {BOOKS[abbr]['name']} ({abbr})")
        
        total_verses = len(self.data)
        logging.info(f"Total verses found: {total_verses}")
        
        if total_verses < TOTAL_VERSES_EXPECTED * 0.9: # Allow some margin if there are discrepancies
            self.warnings.append(f"Total verse count ({total_verses}) is significantly lower than expected ({TOTAL_VERSES_EXPECTED})")

    def run(self):
        logging.info(f"Validating {self.json_path}...")
        if not self.load_data():
            self._print_results()
            return

        self.validate_structure()
        self.validate_completeness()
        self._print_results()

    def _print_results(self):
        if self.errors:
            logging.error("❌ Validation Failed with Errors:")
            for err in self.errors:
                logging.error(f"  - {err}")
        elif self.warnings:
            logging.warning("⚠️ Validation Passed with Warnings:")
            for warn in self.warnings:
                logging.warning(f"  - {warn}")
        else:
            logging.info("✅ Validation Passed Successfully!")

if __name__ == "__main__":
    validator = BibleValidator()
    validator.run()
