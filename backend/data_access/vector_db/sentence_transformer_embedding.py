"""
Sentence Transformers embedding provider.
"""

import logging
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.data_access.vector_db.vector_store import EmbeddingProvider

logger = logging.getLogger(__name__)


class SentenceTransformerEmbedding(EmbeddingProvider):
    """Embedding provider using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logger.info(f"Loading sentence-transformers model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.dimension}")
    
    async def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding vector for text."""
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def generate_embeddings_batch(
        self,
        texts: List[str],
    ) -> List[np.ndarray]:
        """Generate embeddings for multiple texts."""
        try:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                batch_size=32,
                show_progress_bar=len(texts) > 100,
            )
            return [emb for emb in embeddings]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def get_dimension(self) -> int:
        """Return the embedding dimension."""
        return self.dimension