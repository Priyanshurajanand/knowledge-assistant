import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserSettings
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email address."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def create_user(self, user_data: dict) -> User:
        """Create a new user and initialize default UserSettings."""
        # 1. Create user
        user = User(**user_data)
        self.db.add(user)
        await self.db.flush()

        # 2. Initialize settings
        settings = UserSettings(
            user_id=user.id,
            preferred_provider="groq",
            preferred_model="llama-3.3-70b-versatile",
            dark_mode=True
        )
        self.db.add(settings)
        await self.db.flush()
        
        return user

    async def get_settings(self, user_id: uuid.UUID) -> Optional[UserSettings]:
        """Fetch user settings by user ID."""
        result = await self.db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
        return result.scalars().first()

    async def update_settings(self, user_id: uuid.UUID, settings_data: dict) -> Optional[UserSettings]:
        """Update settings for a user, creating them if not present."""
        settings = await self.get_settings(user_id)
        if not settings:
            settings = UserSettings(user_id=user_id, **settings_data)
            self.db.add(settings)
        else:
            for key, val in settings_data.items():
                if val is not None and hasattr(settings, key):
                    setattr(settings, key, val)
            self.db.add(settings)
        
        await self.db.flush()
        return settings
