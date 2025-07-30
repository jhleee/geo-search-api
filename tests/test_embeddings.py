import pytest
import tempfile
import os
import numpy as np
from src.embeddings import EmbeddingManager

@pytest.fixture
def temp_embedding_manager():
    """Create a temporary embedding manager for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = os.path.join(temp_dir, "test_index.bin")
        metadata_path = os.path.join(temp_dir, "test_metadata.pkl")
        
        # Use a smaller model for testing
        em = EmbeddingManager(
            model_name="all-MiniLM-L6-v2",
            index_path=index_path,
            metadata_path=metadata_path
        )
        yield em

def test_embedding_manager_initialization(temp_embedding_manager):
    """Test embedding manager initialization"""
    assert temp_embedding_manager.model is not None
    assert temp_embedding_manager.index is not None
    assert temp_embedding_manager.dimension == 384

def test_encode_text(temp_embedding_manager):
    """Test text encoding"""
    text = "This is a test sentence"
    embedding = temp_embedding_manager.encode_text(text)
    
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (384,)
    assert embedding.dtype == np.float32

def test_encode_multiple_texts(temp_embedding_manager):
    """Test encoding multiple texts"""
    texts = ["First sentence", "Second sentence", "Third sentence"]
    embeddings = temp_embedding_manager.encode_texts(texts)
    
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (3, 384)
    assert embeddings.dtype == np.float32

def test_add_embedding(temp_embedding_manager):
    """Test adding single embedding"""
    text = "Coffee shop with great wifi"
    embedding_id = temp_embedding_manager.add_embedding(text)
    
    assert isinstance(embedding_id, int)
    assert embedding_id >= 0
    assert temp_embedding_manager.get_embedding_count() == 1

def test_add_multiple_embeddings(temp_embedding_manager):
    """Test adding multiple embeddings"""
    texts = [
        "Coffee shop with wifi",
        "Italian restaurant downtown",
        "Beautiful park with lake"
    ]
    embeddings = temp_embedding_manager.encode_texts(texts)
    embedding_ids = temp_embedding_manager.add_embeddings(embeddings)
    
    assert len(embedding_ids) == 3
    assert all(isinstance(eid, int) for eid in embedding_ids)
    assert temp_embedding_manager.get_embedding_count() == 3

def test_search_similar_small_index(temp_embedding_manager):
    """Test similarity search with small index (not trained)"""
    # Add just a few embeddings (not enough to train IVF)
    texts = ["Coffee shop", "Restaurant"]
    for text in texts:
        temp_embedding_manager.add_embedding(text)
    
    # Search should return empty for untrained index
    results = temp_embedding_manager.search_similar("Coffee place", k=5)
    assert len(results) == 0  # Index not trained

def test_search_similar_large_index(temp_embedding_manager):
    """Test similarity search with large enough index to train"""
    # Add enough embeddings to train the index (100+)
    texts = []
    for i in range(150):
        if i < 50:
            texts.append(f"Coffee shop number {i}")
        elif i < 100:
            texts.append(f"Restaurant number {i}")
        else:
            texts.append(f"Park location {i}")
    
    # Add all embeddings
    for text in texts:
        temp_embedding_manager.add_embedding(text)
    
    # Now search should work
    results = temp_embedding_manager.search_similar("Coffee place", k=5, threshold=0.3)
    
    # Should find some coffee-related results
    assert len(results) > 0
    assert all(isinstance(result[0], int) and isinstance(result[1], float) for result in results)
    
    # Scores should be in descending order
    scores = [score for _, score in results]
    assert scores == sorted(scores, reverse=True)

def test_create_combined_text(temp_embedding_manager):
    """Test creating combined text from description and tags"""
    description = "Great coffee shop"
    tags = ["coffee", "wifi", "cozy"]
    
    combined = temp_embedding_manager.create_combined_text(description, tags)
    assert combined == "Great coffee shop coffee wifi cozy"
    
    # Test with empty description
    combined = temp_embedding_manager.create_combined_text("", tags)
    assert combined == "coffee wifi cozy"
    
    # Test with empty tags
    combined = temp_embedding_manager.create_combined_text(description, [])
    assert combined == "Great coffee shop"
    
    # Test with both empty
    combined = temp_embedding_manager.create_combined_text("", [])
    assert combined == "no description"

def test_save_and_load_index(temp_embedding_manager):
    """Test saving and loading index"""
    # Add some embeddings
    texts = ["Test text 1", "Test text 2", "Test text 3"]
    for text in texts:
        temp_embedding_manager.add_embedding(text)
    
    original_count = temp_embedding_manager.get_embedding_count()
    
    # Save index
    temp_embedding_manager.save_index()
    
    # Create new manager with same paths
    new_manager = EmbeddingManager(
        index_path=temp_embedding_manager.index_path,
        metadata_path=temp_embedding_manager.metadata_path
    )
    
    # Should have loaded the same data
    assert new_manager.get_embedding_count() == original_count
    assert new_manager.next_embedding_id == temp_embedding_manager.next_embedding_id

def test_embedding_consistency(temp_embedding_manager):
    """Test that same text produces same embedding"""
    text = "Consistent test text"
    
    embedding1 = temp_embedding_manager.encode_text(text)
    embedding2 = temp_embedding_manager.encode_text(text)
    
    # Should be identical (or very close due to floating point)
    np.testing.assert_array_almost_equal(embedding1, embedding2, decimal=6)