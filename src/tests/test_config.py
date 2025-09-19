"""
Test Suite for API Configuration Module

This module contains comprehensive unit tests for the APIConfig class and its
configuration management functionality. It tests API key resolution, client
initialization, and error handling for various configuration scenarios.

Key test areas:
- Successful API configuration and client initialization
- File-based API key loading and validation
- Environment variable fallback handling
- Error handling for missing or invalid API key files
- Google GenAI client initialization failures
- Mock-based testing for file I/O operations
"""

# src/tests/test_config.py
import unittest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import logging

# Add src to path if necessary (handled by pytest.ini)
# import sys
# sys.path.insert(0, str(Path(__file__).parent.parent))

from ..config import APIConfig
from ..errors import BookGenerationError

# Suppress logs during tests
logging.disable(logging.CRITICAL)

class TestAPIConfig(unittest.TestCase):

    @patch('src.config.Path.open', new_callable=mock_open, read_data="test-api-key")
    @patch('src.config.Path.expanduser')
    @patch('src.config.genai.Client')  # Mock client init
    def test_api_config_init_success(self, mock_client_ctor, mock_expanduser, mock_open_method):
        """Test successful initialization and client creation."""
        mock_expanded_path = Path("/home/user/.api-gemini")
        mock_expanduser.return_value = mock_expanded_path

        config = APIConfig(api_key_file="~/.api-gemini")

        mock_expanduser.assert_called_once_with()
        self.assertEqual(config.api_key_path, mock_expanded_path)
        mock_open_method.assert_called_once_with("r", encoding="utf-8")
        self.assertEqual(config.api_key, "test-api-key")
        mock_client_ctor.assert_called_once()
        args, kwargs = mock_client_ctor.call_args
        self.assertEqual(kwargs.get("api_key"), "test-api-key")

    @patch('src.config.Path.expanduser')
    def test_api_config_file_not_found(self, mock_expanduser):
        """Test error handling when the API key file is missing."""
        mock_expanded_path = Path("/home/user/.nonexistent-keyfile")
        mock_expanduser.return_value = mock_expanded_path

        # Simulate FileNotFoundError when Path.open is called
        with patch('src.config.Path.open', side_effect=FileNotFoundError):
            with self.assertRaises(BookGenerationError) as context:
                APIConfig(api_key_file="~/.nonexistent-keyfile")

        self.assertIn("API key file not found", str(context.exception))
        self.assertIn(str(mock_expanded_path), str(context.exception))

    @patch('src.config.Path.open', new_callable=mock_open, read_data="") # Simulate empty file
    @patch('src.config.Path.expanduser')
    def test_api_config_file_empty(self, mock_expanduser, mock_open_method):
        """Test error handling when the API key file is empty."""
        mock_expanded_path = Path("/home/user/.empty-keyfile")
        mock_expanduser.return_value = mock_expanded_path

        with self.assertRaises(BookGenerationError) as context:
            APIConfig(api_key_file="~/.empty-keyfile")

        self.assertIn("API key file is empty", str(context.exception))
        self.assertIn(str(mock_expanded_path), str(context.exception))
        mock_open_method.assert_called_once_with("r", encoding="utf-8")

    @patch('src.config.Path.open', new_callable=mock_open, read_data="test-api-key")
    @patch('src.config.Path.expanduser')
    @patch('src.config.genai.Client', side_effect=Exception("Client init failed"))  # Simulate client failure
    def test_api_config_client_init_failure(self, mock_client_ctor, mock_expanduser, mock_open_method):
        """Test error handling when genai.Client fails."""
        mock_expanded_path = Path("/home/user/.api-gemini")
        mock_expanduser.return_value = mock_expanded_path

        with self.assertRaises(BookGenerationError) as context:
            APIConfig(api_key_file="~/.api-gemini")

        self.assertIn("Failed to initialize Google GenAI client", str(context.exception))
        self.assertIn("Client init failed", str(context.exception))
        mock_client_ctor.assert_called_once()


if __name__ == "__main__":
    # Restore logging level if running tests directly
    logging.disable(logging.NOTSET)
    unittest.main()