#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# List of Korean versions
VERSIONS=("GAE" "HAN" "SAE" "SAENEW" "COG" "COGNEW")

echo "🚀 Starting batch crawl for Korean versions..."

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

echo "🎉 Korean versions processed."
