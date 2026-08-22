from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_NAME
from typing import List

class LocalEmbeddingModel:
    """Wrapper for SentenceTransformers local embedding generation."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        """Lazy load SentenceTransformer model."""
        if self._model is None:
            print(f"Loading local embedding model: {self.model_name}...")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, text: str) -> List[float]:
        """Encode single text string into float embedding vector."""
        if not text:
            return [0.0] * 384
        vector = self.model.encode(text, convert_to_numpy=True)
        return vector.tolist()

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode batch of text strings."""
        if not texts:
            return []
        vectors = self.model.encode(texts, convert_to_numpy=True)
        return vectors.tolist()

# Global Embedding Instance
embedding_engine = LocalEmbeddingModel()
