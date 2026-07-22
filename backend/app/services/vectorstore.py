import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from app.core.config import settings

class QdrantService:
    def __init__(self):
        # Initialize the Async Qdrant Client
        if settings.QDRANT_API_KEY:
            self.client = AsyncQdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY
            )
        else:
            self.client = AsyncQdrantClient(url=settings.QDRANT_URL)

    def _get_collection_name(self, embedding_provider: str) -> str:
        """Returns collection name suffixed by provider to avoid dimension collisions."""
        return f"{settings.QDRANT_COLLECTION_NAME}_{embedding_provider.lower()}"

    async def ensure_collection(self, embedding_provider: str, dimension: int):
        """Creates collection if it doesn't exist, matching vector dimensions."""
        collection_name = self._get_collection_name(embedding_provider)
        
        # Check if collection exists
        collections_resp = await self.client.get_collections()
        exists = any(c.name == collection_name for c in collections_resp.collections)
        
        if not exists:
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=dimension,
                    distance=models.Distance.COSINE
                )
            )
            
            # Setup payload index for conversation_id (for efficient query isolation)
            await self.client.create_payload_index(
                collection_name=collection_name,
                field_name="conversation_id",
                field_schema=models.PayloadSchemaType.KEYWORD
            )

    async def upsert_chunks(
        self,
        conversation_id: uuid.UUID,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        filename: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        embedding_provider: str
    ):
        """Generates points from chunks and uploads them into Qdrant."""
        if not chunks:
            return

        dimension = len(embeddings[0])
        collection_name = self._get_collection_name(embedding_provider)
        await self.ensure_collection(embedding_provider, dimension)

        points = []
        for idx, chunk in enumerate(chunks):
            # Generate deterministic UUID based on document id and chunk index
            point_id = str(uuid.uuid5(document_id, f"chunk_{idx}"))
            
            payload = {
                "conversation_id": str(conversation_id),
                "document_id": str(document_id),
                "user_id": str(user_id),
                "filename": filename,
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"]
            }
            
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=embeddings[idx],
                    payload=payload
                )
            )
            
        await self.client.upsert(
            collection_name=collection_name,
            points=points
        )

    async def search_vectors(
        self,
        conversation_id: uuid.UUID,
        query_vector: List[float],
        embedding_provider: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Searches the vector space, strictly filtering by conversation_id.
        No global vector search is possible.
        """
        collection_name = self._get_collection_name(embedding_provider)
        
        # Verify collection exists before querying
        collections_resp = await self.client.get_collections()
        exists = any(c.name == collection_name for c in collections_resp.collections)
        if not exists:
            return []

        # Strict conversation-level filter
        conversation_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="conversation_id",
                    match=models.MatchValue(value=str(conversation_id))
                )
            ]
        )

        results = await self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=conversation_filter,
            limit=limit,
            with_payload=True
        )

        hits = []
        for hit in results.points:
            if hit.payload:
                hits.append({
                    "text": hit.payload.get("text"),
                    "filename": hit.payload.get("filename"),
                    "page_number": hit.payload.get("page_number"),
                    "chunk_index": hit.payload.get("chunk_index"),
                    "score": hit.score
                })
        return hits

    async def delete_document_vectors(
        self, 
        conversation_id: uuid.UUID, 
        document_id: uuid.UUID, 
        embedding_provider: str
    ):
        """Removes all vectors belonging to a specific document."""
        collection_name = self._get_collection_name(embedding_provider)
        
        # If collection doesn't exist, nothing to delete
        collections_resp = await self.client.get_collections()
        if not any(c.name == collection_name for c in collections_resp.collections):
            return

        await self.client.delete(
            collection_name=collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="conversation_id",
                            match=models.MatchValue(value=str(conversation_id))
                        ),
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=str(document_id))
                        )
                    ]
                )
            )
        )

    async def delete_conversation_vectors(
        self, 
        conversation_id: uuid.UUID, 
        embedding_provider: str
    ):
        """Removes all vectors belonging to a conversation."""
        collection_name = self._get_collection_name(embedding_provider)
        
        collections_resp = await self.client.get_collections()
        if not any(c.name == collection_name for c in collections_resp.collections):
            return

        await self.client.delete(
            collection_name=collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="conversation_id",
                            match=models.MatchValue(value=str(conversation_id))
                        )
                    ]
                )
            )
        )
