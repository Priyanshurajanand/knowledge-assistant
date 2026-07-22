from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.chat import ChatRequest
from app.services.chat import ChatService
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/stream")
async def chat_stream(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Initiates a Server-Sent Events (SSE) streaming session for the RAG pipeline.
    First chunk contains citations. Succeeding chunks contain generated tokens.
    """
    generator = ChatService.chat_rag(
        conversation_id=chat_request.conversation_id,
        user_id=current_user.id,
        question=chat_request.question
    )

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"  # Prevents Nginx buffering streams
    }

    return StreamingResponse(generator, headers=headers)
