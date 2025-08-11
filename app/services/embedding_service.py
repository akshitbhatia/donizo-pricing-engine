import logging
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
import asyncio
from functools import lru_cache

from app.config import get_embedding_config

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.config = get_embedding_config()
        self.model = None
        self._model_loaded = False
        
    async def _load_model(self):
        """Load the embedding model asynchronously"""
        if self._model_loaded:
            return
            
        try:
            logger.info(f"Loading embedding model: {self.config['model_name']}")
            
            # Run model loading in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, 
                self._load_model_sync
            )
            
            self._model_loaded = True
            logger.info("Embedding model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise
    
    def _load_model_sync(self):
        """Load model synchronously (to be run in thread pool)"""
        try:
            model = SentenceTransformer(
                self.config['model_name'],
                device=self.config['device']
            )
            return model
        except Exception as e:
            logger.error(f"Error in synchronous model loading: {e}")
            raise
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a text string.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            # Ensure model is loaded
            await self._load_model()
            
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return [0.0] * self.config['dimensions']
            
            # Run embedding generation in thread pool
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                self._get_embedding_sync,
                text
            )
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.config['dimensions']
    
    def _get_embedding_sync(self, text: str) -> np.ndarray:
        """Get embedding synchronously (to be run in thread pool)"""
        try:
            # Normalize text
            text = text.strip()
            
            # Generate embedding
            embedding = self.model.encode(
                text,
                batch_size=self.config['batch_size'],
                show_progress_bar=False,
                normalize_embeddings=True
            )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error in synchronous embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(self.config['dimensions'])
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts in batch.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            # Ensure model is loaded
            await self._load_model()
            
            # Filter out empty texts
            valid_texts = [text.strip() for text in texts if text and text.strip()]
            
            if not valid_texts:
                logger.warning("No valid texts provided for batch embedding")
                return [[0.0] * self.config['dimensions']] * len(texts)
            
            # Run batch embedding in thread pool
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                self._get_embeddings_batch_sync,
                valid_texts
            )
            
            # Convert to list of lists
            result = [emb.tolist() for emb in embeddings]
            
            # Pad with zero vectors if needed
            while len(result) < len(texts):
                result.append([0.0] * self.config['dimensions'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error in batch embedding: {e}")
            # Return zero vectors as fallback
            return [[0.0] * self.config['dimensions']] * len(texts)
    
    def _get_embeddings_batch_sync(self, texts: List[str]) -> np.ndarray:
        """Get batch embeddings synchronously (to be run in thread pool)"""
        try:
            # Generate embeddings in batch
            embeddings = self.model.encode(
                texts,
                batch_size=self.config['batch_size'],
                show_progress_bar=False,
                normalize_embeddings=True
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error in synchronous batch embedding: {e}")
            # Return zero vectors as fallback
            return np.zeros((len(texts), self.config['dimensions']))
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score between 0 and 1
        """
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            # Ensure vectors have same shape
            if vec1.shape != vec2.shape:
                logger.error(f"Vector shape mismatch: {vec1.shape} vs {vec2.shape}")
                return 0.0
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Ensure result is between 0 and 1
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def euclidean_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate Euclidean distance between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Euclidean distance
        """
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            # Ensure vectors have same shape
            if vec1.shape != vec2.shape:
                logger.error(f"Vector shape mismatch: {vec1.shape} vs {vec2.shape}")
                return float('inf')
            
            # Calculate Euclidean distance
            distance = np.linalg.norm(vec1 - vec2)
            
            return float(distance)
            
        except Exception as e:
            logger.error(f"Error calculating Euclidean distance: {e}")
            return float('inf')
    
    async def find_most_similar(
        self, 
        query_embedding: List[float], 
        candidate_embeddings: List[List[float]], 
        top_k: int = 5
    ) -> List[tuple[int, float]]:
        """
        Find most similar embeddings to query.
        
        Args:
            query_embedding: Query vector
            candidate_embeddings: List of candidate vectors
            top_k: Number of top results to return
            
        Returns:
            List of (index, similarity_score) tuples
        """
        try:
            similarities = []
            
            for i, candidate in enumerate(candidate_embeddings):
                similarity = self.cosine_similarity(query_embedding, candidate)
                similarities.append((i, similarity))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Return top_k results
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding most similar embeddings: {e}")
            return []
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model"""
        try:
            if not self._model_loaded or not self.model:
                return {
                    "loaded": False,
                    "model_name": self.config['model_name'],
                    "device": self.config['device'],
                    "dimensions": self.config['dimensions']
                }
            
            return {
                "loaded": True,
                "model_name": self.config['model_name'],
                "device": self.config['device'],
                "dimensions": self.config['dimensions'],
                "max_seq_length": getattr(self.model, 'max_seq_length', 'unknown'),
                "model_type": type(self.model).__name__
            }
            
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {"error": str(e)}
    
    async def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for better embedding quality.
        
        Args:
            text: Raw text input
            
        Returns:
            Preprocessed text
        """
        try:
            if not text:
                return ""
            
            # Basic preprocessing
            text = text.strip()
            
            # Remove extra whitespace
            text = ' '.join(text.split())
            
            # Convert to lowercase for consistency
            text = text.lower()
            
            # Remove special characters that might affect embedding
            # Keep alphanumeric, spaces, and common punctuation
            import re
            text = re.sub(r'[^\w\s\-.,!?]', '', text)
            
            return text
            
        except Exception as e:
            logger.error(f"Error preprocessing text: {e}")
            return text if text else ""
    
    async def get_semantic_keywords(self, text: str, top_k: int = 5) -> List[str]:
        """
        Extract semantic keywords from text using embeddings.
        This is a simplified version - in production, you might use more sophisticated methods.
        
        Args:
            text: Input text
            top_k: Number of keywords to extract
            
        Returns:
            List of keywords
        """
        try:
            # Simple keyword extraction based on word frequency and importance
            words = text.lower().split()
            
            # Remove common stop words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
            }
            
            # Filter out stop words and short words
            keywords = [word for word in words if word not in stop_words and len(word) > 2]
            
            # Count frequency
            from collections import Counter
            word_counts = Counter(keywords)
            
            # Return top_k most frequent words
            return [word for word, count in word_counts.most_common(top_k)]
            
        except Exception as e:
            logger.error(f"Error extracting semantic keywords: {e}")
            return []
