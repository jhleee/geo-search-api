#!/usr/bin/env python3
"""
Korean Demo script for the Geo Tag API
Demonstrates all features with Korean language support
"""

import time
import json
from src.service import GeoTagService
from src.models import LocationCreate, LocationUpdate
from src.config import get_config

def print_separator(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}\n")

def print_results(results, search_type="검색"):
    print(f"{search_type} 결과 ({len(results)}개 발견):")
    print("-" * 40)
    for i, result in enumerate(results[:5], 1):  # Show only first 5
        location = result.location if hasattr(result, 'location') else result
        print(f"{i}. {location.description}")
        print(f"   위치: ({location.latitude:.4f}, {location.longitude:.4f})")
        print(f"   태그: {', '.join(location.tags)}")
        if hasattr(result, 'score') and result.score:
            print(f"   유사도 점수: {result.score:.3f}")
        if hasattr(result, 'distance_km') and result.distance_km:
            print(f"   거리: {result.distance_km:.2f} km")
        print()

def main():
    print("Geo Tag API 한국어 데모")
    print("한국어 임베딩을 지원하는 위치 태깅 및 검색 시스템")
    
    # Get configuration
    config = get_config()
    print(f"사용 중인 임베딩 모델: {config.embedding.model_name}")
    
    # Initialize service
    service = GeoTagService("demo_korean_geo_tags.db")
    
    print_separator("한국어 샘플 위치 생성")
    
    # Korean sample locations data
    korean_locations = [
        LocationCreate(
            latitude=37.5665, longitude=126.9780,
            tags=["카페", "와이파이", "조용한"],
            description="블루보틀 커피 - 조용하고 와이파이가 잘 되는 카페"
        ),
        LocationCreate(
            latitude=37.5511, longitude=126.9882,
            tags=["식당", "한식", "맛집"],
            description="명동교자 - 유명한 만두 전문점"
        ),
        LocationCreate(
            latitude=37.5796, longitude=126.9770,
            tags=["공원", "산책", "자연"],
            description="경복궁 - 조선시대 궁궐, 산책하기 좋은 곳"
        ),
        LocationCreate(
            latitude=37.5543, longitude=126.9706,
            tags=["쇼핑", "백화점", "명품"],
            description="롯데백화점 본점 - 명품 브랜드가 많은 백화점"
        ),
        LocationCreate(
            latitude=37.5170, longitude=127.0473,
            tags=["카페", "디저트", "인스타"],
            description="강남 티라미수 카페 - 인스타그램에서 유명한 디저트 카페"
        ),
        LocationCreate(
            latitude=37.5759, longitude=126.9768,
            tags=["서점", "문화", "독서"],
            description="교보문고 광화문점 - 큰 서점, 독서하기 좋은 곳"
        ),
        LocationCreate(
            latitude=37.5133, longitude=127.1028,
            tags=["레스토랑", "이탈리안", "데이트"],
            description="압구정 이탈리안 레스토랑 - 데이트하기 좋은 분위기"
        ),
        LocationCreate(
            latitude=37.5400, longitude=127.0700,
            tags=["헬스장", "운동", "피트니스"],
            description="건대 헬스클럽 - 최신 운동기구가 있는 헬스장"
        )
    ]
    
    # Create locations
    created_locations = []
    for i, location_data in enumerate(korean_locations, 1):
        location = service.create_location(location_data)
        created_locations.append(location)
        print(f"위치 {i} 생성됨: {location.description}")
        time.sleep(0.1)  # Small delay to show progress
    
    print(f"\n총 {len(created_locations)}개 위치가 성공적으로 생성되었습니다!")
    
    print_separator("기본 CRUD 작업")
    
    # Get a location
    print("ID로 위치 조회:")
    location = service.get_location(created_locations[0].id)
    print(f"   {location.description}")
    print(f"   태그: {', '.join(location.tags)}")
    
    # Update a location
    print("\n위치 정보 업데이트:")
    update_data = LocationUpdate(
        description="블루보틀 커피 - 프리미엄 원두를 사용하는 조용한 작업 공간",
        tags=["카페", "와이파이", "조용한", "작업공간", "프리미엄"]
    )
    updated_location = service.update_location(created_locations[0].id, update_data)
    print(f"   업데이트됨: {updated_location.description}")
    print(f"   새 태그: {', '.join(updated_location.tags)}")
    
    print_separator("한국어 텍스트 검색")
    
    # Korean text search
    korean_queries = ["카페", "한식 맛집", "데이트하기 좋은 곳"]
    for query in korean_queries:
        start_time = time.time()
        results = service.search_by_text(query, limit=3)
        search_time = (time.time() - start_time) * 1000
        
        print(f"검색어: '{query}' ({search_time:.1f}ms)")
        print_results(results, "텍스트 검색")
    
    print_separator("지리적 검색")
    
    # Location-based search around Seoul center
    print("서울 중심가 근처 검색:")
    start_time = time.time()
    results = service.search_by_location(37.5665, 126.9780, radius_km=3.0, limit=5)
    search_time = (time.time() - start_time) * 1000
    
    print(f"   검색 시간: {search_time:.1f}ms")
    print_results(results, "지리적 검색")
    
    print_separator("한국어 벡터 유사도 검색")
    
    # Wait for embeddings to be processed
    print("임베딩 처리 중...")
    time.sleep(2)
    
    # Korean vector similarity search
    korean_vector_queries = [
        "노트북으로 작업하기 좋은 카페",
        "로맨틱한 저녁 식사 장소",
        "책을 읽기 좋은 조용한 곳",
        "쇼핑하기 좋은 백화점"
    ]
    
    for query in korean_vector_queries:
        start_time = time.time()
        results = service.search_by_vector(query, limit=3, threshold=0.3)
        search_time = (time.time() - start_time) * 1000
        
        print(f"벡터 검색: '{query}' ({search_time:.1f}ms)")
        if results:
            print_results(results, "벡터 검색")
        else:
            print("   결과 없음 (인덱스가 더 많은 데이터나 훈련이 필요할 수 있음)")
        print()
    
    print_separator("시스템 통계")
    
    # Get system stats
    stats = service.get_stats()
    print("시스템 통계:")
    print(f"   총 위치 수: {stats['total_locations']}")
    print(f"   총 임베딩 수: {stats['total_embeddings']}")
    print(f"   임베딩 모델: {stats['embedding_model']}")
    print(f"   인덱스 타입: {stats['index_type']}")
    
    print_separator("성능 테스트")
    
    # Performance test with Korean queries
    print("한국어 성능 테스트 실행 중...")
    
    test_queries = [
        ("카페 와이파이", "text"),
        ("맛있는 한식", "text"),
        ("조용한 작업공간이 있는 카페", "vector"),
        (37.5665, 126.9780, 2.0, "location")
    ]
    
    total_time = 0
    total_searches = 0
    
    for query in test_queries:
        times = []
        for _ in range(3):  # Run each query 3 times
            start_time = time.time()
            
            if query[1] == "text":
                results = service.search_by_text(query[0], limit=10)
            elif query[1] == "vector":
                results = service.search_by_vector(query[0], limit=10, threshold=0.2)
            elif query[1] == "location":
                results = service.search_by_location(query[0], query[1], query[2], limit=10)
            
            search_time = (time.time() - start_time) * 1000
            times.append(search_time)
            total_time += search_time
            total_searches += 1
        
        avg_time = sum(times) / len(times)
        query_desc = query[0] if isinstance(query[0], str) else f"위치 근처 ({query[0]:.3f}, {query[1]:.3f})"
        print(f"   {query[-1]} 검색 '{query_desc}': {avg_time:.1f}ms 평균")
    
    overall_avg = total_time / total_searches
    print(f"\n전체 평균 검색 시간: {overall_avg:.1f}ms")
    print(f"총 검색 횟수: {total_searches}")
    
    print_separator("데모 완료")
    
    print("한국어 데모가 성공적으로 완료되었습니다!")
    print(f"데이터베이스 저장됨: demo_korean_geo_tags.db")
    print(f"FAISS 인덱스 저장됨: faiss_index.bin")
    print("\nAPI 서버 실행:")
    print("   python main.py")
    print("\n한국어 지원 API 문서:")
    print("   http://localhost:8000/docs")
    
    # Show model configuration
    print(f"\n현재 설정:")
    print(f"   모델: {config.embedding.model_name}")
    print(f"   차원: {config.embedding.dimension}")
    print(f"   쿼리 프리픽스 사용: {config.embedding.use_query_prefix}")
    print(f"   패시지 프리픽스 사용: {config.embedding.use_passage_prefix}")

if __name__ == "__main__":
    main()