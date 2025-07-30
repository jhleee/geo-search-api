# 📚 Examples

이 폴더는 GeoTag API의 다양한 사용 예제를 포함합니다.

## 🎯 예제 스크립트

### 1. **demo.py** - 기본 기능 데모
- 위치 데이터 생성, 조회, 수정, 삭제
- 다양한 검색 방법 시연
- 성능 측정

### 2. **demo_korean.py** - 한국어 데이터 데모
- 한국 실제 위치 데이터 사용
- 한국어 검색 기능 시연
- 임베딩 모델 성능 확인

### 3. **bulk_data_example.py** - 대량 데이터 처리
- 벌크 API 사용법
- 500개 위치 동시 생성
- 성능 비교 (개별 vs 벌크)

### 4. **sample_generate.py** - 샘플 데이터 생성
- 10,000개 샘플 데이터 자동 생성
- 한국 주요 지역 좌표 사용
- 다양한 태그와 설명 조합

### 5. **test_unified_search.py** - 통합 검색 테스트
- 통합 검색 API 사용법
- 다양한 검색 옵션 조합
- 검색 결과 분석

## 🚀 실행 방법

API 서버를 먼저 실행한 후 예제를 실행하세요:

```bash
# API 서버 실행
python main.py

# 새 터미널에서 예제 실행
cd examples
python demo.py
```

## 📝 샘플 데이터

- **sample_locations.json**: 50개의 샘플 위치 데이터 (JSON 형식)