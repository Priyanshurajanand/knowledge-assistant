import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class UserCreate(UserBase):
    name: str = Field(..., min_length=2, max_length=100, description="Name or username is required during registration")
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    role: Optional[str] = Field(default="user", description="Default role is user")

class UserLogin(UserBase):
    password: str

class UserResponse(UserBase):
    id: uuid.UUID
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserSettingsResponse(BaseModel):
    preferred_provider: str
    preferred_model: str
    dark_mode: bool

    class Config:
        from_attributes = True

class UserSettingsUpdate(BaseModel):
    preferred_provider: Optional[str] = None
    preferred_model: Optional[str] = None
    dark_mode: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenPayload(BaseModel):
    sub: str
    type: str
    exp: int
