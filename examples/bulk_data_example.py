#!/usr/bin/env python3
"""
Bulk data insertion example for Geo Tag API
Demonstrates efficient bulk data loading with various formats
"""

import json
import csv
import time
import random
from typing import List, Dict
from src.service import GeoTagService
from src.models import LocationCreate, BulkLocationCreate

def generate_sample_bulk_data(count: int = 100) -> List[LocationCreate]:
    """Generate sample bulk data for testing"""
    
    # Sample data categories
    categories = {
        "카페": {
            "adjectives": ["조용한", "아늑한", "모던한", "빈티지", "넓은"],
            "features": ["와이파이", "작업공간", "디저트", "브런치", "테라스"]
        },
        "식당": {
            "adjectives": ["맛있는", "유명한", "전통적인", "고급", "가성비좋은"],
            "features": ["한식", "양식", "중식", "일식", "분위기좋은"]
        },
        "쇼핑": {
            "adjectives": ["대형", "편리한", "현대적인", "전문", "유명한"],
            "features": ["백화점", "아울렛", "브랜드", "세일", "주차"]
        },
        "문화": {
            "adjectives": ["역사적인", "현대적인", "교육적인", "흥미로운", "유명한"],
            "features": ["박물관", "갤러리", "공연장", "전시", "체험"]
        },
        "운동": {
            "adjectives": ["최신", "넓은", "전문적인", "깨끗한", "편리한"],
            "features": ["헬스장", "수영장", "요가", "필라테스", "개인트레이닝"]
        }
    }
    
    # Seoul area coordinates (rough bounds)
    seoul_bounds = {
        "lat_min": 37.4500, "lat_max": 37.7000,
        "lon_min": 126.8000, "lon_max": 127.2000
    }
    
    bulk_data = []
    
    for i in range(count):
        # Random category
        category = random.choice(list(categories.keys()))
        cat_data = categories[category]
        
        # Random attributes
        adjective = random.choice(cat_data["adjectives"])
        feature = random.choice(cat_data["features"])
        
        # Random Seoul coordinates
        lat = random.uniform(seoul_bounds["lat_min"], seoul_bounds["lat_max"])
        lon = random.uniform(seoul_bounds["lon_min"], seoul_bounds["lon_max"])
        
        # Generate location data
        location = LocationCreate(
            latitude=round(lat, 6),
            longitude=round(lon, 6),
            tags=[category, adjective, feature],
            description=f"{adjective} {category} - {feature} 이용 가능 (#{i+1})"
        )
        
        bulk_data.append(location)
    
    return bulk_data

def load_from_csv(csv_file: str) -> List[LocationCreate]:
    """Load location data from CSV file"""
    locations = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                # Parse tags from comma-separated string
                tags = [tag.strip() for tag in row.get('tags', '').split(',') if tag.strip()]
                
                location = LocationCreate(
                    latitude=float(row['latitude']),
                    longitude=float(row['longitude']),
                    tags=tags,
                    description=row['description']
                )
                locations.append(location)
                
    except FileNotFoundError:
        print(f"CSV file {csv_file} not found")
    except Exception as e:
        print(f"Error loading CSV: {e}")
    
    return locations

def load_from_json(json_file: str) -> List[LocationCreate]:
    """Load location data from JSON file"""
    locations = []
    
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
            # Handle different JSON formats
            if isinstance(data, list):
                # Array of location objects
                for item in data:
                    location = LocationCreate(**item)
                    locations.append(location)
            elif isinstance(data, dict) and 'locations' in data:
                # Object with locations array
                for item in data['locations']:
                    location = LocationCreate(**item)
                    locations.append(location)
                    
    except FileNotFoundError:
        print(f"JSON file {json_file} not found")
    except Exception as e:
        print(f"Error loading JSON: {e}")
    
    return locations

def create_sample_files():
    """Create sample CSV and JSON files for testing"""
    
    # Generate sample data
    sample_data = generate_sample_bulk_data(50)
    
    # Create CSV file
    csv_filename = "sample_locations.csv"
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['latitude', 'longitude', 'tags', 'description']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for location in sample_data:
            writer.writerow({
                'latitude': location.latitude,
                'longitude': location.longitude,
                'tags': ', '.join(location.tags),
                'description': location.description
            })
    
    print(f"Created sample CSV file: {csv_filename}")
    
    # Create JSON file
    json_filename = "sample_locations.json"
    json_data = {
        "locations": [location.dict() for location in sample_data]
    }
    
    with open(json_filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(json_data, jsonfile, ensure_ascii=False, indent=2)
    
    print(f"Created sample JSON file: {json_filename}")
    
    return csv_filename, json_filename

def benchmark_bulk_vs_individual(service: GeoTagService, locations: List[LocationCreate]):
    """Compare bulk insertion vs individual insertion performance"""
    print(f"\n=== 성능 비교: 벌크 vs 개별 입력 ({len(locations)}개 위치) ===")
    
    # Test individual insertion
    print("\n개별 입력 테스트...")
    individual_start = time.time()
    individual_created = []
    
    for i, location in enumerate(locations[:20]):  # Test with first 20 for speed
        try:
            created = service.create_location(location)
            individual_created.append(created)
        except Exception as e:
            print(f"개별 입력 실패 {i}: {e}")
    
    individual_time = time.time() - individual_start
    individual_avg = individual_time / len(individual_created) if individual_created else 0
    
    print(f"개별 입력: {len(individual_created)}개 성공, {individual_time:.2f}초")
    print(f"개별 평균: {individual_avg*1000:.1f}ms per location")
    
    # Test bulk insertion
    print("\n벌크 입력 테스트...")
    bulk_data = BulkLocationCreate(locations=locations[:100])  # Test with first 100
    
    bulk_start = time.time()
    try:
        bulk_result = service.create_locations_bulk(bulk_data)
        bulk_time = time.time() - bulk_start
        bulk_avg = bulk_time / bulk_result.success_count if bulk_result.success_count else 0
        
        print(f"벌크 입력: {bulk_result.success_count}개 성공, {bulk_result.failed_count}개 실패")
        print(f"처리 시간: {bulk_time:.2f}초 (API 측정: {bulk_result.processing_time_ms:.1f}ms)")
        print(f"벌크 평균: {bulk_avg*1000:.1f}ms per location")
        
        # Performance comparison
        if individual_avg > 0 and bulk_avg > 0:
            speedup = individual_avg / bulk_avg
            print(f"\n성능 향상: {speedup:.1f}x 더 빠름")
        
        return bulk_result
        
    except Exception as e:
        print(f"벌크 입력 실패: {e}")
        return None

def main():
    """Main bulk data demo"""
    print("Geo Tag API 벌크 데이터 입력 데모")
    print("=" * 50)
    
    # Initialize service
    service = GeoTagService("bulk_demo_geo_tags.db")
    
    # Create sample files
    print("\n1. 샘플 파일 생성")
    csv_file, json_file = create_sample_files()
    
    # Test different data sources
    print("\n2. 다양한 데이터 소스 테스트")
    
    # Generated data
    print("\n생성된 샘플 데이터:")
    generated_data = generate_sample_bulk_data(200)
    print(f"생성된 위치: {len(generated_data)}개")
    
    # CSV data
    print("\nCSV 파일에서 로드:")
    csv_data = load_from_csv(csv_file)
    print(f"CSV 위치: {len(csv_data)}개")
    
    # JSON data
    print("\nJSON 파일에서 로드:")
    json_data = load_from_json(json_file)
    print(f"JSON 위치: {len(json_data)}개")
    
    # Performance benchmark
    print("\n3. 성능 벤치마크")
    if generated_data:
        benchmark_result = benchmark_bulk_vs_individual(service, generated_data)
    
    # Large batch test
    print("\n4. 대용량 배치 테스트")
    large_data = generate_sample_bulk_data(500)
    bulk_data = BulkLocationCreate(locations=large_data)
    
    print(f"대용량 데이터 입력 테스트: {len(large_data)}개 위치")
    start_time = time.time()
    
    try:
        result = service.create_locations_bulk(bulk_data)
        total_time = time.time() - start_time
        
        print(f"결과:")
        print(f"  - 성공: {result.success_count}개")
        print(f"  - 실패: {result.failed_count}개")
        print(f"  - 총 시간: {total_time:.2f}초")
        print(f"  - 처리 속도: {result.success_count/total_time:.1f} locations/sec")
        print(f"  - API 처리 시간: {result.processing_time_ms:.1f}ms")
        
        if result.errors:
            print(f"  - 첫 번째 오류: {result.errors[0]}")
    
    except Exception as e:
        print(f"대용량 테스트 실패: {e}")
    
    # Final statistics
    print("\n5. 최종 통계")
    stats = service.get_stats()
    print(f"총 위치 수: {stats['total_locations']}")
    print(f"총 임베딩 수: {stats['total_embeddings']}")
    
    print(f"\n데이터베이스 저장됨: bulk_demo_geo_tags.db")
    print("벌크 입력 API 테스트:")
    print("  POST /locations/bulk")
    print("  curl -X POST http://localhost:8000/locations/bulk \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d @sample_locations.json")

if __name__ == "__main__":
    main()