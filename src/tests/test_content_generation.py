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

    @patch('content_generation.Tool')
    @patch('content_generation.GoogleSearchRetrieval')
    @patch('content_generation.genai.GenerativeModel')
    def test_init_success_search_disabled(self, mock_generative_model, mock_search_retrieval, mock_tool):
        """Test successful initialization with search disabled (default)."""
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance

        # Initialize with enable_search=False (or default)
        generator = ContentGenerator(config=self.mock_api_config, model_name="models/gemini-test", enable_search=False)

        # Assert GenerativeModel called correctly
        mock_generative_model.assert_called_once()
        call_args, call_kwargs = mock_generative_model.call_args
        self.assertEqual(call_kwargs.get('model_name'), "models/gemini-test")
        # Assert tools list is empty when search is disabled
        self.assertEqual(call_kwargs.get('tools'), [])

        # Assert search tool classes were NOT instantiated
        mock_search_retrieval.assert_not_called()
        mock_tool.assert_not_called()

        # Assert generator attributes
        self.assertEqual(generator.model_name, "models/gemini-test")
        self.assertEqual(generator.model, mock_model_instance)
        self.assertEqual(generator.config, self.mock_api_config)
        self.assertFalse(generator.enable_search)

    # Add a new test for initialization with search enabled
    @patch('content_generation.Tool')
    @patch('content_generation.GoogleSearchRetrieval')
    @patch('content_generation.genai.GenerativeModel')
    def test_init_success_search_enabled(self, mock_generative_model, mock_search_retrieval, mock_tool):
        """Test successful initialization with search enabled."""
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance
        mock_search_tool_instance = MagicMock()
        mock_tool.return_value = mock_search_tool_instance

        # Initialize with enable_search=True
        generator = ContentGenerator(config=self.mock_api_config, model_name="models/gemini-pro", enable_search=True)

        # Assert search tool classes were instantiated
        mock_search_retrieval.assert_called_once()
        mock_tool.assert_called_once_with(google_search_retrieval=mock_search_retrieval.return_value)

        # Assert GenerativeModel called correctly
        mock_generative_model.assert_called_once()
        call_args, call_kwargs = mock_generative_model.call_args
        self.assertEqual(call_kwargs.get('model_name'), "models/gemini-pro")
        # Assert tools list contains the mocked search tool instance
        self.assertEqual(call_kwargs.get('tools'), [mock_search_tool_instance])

        # Assert generator attributes
        self.assertEqual(generator.model_name, "models/gemini-pro")
        self.assertEqual(generator.model, mock_model_instance)
        self.assertEqual(generator.config, self.mock_api_config)
        self.assertTrue(generator.enable_search)


    @patch('content_generation.genai.GenerativeModel')
    def test_init_failure(self, mock_generative_model):
        """Test handling of Gemini initialization failure."""
        mock_generative_model.side_effect = Exception("Model connection failed")

        # Test failure with search disabled
        with self.assertRaises(BookGenerationError) as context_disabled:
            ContentGenerator(config=self.mock_api_config, model_name="invalid-gemini-model", enable_search=False)
        self.assertIn("Failed to initialize Gemini model 'invalid-gemini-model' without search tool", str(context_disabled.exception))
        self.assertIn("Model connection failed", str(context_disabled.exception))

        # Test failure with search enabled
        with self.assertRaises(BookGenerationError) as context_enabled:
            ContentGenerator(config=self.mock_api_config, model_name="invalid-gemini-model", enable_search=True)
        self.assertIn("Failed to initialize Gemini model 'invalid-gemini-model' with search tool", str(context_enabled.exception))
        self.assertIn("Model connection failed", str(context_enabled.exception))

    @patch('content_generation.genai.GenerativeModel')
    def test_generate_content_success(self, mock_generative_model):
        """Test successful content generation (search disabled)."""
        # Mock the model instance and its generate_content method
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Generated content from Gemini."
        mock_candidate = MagicMock()
        mock_part = MagicMock()
        mock_part.text = "Generated content from Gemini."
        mock_candidate.content.parts = [mock_part]
        # Simulate no citation metadata when search is disabled/not used
        mock_candidate.citation_metadata = None
        mock_response.candidates = [mock_candidate]

        mock_model_instance.generate_content.return_value = mock_response
        mock_generative_model.return_value = mock_model_instance

        # Initialize with search disabled
        generator = ContentGenerator(config=self.mock_api_config, model_name="models/gemini-test", enable_search=False)
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

        # Initialize with search disabled
        generator = ContentGenerator(config=self.mock_api_config, model_name="models/gemini-test", enable_search=False)

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

        # Initialize with search disabled
        generator = ContentGenerator(config=self.mock_api_config, model_name="models/gemini-test", enable_search=False)

        with self.assertRaises(BookGenerationError) as context:
            generator.generate_content("test prompt")

        self.assertIn("Failed to generate content with Gemini: Final API error", str(context.exception))
        # Check generator was called multiple times due to retry
        self.assertEqual(mock_model_instance.generate_content.call_count, 3) # Default retry is 3 attempts

    # Removed Hugging Face specific tests like EOS replacement

if __name__ == "__main__":
    # Restore logging level if running tests directly
    logging.disable(logging.NOTSET)
    unittest.main()