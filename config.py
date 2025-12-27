import os

# Base URLs
BASE_URL = "https://www.bskorea.or.kr"
# Modified pattern based on manual analysis:
# https://www.bskorea.or.kr/bible/korbibReadpage.php?version=GAE&book=gen&chap=1&range=all
READ_PAGE_URL = f"{BASE_URL}/bible/korbibReadpage.php"

# Version File Mapping
VERSION_FILES = {
    "GAE": "bible_krv.json",     # 개역개정
    "HAN": "bible_ksv.json",     # 개역한글
    "SAE": "bible_snkv.json",    # 새번역
    "SAENEW": "bible_ncv.json",  # 표준새번역
    "COG": "bible_kcb.json",     # 공동번역
    "COGNEW": "bible_kcb2.json", # 공동번역 개정판
}

# Version code (Default: 개역개정 GAE)
# Can be overridden by environment variable, e.g., BIBLE_VERSION=HAN python main.py
VERSION = os.getenv("BIBLE_VERSION", "GAE")

# HTTP Settings
REQUEST_TIMEOUT = 30  # seconds
REQUEST_DELAY = 1.0   # seconds (server load consideration)
MAX_RETRIES = 3       # retries on failure
RETRY_BACKOFF = 2     # exponential backoff (1s, 2s, 4s...)

# Async settings (if implemented)
USE_ASYNC = False
MAX_WORKERS = 5

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Files
# Determine filename based on VERSION, default to 'bible_data.json' if unknown
output_filename = VERSION_FILES.get(VERSION, "bible_data.json")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, output_filename)
LOG_FILE = os.path.join(LOG_DIR, "crawler.log")

# Data
TOTAL_VERSES_EXPECTED = 31102
TOTAL_BOOKS = 66
ENCODING = "utf-8"

# UI/Logging
DEBUG = False
VERBOSE = True
