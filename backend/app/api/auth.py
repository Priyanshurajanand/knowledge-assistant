from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, Token, 
    TokenRefreshRequest, UserSettingsResponse, UserSettingsUpdate
)
from app.services.auth import AuthService
from app.repositories.user import UserRepository
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    return await AuthService.register(db, user_in)

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Log in using email and password to retrieve access and refresh tokens."""
    return await AuthService.login(db, login_data)

@router.post("/login/swagger", response_model=Token, include_in_schema=False)
async def login_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    """Fallback endpoint for Swagger UI OAuth2 password flow compatibility."""
    login_data = UserLogin(email=form_data.username, password=form_data.password)
    return await AuthService.login(db, login_data)

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: TokenRefreshRequest, 
    db: AsyncSession = Depends(get_db)
):
    """Exchange a valid refresh token for a new access and refresh token pair."""
    return await AuthService.refresh_tokens(db, refresh_data.refresh_token)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Retrieve details of the currently authenticated user."""
    return current_user

@router.get("/me/settings", response_model=UserSettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve preferences (provider, model, UI theme) for the current user."""
    repo = UserRepository(db)
    settings = await repo.get_settings(current_user.id)
    if not settings:
        # If settings somehow don't exist, create defaults dynamically
        settings = await repo.update_settings(current_user.id, {})
    return settings

@router.put("/me/settings", response_model=UserSettingsResponse)
async def update_settings(
    settings_in: UserSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update settings (preferred LLM provider, default model, UI theme)."""
    repo = UserRepository(db)
    settings_data = settings_in.model_dump(exclude_unset=True)
    return await repo.update_settings(current_user.id, settings_data)
