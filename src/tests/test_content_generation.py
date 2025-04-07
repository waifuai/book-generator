# src/tests/test_content_generation.py
import unittest
from unittest.mock import patch, MagicMock
import logging
import google.generativeai as genai # Import genai
from google.api_core import exceptions as api_core_exceptions # Import google-api-core exceptions

# Add src to path if necessary (handled by pytest.ini)
# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).parent.parent))

from content_generation import ContentGenerator
from errors import BookGenerationError
from config import APIConfig # Need APIConfig for initialization

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
    @patch('content_generation.genai.GenerativeModel')
    def test_init_success(self, mock_generative_model):
        """Test successful initialization (search functionality removed)."""
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance

        # Initialize ContentGenerator (no enable_search parameter)
        generator = ContentGenerator(config=self.mock_api_config, model_name="models/gemini-test")

        # Assert GenerativeModel called correctly
        mock_generative_model.assert_called_once()
        call_args, call_kwargs = mock_generative_model.call_args
        self.assertEqual(call_kwargs.get('model_name'), "models/gemini-test")
        # Assert tools parameter is not passed or is implicitly empty
        self.assertNotIn('tools', call_kwargs) # Or check it's [] if genai lib defaults it

        # Search tool classes are no longer imported/used

        # Assert generator attributes
        self.assertEqual(generator.model_name, "models/gemini-test")
        self.assertEqual(generator.model, mock_model_instance)
        self.assertEqual(generator.config, self.mock_api_config)
        # self.enable_search attribute removed

    # test_init_success_search_enabled was removed.

    @patch('content_generation.genai.GenerativeModel')
    def test_init_failure(self, mock_generative_model):
        """Test handling of Gemini initialization failure."""
        mock_generative_model.side_effect = Exception("Model connection failed")

        # Test initialization failure (no search context)
        with self.assertRaises(BookGenerationError) as context:
            ContentGenerator(config=self.mock_api_config, model_name="invalid-gemini-model")
        self.assertIn("Failed to initialize Gemini model 'invalid-gemini-model'", str(context.exception))
        self.assertIn("Model connection failed", str(context.exception))

    @patch('content_generation.genai.GenerativeModel')
    def test_generate_content_success(self, mock_generative_model):
        """Test successful content generation."""
        # Mock the model instance and its generate_content method
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Generated content from Gemini."
        mock_candidate = MagicMock()
        mock_part = MagicMock()
        mock_part.text = "Generated content from Gemini."
        mock_candidate.content.parts = [mock_part]
        # citation_metadata check was removed from source code.
        mock_response.candidates = [mock_candidate]

        mock_model_instance.generate_content.return_value = mock_response
        mock_generative_model.return_value = mock_model_instance

        # Initialize ContentGenerator
        generator = ContentGenerator(config=self.mock_api_config, model_name="models/gemini-test")
        result = generator.generate_content("Test prompt for Gemini")

        self.assertEqual(result, "Generated content from Gemini.")
        mock_model_instance.generate_content.assert_called_once_with("Test prompt for Gemini")

    @patch('content_generation.genai.GenerativeModel')
    def test_generate_content_empty_response(self, mock_generative_model):
        """Test handling of an empty response from Gemini."""
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.candidates = [] # Simulate no candidates
        mock_response.text = ""
        mock_feedback = MagicMock()
        mock_feedback.block_reason = "SAFETY"
        mock_feedback.block_reason_message = "Blocked due to safety concerns."
        mock_response.prompt_feedback = mock_feedback

        # Use a simple side effect for the mock
        mock_model_instance.generate_content.return_value = mock_response
        mock_generative_model.return_value = mock_model_instance

        # Initialize ContentGenerator
        generator = ContentGenerator(config=self.mock_api_config, model_name="models/gemini-test")

        with self.assertRaises(BookGenerationError) as context:
            generator.generate_content("Risky prompt")

        # Check for specific block reason message
        # The retry logic will re-raise the final BookGenerationError from the source code
        self.assertIn("Content generation blocked. Reason: SAFETY", str(context.exception))
        # Check retry happened
        self.assertEqual(mock_model_instance.generate_content.call_count, 3)
        mock_model_instance.generate_content.assert_called_with("Risky prompt")


    @patch('content_generation.genai.GenerativeModel')
    def test_generate_content_retry(self, mock_generative_model):
        """Test retry logic for Gemini API calls."""
        mock_model_instance = MagicMock()
        # Simulate retryable errors then a final non-retryable one if needed, or just fail always
        mock_model_instance.generate_content.side_effect = [
            api_core_exceptions.ServiceUnavailable("API unavailable"),
            api_core_exceptions.DeadlineExceeded("Timeout"),
            Exception("Final API error") # This will be wrapped by BookGenerationError
        ]
        mock_generative_model.return_value = mock_model_instance

        # Initialize ContentGenerator
        generator = ContentGenerator(config=self.mock_api_config, model_name="models/gemini-test")

        with self.assertRaises(BookGenerationError) as context:
            generator.generate_content("test prompt")

        self.assertIn("Failed to generate content with Gemini: Final API error", str(context.exception))
        # Check generator was called multiple times due to retry
        self.assertEqual(mock_model_instance.generate_content.call_count, 3) # Default retry is 3 attempts

    # No Hugging Face specific tests were present to remove.

if __name__ == "__main__":
    # Restore logging level if running tests directly
    logging.disable(logging.NOTSET)
    unittest.main()