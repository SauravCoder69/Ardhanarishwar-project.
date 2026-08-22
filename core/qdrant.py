from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from config import QDRANT_STORAGE_PATH, QDRANT_COLLECTION_NAME, EMBEDDING_VECTOR_SIZE
from typing import List, Dict, Any, Optional
import uuid

class LocalQdrantManager:
    """Manages Qdrant vector database storage and similarity search locally."""

    def __init__(self, storage_path: str = str(QDRANT_STORAGE_PATH), collection_name: str = QDRANT_COLLECTION_NAME):
        self.collection_name = collection_name
        try:
            self.client = QdrantClient(path=storage_path)
        except Exception as e:
            print(f"Notice: Qdrant disk storage path '{storage_path}' is locked by another instance. Using in-memory Qdrant client: {e}")
            self.client = QdrantClient(":memory:")
        self._ensure_collection()

    def _ensure_collection(self):
        """Create vector collection if it doesn't already exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=EMBEDDING_VECTOR_SIZE,
                        distance=Distance.COSINE
                    )
                )
                print(f"Created Qdrant collection: '{self.collection_name}' with Cosine distance.")
        except Exception as e:
            print(f"Error initializing Qdrant collection: {e}")

    def upsert_chunks(self, vectors: List[List[float]], payloads: List[Dict[str, Any]]):
        """Upsert text chunk embeddings and metadata into Qdrant."""
        points = []
        for vec, payload in zip(vectors, payloads):
            point_id = str(uuid.uuid4())
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vec,
                    payload=payload
                )
            )
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    def search_similar(
        self,
        query_vector: List[float],
        limit: int = 4,
        category_filter: Optional[str] = None,
        tenant_id_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for most similar document chunks in Qdrant.
        Supports category metadata filtering and multi-tenant data isolation.
        """
        must_conditions = []
        if category_filter and category_filter != "All":
            must_conditions.append(
                FieldCondition(key="category", match=MatchValue(value=category_filter))
            )

        should_conditions = []
        if tenant_id_filter:
            should_conditions = [
                FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id_filter)),
                FieldCondition(key="tenant_id", match=MatchValue(value="tenant_global"))
            ]

        query_filter = None
        if must_conditions or should_conditions:
            query_filter = Filter(
                must=must_conditions if must_conditions else None,
                should=should_conditions if should_conditions else None
            )

        try:
            if hasattr(self.client, 'query_points'):
                res = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=query_filter,
                    limit=limit
                )
                search_result = res.points
            else:
                search_result = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=limit
                )
            
            hits = []
            for hit in search_result:
                hits.append({
                    "score": hit.score,
                    "text": hit.payload.get("text", ""),
                    "document_name": hit.payload.get("document_name", "Document"),
                    "category": hit.payload.get("category", "General"),
                    "source": hit.payload.get("source", ""),
                    "tenant_id": hit.payload.get("tenant_id", "tenant_global"),
                    "uploaded_at": hit.payload.get("uploaded_at", "")
                })
            return hits
        except Exception as e:
            print(f"Qdrant search error: {e}")
            return []

    def delete_document_points(self, document_id: str):
        """Delete all vector points associated with a specific document ID."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            )
        except Exception as e:
            print(f"Qdrant points deletion error: {e}")

# Global Qdrant Manager Instance
qdrant_manager = LocalQdrantManager()
