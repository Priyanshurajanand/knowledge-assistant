import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.database import async_session_maker, engine
from sqlalchemy import text as sa_text
from app.core.exceptions import (
    HTTPException, 
    http_exception_handler, 
    global_exception_handler
)
from app.core.middleware import LoggingMiddleware
from app.core.security import hash_password
from app.repositories.user import UserRepository
from app.api.router import api_router

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown lifecycle tasks."""
    # Ensure physical document storage exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Auto-seed database with default user & admin accounts for development
    try:
        async with async_session_maker() as db:
            # Auto-migrate existing database records to Groq since OpenAI keys are not present
            await db.execute(sa_text(
                "UPDATE user_settings SET preferred_provider = 'groq', preferred_model = 'llama-3.3-70b-versatile' WHERE preferred_provider = 'openai'"
            ))
            await db.execute(sa_text(
                "UPDATE conversations SET provider = 'groq', model = 'llama-3.3-70b-versatile' WHERE provider = 'openai'"
            ))
            # Auto-migrate name column in users table if it does not exist
            await db.execute(sa_text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(255)"
            ))
            await db.execute(sa_text(
                "UPDATE users SET name = 'Administrator' WHERE email = 'admin@company.com' AND name IS NULL"
            ))
            await db.execute(sa_text(
                "UPDATE users SET name = 'Standard User' WHERE email = 'user@company.com' AND name IS NULL"
            ))
            await db.commit()

            repo = UserRepository(db)
            existing_admin = await repo.get_by_email("admin@company.com")
            if not existing_admin:
                logger.info("Empty database detected. Seeding default demo accounts...")
                
                # Admin account
                await repo.create_user({
                    "email": "admin@company.com",
                    "password_hash": hash_password("adminpassword123"),
                    "role": "admin",
                    "name": "Administrator",
                    "is_active": True
                })
                
                # Standard user account
                await repo.create_user({
                    "email": "user@company.com",
                    "password_hash": hash_password("userpassword123"),
                    "role": "user",
                    "name": "Standard User",
                    "is_active": True
                })
                
                await db.commit()
                logger.info("Database seeding complete:")
                logger.info("  Admin user: admin@company.com / adminpassword123")
                logger.info("  Standard user: user@company.com / userpassword123")
            else:
                logger.info("Accounts already present, skipping database seeding.")
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")

    yield
    # Cleanup on shutdown
    await engine.dispose()
    logger.info("Database engine connections closed.")

# Instantiate main app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan
)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom middleware
app.add_middleware(LoggingMiddleware)

# Register exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom formatter for validation errors."""
    errors = exc.errors()
    error_detail = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Validation error")
        error_detail.append(f"{loc}: {msg}")
    
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error: " + "; ".join(error_detail)}
    )

# Include aggregate router
app.include_router(api_router)

@app.get("/")
async def root():
    """Simple API status checks."""
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
async def health_check():
    """Service health state check."""
    return {"status": "healthy"}
