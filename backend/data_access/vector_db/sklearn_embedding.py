"""
Scikit-learn TF-IDF embedding provider.
"""

import logging
from typing import List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from backend.data_access.vector_db.vector_store import EmbeddingProvider

logger = logging.getLogger(__name__)


class SklearnTfidfEmbedding(EmbeddingProvider):
    """Lightweight embedding provider using TF-IDF."""
    
    def __init__(self, max_features: int = 384):
        logger.info(f"Initializing TF-IDF embedding with {max_features} features")
        self.max_features = max_features
        self.dimension = max_features
        
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),
            min_df=1,
            stop_words='english',
            sublinear_tf=True,
        )
        
        self._is_fitted = False
        logger.info("TF-IDF embedding provider initialized")
    
    def _ensure_fitted(self, texts: List[str]):
        """Ensure vectorizer is fitted on some data."""
        if not self._is_fitted:
            self.vectorizer.fit(texts)
            self._is_fitted = True
            logger.info(f"Fitted TF-IDF vectorizer on {len(texts)} documents")
    
    async def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding vector for text."""
        try:
            if not self._is_fitted:
                self.vectorizer.fit([text])
                self._is_fitted = True
            
            vector = self.vectorizer.transform([text]).toarray()[0]
            
            if len(vector) < self.dimension:
                vector = np.pad(vector, (0, self.dimension - len(vector)))
            elif len(vector) > self.dimension:
                vector = vector[:self.dimension]
            
            return vector
        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return np.zeros(self.dimension)
    
    async def generate_embeddings_batch(
        self,
        texts: List[str],
    ) -> List[np.ndarray]:
        """Generate embeddings for multiple texts."""
        try:
            self._ensure_fitted(texts)
            vectors = self.vectorizer.transform(texts).toarray()
            
            result = []
            for vector in vectors:
                if len(vector) < self.dimension:
                    vector = np.pad(vector, (0, self.dimension - len(vector)))
                elif len(vector) > self.dimension:
                    vector = vector[:self.dimension]
                result.append(vector)
            
            return result
        
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [np.zeros(self.dimension) for _ in texts]
    
    def get_dimension(self) -> int:
        """Return the embedding dimension."""
        return self.dimension