import uuid
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    conversation_id: uuid.UUID = Field(..., description="ID of the active conversation scope")
    question: str = Field(..., description="User query text")
