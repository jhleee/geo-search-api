import pytest
import time
import tempfile
import os
from src.service import GeoTagService
from src.models import LocationCreate

@pytest.fixture
def performance_service():
    """Create a service for performance testing"""
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

def create_test_data(service: GeoTagService, count: int = 1000):
    """Create test data for performance testing"""
    locations = []
    
    # Create diverse location data
    categories = ["restaurant", "cafe", "park", "shop", "office", "hotel", "museum", "library"]
    adjectives = ["great", "amazing", "cozy", "modern", "historic", "popular", "quiet", "busy"]
    
    for i in range(count):
        category = categories[i % len(categories)]
        adjective = adjectives[i % len(adjectives)]
        
        location_data = LocationCreate(
            latitude=37.7749 + (i % 100) * 0.001,  # Spread around SF
            longitude=-122.4194 + (i % 100) * 0.001,
            tags=[category, adjective, f"tag{i%10}"],
            description=f"{adjective.title()} {category} number {i}"
        )
        
        location = service.create_location(location_data)
        locations.append(location)
        
        if i % 100 == 0:
            print(f"Created {i+1}/{count} locations")
    
    return locations

def test_create_performance(performance_service):
    """Test creation performance"""
    count = 100
    start_time = time.time()
    
    locations = create_test_data(performance_service, count)
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / count
    
    print(f"\nCreated {count} locations in {total_time:.2f}s")
    print(f"Average time per location: {avg_time*1000:.2f}ms")
    
    assert len(locations) == count
    assert avg_time < 0.1  # Should be less than 100ms per location

def test_search_performance_small_dataset(performance_service):
    """Test search performance with small dataset"""
    # Create 100 locations
    locations = create_test_data(performance_service, 100)
    
    # Test different search types
    search_queries = [
        ("restaurant", "text"),
        ("great coffee shop", "vector"),
        (37.7749, -122.4194, 1.0, "location")
    ]
    
    for query in search_queries:
        start_time = time.time()
        
        if query[1] == "text":
            results = performance_service.search_by_text(query[0], limit=10)
        elif query[1] == "vector":
            results = performance_service.search_by_vector(query[0], limit=10, threshold=0.3)
        elif query[1] == "location":
            results = performance_service.search_by_location(query[0], query[1], query[2], limit=10)
        
        end_time = time.time()
        search_time = (end_time - start_time) * 1000
        
        print(f"\n{query[1].title()} search took {search_time:.2f}ms")
        print(f"Found {len(results)} results")
        
        # For small dataset, all searches should be very fast
        assert search_time < 100  # Less than 100ms

def test_search_performance_large_dataset(performance_service):
    """Test search performance with larger dataset (simulating 10k records)"""
    # Create 1000 locations (representative sample)
    locations = create_test_data(performance_service, 1000)
    
    # Test search performance
    queries = [
        ("restaurant italian", "text"),
        ("cozy coffee shop with wifi", "vector"),
        ("historic museum downtown", "vector"),
    ]
    
    for query_text, search_type in queries:
        times = []
        
        # Run multiple searches to get average
        for _ in range(5):
            start_time = time.time()
            
            if search_type == "text":
                results = performance_service.search_by_text(query_text, limit=20)
            elif search_type == "vector":
                results = performance_service.search_by_vector(query_text, limit=20, threshold=0.2)
            
            end_time = time.time()
            search_time = (end_time - start_time) * 1000
            times.append(search_time)
        
        avg_time = sum(times) / len(times)
        print(f"\n{search_type.title()} search average: {avg_time:.2f}ms")
        
        # Should be fast even with 1000 records
        assert avg_time < 200  # Less than 200ms average

def test_concurrent_operations(performance_service):
    """Test performance under concurrent-like load"""
    # Create base data
    locations = create_test_data(performance_service, 200)
    
    # Simulate concurrent operations
    operations = []
    start_time = time.time()
    
    for i in range(50):
        # Mixed operations
        if i % 3 == 0:
            # Create
            location_data = LocationCreate(
                latitude=37.8 + i * 0.001,
                longitude=-122.3 + i * 0.001,
                tags=["concurrent", "test"],
                description=f"Concurrent test location {i}"
            )
            result = performance_service.create_location(location_data)
            operations.append(("create", result.id))
        
        elif i % 3 == 1:
            # Search
            results = performance_service.search_by_text("test", limit=5)
            operations.append(("search", len(results)))
        
        else:
            # Get
            location_id = locations[i % len(locations)].id
            result = performance_service.get_location(location_id)
            operations.append(("get", result.id if result else None))
    
    end_time = time.time()
    total_time = (end_time - start_time) * 1000
    avg_time = total_time / len(operations)
    
    print(f"\n50 mixed operations took {total_time:.2f}ms")
    print(f"Average time per operation: {avg_time:.2f}ms")
    
    assert len(operations) == 50
    assert avg_time < 50  # Less than 50ms per operation

def test_memory_usage(performance_service):
    """Test memory efficiency (basic check)"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Create moderate amount of data
    locations = create_test_data(performance_service, 500)
    
    # Perform various operations
    for i in range(20):
        performance_service.search_by_text("restaurant", limit=10)
        performance_service.search_by_vector("coffee shop", limit=10, threshold=0.3)
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    print(f"\nInitial memory: {initial_memory:.1f}MB")
    print(f"Final memory: {final_memory:.1f}MB")
    print(f"Memory increase: {memory_increase:.1f}MB")
    
    # Should not use excessive memory
    assert memory_increase < 500  # Less than 500MB increase

def test_embedding_index_performance(performance_service):
    """Test embedding index performance specifically"""
    # Create enough data to train the FAISS index
    locations = create_test_data(performance_service, 150)
    
    # Test embedding search performance
    queries = [
        "italian restaurant with good food",
        "quiet coffee shop for working",
        "modern office building downtown",
        "historic museum with artifacts"
    ]
    
    for query in queries:
        start_time = time.time()
        results = performance_service.search_by_vector(query, limit=15, threshold=0.2)
        end_time = time.time()
        
        search_time = (end_time - start_time) * 1000
        print(f"\nVector search '{query}': {search_time:.2f}ms, {len(results)} results")
        
        # Vector search should be fast once index is trained
        if len(results) > 0:  # Only check if index is trained and returns results
            assert search_time < 100  # Less than 100ms

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])