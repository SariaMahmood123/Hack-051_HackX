"""
Custom exception handlers for LUMEN backend
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger("lumen")


class LumenException(Exception):
    """Base exception for LUMEN errors"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ModelLoadException(LumenException):
    """Raised when a model fails to load"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class GenerationException(LumenException):
    """Raised when generation fails"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class InvalidInputException(LumenException):
    """Raised when input validation fails"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


async def lumen_exception_handler(request: Request, exc: LumenException):
    """Handle custom LUMEN exceptions"""
    logger.error(f"LumenException: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "path": str(request.url.path)
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "path": str(request.url.path)
        }
    )
