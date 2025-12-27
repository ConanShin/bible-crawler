#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# List of versions to crawl
VERSIONS=("GAE" "HAN" "SAE" "SAENEW" "COG" "COGNEW")

echo "🚀 Starting batch crawl for all versions..."

for ver in "${VERSIONS[@]}"; do
    echo "----------------------------------------"
    echo "📖 Crawling Version: $ver"
    echo "----------------------------------------"
    
    # Run crawler with specific version
    export BIBLE_VERSION=$ver
    python3 main.py --crawl
    
    if [ $? -eq 0 ]; then
        echo "✅ Finished $ver"
    else
        echo "❌ Failed $ver"
    fi
    
    # Optional: Validate result
    # python3 main.py --validate
    
    # Sleep briefly between versions
    sleep 2
done

echo "🎉 All versions processed."
