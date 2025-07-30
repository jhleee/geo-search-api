import time
import logging
from typing import List, Optional, Tuple
from .database import Database
from .embeddings import EmbeddingManager
from .models import LocationCreate, LocationUpdate, LocationResponse, SearchResult, BulkLocationCreate, BulkLocationResponse
from .config import get_config, setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class GeoTagService:
    def __init__(self, db_path: str = None):
        self.config = get_config()
        
        # Use configured database path if not provided
        if db_path is None:
            db_path = self.config.database.path
            
        self.db = Database(db_path)
        self.embedding_manager = EmbeddingManager()
        logger.info(f"GeoTagService initialized with model: {self.config.embedding.model_name}")
    
    def create_location(self, location_data: LocationCreate) -> LocationResponse:
        """Create a new location with embedding"""
        # Create combined text for embedding
        combined_text = self.embedding_manager.create_combined_text(
            location_data.description, location_data.tags
        )
        
        # Generate embedding
        embedding_id = self.embedding_manager.add_embedding(combined_text)
        
        # Insert into database
        location_id = self.db.insert_location(
            latitude=location_data.latitude,
            longitude=location_data.longitude,
            tags=location_data.tags,
            description=location_data.description,
            embedding_id=embedding_id
        )
        
        # Return the created location
        location_row = self.db.get_location(location_id)
        return LocationResponse.from_db_row(location_row)
    
    def get_location(self, location_id: int) -> Optional[LocationResponse]:
        """Get a location by ID"""
        location_row = self.db.get_location(location_id)
        if location_row:
            return LocationResponse.from_db_row(location_row)
        return None
    
    def update_location(self, location_id: int, update_data: LocationUpdate) -> Optional[LocationResponse]:
        """Update a location"""
        # Get current location
        current_location = self.db.get_location(location_id)
        if not current_location:
            return None
        
        # Prepare update parameters
        update_params = {}
        if update_data.latitude is not None:
            update_params['latitude'] = update_data.latitude
        if update_data.longitude is not None:
            update_params['longitude'] = update_data.longitude
        if update_data.tags is not None:
            update_params['tags'] = update_data.tags
        if update_data.description is not None:
            update_params['description'] = update_data.description
        
        # If description or tags changed, update embedding
        if update_data.description is not None or update_data.tags is not None:
            new_description = update_data.description if update_data.description is not None else current_location['description']
            new_tags = update_data.tags if update_data.tags is not None else json.loads(current_location.get('tags', '[]'))
            
            combined_text = self.embedding_manager.create_combined_text(new_description, new_tags)
            new_embedding_id = self.embedding_manager.add_embedding(combined_text)
            update_params['embedding_id'] = new_embedding_id
        
        # Update in database
        success = self.db.update_location(location_id, **update_params)
        if success:
            updated_location = self.db.get_location(location_id)
            return LocationResponse.from_db_row(updated_location)
        
        return None
    
    def delete_location(self, location_id: int) -> bool:
        """Delete a location"""
        return self.db.delete_location(location_id)
    
    def search_by_location(self, latitude: float, longitude: float, 
                          radius_km: float = 1.0, limit: int = 10) -> List[SearchResult]:
        """Search locations by geographic proximity"""
        start_time = time.time()
        
        locations = self.db.search_by_location(latitude, longitude, radius_km)[:limit]
        
        results = []
        for location_row in locations:
            location = LocationResponse.from_db_row(location_row)
            
            # Calculate actual distance
            distance = self._calculate_distance(
                latitude, longitude, 
                location.latitude, location.longitude
            )
            
            if distance <= radius_km:
                results.append(SearchResult(
                    location=location,
                    distance_km=distance
                ))
        
        # Sort by distance
        results.sort(key=lambda x: x.distance_km or 0)
        
        return results
    
    def search_by_text(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Full-text search in descriptions and tags"""
        locations = self.db.search_by_text(query, limit)
        
        results = []
        for location_row in locations:
            location = LocationResponse.from_db_row(location_row)
            results.append(SearchResult(location=location))
        
        return results
    
    def search_by_vector(self, query: str, limit: int = None, 
                        threshold: float = None) -> List[SearchResult]:
        """Vector similarity search"""
        # Use configured limits if not provided
        if limit is None:
            limit = self.config.search.vector_search_limit
        if threshold is None:
            threshold = self.config.embedding.similarity_threshold
            
        # Search for similar embeddings
        similar_embeddings = self.embedding_manager.search_similar(
            query, k=limit * 2, threshold=threshold  # Get more to filter
        )
        
        if not similar_embeddings:
            return []
        
        # Get embedding IDs and scores
        embedding_ids = [emb_id for emb_id, score in similar_embeddings]
        scores_map = {emb_id: score for emb_id, score in similar_embeddings}
        
        # Get locations from database
        locations = self.db.get_locations_by_embedding_ids(embedding_ids)
        
        results = []
        for location_row in locations:
            location = LocationResponse.from_db_row(location_row)
            score = scores_map.get(location.embedding_id, 0.0)
            
            results.append(SearchResult(
                location=location,
                score=score
            ))
        
        # Sort by score descending
        results.sort(key=lambda x: x.score or 0, reverse=True)
        
        return results[:limit]
    
    def unified_search(self, search_query: 'UnifiedSearchQuery') -> 'UnifiedSearchResponse':
        """통합 검색 - 여러 검색 방법을 조합하여 최적의 결과 제공"""
        from .models import UnifiedSearchResponse
        
        start_time = time.time()
        all_results = []
        search_types_used = []
        search_counts = {}
        
        # 1. 텍스트 검색 (키워드 기반)
        if search_query.use_text:
            text_results = self.search_by_text(search_query.query, limit=search_query.limit)
            all_results.extend(text_results)
            search_types_used.append("text")
            search_counts["text"] = len(text_results)
        
        # 2. 벡터 검색 (의미 기반)
        if search_query.use_vector:
            vector_results = self.search_by_vector(
                search_query.query, 
                limit=search_query.limit, 
                threshold=search_query.vector_threshold
            )
            all_results.extend(vector_results)
            search_types_used.append("vector")
            search_counts["vector"] = len(vector_results)
        
        # 3. 위치 검색 (좌표 기반)
        if (search_query.use_location and 
            search_query.latitude is not None and 
            search_query.longitude is not None):
            location_results = self.search_by_location(
                search_query.latitude,
                search_query.longitude,
                search_query.radius_km,
                limit=search_query.limit
            )
            all_results.extend(location_results)
            search_types_used.append("location")
            search_counts["location"] = len(location_results)
        
        # 중복 제거 및 점수 통합
        unique_results = {}
        for result in all_results:
            location_id = result.location.id
            if location_id not in unique_results:
                unique_results[location_id] = result
            else:
                # 기존 결과와 새 결과의 점수를 결합
                existing = unique_results[location_id]
                new_score = 0.0
                
                # 점수 통합 로직
                if existing.score is not None and result.score is not None:
                    new_score = max(existing.score, result.score)  # 최고 점수 사용
                elif existing.score is not None:
                    new_score = existing.score
                elif result.score is not None:
                    new_score = result.score
                
                # 거리 정보 보존
                if result.distance_km is not None:
                    existing.distance_km = result.distance_km
                
                existing.score = new_score
        
        # 결과 정렬 (점수 기준 내림차순, 거리 기준 오름차순)
        final_results = list(unique_results.values())
        final_results.sort(key=lambda x: (-(x.score or 0), x.distance_km or float('inf')))
        
        # 제한된 결과 반환
        final_results = final_results[:search_query.limit]
        
        query_time_ms = (time.time() - start_time) * 1000
        
        # 검색 요약 정보
        search_summary = {
            "query": search_query.query,
            "search_counts": search_counts,
            "total_before_dedup": len(all_results),
            "total_after_dedup": len(unique_results),
            "final_count": len(final_results),
            "coordinates_used": search_query.latitude is not None and search_query.longitude is not None,
            "radius_km": search_query.radius_km if search_query.latitude is not None else None
        }
        
        return UnifiedSearchResponse(
            results=final_results,
            total_count=len(final_results),
            search_types_used=search_types_used,
            query_time_ms=query_time_ms,
            search_summary=search_summary
        )
    
    def get_all_locations(self, limit: int = 100, offset: int = 0) -> List[LocationResponse]:
        """Get all locations with pagination"""
        locations = self.db.get_all_locations(limit, offset)
        return [LocationResponse.from_db_row(row) for row in locations]
    
    def get_stats(self) -> dict:
        """Get system statistics"""
        return {
            "total_locations": len(self.db.get_all_locations(limit=10000)),  # Rough count
            "total_embeddings": self.embedding_manager.get_embedding_count(),
            "embedding_model": self.embedding_manager.model_name,
            "index_type": "IVFFlat"
        }
    
    def create_locations_bulk(self, bulk_data: BulkLocationCreate) -> BulkLocationResponse:
        """Create multiple locations efficiently with batch processing"""
        start_time = time.time()
        
        created_locations = []
        errors = []
        success_count = 0
        failed_count = 0
        
        # Prepare data for batch processing
        location_texts = []
        db_data = []
        
        # First pass: prepare all data and validate
        for i, location_data in enumerate(bulk_data.locations):
            try:
                # Validate location data
                if not (-90 <= location_data.latitude <= 90):
                    raise ValueError(f"Invalid latitude: {location_data.latitude}")
                if not (-180 <= location_data.longitude <= 180):
                    raise ValueError(f"Invalid longitude: {location_data.longitude}")
                
                # Create combined text for embedding
                combined_text = self.embedding_manager.create_combined_text(
                    location_data.description, location_data.tags
                )
                location_texts.append(combined_text)
                
                # Prepare database data (without embedding_id for now)
                db_data.append((
                    location_data.latitude,
                    location_data.longitude,
                    location_data.tags,
                    location_data.description,
                    None  # Will be updated after embedding generation
                ))
                
            except Exception as e:
                errors.append({
                    "index": i,
                    "location": location_data.dict(),
                    "error": str(e)
                })
                failed_count += 1
        
        # Batch generate embeddings for all valid locations
        embedding_ids = []
        if location_texts:
            try:
                logger.info(f"Generating embeddings for {len(location_texts)} locations")
                
                # Generate embeddings in batches
                batch_size = self.config.embedding.batch_size
                all_embeddings = []
                
                for i in range(0, len(location_texts), batch_size):
                    batch_texts = location_texts[i:i + batch_size]
                    batch_embeddings = self.embedding_manager.encode_texts(batch_texts, is_query=False)
                    all_embeddings.append(batch_embeddings)
                
                # Combine all embeddings
                if all_embeddings:
                    import numpy as np
                    combined_embeddings = np.vstack(all_embeddings)
                    
                    # Add embeddings to FAISS index
                    embedding_ids = self.embedding_manager.add_embeddings(combined_embeddings)
                    
                logger.info(f"Generated {len(embedding_ids)} embeddings")
                
            except Exception as e:
                logger.error(f"Failed to generate embeddings: {e}")
                # If embedding fails, we can still insert without embeddings
                embedding_ids = [None] * len(location_texts)
        
        # Update db_data with embedding_ids
        valid_db_data = []
        embedding_idx = 0
        
        for i, (lat, lon, tags, desc, _) in enumerate(db_data):
            if i < len(embedding_ids):
                # Convert tags to JSON string for database
                tags_json = json.dumps(tags) if tags else "[]"
                valid_db_data.append((lat, lon, tags_json, desc, embedding_ids[embedding_idx]))
                embedding_idx += 1
        
        # Bulk insert into database
        if valid_db_data:
            try:
                logger.info(f"Bulk inserting {len(valid_db_data)} locations")
                location_ids = self.db.insert_locations_bulk(valid_db_data)
                
                # Create response objects
                for i, location_id in enumerate(location_ids):
                    location_row = self.db.get_location(location_id)
                    if location_row:
                        created_locations.append(LocationResponse.from_db_row(location_row))
                        success_count += 1
                    else:
                        failed_count += 1
                        errors.append({
                            "index": i,
                            "error": "Failed to retrieve created location"
                        })
                        
                logger.info(f"Successfully created {success_count} locations")
                
            except Exception as e:
                logger.error(f"Bulk database insert failed: {e}")
                failed_count += len(valid_db_data)
                errors.append({
                    "error": f"Database bulk insert failed: {str(e)}"
                })
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return BulkLocationResponse(
            success_count=success_count,
            failed_count=failed_count,
            total_count=len(bulk_data.locations),
            created_locations=created_locations,
            errors=errors,
            processing_time_ms=processing_time_ms
        )
    
    def _calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        import math
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        
        return c * r

import json