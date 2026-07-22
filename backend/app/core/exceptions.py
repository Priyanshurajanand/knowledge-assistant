from fastapi import HTTPException as FastAPIHTTPException, status
from fastapi.responses import JSONResponse
from fastapi.requests import Request
import logging

logger = logging.getLogger(__name__)

class HTTPException(FastAPIHTTPException):
    """Subclass of FastAPI's HTTPException for custom application error reporting."""
    def __init__(self, status_code: int, detail: str, headers: dict = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class DocumentParsingError(HTTPException):
    def __init__(self, filename: str, reason: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse document '{filename}': {reason}"
        )

class VectorDBError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector Database operation failed: {detail}"
        )

class RAGPipelineError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG Pipeline error: {detail}"
        )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches all unhandled exceptions globally and formats a structured JSON response."""
    logger.exception(f"Unhandled error occurred: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact system administration."}
    )

async def http_exception_handler(request: Request, exc: FastAPIHTTPException) -> JSONResponse:
    """Formats standard HTTPExceptions in a clean, structured schema."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )
