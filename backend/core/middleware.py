"""
Custom middleware for LUMEN backend
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging

logger = logging.getLogger("lumen")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"→ {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        duration = time.time() - start_time
        logger.info(
            f"← {request.method} {request.url.path} "
            f"status={response.status_code} duration={duration:.2f}s"
        )
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting (basic implementation)"""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # IP -> list of timestamps
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health checks
        if request.url.path in ["/", "/health"]:
            return await call_next(request)
        
        # Check rate limit
        current_time = time.time()
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Clean old requests
        self.requests[client_ip] = [
            ts for ts in self.requests[client_ip]
            if current_time - ts < self.window_seconds
        ]
        
        # Check limit
        if len(self.requests[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return Response(
                content="Rate limit exceeded",
                status_code=429
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)
        
        return await call_next(request)
