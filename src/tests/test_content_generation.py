"""
Test Suite for Content Generation Module

This module contains comprehensive unit tests for the ContentGenerator class and its
AI-powered content generation functionality. It tests Gemini AI integration, retry
logic, error handling, and content validation.

Key test areas:
- Google Gemini AI client integration and initialization
- Successful content generation with mocked responses
- Empty response handling and error cases
- Retry logic with exponential backoff for API failures
- Error handling for various API exceptions
- Mock-based testing for external AI service dependencies
"""

# src/tests/test_content_generation.py
import unittest
from unittest.mock import MagicMock
import logging
from google.api_core import exceptions as api_core_exceptions # Import google-api-core exceptions

# Add src to path if necessary (handled by pytest.ini)
# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).parent.parent))

from ..content_generation import ContentGenerator
from ..errors import BookGenerationError
from ..config import APIConfig # Need APIConfig for initialization

# Suppress googleapiclient discovery_cache errors during tests
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
# Suppress other verbose logs if needed
logging.disable(logging.WARNING) # Disable warnings and below for cleaner test output

class TestContentGenerator(unittest.TestCase):

    def setUp(self):
        # Mock APIConfig to avoid actual file reading/API configuration
        self.mock_api_config = MagicMock(spec=APIConfig)
        self.mock_api_config.api_key = "fake-api-key" # Provide a dummy key

    # Removed Tool and GoogleSearchRetrieval mocks
    def test_init_success(self):
        """Test successful initialization with central client."""
        # Prepare a fake client on config
        fake_client = MagicMock()
        self.mock_api_config.client = fake_client

        generator = ContentGenerator(config=self.mock_api_config, model_name="gemini-test")

        self.assertEqual(generator.model_name, "gemini-test")
        self.assertIs(generator.client, fake_client)
        self.assertIs(generator.config, self.mock_api_config)

    # test_init_success_search_enabled was removed.

    def test_init_no_failure_path(self):
        """Initialization uses provided client; no construction to fail here."""
        self.mock_api_config.client = MagicMock()
        ContentGenerator(config=self.mock_api_config, model_name="gemini-x")

    def test_generate_content_success(self):
        """Test successful content generation via client."""
        fake_client = MagicMock()
        self.mock_api_config.client = fake_client
        mock_response = MagicMock()
        mock_response.text = "Generated content from Gemini."
        fake_client.models.generate_content.return_value = mock_response

        generator = ContentGenerator(config=self.mock_api_config, model_name="gemini-test")
        result = generator.generate_content("Test prompt for Gemini")

        self.assertEqual(result, "Generated content from Gemini.")
        fake_client.models.generate_content.assert_called_once_with(model="gemini-test", contents="Test prompt for Gemini")

    def test_generate_content_empty_response(self):
        """Test handling of an empty response from GenAI."""
        fake_client = MagicMock()
        self.mock_api_config.client = fake_client
        mock_response = MagicMock()
        mock_response.text = ""
        mock_response.candidates = []  # emulate no content
        fake_client.models.generate_content.return_value = mock_response

        generator = ContentGenerator(config=self.mock_api_config, model_name="gemini-test")

        with self.assertRaises(BookGenerationError) as context:
            generator.generate_content("Risky prompt")

        self.assertIn("Failed to generate content with Gemini", str(context.exception))
        # retry decorator triggers 3 attempts
        self.assertEqual(fake_client.models.generate_content.call_count, 3)
        fake_client.models.generate_content.assert_called_with(model="gemini-test", contents="Risky prompt")


    def test_generate_content_retry(self):
        """Test retry logic for GenAI API calls."""
        fake_client = MagicMock()
        self.mock_api_config.client = fake_client
        fake_client.models.generate_content.side_effect = [
            api_core_exceptions.ServiceUnavailable("API unavailable"),
            api_core_exceptions.DeadlineExceeded("Timeout"),
            Exception("Final API error")
        ]

        generator = ContentGenerator(config=self.mock_api_config, model_name="gemini-test")

        with self.assertRaises(BookGenerationError) as context:
            generator.generate_content("test prompt")

        self.assertIn("Failed to generate content with Gemini: Final API error", str(context.exception))
        self.assertEqual(fake_client.models.generate_content.call_count, 3)

    # No Hugging Face specific tests were present to remove.

if __name__ == "__main__":
    # Restore logging if running directly
    logging.disable(logging.NOTSET)
    unittest.main()