import argparse
import sys
import logging
from crawler import BibleCrawler
from bible_com_crawler import BibleComCrawler
from validator import BibleValidator
from config import VERSION, BIBLE_COM_VERSION_IDS

def main():
    parser = argparse.ArgumentParser(description="Bible Crawler & Validator")
    parser.add_argument('--crawl', action='store_true', help="Run the crawler")
    parser.add_argument('--validate', action='store_true', help="Run the validator")
    parser.add_argument('--full', action='store_true', help="Run full pipeline (crawl then validate)")
    
    args = parser.parse_args()
    
    # Default to full if no args provided
    if not (args.crawl or args.validate or args.full):
        print("No arguments provided. Use --help to see options.")
        return

    if args.crawl or args.full:
        print(f"🚀 Starting Crawler for version: {VERSION}...")
        
        # Select crawler based on version
        if VERSION in BIBLE_COM_VERSION_IDS:
            crawler = BibleComCrawler()
        else:
            crawler = BibleCrawler()
            
        try:
            crawler.crawl_all()
            print("✅ Crawling finished.")
        except KeyboardInterrupt:
            print("\n⚠️ Crawling interrupted by user.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Crawling failed: {e}")
            sys.exit(1)

    if args.validate or args.full:
        print("\n🔍 Starting Validation...")
        validator = BibleValidator()
        validator.run()

if __name__ == "__main__":
    main()
