import unittest
import os
import json
from crawler import BibleCrawler
from validator import BibleValidator
from config import OUTPUT_DIR

class TestBibleCrawler(unittest.TestCase):
    def setUp(self):
        self.crawler = BibleCrawler()
        self.test_output = os.path.join(OUTPUT_DIR, "test_bible_data.json")
        # Ensure output dir exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def test_fetch_genesis_1(self):
        print("\nTesting: Fetch Genesis Chapter 1...")
        chapter_data = self.crawler.fetch_chapter("창", 1)
        
        # Basic checks
        self.assertTrue(len(chapter_data) > 0, "Should return verses")
        self.assertIn("창1:1", chapter_data, "Should contain Genesis 1:1")
        print(f"Fetched {len(chapter_data)} verses.")
        print(f"Sample: 창1:1 -> {chapter_data.get('창1:1')}")

        # Save to test file
        with open(self.test_output, 'w', encoding='utf-8') as f:
            json.dump(chapter_data, f, ensure_ascii=False, indent=2)
        
        # Run Validator on test file
        print("Running Validator on test output...")
        validator = BibleValidator(json_path=self.test_output)
        validator.run()
        
        # We expect warnings because it's incomplete, but no errors
        self.assertEqual(len(validator.errors), 0, "Validator found errors")

    def test_fetch_psalms_1(self):
        print("\nTesting: Fetch Psalms Chapter 1...")
        # Psalms uses '편' instead of '장'
        chapter_data = self.crawler.fetch_chapter("시", 1)
        
        self.assertTrue(len(chapter_data) > 0, "Should return verses for Psalms")
        self.assertIn("시1:1", chapter_data, "Should contain Psalms 1:1")
        print(f"Fetched {len(chapter_data)} verses.")
        print(f"Sample: 시1:1 -> {chapter_data.get('시1:1')}")

    def tearDown(self):
        # Cleanup test file
        if os.path.exists(self.test_output):
            os.remove(self.test_output)

if __name__ == '__main__':
    unittest.main()
