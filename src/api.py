from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import time
import logging

from .service import GeoTagService
from .models import (
    LocationCreate, LocationUpdate, LocationResponse,
    SearchQuery, LocationSearchQuery, VectorSearchQuery,
    SearchResult, SearchResponse, BulkLocationCreate, BulkLocationResponse,
    UnifiedSearchQuery, UnifiedSearchResponse
)
from .config import get_config, setup_logging, config_manager

# Setup logging and get config
setup_logging()
config = get_config()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=config.api.title,
    description=config.api.description,
    version=config.api.version
)

# Initialize service
geo_service = GeoTagService()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": f"{config.api.title} - {config.api.description}",
        "version": config.api.version,
        "embedding_model": config.embedding.model_name,
        "endpoints": {
            "locations": "/locations",
            "search": "/search/*",
            "stats": "/stats",
            "config": "/config"
        }
    }

@app.post("/locations", response_model=LocationResponse)
async def create_location(location: LocationCreate):
    """Create a new location"""
    try:
        result = geo_service.create_location(location)
        logger.info(f"Created location {result.id}")
        return result
    except Exception as e:
        logger.error(f"Error creating location: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/locations/{location_id}", response_model=LocationResponse)
async def get_location(location_id: int):
    """Get a location by ID"""
    location = geo_service.get_location(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

@app.put("/locations/{location_id}", response_model=LocationResponse)
async def update_location(location_id: int, update_data: LocationUpdate):
    """Update a location"""
    location = geo_service.update_location(location_id, update_data)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    logger.info(f"Updated location {location_id}")
    return location

@app.delete("/locations/{location_id}")
async def delete_location(location_id: int):
    """Delete a location"""
    success = geo_service.delete_location(location_id)
    if not success:
        raise HTTPException(status_code=404, detail="Location not found")
    logger.info(f"Deleted location {location_id}")
    return {"message": "Location deleted successfully"}

@app.get("/locations", response_model=List[LocationResponse])
async def list_locations(
    limit: int = Query(config.search.default_limit, ge=1, le=config.search.max_limit, 
                      description="Number of locations to return"),
    offset: int = Query(0, ge=0, description="Number of locations to skip")
):
    """List all locations with pagination"""
    locations = geo_service.get_all_locations(limit=limit, offset=offset)
    return locations

@app.post("/locations/bulk", response_model=BulkLocationResponse)
async def create_locations_bulk(bulk_data: BulkLocationCreate):
    """Create multiple locations efficiently with batch processing"""
    try:
        result = geo_service.create_locations_bulk(bulk_data)
        logger.info(f"Bulk created {result.success_count}/{result.total_count} locations "
                   f"in {result.processing_time_ms:.1f}ms")
        return result
    except Exception as e:
        logger.error(f"Error in bulk location creation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/location", response_model=SearchResponse)
async def search_by_location(search_query: LocationSearchQuery):
    """Search locations by geographic proximity"""
    start_time = time.time()
    
    results = geo_service.search_by_location(
        latitude=search_query.latitude,
        longitude=search_query.longitude,
        radius_km=search_query.radius_km,
        limit=search_query.limit
    )
    
    query_time_ms = (time.time() - start_time) * 1000
    
    return SearchResponse(
        results=results,
        total_count=len(results),
        search_type="location",
        query_time_ms=query_time_ms
    )

@app.post("/search/text", response_model=SearchResponse)
async def search_by_text(search_query: SearchQuery):
    """Full-text search in descriptions and tags"""
    start_time = time.time()
    
    results = geo_service.search_by_text(
        query=search_query.query,
        limit=search_query.limit
    )
    
    query_time_ms = (time.time() - start_time) * 1000
    
    return SearchResponse(
        results=results,
        total_count=len(results),
        search_type="text",
        query_time_ms=query_time_ms
    )

@app.post("/search/vector", response_model=SearchResponse)
async def search_by_vector(search_query: VectorSearchQuery):
    """Vector similarity search using embeddings"""
    start_time = time.time()
    
    results = geo_service.search_by_vector(
        query=search_query.query,
        limit=search_query.limit,
        threshold=search_query.threshold
    )
    
    query_time_ms = (time.time() - start_time) * 1000
    
    return SearchResponse(
        results=results,
        total_count=len(results),
        search_type="vector",
        query_time_ms=query_time_ms
    )

@app.get("/search/combined")
async def search_combined(
    query: str = Query(..., description="Search query"),
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    radius_km: float = Query(config.search.default_radius_km, ge=0.001, le=config.search.max_radius_km),
    use_vector: bool = Query(True, description="Include vector similarity search"),
    limit: int = Query(config.search.default_limit, ge=1, le=config.search.max_limit)
):
    """Combined search using multiple methods"""
    start_time = time.time()
    
    all_results = []
    search_types = []
    
    # Text search
    text_results = geo_service.search_by_text(query, limit=limit)
    all_results.extend(text_results)
    search_types.append("text")
    
    # Vector search
    if use_vector:
        vector_results = geo_service.search_by_vector(query, limit=limit, threshold=0.3)
        all_results.extend(vector_results)
        search_types.append("vector")
    
    # Location search (if coordinates provided)
    if latitude is not None and longitude is not None:
        location_results = geo_service.search_by_location(
            latitude, longitude, radius_km, limit=limit
        )
        all_results.extend(location_results)
        search_types.append("location")
    
    # Remove duplicates by location ID
    seen_ids = set()
    unique_results = []
    for result in all_results:
        if result.location.id not in seen_ids:
            unique_results.append(result)
            seen_ids.add(result.location.id)
    
    # Sort by relevance (score for vector, distance for location, order for text)
    def sort_key(result):
        if result.score is not None:
            return -result.score  # Higher score first
        elif result.distance_km is not None:
            return result.distance_km  # Closer distance first
        else:
            return 0  # Text results keep original order
    
    unique_results.sort(key=sort_key)
    unique_results = unique_results[:limit]
    
    query_time_ms = (time.time() - start_time) * 1000
    
    return SearchResponse(
        results=unique_results,
        total_count=len(unique_results),
        search_type="+".join(search_types),
        query_time_ms=query_time_ms
    )

@app.post("/search", response_model=UnifiedSearchResponse, 
         summary="통합 검색",
         description="""
         모든 검색 기능을 하나로 통합한 스마트 검색 API
         
         **사용법:**
         - `query`: 검색할 키워드 (필수)
         - `latitude`, `longitude`: 위치 기반 검색 (선택)
         - `radius_km`: 검색 반경 (기본 1km)
         - `use_text`: 텍스트 검색 사용 여부 (기본 true)
         - `use_vector`: 벡터 검색 사용 여부 (기본 true)
         - `use_location`: 위치 검색 사용 여부 (기본 true, 좌표 제공시만)
         
         **검색 우선순위:**
         1. 정확한 키워드 매칭 (텍스트 검색)
         2. 의미적 유사성 (벡터 검색)
         3. 지리적 근접성 (위치 검색)
         """)
async def unified_search(search_query: UnifiedSearchQuery):
    """통합 검색 - 키워드, 의미, 위치를 조합한 스마트 검색"""
    return geo_service.unified_search(search_query)

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    stats = geo_service.get_stats()
    model_info = config_manager.get_embedding_model_info()
    
    return {
        **stats,
        "model_info": model_info,
        "config": {
            "embedding_model": config.embedding.model_name,
            "index_type": config.embedding.index_type,
            "default_threshold": config.embedding.similarity_threshold,
            "max_threads": config.performance.max_threads,
            "auto_save_interval": config.performance.auto_save_interval
        }
    }

@app.get("/config")
async def get_config_info():
    """Get current configuration"""
    model_info = config_manager.get_embedding_model_info()
    
    return {
        "embedding": {
            "model_name": config.embedding.model_name,
            "dimension": config.embedding.dimension,
            "use_prefix": config.embedding.use_query_prefix,
            "model_info": model_info
        },
        "search": {
            "default_limit": config.search.default_limit,
            "max_limit": config.search.max_limit,
            "default_radius_km": config.search.default_radius_km,
            "similarity_threshold": config.embedding.similarity_threshold
        },
        "performance": {
            "max_memory_mb": config.performance.max_memory_mb,
            "max_threads": config.performance.max_threads,
            "auto_save_interval": config.performance.auto_save_interval
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": time.time(),
        "model": config.embedding.model_name,
        "version": config.api.version
    }

# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )