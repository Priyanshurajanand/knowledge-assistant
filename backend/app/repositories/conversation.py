import uuid
from typing import List, Optional
from sqlalchemy import select, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation, Message
from app.repositories.base import BaseRepository

class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, db: AsyncSession):
        super().__init__(Conversation, db)

    async def get_user_conversations(
        self, 
        user_id: uuid.UUID, 
        search_query: Optional[str] = None
    ) -> List[Conversation]:
        """Fetch all conversations for a user, sorted by pinned first, then last updated."""
        conditions = [Conversation.user_id == user_id]
        
        if search_query:
            conditions.append(Conversation.title.ilike(f"%{search_query}%"))
            
        stmt = (
            select(Conversation)
            .where(and_(*conditions))
            .order_by(Conversation.is_pinned.desc(), Conversation.updated_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_messages(self, conversation_id: uuid.UUID) -> List[Message]:
        """Retrieve all messages for a conversation, ordered chronologically."""
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_message(
        self, 
        conversation_id: uuid.UUID, 
        role: str, 
        content: str, 
        citations: Optional[List[dict]] = None
    ) -> Message:
        """Create a message inside a conversation and update the conversation's timestamp."""
        # 1. Create message
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations=citations
        )
        self.db.add(message)
        
        # 2. Update conversation modified timestamp
        stmt = (
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(updated_at=func.now())  # triggers SQLAlchemy's auto onupdate
        )
        await self.db.execute(stmt)
        await self.db.flush()
        
        return message

    async def verify_user_ownership(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Check if a conversation belongs to a specific user."""
        stmt = select(Conversation.user_id).where(Conversation.id == conversation_id)
        result = await self.db.execute(stmt)
        owner_id = result.scalar_one_or_none()
        return owner_id == user_id
