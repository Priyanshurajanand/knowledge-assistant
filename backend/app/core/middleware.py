import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.request")

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs the details (method, path, status, latency) of every API request."""
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process the request
        try:
            response = await call_next(request)
        except Exception as e:
            # Exceptions will be caught by global handlers, but we log the crash here as well
            duration = time.time() - start_time
            logger.error(
                f"Method={request.method} Path={request.url.path} Status=500 "
                f"Latency={duration:.4f}s Error={str(e)}"
            )
            raise e

        duration = time.time() - start_time
        
        # Log request stats
        log_level = logging.INFO
        if response.status_code >= 400:
            log_level = logging.WARNING
        if response.status_code >= 500:
            log_level = logging.ERROR
            
        logger.log(
            log_level,
            f"Method={request.method} Path={request.url.path} "
            f"Status={response.status_code} Latency={duration:.4f}s"
        )
        
        return response
