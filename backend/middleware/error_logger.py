"""
Error logging middleware for debugging.
"""

import logging
import traceback
from datetime import datetime
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Log errors with detailed information."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            
            # Log 4xx and 5xx errors
            if response.status_code >= 400:
                logger.warning(
                    f"❌ {response.status_code} | "
                    f"{request.method} {request.url.path} | "
                    f"IP: {request.client.host}"
                )
            
            return response
            
        except Exception as e:
            # Log detailed error
            logger.error(
                f"🔥 EXCEPTION | "
                f"{request.method} {request.url.path} | "
                f"IP: {request.client.host} | "
                f"Error: {str(e)}\n"
                f"{traceback.format_exc()}"
            )
            raise