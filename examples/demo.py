#!/usr/bin/env python3
"""
Demo script for the Geo Tag API
Demonstrates all the features of the system
"""

import time
import json
from src.service import GeoTagService
from src.models import LocationCreate, LocationUpdate

def print_separator(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}\n")

def print_results(results, search_type="Search"):
    print(f"{search_type} Results ({len(results)} found):")
    print("-" * 40)
    for i, result in enumerate(results[:5], 1):  # Show only first 5
        location = result.location if hasattr(result, 'location') else result
        print(f"{i}. {location.description}")
        print(f"   Location: ({location.latitude:.4f}, {location.longitude:.4f})")
        print(f"   Tags: {', '.join(location.tags)}")
        if hasattr(result, 'score') and result.score:
            print(f"   Similarity Score: {result.score:.3f}")
        if hasattr(result, 'distance_km') and result.distance_km:
            print(f"   Distance: {result.distance_km:.2f} km")
        print()

def main():
    print("Geo Tag API Demo")
    print("A lightweight location tagging and search system")
    
    # Initialize service
    service = GeoTagService("demo_geo_tags.db")
    
    print_separator("Creating Sample Locations")
    
    # Sample locations data
    sample_locations = [
        LocationCreate(
            latitude=37.7749, longitude=-122.4194,
            tags=["coffee", "wifi", "cozy"],
            description="Blue Bottle Coffee - Artisanal coffee with great wifi"
        ),
        LocationCreate(
            latitude=37.7849, longitude=-122.4094,
            tags=["restaurant", "italian", "romantic"],
            description="Tony's Little Star Pizza - Authentic Italian pizza"
        ),
        LocationCreate(
            latitude=37.7649, longitude=-122.4294,
            tags=["park", "nature", "running"],
            description="Golden Gate Park - Beautiful park for jogging and relaxation"
        ),
        LocationCreate(
            latitude=37.7949, longitude=-122.3994,
            tags=["bookstore", "quiet", "reading"],
            description="City Lights Bookstore - Historic independent bookstore"
        ),
        LocationCreate(
            latitude=37.7549, longitude=-122.4394,
            tags=["museum", "art", "culture"],
            description="SFMOMA - Modern art museum with contemporary exhibitions"
        ),
        LocationCreate(
            latitude=37.8049, longitude=-122.4094,
            tags=["cafe", "brunch", "outdoor"],
            description="Tartine Bakery - French bakery with outdoor seating"
        ),
        LocationCreate(
            latitude=37.7749, longitude=-122.3994,
            tags=["bar", "cocktails", "nightlife"],
            description="The Alembic - Craft cocktails and whiskey bar"
        ),
        LocationCreate(
            latitude=37.7849, longitude=-122.4294,
            tags=["gym", "fitness", "yoga"],
            description="Equinox Fitness - Premium gym with yoga classes"
        )
    ]
    
    # Create locations
    created_locations = []
    for i, location_data in enumerate(sample_locations, 1):
        location = service.create_location(location_data)
        created_locations.append(location)
        print(f"Created location {i}: {location.description}")
        time.sleep(0.1)  # Small delay to show progress
    
    print(f"\nCreated {len(created_locations)} locations successfully!")
    
    print_separator("Basic CRUD Operations")
    
    # Get a location
    print("Getting location by ID:")
    location = service.get_location(created_locations[0].id)
    print(f"   {location.description}")
    print(f"   Tags: {', '.join(location.tags)}")
    
    # Update a location
    print("\nUpdating location:")
    update_data = LocationUpdate(
        description="Blue Bottle Coffee - Premium artisanal coffee with excellent wifi and workspace",
        tags=["coffee", "wifi", "cozy", "workspace", "premium"]
    )
    updated_location = service.update_location(created_locations[0].id, update_data)
    print(f"   Updated: {updated_location.description}")
    print(f"   New tags: {', '.join(updated_location.tags)}")
    
    print_separator("Text Search")
    
    # Full-text search
    queries = ["coffee", "italian restaurant", "art museum"]
    for query in queries:
        start_time = time.time()
        results = service.search_by_text(query, limit=3)
        search_time = (time.time() - start_time) * 1000
        
        print(f"Search query: '{query}' ({search_time:.1f}ms)")
        print_results(results, "Text Search")
    
    print_separator("Geographic Search")
    
    # Location-based search
    print("Searching near San Francisco center:")
    start_time = time.time()
    results = service.search_by_location(37.7749, -122.4194, radius_km=2.0, limit=5)
    search_time = (time.time() - start_time) * 1000
    
    print(f"   Search time: {search_time:.1f}ms")
    print_results(results, "Geographic Search")
    
    print_separator("Vector Similarity Search")
    
    # Wait a moment for embeddings to be processed
    print("Processing embeddings...")
    time.sleep(2)
    
    # Vector similarity search
    vector_queries = [
        "place to work with laptop and coffee",
        "romantic dinner spot with good food",
        "outdoor activity in nature"
    ]
    
    for query in vector_queries:
        start_time = time.time()
        results = service.search_by_vector(query, limit=3, threshold=0.3)
        search_time = (time.time() - start_time) * 1000
        
        print(f"Vector search: '{query}' ({search_time:.1f}ms)")
        if results:
            print_results(results, "Vector Search")
        else:
            print("   No results found (index may need more data or training)")
        print()
    
    print_separator("System Statistics")
    
    # Get system stats
    stats = service.get_stats()
    print("System Statistics:")
    for key, value in stats.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    print_separator("Performance Test")
    
    # Performance test with rapid searches
    print("Running performance test...")
    
    test_queries = [
        ("coffee wifi", "text"),
        ("romantic restaurant", "text"),
        ("cozy cafe with workspace", "vector"),
        (37.7849, -122.4094, 1.0, "location")
    ]
    
    total_time = 0
    total_searches = 0
    
    for query in test_queries:
        times = []
        for _ in range(5):  # Run each query 5 times
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
        query_desc = query[0] if isinstance(query[0], str) else f"location near ({query[0]:.3f}, {query[1]:.3f})"
        print(f"   {query[-1].title()} search '{query_desc}': {avg_time:.1f}ms avg")
    
    overall_avg = total_time / total_searches
    print(f"\nOverall average search time: {overall_avg:.1f}ms")
    print(f"Total searches performed: {total_searches}")
    
    print_separator("Demo Complete")
    
    print("Demo completed successfully!")
    print(f"Database saved as: demo_geo_tags.db")
    print(f"FAISS index saved as: faiss_index.bin")
    print("\nTry running the API server with:")
    print("   python main.py")
    print("\nThen visit http://localhost:8000/docs for the interactive API documentation")

if __name__ == "__main__":
    main()