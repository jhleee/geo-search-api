import pytest
import tempfile
import os
from src.service import GeoTagService
from src.models import LocationCreate, LocationUpdate

@pytest.fixture
def temp_service():
    """Create a temporary service for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    service = GeoTagService(db_path)
    yield service
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)
    # Cleanup embedding files
    if os.path.exists("faiss_index.bin"):
        os.unlink("faiss_index.bin")
    if os.path.exists("faiss_metadata.pkl"):
        os.unlink("faiss_metadata.pkl")

def test_create_location(temp_service):
    """Test creating a location"""
    location_data = LocationCreate(
        latitude=37.7749,
        longitude=-122.4194,
        tags=["coffee", "wifi"],
        description="Great coffee shop"
    )
    
    location = temp_service.create_location(location_data)
    
    assert location.id > 0
    assert location.latitude == 37.7749
    assert location.longitude == -122.4194
    assert location.tags == ["coffee", "wifi"]
    assert location.description == "Great coffee shop"
    assert location.embedding_id is not None

def test_get_location(temp_service):
    """Test getting a location"""
    # First create a location
    location_data = LocationCreate(
        latitude=40.7128,
        longitude=-74.0060,
        tags=["restaurant"],
        description="Italian restaurant"
    )
    created_location = temp_service.create_location(location_data)
    
    # Then retrieve it
    retrieved_location = temp_service.get_location(created_location.id)
    
    assert retrieved_location is not None
    assert retrieved_location.id == created_location.id
    assert retrieved_location.description == "Italian restaurant"

def test_update_location(temp_service):
    """Test updating a location"""
    # Create a location
    location_data = LocationCreate(
        latitude=51.5074,
        longitude=-0.1278,
        tags=["pub"],
        description="Local pub"
    )
    created_location = temp_service.create_location(location_data)
    
    # Update it
    update_data = LocationUpdate(
        description="Historic local pub",
        tags=["pub", "historic", "cozy"]
    )
    updated_location = temp_service.update_location(created_location.id, update_data)
    
    assert updated_location is not None
    assert updated_location.description == "Historic local pub"
    assert updated_location.tags == ["pub", "historic", "cozy"]
    # New embedding should be created
    assert updated_location.embedding_id != created_location.embedding_id

def test_delete_location(temp_service):
    """Test deleting a location"""
    # Create a location
    location_data = LocationCreate(
        latitude=48.8566,
        longitude=2.3522,
        tags=["museum"],
        description="Art museum"
    )
    created_location = temp_service.create_location(location_data)
    
    # Delete it
    success = temp_service.delete_location(created_location.id)
    assert success is True
    
    # Verify it's gone
    deleted_location = temp_service.get_location(created_location.id)
    assert deleted_location is None

def test_search_by_location(temp_service):
    """Test geographic search"""
    # Create multiple locations
    locations_data = [
        LocationCreate(latitude=37.7749, longitude=-122.4194, tags=["sf"], description="San Francisco"),
        LocationCreate(latitude=37.8044, longitude=-122.2712, tags=["oakland"], description="Oakland"),
        LocationCreate(latitude=40.7128, longitude=-74.0060, tags=["nyc"], description="New York"),
    ]
    
    for loc_data in locations_data:
        temp_service.create_location(loc_data)
    
    # Search near San Francisco
    results = temp_service.search_by_location(37.7749, -122.4194, radius_km=20, limit=10)
    
    # Should find SF and potentially Oakland
    assert len(results) >= 1
    descriptions = [result.location.description for result in results]
    assert "San Francisco" in descriptions
    
    # Check distance calculation
    for result in results:
        assert result.distance_km is not None
        assert result.distance_km >= 0

def test_search_by_text(temp_service):
    """Test full-text search"""
    # Create locations
    locations_data = [
        LocationCreate(latitude=37.7749, longitude=-122.4194, tags=["restaurant"], description="Italian restaurant"),
        LocationCreate(latitude=37.8044, longitude=-122.2712, tags=["cafe"], description="Coffee shop"),
        LocationCreate(latitude=40.7128, longitude=-74.0060, tags=["restaurant"], description="Pizza restaurant"),
    ]
    
    for loc_data in locations_data:
        temp_service.create_location(loc_data)
    
    # Search for restaurants
    results = temp_service.search_by_text("restaurant", limit=10)
    
    assert len(results) >= 1
    descriptions = [result.location.description for result in results]
    assert any("restaurant" in desc.lower() for desc in descriptions)

def test_get_stats(temp_service):
    """Test getting system statistics"""
    # Create a few locations
    for i in range(3):
        location_data = LocationCreate(
            latitude=37.0 + i * 0.1,
            longitude=-122.0 + i * 0.1,
            tags=[f"tag{i}"],
            description=f"Location {i}"
        )
        temp_service.create_location(location_data)
    
    stats = temp_service.get_stats()
    
    assert "total_locations" in stats
    assert "total_embeddings" in stats
    assert "embedding_model" in stats
    assert "index_type" in stats
    
    assert stats["total_locations"] == 3
    assert stats["total_embeddings"] == 3
    assert stats["embedding_model"] == "all-MiniLM-L6-v2"

def test_calculate_distance(temp_service):
    """Test distance calculation"""
    # Test known distances
    # San Francisco to Oakland (approximately 13km)
    distance = temp_service._calculate_distance(37.7749, -122.4194, 37.8044, -122.2712)
    assert 10 < distance < 20  # Should be around 13km
    
    # Same point should be 0 distance
    distance = temp_service._calculate_distance(37.7749, -122.4194, 37.7749, -122.4194)
    assert distance < 0.001  # Essentially 0

def test_location_validation():
    """Test location data validation"""
    # Invalid latitude
    with pytest.raises(ValueError):
        LocationCreate(
            latitude=91.0,  # Invalid
            longitude=-122.4194,
            tags=["test"],
            description="Test"
        )
    
    # Invalid longitude
    with pytest.raises(ValueError):
        LocationCreate(
            latitude=37.7749,
            longitude=181.0,  # Invalid
            tags=["test"],
            description="Test"
        )

def test_tag_normalization():
    """Test that tags are normalized (lowercase, stripped)"""
    location_data = LocationCreate(
        latitude=37.7749,
        longitude=-122.4194,
        tags=["  Coffee  ", "WIFI", " cozy"],
        description="Test location"
    )
    
    assert location_data.tags == ["coffee", "wifi", "cozy"]