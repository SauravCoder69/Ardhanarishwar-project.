import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from utils.pdf import extract_text_from_file
from core.embeddings import embedding_engine
from core.qdrant import qdrant_manager
from database.models import register_document, delete_document_record, get_document_by_id, can_delete_document
from config import get_role_categories

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping character chunks cleanly on paragraph/sentence boundaries.
    """
    if not text:
        return []
    
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk += ("\n\n" if current_chunk else "") + para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            
            # Handle extra long paragraphs
            if len(para) > chunk_size:
                for i in range(0, len(para), chunk_size - overlap):
                    chunks.append(para[i:i + chunk_size])
                current_chunk = ""
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

class RAGPipeline:
    """End-to-End RAG Knowledge Ingestion and Retrieval Pipeline."""

    def ingest_document(
        self,
        file_name: str,
        file_bytes: bytes,
        category: str,
        source: str = "Knowledge Upload",
        tenant_id: str = "tenant_global",
        uploaded_by: int = 1,
        user_role: Optional[str] = None
    ) -> Tuple[bool, str, int]:
        """
        Full ingestion pipeline:
        File -> Text Extraction -> Chunking -> Vector Embedding -> Qdrant Upsert -> SQLite Registry
        """
        if user_role:
            allowed_categories = get_role_categories(user_role)
            if category not in allowed_categories:
                return False, f"Invalid category for {user_role}. Please choose a valid category for this role.", 0

        raw_text = extract_text_from_file(file_name, file_bytes)
        if not raw_text or len(raw_text.strip()) < 10:
            return False, "Failed to extract text from document. File may be empty or unreadable.", 0

        chunks = chunk_text(raw_text, chunk_size=600, overlap=120)
        if not chunks:
            return False, "Document contains no readable text chunks.", 0

        doc_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Generate Embeddings in Batch
        embeddings = embedding_engine.encode_batch(chunks)

        # Prepare Qdrant Payloads
        payloads = []
        for idx, chunk in enumerate(chunks):
            payloads.append({
                "document_id": doc_id,
                "document_name": file_name,
                "category": category,
                "source": source,
                "tenant_id": tenant_id,
                "chunk_index": idx,
                "text": chunk,
                "uploaded_at": timestamp
            })

        # Upsert into Qdrant Vector Store
        qdrant_manager.upsert_chunks(embeddings, payloads)

        # Save metadata record in SQLite database
        register_document(
            doc_id=doc_id,
            document_name=file_name,
            category=category,
            source=source,
            tenant_id=tenant_id,
            uploaded_by=uploaded_by,
            chunk_count=len(chunks)
        )

        return True, f"Successfully indexed '{file_name}' with {len(chunks)} chunks into Qdrant.", len(chunks)

    def retrieve_context(
        self,
        query: str,
        limit: int = 3,
        category_filter: Optional[str] = None,
        tenant_id_filter: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Query vector search to retrieve relevant text chunks & construct prompt context block.
        Enforces tenant_id data isolation.
        """
        if not query.strip():
            return "", []

        query_vector = embedding_engine.encode(query)
        search_hits = qdrant_manager.search_similar(
            query_vector,
            limit=limit,
            category_filter=category_filter,
            tenant_id_filter=tenant_id_filter
        )

        if not search_hits:
            return "", []

        context_blocks = []
        sources = []

        for idx, hit in enumerate(search_hits, 1):
            if hit['score'] >= 0.35:  # Relevance threshold
                context_blocks.append(f"[Source {idx}: {hit['document_name']} ({hit['category']})]\n{hit['text']}")
                sources.append({
                    "document_name": hit['document_name'],
                    "category": hit['category'],
                    "relevance_score": round(hit['score'] * 100, 1),
                    "snippet": hit['text'][:150] + "..."
                })

        formatted_context = "\n\n---\n\n".join(context_blocks)
        return formatted_context, sources

    def delete_document(self, doc_id: str, current_user: Optional[Dict[str, Any]] = None):
        """Remove document vectors from Qdrant and metadata from SQLite only when authorized."""
        document = get_document_by_id(doc_id)
        if not current_user or not can_delete_document(current_user, document):
            return False, "You are not authorized to delete this document."

        qdrant_manager.delete_document_points(doc_id)
        delete_document_record(doc_id)
        return True, "Document deleted successfully."

# Global RAG Pipeline Instance
rag_pipeline = RAGPipeline()
