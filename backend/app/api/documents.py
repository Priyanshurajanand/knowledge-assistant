import uuid
from typing import List
from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.document import DocumentResponse
from app.services.document import DocumentService
from app.repositories.document import DocumentRepository
from app.repositories.conversation import ConversationRepository
from app.models.user import User

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    conversation_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and process a document (PDF, DOCX, or TXT) inside a specific conversation.
    Text is parsed, chunked, embedded, and indexed in Qdrant.
    """
    return await DocumentService.upload_and_process(
        db=db,
        file=file,
        conversation_id=conversation_id,
        user_id=current_user.id
    )

@router.get("/conversation/{conversation_id}", response_model=List[DocumentResponse])
async def list_conversation_documents(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all uploaded documents inside a specific conversation scope."""
    # Verify ownership
    conv_repo = ConversationRepository(db)
    owned = await conv_repo.verify_user_ownership(conversation_id, current_user.id)
    if not owned:
        from app.core.exceptions import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found.")
        
    doc_repo = DocumentRepository(db)
    return await doc_repo.get_conversation_documents(conversation_id)

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Deletes a document metadata, local file, and its vectors from Qdrant."""
    await DocumentService.delete_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id
    )
    return None
