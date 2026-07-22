import uuid
from datetime import datetime
from pydantic import BaseModel

class DocumentResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    filename: str
    file_size: int
    mime_type: str
    created_at: datetime

    class Config:
        from_attributes = True
