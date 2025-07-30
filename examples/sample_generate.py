import requests
import random
import time
from typing import List

# API 엔드포인트
API_URL = "http://localhost:8000/locations/bulk"

# 다양한 태그 옵션들 (한글)
TAGS_POOL = [
    "음식점", "카페", "공원", "박물관", "쇼핑", "호텔", "병원",
    "학교", "은행", "주유소", "약국", "도서관", "헬스장", "영화관",
    "해변", "산", "호수", "숲", "다리", "기념물", "교회",
    "절", "사찰", "시장", "백화점", "사무실", "공장", "공항",
    "기차역", "버스정류장", "주차장", "관광지", "전망대", "맛집",
    "폭포", "동굴", "정원", "동물원", "수족관", "경기장", "극장",
    "클럽", "술집", "베이커리", "서점", "전자제품", "의류",
    "미용실", "이발소", "애완용품", "꽃집", "보석", "갤러리",
    "편의점", "마트", "약국", "문구점", "스포츠용품", "화장품"
]

# 다양한 설명 템플릿들 (한글)
DESCRIPTION_TEMPLATES = [
    "{area}에 위치한 아름다운 {place_type}입니다",
    "뛰어난 {feature}로 유명한 인기 {place_type}입니다",
    "{year}년부터 시작된 역사 깊은 {place_type}입니다",
    "최신 시설을 갖춘 현대적인 {place_type}입니다",
    "{activity}하기에 완벽한 가족친화적인 {place_type}입니다",
    "{landscape}의 멋진 경치를 감상할 수 있는 {place_type}입니다",
    "정통 {cuisine} 요리를 제공하는 전통적인 {place_type}입니다",
    "따뜻하고 친근한 분위기의 아늑한 {place_type}입니다",
    "고급스러운 {service}를 제공하는 럭셔리 {place_type}입니다",
    "현지인들이 발견한 숨겨진 보석 같은 {place_type}입니다",
    "친환경을 추구하는 지속가능한 {place_type}입니다",
    "{achievement} 분야에서 수상 경력이 있는 {place_type}입니다",
    "{setting}에 자리잡은 매력적인 {place_type}입니다",
    "{activity}로 활기찬 분위기의 생동감 넘치는 {place_type}입니다",
    "휴식과 {activity}에 이상적인 평화로운 {place_type}입니다"
]

PLACE_TYPES = [
    "음식점", "카페", "호텔", "상점", "갤러리", "박물관", "공원",
    "센터", "장소", "위치", "시설", "매장", "건물", "공간"
]

AREAS = [
    "시내 중심가", "도심", "구시가지", "비즈니스 지구", "해안가",
    "교외", "시골", "산간 지역", "연안 지역", "역사 지구",
    "신도시", "주택가", "상업 지구", "문화 지구", "금융가"
]

FEATURES = [
    "서비스", "분위기", "디자인", "음식", "직원", "위치", "전망",
    "건축", "분위기", "품질", "선택", "경험", "맛", "인테리어"
]

LANDSCAPES = [
    "바다", "산", "도시 스카이라인", "숲", "강", "호수",
    "계곡", "언덕", "노을", "항구", "정원", "시골 풍경"
]

CUISINES = [
    "한식", "일식", "중식", "양식", "이탈리아", "프랑스", "멕시코",
    "태국", "인도", "지중해", "베트남", "스페인", "그리스"
]

SERVICES = [
    "서비스", "편의시설", "시설", "편안함", "접대", "케어",
    "도움", "상담", "치료", "엔터테인먼트", "식사"
]

ACTIVITIES = [
    "가족 나들이", "데이트", "친구 모임", "비즈니스 미팅", "축하",
    "휴식", "운동", "학습", "쇼핑", "관광"
]

SETTINGS = [
    "조용한 동네", "번화가", "경치 좋은 계곡", "역사적인 건물",
    "현대적인 복합 시설", "정원", "해안가", "산기슭"
]

ACHIEVEMENTS = [
    "우수성", "혁신", "고객 서비스", "품질", "디자인",
    "지속가능성", "사회공헌", "요리 예술", "접객"
]

# 한국 지역별 좌표 범위 (더 현실적인 한국 위치)
KOREA_REGIONS = [
    {"name": "서울", "lat_range": (37.4, 37.7), "lng_range": (126.8, 127.2)},
    {"name": "부산", "lat_range": (35.0, 35.3), "lng_range": (128.9, 129.3)},
    {"name": "대구", "lat_range": (35.7, 36.0), "lng_range": (128.4, 128.8)},
    {"name": "인천", "lat_range": (37.3, 37.6), "lng_range": (126.5, 126.9)},
    {"name": "광주", "lat_range": (35.0, 35.3), "lng_range": (126.7, 127.1)},
    {"name": "대전", "lat_range": (36.2, 36.5), "lng_range": (127.2, 127.6)},
    {"name": "울산", "lat_range": (35.4, 35.7), "lng_range": (129.1, 129.5)},
    {"name": "경기도", "lat_range": (37.0, 37.9), "lng_range": (126.5, 127.8)},
    {"name": "강원도", "lat_range": (37.0, 38.6), "lng_range": (127.0, 129.4)},
    {"name": "충청도", "lat_range": (35.8, 37.2), "lng_range": (126.1, 128.4)},
    {"name": "전라도", "lat_range": (34.2, 36.3), "lng_range": (125.4, 127.7)},
    {"name": "경상도", "lat_range": (34.6, 37.0), "lng_range": (127.4, 129.9)},
    {"name": "제주도", "lat_range": (33.1, 33.6), "lng_range": (126.1, 126.9)}
]

def generate_random_coordinates():
    """한국 지역 기반 좌표 생성 (70%) 또는 전세계 좌표 생성 (30%)"""
    if random.random() < 0.7:  # 70% 확률로 한국 지역
        region = random.choice(KOREA_REGIONS)
        latitude = round(random.uniform(region["lat_range"][0], region["lat_range"][1]), 6)
        longitude = round(random.uniform(region["lng_range"][0], region["lng_range"][1]), 6)
    else:  # 30% 확률로 전세계
        latitude = round(random.uniform(-85, 85), 6)
        longitude = round(random.uniform(-180, 180), 6)

    return latitude, longitude

def generate_random_tags():
    """랜덤한 태그 리스트 생성"""
    num_tags = random.randint(1, 5)  # 1-5개의 태그
    return random.sample(TAGS_POOL, num_tags)

def generate_random_description():
    """랜덤한 설명 생성"""
    template = random.choice(DESCRIPTION_TEMPLATES)

    # 템플릿에 따라 적절한 단어들로 치환
    description = template.format(
        place_type=random.choice(PLACE_TYPES),
        area=random.choice(AREAS),
        feature=random.choice(FEATURES),
        year=random.randint(1950, 2020),
        activity=random.choice(ACTIVITIES),
        landscape=random.choice(LANDSCAPES),
        cuisine=random.choice(CUISINES),
        service=random.choice(SERVICES),
        achievement=random.choice(ACHIEVEMENTS),
        setting=random.choice(SETTINGS)
    )

    return description

def create_location_data():
    """위치 데이터 객체 생성"""
    latitude, longitude = generate_random_coordinates()
    tags = generate_random_tags()
    description = generate_random_description()

    return {
        "latitude": latitude,
        "longitude": longitude,
        "tags": tags,
        "description": description
    }

def send_bulk_location_data(locations_batch):
    """위치 데이터 배치를 벌크 API로 전송"""
    try:
        payload = {"locations": locations_batch}
        response = requests.post(API_URL, json=payload, timeout=30)
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            return result.get("success_count", 0), result.get("error_count", 0)
        else:
            print(f"API 오류: {response.status_code} - {response.text}")
            return 0, len(locations_batch)
    except requests.exceptions.RequestException as e:
        print(f"데이터 전송 오류: {e}")
        return 0, len(locations_batch)

def main():
    """메인 실행 함수"""
    total_records = 10000
    bulk_batch_size = 500  # 벌크 API용 배치 크기
    progress_report_size = 1000  # 진행상황 보고 단위
    
    total_success = 0
    total_errors = 0
    
    print(f"{total_records}개의 위치 데이터 생성 및 벌크 전송을 시작합니다...")
    print(f"배치 크기: {bulk_batch_size}개씩 전송")
    
    # 전체 데이터를 배치 단위로 처리
    for batch_start in range(0, total_records, bulk_batch_size):
        batch_end = min(batch_start + bulk_batch_size, total_records)
        
        # 현재 배치의 위치 데이터 생성
        current_batch = []
        for _ in range(batch_end - batch_start):
            location_data = create_location_data()
            current_batch.append(location_data)
        
        # 벌크 API로 전송
        batch_success, batch_errors = send_bulk_location_data(current_batch)
        total_success += batch_success
        total_errors += batch_errors
        
        # 진행상황 출력
        processed = batch_end
        if processed % progress_report_size == 0 or processed == total_records:
            print(f"진행: {processed}/{total_records} | 성공: {total_success} | 실패: {total_errors}")
        
        # API 서버 부하 방지를 위한 짧은 지연 (배치당)
        time.sleep(0.5)
    
    print(f"\n=== 최종 결과 ===")
    print(f"전송 시도: {total_records}")
    print(f"성공: {total_success}")
    print(f"실패: {total_errors}")
    print(f"성공률: {(total_success/total_records)*100:.2f}%")
    print(f"배치 수: {(total_records + bulk_batch_size - 1) // bulk_batch_size}개")

# 샘플 데이터 미리보기 함수
def preview_sample_data(count=5):
    """생성될 데이터 샘플 미리보기"""
    print("=== 샘플 데이터 미리보기 ===")
    for i in range(count):
        sample = create_location_data()
        print(f"\n샘플 {i+1}:")
        print(f"  위도: {sample['latitude']}")
        print(f"  경도: {sample['longitude']}")
        print(f"  태그: {sample['tags']}")
        print(f"  설명: {sample['description']}")

if __name__ == "__main__":
    # 실행 전 샘플 데이터 미리보기
    preview_sample_data(3)

    # 사용자 확인
    user_input = input("\nAPI로 데이터 전송을 진행하시겠습니까? (y/n): ")
    if user_input.lower() == 'y':
        main()
    else:
        print("작업이 취소되었습니다.")