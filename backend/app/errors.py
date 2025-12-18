# /backend/app/errors.py
"""
Standard error responses with proper HTTP status codes
"""

from enum import Enum
from fastapi import HTTPException, status
from typing import Dict, Any

class ErrorCode(str, Enum):
    # Authentication
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_TOKEN = "INVALID_TOKEN"
    MFA_REQUIRED = "MFA_REQUIRED"
    
    # Validation
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_EMAIL = "INVALID_EMAIL"
    PASSWORD_WEAK = "PASSWORD_WEAK"
    USERNAME_TAKEN = "USERNAME_TAKEN"
    EMAIL_TAKEN = "EMAIL_TAKEN"
    
    # Resources
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    FORBIDDEN = "FORBIDDEN"
    NOT_MEMBER = "NOT_MEMBER"
    
    # Limits
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    
    # Server
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"

class APIError(Exception):
    """Base API error"""
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int,
        details: Dict[str, Any] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

class BadRequestError(APIError):
    def __init__(self, code: ErrorCode, message: str, details=None):
        super().__init__(code, message, status.HTTP_400_BAD_REQUEST, details)

class UnauthorizedError(APIError):
    def __init__(self, code: ErrorCode, message: str):
        super().__init__(code, message, status.HTTP_401_UNAUTHORIZED)

class ForbiddenError(APIError):
    def __init__(self, code: ErrorCode, message: str):
        super().__init__(code, message, status.HTTP_403_FORBIDDEN)

class NotFoundError(APIError):
    def __init__(self, resource: str):
        super().__init__(
            ErrorCode.NOT_FOUND,
            f"{resource} not found",
            status.HTTP_404_NOT_FOUND
        )

class ConflictError(APIError):
    def __init__(self, code: ErrorCode, message: str):
        super().__init__(code, message, status.HTTP_409_CONFLICT)

class TooManyRequestsError(APIError):
    def __init__(self, retry_after: int):
        super().__init__(
            ErrorCode.RATE_LIMIT_EXCEEDED,
            "Too many requests",
            status.HTTP_429_TOO_MANY_REQUESTS,
            {"retry_after": retry_after}
        )

class InternalServerError(APIError):
    def __init__(self, code: ErrorCode, message: str, request_id: str = None):
        details = {"request_id": request_id} if request_id else {}
        super().__init__(code, message, status.HTTP_500_INTERNAL_SERVER_ERROR, details)

# Error response formatter
def format_error_response(error: APIError):
    """Format error for HTTP response"""
    return {
        "error": error.message,
        "code": error.code,
        **error.details
    }

# Exception handlers
@app.exception_handler(APIError)
async def api_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(exc)
    )
