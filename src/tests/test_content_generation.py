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

    @patch('content_generation.genai.GenerativeModel')
    def test_init_success(self, mock_generative_model):
        """Test successful initialization of ContentGenerator with Gemini."""
        mock_model_instance = MagicMock()
        mock_generative_model.return_value = mock_model_instance

        generator = ContentGenerator(config=self.mock_api_config, model_name="models/gemini-test")

        mock_generative_model.assert_called_once_with(model_name="models/gemini-test")
        self.assertEqual(generator.model_name, "models/gemini-test")
        self.assertEqual(generator.model, mock_model_instance)
        self.assertEqual(generator.config, self.mock_api_config)

    @patch('content_generation.genai.GenerativeModel')
    def test_init_failure(self, mock_generative_model):
        """Test handling of Gemini initialization failure."""
        mock_generative_model.side_effect = Exception("Model connection failed")

        with self.assertRaises(BookGenerationError) as context:
            ContentGenerator(config=self.mock_api_config, model_name="invalid-gemini-model")
        self.assertIn("Failed to initialize Gemini model", str(context.exception))
        self.assertIn("Model connection failed", str(context.exception))

    @patch('content_generation.genai.GenerativeModel')
    def test_generate_content_success(self, mock_generative_model):
        """Test successful content generation with Gemini."""
        # Mock the model instance and its generate_content method
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        # Simulate the response structure: candidates -> content -> parts -> text
        # Using .text attribute directly is simpler if the mock supports it well
        mock_response.text = "Generated content from Gemini."
        # Ensure candidates and parts exist for the check in generate_content
        mock_candidate = MagicMock()
        mock_part = MagicMock()
        mock_part.text = "Generated content from Gemini."
        mock_candidate.content.parts = [mock_part]
        mock_response.candidates = [mock_candidate]

        mock_model_instance.generate_content.return_value = mock_response
        mock_generative_model.return_value = mock_model_instance

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
        mock_response.text = "" # .text would likely be empty too
        # Add mock prompt_feedback
        mock_feedback = MagicMock()
        mock_feedback.block_reason = "SAFETY"
        mock_feedback.block_reason_message = "Blocked due to safety concerns."
        mock_response.prompt_feedback = mock_feedback

        # Simulate the exception being raised within the generate_content method
        # This needs to happen *after* the check for candidates/parts
        def side_effect_func(*args, **kwargs):
            # First check if the response indicates blocking
            if not mock_response.candidates: # Simplified check
                 if hasattr(mock_response, 'prompt_feedback') and hasattr(mock_response.prompt_feedback, 'block_reason'):
                     raise BookGenerationError(f"Content generation blocked. Reason: {mock_response.prompt_feedback.block_reason}. Details: {getattr(mock_response.prompt_feedback, 'block_reason_message', 'N/A')}")
                 raise BookGenerationError("Received an empty response from the Gemini API.")
            # Check parts if candidates exist
            if not mock_response.candidates[0].content.parts:
                 raise BookGenerationError("Received an empty response (no parts) from the Gemini API.")

            return mock_response # Should not be reached in this test case path

        mock_model_instance.generate_content.side_effect = side_effect_func
        mock_generative_model.return_value = mock_model_instance

        generator = ContentGenerator(config=self.mock_api_config, model_name="models/gemini-test")

        with self.assertRaises(BookGenerationError) as context:
            generator.generate_content("Risky prompt")

        # Check for specific block reason message in the final exception
        self.assertIn("Content generation blocked. Reason: SAFETY", str(context.exception))
        # Check that the mocked method was called 3 times due to retry
        self.assertEqual(mock_model_instance.generate_content.call_count, 3)
        # Optionally, check the arguments of the last call (or any call)
        mock_model_instance.generate_content.assert_called_with("Risky prompt")


    @patch('content_generation.genai.GenerativeModel')
    def test_generate_content_retry(self, mock_generative_model):
        """Test retry logic for Gemini API calls."""
        mock_model_instance = MagicMock()
        # Simulate failure on first calls, success on the last if retry is working
        mock_model_instance.generate_content.side_effect = [
            api_core_exceptions.ServiceUnavailable("API unavailable"), # Use google-api-core exception
            api_core_exceptions.DeadlineExceeded("Timeout"), # Another potentially retryable error
            Exception("Final API error") # Should fail after retries
        ]
        mock_generative_model.return_value = mock_model_instance

        generator = ContentGenerator(config=self.mock_api_config, model_name="models/gemini-test")

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