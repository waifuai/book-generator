# src/tests/test_content_generation.py
import unittest
from unittest.mock import patch, MagicMock
import logging

# Add src to path if necessary (handled by pytest.ini)
# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).parent.parent))

from content_generation import ContentGenerator
from errors import BookGenerationError

# Suppress transformers logging during tests for cleaner output
logging.getLogger("transformers").setLevel(logging.ERROR)

class TestContentGenerator(unittest.TestCase):

    @patch('content_generation.pipeline')
    @patch('content_generation.set_seed') # Patch set_seed to avoid side effects
    def test_init_success(self, mock_set_seed, mock_pipeline):
        """Test successful initialization of ContentGenerator."""
        mock_generator_instance = MagicMock()
        mock_tokenizer = MagicMock()
        mock_tokenizer.eos_token_id = 50256
        mock_tokenizer.eos_token = '<|eos|>'
        mock_tokenizer.pad_token_id = 50256 # Assume it's set correctly or needs setting
        mock_generator_instance.tokenizer = mock_tokenizer
        mock_generator_instance.model.config.pad_token_id = 50256
        mock_pipeline.return_value = mock_generator_instance

        generator = ContentGenerator(model_name="distilgpt2-test")

        mock_pipeline.assert_called_once_with('text-generation', model="distilgpt2-test", device=-1)
        self.assertEqual(generator.model_name, "distilgpt2-test")
        self.assertEqual(generator.generator, mock_generator_instance)
        self.assertEqual(generator.eos_token_id, 50256)
        # Check if pad_token_id was potentially set if it was None initially
        # This requires a more complex mock setup, for now, we assume pipeline returns a configured one
        self.assertEqual(generator.generator.tokenizer.pad_token_id, 50256)
        # mock_set_seed.assert_called_once_with(42) # Removed: Called at module level, not instance level

    @patch('content_generation.pipeline')
    @patch('content_generation.set_seed')
    def test_init_failure(self, mock_set_seed, mock_pipeline):
        """Test handling of initialization failure."""
        mock_pipeline.side_effect = Exception("Model loading failed")

        with self.assertRaises(BookGenerationError) as context:
            ContentGenerator(model_name="invalid-model")
        self.assertIn("Failed to initialize Hugging Face pipeline", str(context.exception))
        self.assertIn("Model loading failed", str(context.exception))

    @patch('content_generation.pipeline')
    @patch('content_generation.set_seed')
    def test_generate_content_success(self, mock_set_seed, mock_pipeline):
        """Test successful content generation."""
        mock_generator_instance = MagicMock()
        mock_tokenizer = MagicMock()
        mock_tokenizer.eos_token_id = 50256
        mock_tokenizer.pad_token_id = 50256
        mock_generator_instance.tokenizer = mock_tokenizer
        mock_generator_instance.model.config.pad_token_id = 50256
        # Simulate pipeline output
        mock_generator_instance.return_value = [{'generated_text': 'Test prompt Generated content'}]
        mock_pipeline.return_value = mock_generator_instance

        generator = ContentGenerator(model_name="distilgpt2-test")
        result = generator.generate_content("Test prompt", max_length=50, min_length=5)

        self.assertEqual(result, "Generated content") # Expecting prompt removal
        mock_generator_instance.assert_called_once_with(
            "Test prompt",
            max_length=50,
            min_length=5,
            num_return_sequences=1,
            pad_token_id=50256,
            eos_token_id=50256,
            truncation=True
        )

    @patch('content_generation.pipeline')
    @patch('content_generation.set_seed')
    def test_generate_content_success_no_prompt_removal(self, mock_set_seed, mock_pipeline):
        """Test successful content generation when prompt isn't in output."""
        mock_generator_instance = MagicMock()
        mock_tokenizer = MagicMock()
        mock_tokenizer.eos_token_id = 50256
        mock_tokenizer.pad_token_id = 50256
        mock_generator_instance.tokenizer = mock_tokenizer
        mock_generator_instance.model.config.pad_token_id = 50256
        mock_generator_instance.return_value = [{'generated_text': 'Only generated content'}]
        mock_pipeline.return_value = mock_generator_instance

        generator = ContentGenerator(model_name="distilgpt2-test")
        result = generator.generate_content("Test prompt")

        self.assertEqual(result, "Only generated content") # Prompt wasn't there

    @patch('content_generation.pipeline')
    @patch('content_generation.set_seed')
    def test_generate_content_retry(self, mock_set_seed, mock_pipeline):
        """Test retry logic for local model generation."""
        mock_generator_instance = MagicMock()
        mock_tokenizer = MagicMock()
        mock_tokenizer.eos_token_id = 50256
        mock_tokenizer.pad_token_id = 50256
        mock_generator_instance.tokenizer = mock_tokenizer
        mock_generator_instance.model.config.pad_token_id = 50256
        # Simulate failure on first calls, success on the last if retry is working
        mock_generator_instance.side_effect = [
            RuntimeError("GPU OOM"), # Example retryable error
            Exception("Another error"),
            Exception("Final error") # Should fail after retries
        ]
        mock_pipeline.return_value = mock_generator_instance

        generator = ContentGenerator(model_name="distilgpt2-test")

        with self.assertRaises(BookGenerationError) as context:
            generator.generate_content("test prompt")

        self.assertIn("Failed to generate content locally: Final error", str(context.exception))
        # Check generator was called multiple times due to retry
        self.assertEqual(mock_generator_instance.call_count, 3) # Default retry is 3 attempts

    @patch('content_generation.pipeline')
    @patch('content_generation.set_seed')
    def test_generate_content_eos_replacement(self, mock_set_seed, mock_pipeline):
        """Test replacement of <|endoftext|> with <|eos|>."""
        mock_generator_instance = MagicMock()
        mock_tokenizer = MagicMock()
        mock_tokenizer.eos_token_id = 50256
        mock_tokenizer.pad_token_id = 50256
        mock_generator_instance.tokenizer = mock_tokenizer
        mock_generator_instance.model.config.pad_token_id = 50256
        mock_generator_instance.return_value = [{'generated_text': 'Some content<|endoftext|>more content'}]
        mock_pipeline.return_value = mock_generator_instance

        generator = ContentGenerator(model_name="distilgpt2-test")
        result = generator.generate_content("Test prompt")

        self.assertEqual(result, "Some content<|eos|>more content")


if __name__ == "__main__":
    unittest.main()