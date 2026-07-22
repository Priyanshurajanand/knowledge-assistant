import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class MessageBase(BaseModel):
    role: str # 'user' or 'assistant'
    content: str

class MessageCreate(MessageBase):
    citations: Optional[List[Dict[str, Any]]] = None

class MessageResponse(MessageBase):
    id: uuid.UUID
    conversation_id: uuid.UUID
    citations: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    title: str

class ConversationCreate(BaseModel):
    title: str = "New Conversation"
    provider: Optional[str] = None
    model: Optional[str] = None

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    is_pinned: Optional[bool] = None

class ConversationResponse(ConversationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    provider: str
    model: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
