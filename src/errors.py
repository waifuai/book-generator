"""
Custom exceptions for the book generation system.
"""
from typing import Any, Optional


class BookGenerationError(Exception):
    """Custom exception for book generation errors with enhanced error information."""

    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message