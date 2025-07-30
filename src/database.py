import sqlite3
import json
from typing import List, Optional, Tuple
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "geo_tags.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables and indexes"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                -- Main locations table
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    tags TEXT,  -- JSON array
                    description TEXT,
                    embedding_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- FTS5 full-text search virtual table
                CREATE VIRTUAL TABLE IF NOT EXISTS locations_fts USING fts5(
                    description, tags, content=locations, content_rowid=id
                );
                
                -- R-tree spatial index
                CREATE VIRTUAL TABLE IF NOT EXISTS locations_rtree USING rtree(
                    id, min_lat, max_lat, min_lon, max_lon
                );
                
                -- Triggers to keep FTS and R-tree in sync
                CREATE TRIGGER IF NOT EXISTS locations_ai AFTER INSERT ON locations BEGIN
                    INSERT INTO locations_fts(rowid, description, tags) 
                    VALUES (new.id, new.description, new.tags);
                    INSERT INTO locations_rtree(id, min_lat, max_lat, min_lon, max_lon)
                    VALUES (new.id, new.latitude, new.latitude, new.longitude, new.longitude);
                END;
                
                CREATE TRIGGER IF NOT EXISTS locations_ad AFTER DELETE ON locations BEGIN
                    INSERT INTO locations_fts(locations_fts, rowid, description, tags) 
                    VALUES('delete', old.id, old.description, old.tags);
                    DELETE FROM locations_rtree WHERE id = old.id;
                END;
                
                CREATE TRIGGER IF NOT EXISTS locations_au AFTER UPDATE ON locations BEGIN
                    INSERT INTO locations_fts(locations_fts, rowid, description, tags) 
                    VALUES('delete', old.id, old.description, old.tags);
                    INSERT INTO locations_fts(rowid, description, tags) 
                    VALUES (new.id, new.description, new.tags);
                    UPDATE locations_rtree SET 
                        min_lat = new.latitude, max_lat = new.latitude,
                        min_lon = new.longitude, max_lon = new.longitude
                    WHERE id = new.id;
                END;
                
                -- Index for faster queries
                CREATE INDEX IF NOT EXISTS idx_locations_created_at ON locations(created_at);
                CREATE INDEX IF NOT EXISTS idx_locations_embedding_id ON locations(embedding_id);
            """)
            conn.commit()
            logger.info("Database initialized successfully")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def insert_location(self, latitude: float, longitude: float, 
                       tags: List[str], description: str, 
                       embedding_id: Optional[int] = None) -> int:
        """Insert a new location record"""
        tags_json = json.dumps(tags) if tags else "[]"
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO locations (latitude, longitude, tags, description, embedding_id)
                VALUES (?, ?, ?, ?, ?)
            """, (latitude, longitude, tags_json, description, embedding_id))
            conn.commit()
            return cursor.lastrowid
    
    def insert_locations_bulk(self, locations_data: List[Tuple]) -> List[int]:
        """Insert multiple location records efficiently"""
        if not locations_data:
            return []
            
        with self.get_connection() as conn:
            # Use executemany for efficient bulk insert
            cursor = conn.executemany("""
                INSERT INTO locations (latitude, longitude, tags, description, embedding_id)
                VALUES (?, ?, ?, ?, ?)
            """, locations_data)
            conn.commit()
            
            # Get the inserted IDs
            count = cursor.rowcount
            if count == 0:
                return []
            
            # For bulk inserts, lastrowid gives the last inserted ID
            # We need to get all IDs by querying the most recent inserts
            last_id = cursor.lastrowid
            if last_id is None:
                # Fallback: query for recent IDs
                cursor = conn.execute("""
                    SELECT id FROM locations 
                    ORDER BY id DESC 
                    LIMIT ?
                """, (count,))
                ids = [row[0] for row in cursor.fetchall()]
                return list(reversed(ids))  # Return in insertion order
            else:
                # Return sequential IDs
                return list(range(last_id - count + 1, last_id + 1))
    
    def get_location(self, location_id: int) -> Optional[dict]:
        """Get a location by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM locations WHERE id = ?
            """, (location_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def update_location(self, location_id: int, latitude: float = None, 
                       longitude: float = None, tags: List[str] = None, 
                       description: str = None, embedding_id: int = None) -> bool:
        """Update a location record"""
        updates = []
        params = []
        
        if latitude is not None:
            updates.append("latitude = ?")
            params.append(latitude)
        if longitude is not None:
            updates.append("longitude = ?")
            params.append(longitude)
        if tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(tags))
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if embedding_id is not None:
            updates.append("embedding_id = ?")
            params.append(embedding_id)
        
        if not updates:
            return False
        
        params.append(location_id)
        
        with self.get_connection() as conn:
            cursor = conn.execute(f"""
                UPDATE locations SET {', '.join(updates)} WHERE id = ?
            """, params)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_location(self, location_id: int) -> bool:
        """Delete a location record"""
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM locations WHERE id = ?", (location_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def search_by_location(self, latitude: float, longitude: float, 
                          radius_km: float = 1.0) -> List[dict]:
        """Search locations within a radius (approximate using bounding box)"""
        # Rough conversion: 1 degree ≈ 111 km
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * abs(math.cos(math.radians(latitude))))
        
        min_lat = latitude - lat_delta
        max_lat = latitude + lat_delta
        min_lon = longitude - lon_delta
        max_lon = longitude + lon_delta
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT l.* FROM locations l
                JOIN locations_rtree r ON l.id = r.id
                WHERE r.min_lat >= ? AND r.max_lat <= ?
                AND r.min_lon >= ? AND r.max_lon <= ?
            """, (min_lat, max_lat, min_lon, max_lon))
            return [dict(row) for row in cursor.fetchall()]
    
    def search_by_text(self, query: str, limit: int = 100) -> List[dict]:
        """Full-text search in descriptions and tags"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT l.* FROM locations l
                JOIN locations_fts fts ON l.id = fts.rowid
                WHERE locations_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_locations(self, limit: int = 1000, offset: int = 0) -> List[dict]:
        """Get all locations with pagination"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM locations 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_locations_by_embedding_ids(self, embedding_ids: List[int]) -> List[dict]:
        """Get locations by embedding IDs (for vector search results)"""
        if not embedding_ids:
            return []
        
        placeholders = ','.join('?' * len(embedding_ids))
        
        with self.get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT * FROM locations 
                WHERE embedding_id IN ({placeholders})
                ORDER BY created_at DESC
            """, embedding_ids)
            return [dict(row) for row in cursor.fetchall()]

import math