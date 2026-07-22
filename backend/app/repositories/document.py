import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document, DocumentChunk
from app.repositories.base import BaseRepository

class DocumentRepository(BaseRepository[Document]):
    def __init__(self, db: AsyncSession):
        super().__init__(Document, db)

    async def create_document(self, doc_data: dict, chunks_data: List[dict]) -> Document:
        """Create a document record and bulk insert all associated chunks."""
        # 1. Insert Document
        document = Document(**doc_data)
        self.db.add(document)
        await self.db.flush() # populates document.id
        
        # 2. Bulk Create DocumentChunks
        db_chunks = []
        for chunk in chunks_data:
            db_chunk = DocumentChunk(
                document_id=document.id,
                conversation_id=document.conversation_id,
                chunk_index=chunk["chunk_index"],
                page_number=chunk["page_number"],
                text=chunk["text"]
            )
            db_chunks.append(db_chunk)
            
        self.db.add_all(db_chunks)
        await self.db.flush()
        
        return document

    async def get_conversation_documents(self, conversation_id: uuid.UUID) -> List[Document]:
        """Fetch all documents belonging to a specific conversation."""
        stmt = (
            select(Document)
            .where(Document.conversation_id == conversation_id)
            .order_by(Document.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_chunk_count_by_conversation(self, conversation_id: uuid.UUID) -> int:
        """Get the total count of document chunks in a conversation."""
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.conversation_id == conversation_id)
        )
        result = await self.db.execute(stmt)
        return len(result.scalars().all())
