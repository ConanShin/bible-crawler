# Bible Crawler (성경 크롤러)

대한성서공회(bskorea.or.kr) 웹사이트에서 성경 구절을 수집하여 구조화된 JSON 데이터로 저장하는 파이썬 기반 웹 크롤러입니다.

## 기능 (Features)
- 성경 66권 전체 크롤링
- 다양한 성경 역본 지원 (개역개정, 개역한글, 새번역 등)
- 자동 재시도 및 에러 처리 (HTTP Retries)
- **데이터 검증**: JSON 구조 및 데이터 무결성 검증 도구 포함

## 사전 요구사항 (Prerequisites)
- Python 3.8 이상
- `pip` (Python 패키지 관리자)

## 설치 방법 (Installation)

1. 저장소를 클론하거나 다운로드합니다.
2. 가상 환경을 생성하고 활성화합니다:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. 의존성 패키지를 설치합니다:
   ```bash
   pip install -r requirements.txt
   ```

## 사용 방법 (Usage)

### 1. 특정 버전 크롤링
`BIBLE_VERSION` 환경 변수를 설정하여 특정 성경 역본을 크롤링할 수 있습니다.

```bash
# 기본 실행 (GAE: 개역개정)
python3 main.py --crawl

# 특정 버전 실행 (예: HAN: 개역한글)
BIBLE_VERSION=HAN python3 main.py --crawl
```

**지원되는 역본 목록:**
| 코드 | 이름 | 출력 파일명 |
|------|------|-----------------|
| `GAE` | 개역개정 | `bible_krv.json` |
| `HAN` | 개역한글 | `bible_ksv.json` |
| `SAE` | 새번역 | `bible_snkv.json` |
| `SAENEW` | 표준새번역 | `bible_ncv.json` |
| `COG` | 공동번역 | `bible_kcb.json` |
| `COGNEW` | 공동번역 개정 | `bible_kcb2.json` |

### 2. 전체 버전 일괄 크롤링 (Batch Mode)
지원되는 모든 역본을 순차적으로 크롤링하려면 아래 스크립트를 실행하세요:

```bash
./run_all_versions.sh
# 로그를 파일로 저장하려면:
# ./run_all_versions.sh > logs/batch_run.log 2>&1
```

### 3. 데이터 검증 (Validation)
수집된 데이터의 무결성(JSON 구조, 누락된 구절 확인 등)을 검사합니다:

```bash
# 기본 파일(개역개정) 검증
python3 main.py --validate

# 특정 역본 파일 검증
BIBLE_VERSION=HAN python3 main.py --validate
```

### 4. 전체 파이프라인 (크롤링 + 검증)
```bash
python3 main.py --full
```

## 디렉토리 구조
- `crawler.py`: 핵심 크롤러 로직
- `validator.py`: 데이터 무결성 검사 도구
- `books_data.py`: 성경 66권에 대한 메타데이터
- `config.py`: 설정 파일 (URL, 파일 경로, 버전 정보 등)
- `output/`: 생성된 JSON 파일이 저장되는 곳
- `logs/`: 애플리케이션 로그
