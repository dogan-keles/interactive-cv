"""
Sentence Transformers embedding provider.

Uses sentence-transformers library for generating text embeddings.
"""

import logging
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.data_access.vector_db.vector_store import EmbeddingProvider

logger = logging.getLogger(__name__)


class SentenceTransformerEmbedding(EmbeddingProvider):
    """
    Embedding provider using sentence-transformers.
    
    Uses 'all-MiniLM-L6-v2' model:
    - 384 dimensions
    - Fast inference
    - Good quality embeddings
    - Small model size (~80MB)
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding provider.
        
        Args:
            model_name: Name of sentence-transformers model to use
        """
        logger.info(f"Loading sentence-transformers model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.dimension}")
    
    async def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for a text string.
        
        Args:
            text: Input text
            
        Returns:
            Numpy array of embedding vector
        """
        try:
            # sentence-transformers encode() returns numpy array
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def generate_embeddings_batch(
        self,
        texts: List[str],
    ) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts (batched for efficiency).
        
        Args:
            texts: List of input texts
            
        Returns:
            List of numpy arrays (embeddings)
        """
        try:
            # Batch encoding is more efficient
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                batch_size=32,  # Process 32 texts at a time
                show_progress_bar=len(texts) > 100,  # Show progress for large batches
            )
            return [emb for emb in embeddings]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def get_dimension(self) -> int:
        """Return the embedding dimension."""
        return self.dimension