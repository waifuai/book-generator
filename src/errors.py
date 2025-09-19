"""
Custom Exception Classes

This module defines custom exception classes for the book generation system,
providing structured error handling with additional context information.

Key responsibilities:
- Custom exception definitions for book generation errors
- Enhanced error information with error codes and details
- Consistent error handling across the application
- Detailed error reporting and debugging information
"""

from typing import Any, Optional


class BookGenerationError(Exception):
    """
Custom Exception Classes

This module defines custom exception classes for the book generation system,
providing structured error handling with additional context information.

Key responsibilities:
- Custom exception definitions for book generation errors
- Enhanced error information with error codes and details
- Consistent error handling across the application
- Detailed error reporting and debugging information
"""


    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message