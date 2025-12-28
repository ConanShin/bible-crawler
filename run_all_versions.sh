#!/bin/bash

echo "🚀 Starting full batch crawl (KO + EN)..."

chmod +x run_ko_versions.sh run_en_versions.sh

./run_ko_versions.sh
./run_en_versions.sh

echo "🎉 All language versions processed."
