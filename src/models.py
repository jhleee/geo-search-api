from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
import json

class LocationCreate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    tags: List[str] = Field(default_factory=list, description="List of tags")
    description: str = Field("", description="Description of the location")
    
    @validator('tags')
    def validate_tags(cls, v):
        return [tag.strip().lower() for tag in v if tag.strip()]
    
    @validator('description')
    def validate_description(cls, v):
        return v.strip()

class LocationUpdate(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            return [tag.strip().lower() for tag in v if tag.strip()]
        return v
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            return v.strip()
        return v

class LocationResponse(BaseModel):
    id: int
    latitude: float
    longitude: float
    tags: List[str]
    description: str
    embedding_id: Optional[int]
    created_at: datetime
    
    @classmethod
    def from_db_row(cls, row: dict) -> 'LocationResponse':
        """Create LocationResponse from database row"""
        tags = json.loads(row.get('tags', '[]')) if row.get('tags') else []
        return cls(
            id=row['id'],
            latitude=row['latitude'],
            longitude=row['longitude'],
            tags=tags,
            description=row.get('description', ''),
            embedding_id=row.get('embedding_id'),
            created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')) 
                      if isinstance(row['created_at'], str) 
                      else row['created_at']
        )

class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, description="Search query text")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")

class LocationSearchQuery(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(1.0, ge=0.001, le=100.0, description="Search radius in kilometers")
    limit: int = Field(10, ge=1, le=100)

class VectorSearchQuery(BaseModel):
    query: str = Field(..., min_length=1, description="Text to search for similar content")
    limit: int = Field(10, ge=1, le=100)
    threshold: float = Field(0.5, ge=0.0, le=1.0, description="Similarity threshold")

class SearchResult(BaseModel):
    location: LocationResponse
    score: Optional[float] = None
    distance_km: Optional[float] = None

# 통합 검색 요청 모델
class UnifiedSearchQuery(BaseModel):
    query: str = Field(..., min_length=1, description="검색 키워드")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="위도 (위치 검색시)")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="경도 (위치 검색시)")
    radius_km: Optional[float] = Field(1.0, ge=0.001, le=100.0, description="검색 반경(km)")
    limit: int = Field(10, ge=1, le=100, description="최대 결과 수")
    use_text: bool = Field(True, description="텍스트 검색 사용")
    use_vector: bool = Field(True, description="벡터 검색 사용")
    use_location: bool = Field(True, description="위치 검색 사용 (좌표 제공시)")
    vector_threshold: float = Field(0.3, ge=0.0, le=1.0, description="벡터 유사도 임계값")

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_count: int
    search_type: str
    query_time_ms: float

# 통합 검색 응답 모델
class UnifiedSearchResponse(BaseModel):
    results: List[SearchResult]
    total_count: int
    search_types_used: List[str]
    query_time_ms: float
    search_summary: dict

class BulkLocationCreate(BaseModel):
    locations: List[LocationCreate] = Field(..., min_items=1, max_items=1000, 
                                          description="List of locations to create (max 1000)")

class BulkLocationResponse(BaseModel):
    success_count: int
    failed_count: int
    total_count: int
    created_locations: List[LocationResponse]
    errors: List[dict] = Field(default_factory=list)
    processing_time_ms: float