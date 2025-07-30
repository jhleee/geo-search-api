#!/usr/bin/env python3
"""
GeoTag API Server Entry Point

Run the FastAPI server for the GeoTag location tagging system.
"""

import uvicorn
from src.config import get_config

def main():
    """Start the API server"""
    config = get_config()
    
    print(f"🚀 Starting GeoTag API Server...")
    print(f"📍 Host: {config.api.host}:{config.api.port}")
    print(f"📚 API Docs: http://{config.api.host}:{config.api.port}/docs")
    print(f"🔧 Model: {config.embedding.model_name}")
    
    uvicorn.run(
        "src.api:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.reload,
        log_level=config.api.log_level
    )

if __name__ == "__main__":
    main()