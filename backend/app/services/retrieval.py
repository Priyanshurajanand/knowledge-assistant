import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.document import DocumentChunk, Document
from app.services.embedding import EmbeddingFactory
from app.services.vectorstore import QdrantService

logger = logging.getLogger(__name__)

class HybridRetrievalService:
    @staticmethod
    async def retrieve_context(
        db: AsyncSession,
        conversation_id: uuid.UUID,
        query_text: str,
        embedding_provider: str,
        limit: int = 5,
        rrf_k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the top K chunks for the query using Reciprocal Rank Fusion (RRF).
        Fuses Semantic Search (Qdrant vectors) and Keyword Search (Postgres English Full-Text Search).
        """
        # Clean the search input query
        query_clean = query_text.strip()
        if not query_clean:
            return []

        # ----------------------------------------------------
        # 1. SEMANTIC SEARCH PIPELINE (Qdrant Vector DB)
        # ----------------------------------------------------
        semantic_results = []
        try:
            # Generate embedding vector for user query
            embedder = EmbeddingFactory.get_embedding_provider(embedding_provider)
            query_vector = await embedder.embed_query(query_clean)
            
            # Query vector database for matching records in the active conversation
            qdrant = QdrantService()
            # Fetch limit * 3 items to get a larger candidates list for RRF rank merging
            semantic_results = await qdrant.search_vectors(
                conversation_id=conversation_id,
                query_vector=query_vector,
                embedding_provider=embedding_provider,
                limit=limit * 3
            )
        except Exception as e:
            logger.warning(f"Semantic search failed, falling back to keyword search only: {str(e)}")

        # ----------------------------------------------------
        # 2. KEYWORD SEARCH PIPELINE (PostgreSQL FTS)
        # ----------------------------------------------------
        keyword_results = []
        try:
            # Query database matches using PostgreSQL GIN Index for English full-text search
            stmt = (
                select(DocumentChunk, Document.filename)
                .join(Document, Document.id == DocumentChunk.document_id)
                .where(DocumentChunk.conversation_id == conversation_id)
                .where(func.to_tsvector("english", DocumentChunk.text).op("@@")(func.plainto_tsquery("english", query_clean)))
                .limit(limit * 3)
            )
            res = await db.execute(stmt)
            for row in res.all():
                chunk_obj = row[0]
                filename = row[1]
                keyword_results.append({
                    "text": chunk_obj.text,
                    "filename": filename,
                    "page_number": chunk_obj.page_number,
                    "chunk_index": chunk_obj.chunk_index
                })
        except Exception as e:
            logger.warning(f"Postgres FTS search failed, falling back to semantic search only: {str(e)}")

        # ----------------------------------------------------
        # 3. RECIPROCAL RANK FUSION (RRF) rank merging algorithm
        # ----------------------------------------------------
        # RRF matches items based on their ranks rather than raw match scores:
        # Score = Sum ( 1 / (RRF_K + Rank) )
        # Using (filename, chunk_index) as unique identifier key for chunks.
        rrf_scores = {}
        chunks_map = {}

        # Apply RRF score for semantic ranking list (lower rank index = higher priority)
        for rank, item in enumerate(semantic_results):
            key = (item["filename"], item["chunk_index"])
            chunks_map[key] = item
            # rank starts at 0, adding +1 to make it 1-based index rank
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (rrf_k + (rank + 1)))

        # Apply RRF score for keyword ranking list
        for rank, item in enumerate(keyword_results):
            key = (item["filename"], item["chunk_index"])
            if key not in chunks_map:
                chunks_map[key] = item
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (rrf_k + (rank + 1)))

        # If both pipelines failed or returned no results, exit early
        if not rrf_scores:
            return []

        # Sort the accumulated chunks by their combined RRF rank scores descending
        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)

        # Slice and return the top K relevant context chunks
        top_chunks = []
        for key in sorted_keys[:limit]:
            chunk_data = chunks_map[key]
            chunk_data["rrf_score"] = rrf_scores[key]
            top_chunks.append(chunk_data)

        return top_chunks
