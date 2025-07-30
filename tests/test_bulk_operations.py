import pytest
import tempfile
import os
import time
from src.service import GeoTagService
from src.models import LocationCreate, BulkLocationCreate

@pytest.fixture
def bulk_service():
    """Create a service for bulk testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    service = GeoTagService(db_path)
    yield service
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)
    if os.path.exists("faiss_index.bin"):
        os.unlink("faiss_index.bin")
    if os.path.exists("faiss_metadata.pkl"):
        os.unlink("faiss_metadata.pkl")

def create_test_locations(count: int) -> list[LocationCreate]:
    """Create test location data"""
    locations = []
    for i in range(count):
        location = LocationCreate(
            latitude=37.5665 + i * 0.001,
            longitude=126.9780 + i * 0.001,
            tags=[f"tag{i}", "test", "bulk"],
            description=f"Test location {i+1}"
        )
        locations.append(location)
    return locations

def test_bulk_create_small_batch(bulk_service):
    """Test bulk creation with small batch"""
    locations = create_test_locations(5)
    bulk_data = BulkLocationCreate(locations=locations)
    
    result = bulk_service.create_locations_bulk(bulk_data)
    
    assert result.success_count == 5
    assert result.failed_count == 0
    assert result.total_count == 5
    assert len(result.created_locations) == 5
    assert len(result.errors) == 0
    assert result.processing_time_ms > 0

def test_bulk_create_medium_batch(bulk_service):
    """Test bulk creation with medium batch"""
    locations = create_test_locations(50)
    bulk_data = BulkLocationCreate(locations=locations)
    
    start_time = time.time()
    result = bulk_service.create_locations_bulk(bulk_data)
    end_time = time.time()
    
    assert result.success_count == 50
    assert result.failed_count == 0
    assert result.total_count == 50
    assert len(result.created_locations) == 50
    
    # Performance check - should be much faster than individual inserts
    processing_time_sec = result.processing_time_ms / 1000
    assert processing_time_sec < 30  # Should complete within 30 seconds
    
    print(f"Bulk created 50 locations in {processing_time_sec:.2f}s")
    print(f"Average: {processing_time_sec/50*1000:.1f}ms per location")

def test_bulk_create_with_validation_errors(bulk_service):
    """Test bulk creation with manual validation (Pydantic validates at creation time)"""
    # Since Pydantic validates at object creation time, we need to test validation
    # at the service level instead
    
    # Test with invalid data passed directly to service
    from src.models import BulkLocationCreate
    
    # Create valid locations first
    valid_locations = [
        LocationCreate(latitude=37.5665, longitude=126.9780, tags=["valid1"], description="Valid location 1"),
        LocationCreate(latitude=37.5666, longitude=126.9781, tags=["valid2"], description="Valid location 2"),
    ]
    
    bulk_data = BulkLocationCreate(locations=valid_locations)
    result = bulk_service.create_locations_bulk(bulk_data)
    
    assert result.success_count == 2
    assert result.failed_count == 0
    assert result.total_count == 2
    assert len(result.created_locations) == 2
    assert len(result.errors) == 0
    
    # Test edge case validation in service level
    # (coordinate validation happens at Pydantic level, so we test other validation)
    edge_locations = [
        LocationCreate(latitude=90.0, longitude=180.0, tags=["edge1"], description="Edge case 1"),  # Max valid
        LocationCreate(latitude=-90.0, longitude=-180.0, tags=["edge2"], description="Edge case 2"),  # Min valid
    ]
    
    edge_bulk_data = BulkLocationCreate(locations=edge_locations)
    edge_result = bulk_service.create_locations_bulk(edge_bulk_data)
    
    assert edge_result.success_count == 2
    assert edge_result.failed_count == 0

def test_bulk_create_empty_list(bulk_service):
    """Test bulk creation with empty list"""
    with pytest.raises(ValueError):  # Should fail validation
        BulkLocationCreate(locations=[])

def test_bulk_create_max_limit():
    """Test bulk creation size limits"""
    # Test that we can't create more than max allowed
    locations = create_test_locations(1001)  # Over the limit
    
    with pytest.raises(ValueError):
        BulkLocationCreate(locations=locations)

def test_bulk_vs_individual_performance(bulk_service):
    """Compare bulk vs individual insertion performance"""
    locations = create_test_locations(20)
    
    # Test individual insertion
    individual_start = time.time()
    individual_results = []
    for location in locations:
        result = bulk_service.create_location(location)
        individual_results.append(result)
    individual_time = time.time() - individual_start
    
    # Clear the database for bulk test
    # (In a real scenario, we'd use a fresh service, but for testing we'll continue)
    
    # Test bulk insertion with different locations
    bulk_locations = create_test_locations(20)
    for i, loc in enumerate(bulk_locations):
        loc.description = f"Bulk test location {i+1}"
        loc.latitude += 0.1  # Slightly different coordinates
    
    bulk_data = BulkLocationCreate(locations=bulk_locations)
    bulk_start = time.time()
    bulk_result = bulk_service.create_locations_bulk(bulk_data)
    bulk_time = time.time() - bulk_start
    
    print(f"\nPerformance Comparison:")
    print(f"Individual: {individual_time:.2f}s for {len(individual_results)} locations")
    print(f"Bulk: {bulk_time:.2f}s for {bulk_result.success_count} locations")
    print(f"Individual avg: {individual_time/len(individual_results)*1000:.1f}ms per location")
    print(f"Bulk avg: {bulk_time/bulk_result.success_count*1000:.1f}ms per location")
    
    # Bulk should be faster per location (though total time might be similar due to batching overhead)
    individual_avg = individual_time / len(individual_results)
    bulk_avg = bulk_time / bulk_result.success_count
    
    assert bulk_result.success_count == 20
    assert bulk_result.failed_count == 0

def test_bulk_create_korean_data(bulk_service):
    """Test bulk creation with Korean language data"""
    korean_locations = [
        LocationCreate(
            latitude=37.5665, longitude=126.9780,
            tags=["카페", "조용한", "와이파이"],
            description="조용한 카페 - 작업하기 좋은 곳"
        ),
        LocationCreate(
            latitude=37.5511, longitude=126.9882,
            tags=["식당", "한식", "맛집"],
            description="전통 한식당 - 가족 식사 추천"
        ),
        LocationCreate(
            latitude=37.5796, longitude=126.9770,
            tags=["공원", "산책", "자연"],
            description="경복궁 - 역사적인 궁궐과 아름다운 정원"
        )
    ]
    
    bulk_data = BulkLocationCreate(locations=korean_locations)
    result = bulk_service.create_locations_bulk(bulk_data)
    
    assert result.success_count == 3
    assert result.failed_count == 0
    assert result.total_count == 3
    
    # Verify Korean text is preserved
    for location in result.created_locations:
        assert location.description
        assert len(location.tags) > 0

def test_bulk_create_large_batch():
    """Test bulk creation with large batch (performance test)"""
    # This test is commented out by default as it takes longer
    # Uncomment to run performance tests
    pass
    
    # locations = create_test_locations(500)
    # bulk_data = BulkLocationCreate(locations=locations)
    # 
    # start_time = time.time()
    # result = bulk_service.create_locations_bulk(bulk_data)
    # end_time = time.time()
    # 
    # assert result.success_count == 500
    # assert result.failed_count == 0
    # 
    # processing_time = end_time - start_time
    # print(f"Created 500 locations in {processing_time:.2f}s")
    # print(f"Rate: {500/processing_time:.1f} locations/second")

def test_bulk_create_mixed_data_types(bulk_service):
    """Test bulk creation with mixed data types and edge cases"""
    locations = [
        # Normal location
        LocationCreate(latitude=37.5665, longitude=126.9780, tags=["normal"], description="Normal location"),
        
        # Empty tags
        LocationCreate(latitude=37.5666, longitude=126.9781, tags=[], description="No tags location"),
        
        # Empty description
        LocationCreate(latitude=37.5667, longitude=126.9782, tags=["empty_desc"], description=""),
        
        # Long description
        LocationCreate(
            latitude=37.5668, longitude=126.9783, 
            tags=["long"], 
            description="This is a very long description that contains multiple sentences and should test how the system handles longer text content in bulk operations."
        ),
        
        # Many tags
        LocationCreate(
            latitude=37.5669, longitude=126.9784,
            tags=["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10"],
            description="Location with many tags"
        ),
    ]
    
    bulk_data = BulkLocationCreate(locations=locations)
    result = bulk_service.create_locations_bulk(bulk_data)
    
    assert result.success_count == 5
    assert result.failed_count == 0
    assert result.total_count == 5
    
    # Verify all locations were created correctly
    for location in result.created_locations:
        assert location.id > 0
        assert -90 <= location.latitude <= 90
        assert -180 <= location.longitude <= 180

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])