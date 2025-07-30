import yaml
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

@dataclass
class DatabaseConfig:
    path: str = "geo_tags.db"

@dataclass
class EmbeddingConfig:
    model_name: str = "dragonkue/multilingual-e5-small-ko"
    dimension: int = 384
    max_sequence_length: int = 512
    use_query_prefix: bool = True
    use_passage_prefix: bool = True
    index_path: str = "faiss_index.bin"
    metadata_path: str = "faiss_metadata.pkl"
    index_type: str = "IVFFlat"
    n_centroids: int = 100
    n_probe: int = 10
    similarity_threshold: float = 0.5
    batch_size: int = 32

@dataclass
class APIConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    log_level: str = "info"
    title: str = "Geo Tag API"
    description: str = "A lightweight location tagging and search system with Korean language support"
    version: str = "1.0.0"

@dataclass
class SearchConfig:
    default_limit: int = 10
    max_limit: int = 100
    default_radius_km: float = 1.0
    max_radius_km: float = 100.0
    text_search_limit: int = 100
    vector_search_limit: int = 50

@dataclass
class PerformanceConfig:
    max_memory_mb: int = 512
    max_threads: int = 2
    auto_save_interval: int = 100

@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None

@dataclass
class Config:
    database: DatabaseConfig
    embedding: EmbeddingConfig
    api: APIConfig
    search: SearchConfig
    performance: PerformanceConfig
    logging: LoggingConfig

class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self._config: Optional[Config] = None
        
    def load_config(self) -> Config:
        """Load configuration from YAML file"""
        if self._config is None:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    config_data = yaml.safe_load(file)
                self._config = self._create_config_from_dict(config_data)
            else:
                # Create default config if file doesn't exist
                self._config = self._create_default_config()
                self.save_config()
        
        return self._config
    
    def save_config(self):
        """Save current configuration to YAML file"""
        if self._config:
            config_dict = self._config_to_dict(self._config)
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(config_dict, file, default_flow_style=False, allow_unicode=True)
    
    def _create_config_from_dict(self, config_data: Dict[str, Any]) -> Config:
        """Create Config object from dictionary"""
        database_config = DatabaseConfig(**config_data.get('database', {}))
        embedding_config = EmbeddingConfig(**config_data.get('embedding', {}))
        api_config = APIConfig(**config_data.get('api', {}))
        search_config = SearchConfig(**config_data.get('search', {}))
        performance_config = PerformanceConfig(**config_data.get('performance', {}))
        logging_config = LoggingConfig(**config_data.get('logging', {}))
        
        return Config(
            database=database_config,
            embedding=embedding_config,
            api=api_config,
            search=search_config,
            performance=performance_config,
            logging=logging_config
        )
    
    def _create_default_config(self) -> Config:
        """Create default configuration"""
        return Config(
            database=DatabaseConfig(),
            embedding=EmbeddingConfig(),
            api=APIConfig(),
            search=SearchConfig(),
            performance=PerformanceConfig(),
            logging=LoggingConfig()
        )
    
    def _config_to_dict(self, config: Config) -> Dict[str, Any]:
        """Convert Config object to dictionary"""
        return {
            'database': {
                'path': config.database.path
            },
            'embedding': {
                'model_name': config.embedding.model_name,
                'dimension': config.embedding.dimension,
                'max_sequence_length': config.embedding.max_sequence_length,
                'use_query_prefix': config.embedding.use_query_prefix,
                'use_passage_prefix': config.embedding.use_passage_prefix,
                'index_path': config.embedding.index_path,
                'metadata_path': config.embedding.metadata_path,
                'index_type': config.embedding.index_type,
                'n_centroids': config.embedding.n_centroids,
                'n_probe': config.embedding.n_probe,
                'similarity_threshold': config.embedding.similarity_threshold,
                'batch_size': config.embedding.batch_size
            },
            'api': {
                'host': config.api.host,
                'port': config.api.port,
                'reload': config.api.reload,
                'log_level': config.api.log_level,
                'title': config.api.title,
                'description': config.api.description,
                'version': config.api.version
            },
            'search': {
                'default_limit': config.search.default_limit,
                'max_limit': config.search.max_limit,
                'default_radius_km': config.search.default_radius_km,
                'max_radius_km': config.search.max_radius_km,
                'text_search_limit': config.search.text_search_limit,
                'vector_search_limit': config.search.vector_search_limit
            },
            'performance': {
                'max_memory_mb': config.performance.max_memory_mb,
                'max_threads': config.performance.max_threads,
                'auto_save_interval': config.performance.auto_save_interval
            },
            'logging': {
                'level': config.logging.level,
                'format': config.logging.format,
                'file': config.logging.file
            }
        }
    
    def get_embedding_model_info(self) -> Dict[str, Any]:
        """Get embedding model information"""
        model_info = {
            'dragonkue/multilingual-e5-small-ko': {
                'dimension': 384,
                'max_length': 512,
                'language': 'Korean + Multilingual',
                'size': '118MB',
                'requires_prefix': True,
                'description': 'Korean-optimized multilingual E5 model'
            },
            'all-MiniLM-L6-v2': {
                'dimension': 384,
                'max_length': 256,
                'language': 'English',
                'size': '22MB',
                'requires_prefix': False,
                'description': 'Lightweight English sentence transformer'
            },
            'intfloat/multilingual-e5-small': {
                'dimension': 384,
                'max_length': 512,
                'language': 'Multilingual',
                'size': '118MB',
                'requires_prefix': True,
                'description': 'Original multilingual E5 small model'
            },
            'dragonkue/BGE-m3-ko': {
                'dimension': 1024,
                'max_length': 8192,
                'language': 'Korean + Multilingual',
                'size': '600MB',
                'requires_prefix': False,
                'description': 'High-performance Korean BGE model'
            }
        }
        
        return model_info.get(self._config.embedding.model_name, {
            'dimension': self._config.embedding.dimension,
            'max_length': self._config.embedding.max_sequence_length,
            'language': 'Unknown',
            'size': 'Unknown',
            'requires_prefix': self._config.embedding.use_query_prefix,
            'description': 'Custom model'
        })

# Global config manager instance
config_manager = ConfigManager()

def get_config() -> Config:
    """Get global configuration instance"""
    return config_manager.load_config()

def setup_logging():
    """Setup logging based on configuration"""
    config = get_config()
    
    # Configure logging
    log_config = {
        'level': getattr(logging, config.logging.level.upper()),
        'format': config.logging.format
    }
    
    if config.logging.file:
        log_config['filename'] = config.logging.file
    
    logging.basicConfig(**log_config)
    
    # Set specific loggers
    logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
    logging.getLogger('transformers').setLevel(logging.WARNING)
    logging.getLogger('torch').setLevel(logging.WARNING)