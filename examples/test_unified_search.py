import requests
import json
import time

# API 기본 URL
BASE_URL = "http://localhost:8000"

def test_unified_search():
    """통합 검색 테스트"""
    
    print("=== 통합 검색 API 테스트 ===\n")
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "단순 키워드 검색",
            "query": {
                "query": "카페"
            }
        },
        {
            "name": "키워드 + 위치 검색",
            "query": {
                "query": "음식점",
                "latitude": 37.5665,
                "longitude": 126.9780,
                "radius_km": 2.0
            }
        },
        {
            "name": "벡터 검색만 사용",
            "query": {
                "query": "맛있는 한식",
                "use_text": False,
                "use_vector": True,
                "use_location": False
            }
        },
        {
            "name": "텍스트 검색만 사용",
            "query": {
                "query": "카페",
                "use_text": True,
                "use_vector": False,
                "use_location": False
            }
        },
        {
            "name": "모든 검색 방법 조합",
            "query": {
                "query": "전통 한식 맛집",
                "latitude": 37.5665,
                "longitude": 126.9780,
                "radius_km": 5.0,
                "use_text": True,
                "use_vector": True,
                "use_location": True,
                "vector_threshold": 0.3,
                "limit": 5
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}")
        print("=" * 50)
        
        try:
            # API 요청
            response = requests.post(
                f"{BASE_URL}/search",
                json=test_case['query'],
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"쿼리: {test_case['query']['query']}")
                print(f"검색 시간: {result['query_time_ms']:.2f}ms")
                print(f"사용된 검색 방법: {', '.join(result['search_types_used'])}")
                print(f"총 결과 수: {result['total_count']}")
                
                print("\n검색 요약:")
                summary = result['search_summary']
                for key, value in summary.items():
                    print(f"  {key}: {value}")
                
                print("\n상위 결과:")
                for j, search_result in enumerate(result['results'][:3], 1):
                    location = search_result['location']
                    score = search_result.get('score')
                    distance = search_result.get('distance_km')
                    
                    print(f"  {j}. ID: {location['id']}")
                    print(f"     설명: {location['description']}")
                    print(f"     태그: {', '.join(location['tags'])}")
                    print(f"     좌표: ({location['latitude']}, {location['longitude']})")
                    if score is not None:
                        print(f"     점수: {score:.3f}")
                    if distance is not None:
                        print(f"     거리: {distance:.2f}km")
                    print()
                
            else:
                print(f"오류: {response.status_code}")
                print(response.text)
        
        except Exception as e:
            print(f"요청 오류: {e}")
        
        print("\n" + "=" * 70 + "\n")
        time.sleep(1)  # API 부하 방지

def test_simple_query():
    """간단한 쿼리 테스트"""
    print("=== 간단한 통합 검색 테스트 ===\n")
    
    simple_query = {
        "query": "카페"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/search",
            json=simple_query,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"검색어: {simple_query['query']}")
            print(f"결과 수: {result['total_count']}")
            print(f"검색 시간: {result['query_time_ms']:.2f}ms")
            print(f"사용된 검색: {', '.join(result['search_types_used'])}")
            
            if result['results']:
                first_result = result['results'][0]
                print(f"\n첫 번째 결과:")
                print(f"  설명: {first_result['location']['description']}")
                print(f"  태그: {', '.join(first_result['location']['tags'])}")
        else:
            print(f"오류: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    print("통합 검색 API 테스트 시작 (http://localhost:8000)")
    print("=" * 50)
    
    # 간단한 테스트부터
    test_simple_query()
    
    print("\n" + "=" * 70)
    print("상세 테스트 진행 중...")
    
    # 상세 테스트
    test_unified_search()