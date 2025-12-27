"""
Quick test script to crawl a few sample books and generate a test JSON file.
This is faster than the full 66-book crawl and demonstrates the output format.
"""

from crawler import BibleCrawler
import json
import os

def test_crawler():
    """Test crawler with a few sample books"""
    crawler = BibleCrawler()
    
    # Sample books to test (covers different types)
    test_books = [
        ('창', 1, 2),    # Genesis chapters 1-2
        ('시', 1, 1),    # Psalms chapter 1 (tests "편" format)
        ('마', 1, 1),    # Matthew chapter 1
        ('계', 22, 22),  # Revelation chapter 22 (last chapter)
    ]
    
    print("🔄 Testing crawler with sample books...")
    print("=" * 60)
    
    for book_abbr, start_chap, end_chap in test_books:
        book_name = crawler.results.get(f"{book_abbr}1:1", {}) or BOOKS[book_abbr]['name']
        print(f"\n📚 Crawling {BOOKS[book_abbr]['name']}...")
        
        for chapter in range(start_chap, end_chap + 1):
            chapter_data = crawler.fetch_chapter(book_abbr, chapter)
            if chapter_data:
                crawler.results.update(chapter_data)
                print(f"  ✓ Chapter {chapter}: {len(chapter_data)} verses")
            else:
                print(f"  ✗ Chapter {chapter}: Failed")
    
    # Save test results
    test_output = "output/bible_data_test.json"
    os.makedirs(os.path.dirname(test_output), exist_ok=True)
    
    with open(test_output, 'w', encoding='utf-8') as f:
        json.dump(crawler.results, f, ensure_ascii=False, indent=2)
    
    file_size = os.path.getsize(test_output) / 1024
    print(f"\n💾 Test JSON saved: {test_output} ({file_size:.1f} KB)")
    print(f"📊 Total verses in test: {len(crawler.results):,}")
    
    # Show sample output
    print("\n📄 Sample verses:")
    for i, (key, value) in enumerate(list(crawler.results.items())[:5]):
        print(f"  {key}: {value[:60]}..." if len(value) > 60 else f"  {key}: {value}")
    
    print("\n✅ Test completed successfully!")
    return crawler.results

if __name__ == "__main__":
    from books_data import BOOKS
    test_crawler()
