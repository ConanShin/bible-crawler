#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# List of English versions
VERSIONS=("NIV" "ESV" "NKJV" "NLT" "NASB" "KJV")

echo "🚀 Starting batch crawl for English versions..."

for ver in "${VERSIONS[@]}"; do
    echo "----------------------------------------"
    echo "📖 Crawling Version: $ver"
    echo "----------------------------------------"
    
    export BIBLE_VERSION=$ver
    python3 main.py --crawl
    
    if [ $? -eq 0 ]; then
        echo "✅ Finished $ver"
    else
        echo "❌ Failed $ver"
    fi
    
    sleep 2
done

echo "🎉 English versions processed."
