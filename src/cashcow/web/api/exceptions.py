"""
CashCow Web API - Custom exception handlers.
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


class CashCowAPIException(HTTPException):
    """Base exception class for CashCow API errors."""
    pass


class EntityNotFoundError(CashCowAPIException):
    """Raised when an entity is not found."""
    def __init__(self, entity_id: str, entity_type: str = "entity"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_type.capitalize()} with ID '{entity_id}' not found"
        )


class EntityValidationError(CashCowAPIException):
    """Raised when entity validation fails."""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Entity validation failed: {message}"
        )


async def validation_exception_handler(request: Request, exc: ValidationError):
    """
    Handle Pydantic validation errors.
    
    Args:
        request: FastAPI request object
        exc: ValidationError exception
        
    Returns:
        JSONResponse with error details
    """
    logger.error(f"Validation error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
            "message": "Invalid input data provided"
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle general exceptions.
    
    Args:
        request: FastAPI request object
        exc: Exception instance
        
    Returns:
        JSONResponse with error details
    """
    logger.error(f"Unhandled exception on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )