import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.user import UserResponse
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.document import Document, DocumentChunk
from app.models.audit import AuditLog

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])

@router.get("/stats")
async def get_admin_stats(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Retrieves aggregated metrics (totals, storage usage, provider split) for admin view."""
    
    # 1. Total Users
    users_stmt = select(func.count(User.id))
    total_users = (await db.execute(users_stmt)).scalar() or 0
    
    # 2. Total Conversations
    convs_stmt = select(func.count(Conversation.id))
    total_convs = (await db.execute(convs_stmt)).scalar() or 0
    
    # 3. Total Documents & Storage Size
    docs_stmt = select(func.count(Document.id), func.sum(Document.file_size))
    docs_res = (await db.execute(docs_stmt)).first()
    total_docs = docs_res[0] if docs_res else 0
    total_storage = docs_res[1] if docs_res and docs_res[1] is not None else 0
    
    # 4. Total Chunks
    chunks_stmt = select(func.count(DocumentChunk.id))
    total_chunks = (await db.execute(chunks_stmt)).scalar() or 0
    
    # 5. LLM Provider Usage distribution
    provider_stmt = (
        select(Conversation.provider, func.count(Conversation.id))
        .group_by(Conversation.provider)
    )
    provider_res = await db.execute(provider_stmt)
    provider_usage = {row[0]: row[1] for row in provider_res.all()}

    # 6. Recent Audit Logs
    audit_stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(15)
    audit_res = await db.execute(audit_stmt)
    audit_logs = []
    for log in audit_res.scalars().all():
        audit_logs.append({
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "action": log.action,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat()
        })
        
    return {
        "total_users": total_users,
        "total_conversations": total_convs,
        "total_documents": total_docs,
        "total_chunks": total_chunks,
        "total_storage_bytes": total_storage,
        "provider_usage": provider_usage,
        "recent_activity": audit_logs
    }

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    """Retrieve lists of all users (for management page)."""
    stmt = select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())

@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: uuid.UUID,
    role: str,
    db: AsyncSession = Depends(get_db)
):
    """Modify user role ('admin' or 'user')."""
    if role not in ["admin", "user"]:
        from app.core.exceptions import HTTPException
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin' or 'user'.")
        
    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        from app.core.exceptions import HTTPException
        raise HTTPException(status_code=404, detail="User not found.")
        
    user.role = role
    db.add(user)
    await db.flush()
    
    # Log the admin action
    audit = AuditLog(
        action="change_role",
        details=f"User {user_id} role updated to {role}",
        ip_address="system"
    )
    db.add(audit)
    
    return user

@router.put("/users/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_user_active(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Enable or disable user access status."""
    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        from app.core.exceptions import HTTPException
        raise HTTPException(status_code=404, detail="User not found.")
        
    user.is_active = not user.is_active
    db.add(user)
    await db.flush()
    
    # Log action
    audit = AuditLog(
        action="toggle_active",
        details=f"User {user_id} active status set to {user.is_active}",
        ip_address="system"
    )
    db.add(audit)
    
    return user
