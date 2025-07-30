import numpy as np
import faiss
import pickle
import os
from typing import List, Tuple, Optional
from sentence_transformers import SentenceTransformer
import logging
from .config import get_config

try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

logger = logging.getLogger(__name__)

class EmbeddingManager:
    def __init__(self, config_path: str = None):
        self.config = get_config()
        
        # Model configuration
        self.model_name = self.config.embedding.model_name
        self.index_path = self.config.embedding.index_path
        self.metadata_path = self.config.embedding.metadata_path
        self.dimension = self.config.embedding.dimension
        self.use_query_prefix = self.config.embedding.use_query_prefix
        self.use_passage_prefix = self.config.embedding.use_passage_prefix
        self.batch_size = self.config.embedding.batch_size
        
        # Set performance limits
        self._set_performance_limits()
        
        # Initialize sentence transformer
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        
        # Get model info for validation
        model_info = self.config.embedding
        logger.info(f"Model info: {model_info}")
        
        # Initialize FAISS index
        self.index = None
        self.id_mapping = {}  # Maps FAISS index positions to embedding IDs
        self.next_embedding_id = 0
        self.operation_count = 0  # For auto-save tracking
        
        self.load_or_create_index()
    
    def _set_performance_limits(self):
        """Set performance limits for resource-constrained environments"""
        if HAS_RESOURCE:
            try:
                # Set memory limit
                max_memory = self.config.performance.max_memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (max_memory, -1))
                logger.info(f"Set memory limit to {self.config.performance.max_memory_mb}MB")
            except (OSError, AttributeError):
                logger.warning("Could not set memory limit (not supported on this platform)")
        else:
            logger.info("Memory limit setting not available on Windows")
        
        try:
            # Set FAISS thread count
            faiss.omp_set_num_threads(self.config.performance.max_threads)
            logger.info(f"Set FAISS threads to {self.config.performance.max_threads}")
        except AttributeError:
            logger.warning("Could not set FAISS thread count")
    
    def load_or_create_index(self):
        """Load existing index or create a new one"""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            self.load_index()
        else:
            self.create_new_index()
    
    def create_new_index(self):
        """Create a new FAISS index"""
        index_type = self.config.embedding.index_type
        n_centroids = self.config.embedding.n_centroids
        n_probe = self.config.embedding.n_probe
        
        if index_type == "IVFFlat":
            # Use IVFFlat for memory efficiency
            quantizer = faiss.IndexFlatIP(self.dimension)  # Inner Product for cosine similarity
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, n_centroids)
            self.index.nprobe = n_probe
            logger.info(f"Created new FAISS IVFFlat index (centroids={n_centroids}, probe={n_probe})")
        else:
            # Fallback to flat index
            self.index = faiss.IndexFlatIP(self.dimension)
            logger.info("Created new FAISS Flat index")
    
    def load_index(self):
        """Load existing FAISS index and metadata"""
        try:
            self.index = faiss.read_index(self.index_path)
            
            with open(self.metadata_path, 'rb') as f:
                metadata = pickle.load(f)
                self.id_mapping = metadata['id_mapping']
                self.next_embedding_id = metadata['next_embedding_id']
            
            logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            self.create_new_index()
    
    def save_index(self):
        """Save FAISS index and metadata"""
        try:
            faiss.write_index(self.index, self.index_path)
            
            metadata = {
                'id_mapping': self.id_mapping,
                'next_embedding_id': self.next_embedding_id
            }
            
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info("FAISS index saved successfully")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    def _add_prefix(self, text: str, is_query: bool = True) -> str:
        """Add appropriate prefix to text for E5 models"""
        if not (self.use_query_prefix or self.use_passage_prefix):
            return text
        
        # Check if already has prefix
        if text.startswith(("query:", "passage:")):
            return text
        
        if is_query and self.use_query_prefix:
            return f"query: {text}"
        elif not is_query and self.use_passage_prefix:
            return f"passage: {text}"
        else:
            return text
    
    def encode_text(self, text: str, is_query: bool = True) -> np.ndarray:
        """Encode text to embedding vector"""
        # Add prefix for E5 models
        text_with_prefix = self._add_prefix(text, is_query)
        
        embedding = self.model.encode([text_with_prefix], normalize_embeddings=True)
        return embedding[0].astype('float32')
    
    def encode_texts(self, texts: List[str], is_query: bool = True) -> np.ndarray:
        """Encode multiple texts to embedding vectors"""
        # Add prefixes for E5 models
        texts_with_prefix = [self._add_prefix(text, is_query) for text in texts]
        
        # Process in batches if configured
        if len(texts_with_prefix) > self.batch_size:
            all_embeddings = []
            for i in range(0, len(texts_with_prefix), self.batch_size):
                batch = texts_with_prefix[i:i + self.batch_size]
                batch_embeddings = self.model.encode(batch, normalize_embeddings=True)
                all_embeddings.append(batch_embeddings)
            embeddings = np.vstack(all_embeddings)
        else:
            embeddings = self.model.encode(texts_with_prefix, normalize_embeddings=True)
        
        return embeddings.astype('float32')
    
    def add_embedding(self, text: str, is_query: bool = False) -> int:
        """Add a single embedding to the index"""
        # For location data, treat as passage (not query)
        embedding = self.encode_text(text, is_query=is_query)
        return self.add_embeddings([embedding])[0]
    
    def add_embeddings(self, embeddings) -> List[int]:
        """Add multiple embeddings to the index"""
        # Convert to numpy array if it's a list
        if isinstance(embeddings, list):
            embeddings = np.array(embeddings)
        
        if len(embeddings.shape) == 1:
            embeddings = embeddings.reshape(1, -1)
        
        # Train index if it's IVF and not trained yet
        if hasattr(self.index, 'is_trained') and not self.index.is_trained:
            # Need at least 100 vectors for IVF training
            if self.index.ntotal + len(embeddings) >= 100:
                # Collect enough training data
                training_data = embeddings.copy()
                # If we need more data, create some dummy vectors
                if len(training_data) < 100:
                    dummy_size = 100 - len(training_data)
                    dummy_vectors = np.random.normal(0, 1, (dummy_size, self.dimension)).astype('float32')
                    training_data = np.vstack([training_data, dummy_vectors])
                
                self.index.train(training_data)
                logger.info("FAISS index trained")
            else:
                # For small datasets, switch to a flat index temporarily
                logger.info("Using flat index for small dataset")
                flat_index = faiss.IndexFlatIP(self.dimension)
                if self.index.ntotal > 0:
                    # Copy existing vectors if any
                    existing_vectors = faiss.vector_to_array(self.index.get_xb()).reshape(-1, self.dimension)
                    flat_index.add(existing_vectors)
                self.index = flat_index
        
        # Generate embedding IDs
        embedding_ids = []
        start_pos = self.index.ntotal
        
        for i in range(len(embeddings)):
            embedding_id = self.next_embedding_id
            embedding_ids.append(embedding_id)
            self.id_mapping[start_pos + i] = embedding_id
            self.next_embedding_id += 1
        
        # Add to index
        self.index.add(embeddings)
        
        # Update operation count and auto-save
        self.operation_count += len(embeddings)
        if self.operation_count >= self.config.performance.auto_save_interval:
            self.save_index()
            self.operation_count = 0
        
        return embedding_ids
    
    def search_similar(self, query_text: str, k: int = 10, 
                      threshold: float = None) -> List[Tuple[int, float]]:
        """Search for similar embeddings"""
        if self.index.ntotal == 0:
            return []
        
        # Use configured threshold if not provided
        if threshold is None:
            threshold = self.config.embedding.similarity_threshold
        
        # Encode as query (not passage)
        query_embedding = self.encode_text(query_text, is_query=True).reshape(1, -1)
        
        # Ensure index is trained for IVF
        if hasattr(self.index, 'is_trained') and not self.index.is_trained:
            logger.warning("Index not trained yet, returning empty results")
            return []
        
        scores, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and score >= threshold:  # Filter by threshold
                embedding_id = self.id_mapping.get(idx)
                if embedding_id is not None:
                    results.append((embedding_id, float(score)))
        
        return results
    
    def get_embedding_count(self) -> int:
        """Get total number of embeddings in the index"""
        return self.index.ntotal
    
    def remove_embedding(self, embedding_id: int) -> bool:
        """Remove an embedding (FAISS doesn't support direct removal, so we rebuild)"""
        # For simplicity, we don't implement removal as it requires rebuilding the entire index
        # In a production system, you might want to implement a more sophisticated approach
        logger.warning("Embedding removal not implemented - requires index rebuild")
        return False
    
    def create_combined_text(self, description: str, tags: List[str]) -> str:
        """Create combined text for embedding from description and tags"""
        tags_text = " ".join(tags) if tags else ""
        combined = f"{description} {tags_text}".strip()
        return combined if combined else "no description"
    
    def __del__(self):
        """Destructor to save index on cleanup"""
        if hasattr(self, 'index') and self.index is not None:
            self.save_index()