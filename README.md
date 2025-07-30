# 🌍 GeoTag API - 지능형 위치 태깅 시스템

한국어에 최적화된 지능형 위치 태깅 및 검색 시스템입니다. SQLite, FAISS, 그리고 한국어 임베딩 모델을 활용하여 빠르고 정확한 위치 기반 검색을 제공합니다.

## ✨ 주요 기능

- **🔍 통합 검색 API**: 하나의 엔드포인트로 모든 검색 기능 제공
  - 텍스트 검색 (FTS5 기반 키워드 매칭)
  - 벡터 검색 (AI 임베딩 기반 의미 검색)
  - 위치 검색 (좌표 기반 근접 검색)
- **🚀 대용량 데이터 처리**: 벌크 API로 수천 개의 위치 데이터를 한 번에 처리
- **🇰🇷 한국어 최적화**: 한국어 특화 임베딩 모델 사용 (dragonkue/multilingual-e5-small-ko)
- **⚡ 고성능**: 100,000개 데이터에서 밀리초 단위 검색 속도
- **📊 완전한 CRUD**: 위치 데이터의 생성, 조회, 수정, 삭제 지원
- **🔧 유연한 설정**: YAML 기반 설정으로 쉬운 커스터마이징

## 🛠️ 기술 스택

- **Backend**: FastAPI, SQLite (FTS5, R-tree)
- **ML/AI**: Sentence Transformers, FAISS
- **Language Model**: dragonkue/multilingual-e5-small-ko
- **Configuration**: YAML 기반 설정 관리

## 📦 설치

### 1. 저장소 클론
```bash
git clone https://github.com/jhleee/geo-search-api.git
cd geo-search-api
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 설정 파일 확인
`config.yaml` 파일에서 필요에 따라 설정을 조정할 수 있습니다.

## 🚀 실행

### API 서버 시작
```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

API 문서는 http://localhost:8000/docs 에서 확인할 수 있습니다.

## 📝 API 사용법

### 통합 검색 API

#### 간단한 검색
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "카페"}'
```

#### 위치 기반 검색
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "음식점",
    "latitude": 37.5665,
    "longitude": 126.9780,
    "radius_km": 2.0
  }'
```

#### 맞춤형 검색
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "전통 한식 맛집",
    "use_text": true,
    "use_vector": true,
    "use_location": false,
    "vector_threshold": 0.3,
    "limit": 5
  }'
```

### 위치 데이터 관리

#### 단일 위치 생성
```bash
curl -X POST "http://localhost:8000/locations" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 37.5665,
    "longitude": 126.9780,
    "tags": ["카페", "와이파이"],
    "description": "조용한 분위기의 카페"
  }'
```

#### 대량 위치 생성 (벌크 API)
```bash
curl -X POST "http://localhost:8000/locations/bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {
        "latitude": 37.5665,
        "longitude": 126.9780,
        "tags": ["카페", "와이파이"],
        "description": "조용한 분위기의 카페"
      },
      {
        "latitude": 37.5735,
        "longitude": 126.9769,
        "tags": ["음식점", "한식"],
        "description": "전통 한식 맛집"
      }
    ]
  }'
```

## 💻 Python SDK 사용 예제

### 기본 사용법
```python
from src.service import GeoTagService
from src.models import LocationCreate

service = GeoTagService()

# 위치 생성
location = LocationCreate(
    latitude=37.5665,
    longitude=126.9780,
    tags=["카페", "와이파이", "조용한"],
    description="강남역 근처 조용한 카페"
)
result = service.create_location(location)
print(f"생성된 위치 ID: {result.id}")

# 통합 검색
from src.models import UnifiedSearchQuery

search_query = UnifiedSearchQuery(
    query="카페 와이파이",
    latitude=37.5665,
    longitude=126.9780,
    radius_km=2.0
)
results = service.unified_search(search_query)
```

## 📊 성능

- **검색 속도**: 100,000개 데이터에서 평균 50ms 이하
- **벌크 처리**: 500개 위치 데이터 동시 처리 가능
- **메모리 사용**: 100,000개 데이터 기준 약 500MB
- **임베딩 생성**: 위치당 약 10ms

### 검색 유형별 성능
- **텍스트 검색**: < 2ms
- **위치 검색**: < 1ms
- **벡터 검색**: ~10ms
- **통합 검색**: ~20ms

## 🧪 테스트

```bash
# 전체 테스트
pytest

# 특정 테스트
pytest tests/test_service.py

# 성능 테스트
pytest tests/test_performance.py -v

# 커버리지 확인
pytest --cov=src tests/
```

## 📁 프로젝트 구조

```
geotag-api/
├── src/                    # 소스 코드
│   ├── api.py             # FastAPI 엔드포인트
│   ├── service.py         # 비즈니스 로직
│   ├── database.py        # 데이터베이스 작업
│   ├── embeddings.py      # 임베딩 관리
│   ├── models.py          # Pydantic 모델
│   └── config.py          # 설정 관리
├── tests/                  # 테스트 코드
├── config.yaml            # 설정 파일
├── requirements.txt       # 의존성
└── README.md             # 문서
```

## 🔧 설정 옵션

`config.yaml`에서 다양한 옵션을 설정할 수 있습니다:

- **임베딩 모델**: 다른 한국어 모델로 변경 가능
- **검색 임계값**: 벡터 검색의 유사도 임계값 조정
- **성능 튜닝**: 스레드 수, 배치 크기 등
- **인덱스 타입**: FAISS 인덱스 종류 선택

### 저사양 환경

리소스가 제한된 환경에서의 실행:

```yaml
# config.yaml
performance:
  max_threads: 2
  memory_limit_mb: 512
  auto_save_interval: 300
```

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.
