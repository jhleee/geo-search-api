import pytest
import tempfile
import os
from src.database import Database

@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db = Database(db_path)
    yield db
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_database_initialization(temp_db):
    """Test database initialization"""
    assert temp_db.db_path is not None
    
    # Test table creation by inserting a record
    location_id = temp_db.insert_location(
        latitude=37.7749,
        longitude=-122.4194,
        tags=["test", "location"],
        description="Test location"
    )
    assert location_id is not None
    assert location_id > 0

def test_insert_location(temp_db):
    """Test location insertion"""
    location_id = temp_db.insert_location(
        latitude=37.7749,
        longitude=-122.4194,
        tags=["san francisco", "city"],
        description="San Francisco city center",
        embedding_id=1
    )
    
    assert location_id is not None
    assert location_id > 0

def test_get_location(temp_db):
    """Test location retrieval"""
    # Insert a location
    location_id = temp_db.insert_location(
        latitude=40.7128,
        longitude=-74.0060,
        tags=["new york", "city"],
        description="New York City"
    )
    
    # Retrieve the location
    location = temp_db.get_location(location_id)
    
    assert location is not None
    assert location['id'] == location_id
    assert location['latitude'] == 40.7128
    assert location['longitude'] == -74.0060
    assert location['description'] == "New York City"

def test_update_location(temp_db):
    """Test location update"""
    # Insert a location
    location_id = temp_db.insert_location(
        latitude=51.5074,
        longitude=-0.1278,
        tags=["london"],
        description="London"
    )
    
    # Update the location
    success = temp_db.update_location(
        location_id,
        description="London, UK",
        tags=["london", "uk", "capital"]
    )
    
    assert success is True
    
    # Verify the update
    location = temp_db.get_location(location_id)
    assert location['description'] == "London, UK"

def test_delete_location(temp_db):
    """Test location deletion"""
    # Insert a location
    location_id = temp_db.insert_location(
        latitude=48.8566,
        longitude=2.3522,
        tags=["paris"],
        description="Paris"
    )
    
    # Delete the location
    success = temp_db.delete_location(location_id)
    assert success is True
    
    # Verify deletion
    location = temp_db.get_location(location_id)
    assert location is None

def test_search_by_location(temp_db):
    """Test geographic search"""
    # Insert multiple locations
    temp_db.insert_location(37.7749, -122.4194, ["sf"], "San Francisco")
    temp_db.insert_location(37.8044, -122.2712, ["oakland"], "Oakland")  # ~13km from SF
    temp_db.insert_location(40.7128, -74.0060, ["nyc"], "New York")     # Far away
    
    # Search near San Francisco
    results = temp_db.search_by_location(37.7749, -122.4194, radius_km=20)
    
    # Should find SF and Oakland, but not NYC
    assert len(results) >= 1  # At least SF
    descriptions = [r['description'] for r in results]
    assert "San Francisco" in descriptions

def test_search_by_text(temp_db):
    """Test full-text search"""
    # Insert locations with different descriptions
    temp_db.insert_location(37.7749, -122.4194, ["restaurant"], "Great Italian restaurant")
    temp_db.insert_location(37.8044, -122.2712, ["cafe"], "Cozy coffee shop")
    temp_db.insert_location(40.7128, -74.0060, ["restaurant"], "Amazing pizza place")
    
    # Search for restaurants
    results = temp_db.search_by_text("restaurant")
    
    assert len(results) >= 1
    descriptions = [r['description'] for r in results]
    assert any("restaurant" in desc.lower() for desc in descriptions)

def test_get_all_locations(temp_db):
    """Test getting all locations with pagination"""
    # Insert multiple locations
    for i in range(5):
        temp_db.insert_location(
            latitude=37.0 + i * 0.1,
            longitude=-122.0 + i * 0.1,
            tags=[f"tag{i}"],
            description=f"Location {i}"
        )
    
    # Get all locations
    all_locations = temp_db.get_all_locations(limit=10)
    assert len(all_locations) == 5
    
    # Test pagination
    first_page = temp_db.get_all_locations(limit=3, offset=0)
    second_page = temp_db.get_all_locations(limit=3, offset=3)
    
    assert len(first_page) == 3
    assert len(second_page) == 2  # Remaining 2 locations

def test_get_locations_by_embedding_ids(temp_db):
    """Test getting locations by embedding IDs"""
    # Insert locations with embedding IDs
    id1 = temp_db.insert_location(37.7749, -122.4194, ["tag1"], "Loc 1", embedding_id=10)
    id2 = temp_db.insert_location(40.7128, -74.0060, ["tag2"], "Loc 2", embedding_id=20)
    temp_db.insert_location(51.5074, -0.1278, ["tag3"], "Loc 3", embedding_id=30)
    
    # Search by embedding IDs
    results = temp_db.get_locations_by_embedding_ids([10, 20])
    
    assert len(results) == 2
    embedding_ids = [r['embedding_id'] for r in results]
    assert 10 in embedding_ids
    assert 20 in embedding_ids
    assert 30 not in embedding_ids