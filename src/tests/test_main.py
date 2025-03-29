# src/tests/test_main.py
import unittest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import json
import google.generativeai as genai
import os
import requests
import sys

# Add src to path for imports if necessary (pytest.ini should handle this)
# sys.path.insert(0, str(Path(__file__).parent.parent))

# Import components from the src directory
from book_generator import BookGenerator
from book_writer import BookWriter
from table_of_contents import TableOfContents, Chapter
from content_generation import ContentGenerator
from config import APIConfig
from errors import BookGenerationError # Import from the new central location


class TestAPIConfig(unittest.TestCase):

    @patch('config.genai.configure')
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test_gemini_key"}, clear=True)
    def test_api_config_init_success_gemini(self, mock_configure):
        """Test successful API key loading and configuration for Gemini from env."""
        api_config = APIConfig(api_provider="gemini")
        self.assertEqual(api_config.api_key, "test_gemini_key")
        self.assertEqual(api_config.api_provider, "gemini")
        mock_configure.assert_called_once_with(api_key="test_gemini_key")

    @patch('config.genai.configure') # Still need to patch this even if not called
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_openrouter_key"}, clear=True)
    def test_api_config_init_success_openrouter(self, mock_configure):
        """Test successful API key loading for OpenRouter from env."""
        api_config = APIConfig(api_provider="openrouter")
        self.assertEqual(api_config.api_key, "test_openrouter_key")
        self.assertEqual(api_config.api_provider, "openrouter")
        # No specific configure call for openrouter in this setup
        mock_configure.assert_not_called()
        # Check if the key is still in environ (dotenv should load it)
        self.assertEqual(os.getenv("OPENROUTER_API_KEY"), "test_openrouter_key")

    @patch.dict(os.environ, {}, clear=True) # Ensure env var is not set
    def test_api_config_gemini_key_not_found(self):
        """Test handling of missing Gemini API key environment variable."""
        with self.assertRaises(BookGenerationError) as context:
            APIConfig(api_provider="gemini")
        self.assertIn("GEMINI_API_KEY environment variable not found", str(context.exception))

    @patch.dict(os.environ, {}, clear=True) # Ensure env var is not set
    def test_api_config_openrouter_key_not_found(self):
        """Test handling of missing OpenRouter API key environment variable."""
        with self.assertRaises(BookGenerationError) as context:
            APIConfig(api_provider="openrouter")
        self.assertIn("OPENROUTER_API_KEY environment variable not found", str(context.exception))

    @patch.dict(os.environ, {"GEMINI_API_KEY": "key"}, clear=True) # Need some key present
    def test_api_config_invalid_provider(self):
        """Test handling of invalid API provider."""
        with self.assertRaises(BookGenerationError) as context:
            APIConfig(api_provider="invalid")
        self.assertIn("Invalid API provider", str(context.exception))


class TestContentGenerator(unittest.TestCase):

    def setUp(self):
        # Create mock APIConfig instances for tests
        self.mock_api_config_gemini = MagicMock(spec=APIConfig)
        self.mock_api_config_gemini.api_provider = "gemini"
        self.mock_api_config_gemini.api_key = "fake_gemini_key"

        self.mock_api_config_openrouter = MagicMock(spec=APIConfig)
        self.mock_api_config_openrouter.api_provider = "openrouter"
        self.mock_api_config_openrouter.api_key = "fake_openrouter_key"


    @patch('content_generation.genai.GenerativeModel')
    def test_generate_content_success_gemini(self, MockGenerativeModel):
        """Test successful content generation with Gemini."""
        mock_model_instance = MockGenerativeModel.return_value
        mock_response = MagicMock()
        mock_response.text = "Generated content"
        mock_model_instance.generate_content.return_value = mock_response

        # Pass mock config and model name
        generator = ContentGenerator(api_config=self.mock_api_config_gemini, model_name="gemini-test-model")
        result = generator.generate_content("Test prompt")

        self.assertEqual(result, "Generated content")
        MockGenerativeModel.assert_called_once_with("gemini-test-model")
        mock_model_instance.generate_content.assert_called_once_with("Test prompt")

    @patch('content_generation.requests.post')
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_openrouter_api_key"}, clear=True) # Still need env var for the call itself
    def test_generate_content_success_openrouter(self, mock_post):
        """Test successful content generation with OpenRouter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "Generated content"}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Pass mock config and model name
        generator = ContentGenerator(api_config=self.mock_api_config_openrouter, model_name="openrouter-test-model")
        result = generator.generate_content("Test prompt")

        self.assertEqual(result, "Generated content")
        mock_post.assert_called_once()
        # Check payload in call args
        call_args, call_kwargs = mock_post.call_args
        self.assertIn("json", call_kwargs)
        self.assertEqual(call_kwargs["json"]["model"], "openrouter-test-model")
        self.assertEqual(call_kwargs["json"]["messages"], [{"role": "user", "content": "Test prompt"}])
        self.assertIn("Authorization", call_kwargs["headers"])
        self.assertEqual(call_kwargs["headers"]["Authorization"], "Bearer test_openrouter_api_key")


    @patch('content_generation.genai.GenerativeModel')
    def test_generate_content_retry_gemini(self, MockGenerativeModel):
        """Test retry logic for Gemini."""
        mock_model_instance = MockGenerativeModel.return_value
        # Simulate failure on first calls, success on the last if retry is working
        mock_model_instance.generate_content.side_effect = [
            genai.types.generation_types.BlockedPromptException("Blocked"), # Example retryable error
            Exception("API error"),
            Exception("API error final") # Should fail after retries
        ]

        generator = ContentGenerator(api_config=self.mock_api_config_gemini, model_name="gemini-test-model")

        with self.assertRaises(BookGenerationError) as context:
            generator.generate_content("test prompt")

        self.assertIn("Failed to generate content: API error final", str(context.exception))
        # Check generate_content was called multiple times due to retry
        self.assertEqual(mock_model_instance.generate_content.call_count, 3) # Default retry is 3 attempts

    @patch('content_generation.requests.post')
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_openrouter_api_key"}, clear=True)
    def test_generate_content_retry_openrouter(self, mock_post):
        """Test retry logic for OpenRouter."""
        mock_post.side_effect = [
            requests.exceptions.Timeout("Timeout"), # Example retryable error
            requests.exceptions.RequestException("API error"),
            requests.exceptions.RequestException("API error final") # Should fail after retries
        ]

        generator = ContentGenerator(api_config=self.mock_api_config_openrouter, model_name="openrouter-test-model")

        with self.assertRaises(BookGenerationError) as context:
            generator.generate_content("test prompt")

        self.assertIn("Failed to generate content: API error final", str(context.exception))
        self.assertEqual(mock_post.call_count, 3) # Default retry is 3 attempts


class TestTableOfContents(unittest.TestCase):

    def test_parse_toc(self):
        toc_json = """
        [
            {
                "title": "Chapter 1",
                "subchapters": ["Subchapter 1.1", "Subchapter 1.2"]
            },
            {
                "title": "Chapter 2",
                "subchapters": ["Subchapter 2.1"]
            }
        ]
        """
        toc = TableOfContents(toc_json)
        self.assertEqual(len(toc.chapters), 2)
        self.assertEqual(toc.chapters[0].title, "Chapter 1")
        self.assertEqual(toc.chapters[0].subchapters, ["Subchapter 1.1", "Subchapter 1.2"])
        self.assertEqual(toc.chapters[1].title, "Chapter 2")
        self.assertEqual(toc.chapters[1].subchapters, ["Subchapter 2.1"])

    def test_parse_toc_invalid_json(self):
        with self.assertRaises(BookGenerationError):
            TableOfContents("invalid json")

    def test_clean_response(self):
        test_cases = [
            ("```python\nhello\n```", "hello"),
            ("```json\n{\"key\": \"value\"}\n```", "{\"key\": \"value\"}"),
            ("```\nworld\n```", "world"),
            ("no wrappers here", "no wrappers here"),
            ("  ```json\n  indented\n  ```  ", "indented"), # Test stripping
        ]
        for input_str, expected_output in test_cases:
            self.assertEqual(TableOfContents._clean_response(input_str), expected_output)

    def test_assign_numbers(self):
        toc = TableOfContents("[]")  # Initialize with an empty list
        toc.chapters = [
            Chapter("Chapter One", []),
            Chapter("Chapter Two", ["Subchapter 2.1"]),
        ]
        toc._assign_numbers()
        self.assertEqual(toc.chapters[0].number, 1)
        self.assertEqual(toc.chapters[1].number, 2)

    def test_to_markdown(self):
        toc_json = """
        [
            {
                "title": "Chapter 1",
                "subchapters": ["Subchapter 1.1", "Subchapter 1.2"]
            },
            {
                "title": "Chapter 2",
                "subchapters": ["Subchapter 2.1"]
            }
        ]
        """
        toc = TableOfContents(toc_json)
        expected_markdown = """# Table of Contents

1. [Chapter 1](#chapter-1)
    * [1.1. Subchapter 1.1](#chapter-1-1)
    * [1.2. Subchapter 1.2](#chapter-1-2)
2. [Chapter 2](#chapter-2)
    * [2.1. Subchapter 2.1](#chapter-2-1)

""" # Note: Added newline consistency
        self.assertEqual(toc.to_markdown(), expected_markdown)

    def test_chapter_toc(self):
        chapter = Chapter("Chapter 1", ["Subchapter 1.1", "Subchapter 1.2"], 1)
        expected_markdown = """### Chapter 1 Contents

1. [Chapter 1](#chapter-1)
    * [1.1. Subchapter 1.1](#chapter-1-1)
    * [1.2. Subchapter 1.2](#chapter-1-2)

""" # Note: Added newline consistency
        # Need a valid TOC instance to call the method
        toc_instance = TableOfContents('[{"title": "Temp", "subchapters": []}]')
        self.assertEqual(toc_instance.chapter_toc(chapter), expected_markdown)

    def test_to_json(self):
        # Test with numbers assigned
        toc = TableOfContents('[{"title": "Ch1", "subchapters": ["S1"]}]')
        expected_data = [{"title": "Ch1", "subchapters": ["S1"], "number": 1}]
        # Compare parsed JSON objects for robustness against formatting differences
        self.assertEqual(json.loads(toc.to_json()), expected_data)


    def test_update_from_json(self):
        toc = TableOfContents("[]")
        updated_toc_json = """
        [
            {
                "title": "Chapter 1",
                "subchapters": ["Subchapter 1.1"],
                "number": 1
            },
            {
                "title": "Chapter 3",
                "subchapters": [],
                "number": 3
            }
        ]
        """
        toc.update_from_json(updated_toc_json)
        self.assertEqual(len(toc.chapters), 2)
        self.assertEqual(toc.chapters[0].title, "Chapter 1")
        self.assertEqual(toc.chapters[0].subchapters, ["Subchapter 1.1"])
        self.assertEqual(toc.chapters[0].number, 1)
        self.assertEqual(toc.chapters[1].title, "Chapter 3")
        self.assertEqual(toc.chapters[1].subchapters, [])
        self.assertEqual(toc.chapters[1].number, 3)

    def test_update_from_json_invalid_json(self):
        toc = TableOfContents("[]")
        with self.assertRaises(BookGenerationError):
            toc.update_from_json("invalid json")

class TestBookWriter(unittest.TestCase):

    @patch('book_writer.Path.mkdir') # Mock mkdir
    def test_get_filepath(self, mock_mkdir):
        writer = BookWriter("test_output")
        title = "My Awesome Book"
        expected_filepath = Path("test_output/my_awesome_book.md")
        self.assertEqual(writer.get_filepath(title), expected_filepath)
        mock_mkdir.assert_called_once_with(exist_ok=True) # Check mkdir was called

    @patch('builtins.open', new_callable=mock_open)
    @patch('book_writer.Path.mkdir')
    def test_write_chapter(self, mock_mkdir, mock_file):
        writer = BookWriter("test_output")
        filepath = Path("test_output/my_book.md")
        chapter = Chapter("Chapter 1", ["Subchapter 1.1"], 1)
        content = "This is the content of Chapter 1."
        chapter_toc = "Chapter 1 TOC\n\n" # Ensure newline consistency

        writer.write_chapter(filepath, chapter, content, chapter_toc)

        mock_file.assert_called_once_with(filepath, "a", encoding="utf-8")
        handle = mock_file()
        handle.write.assert_any_call("<a id='chapter-1'></a>\n\n")
        handle.write.assert_any_call("## Chapter 1. Chapter 1\n\n")
        handle.write.assert_any_call("<a id='chapter-1-contents'></a>\n\n")
        handle.write.assert_any_call("[Back to Main Table of Contents](#table-of-contents)\n\n")
        handle.write.assert_any_call(chapter_toc) # Already has newlines
        handle.write.assert_any_call(f"{content}\n\n")


    @patch('builtins.open', new_callable=mock_open)
    @patch('book_writer.Path.mkdir')
    def test_write_subchapter(self, mock_mkdir, mock_file):
        writer = BookWriter("test_output")
        filepath = Path("test_output/my_book.md")
        chapter = Chapter("Chapter 1", ["Subchapter 1.1"], 1)
        subchapter_num = 1
        title = "Subchapter 1.1"
        content = "This is the content of Subchapter 1.1."

        writer.write_subchapter(filepath, chapter, subchapter_num, title, content)

        mock_file.assert_called_once_with(filepath, "a", encoding="utf-8")
        handle = mock_file()
        handle.write.assert_any_call("<a id='chapter-1-1'></a>\n\n")
        handle.write.assert_any_call("### 1.1. Subchapter 1.1\n\n")
        handle.write.assert_any_call("[Back to Chapter Contents](#chapter-1-contents)\n")
        handle.write.assert_any_call("[Back to Main Table of Contents](#table-of-contents)\n\n")
        handle.write.assert_any_call(f"{content}\n\n")

    @patch('builtins.open', new_callable=mock_open)
    @patch('book_writer.Path.mkdir')
    def test_write_toc(self, mock_mkdir, mock_file):
        writer = BookWriter("test_output")
        filepath = Path("test_output/my_book.md")
        title = "My Awesome Book"
        # Create a real TOC instance to test its method call
        toc_instance = TableOfContents('[{"title": "Ch1", "subchapters": ["S1"]}]')
        # Spy on the real method if needed, or just let it run
        # toc_instance.to_markdown = MagicMock(return_value="Mock TOC Markdown")

        writer.write_toc(filepath, title, toc_instance)

        mock_file.assert_called_once_with(filepath, "w", encoding="utf-8")
        handle = mock_file()
        handle.write.assert_any_call("# My Awesome Book\n\n")
        handle.write.assert_any_call("<a id='table-of-contents'></a>\n\n")
        # Check it wrote the actual markdown from the instance
        handle.write.assert_any_call(toc_instance.to_markdown())


class TestBookGenerator(unittest.TestCase):

    def setUp(self):
        # Mock dependencies passed to BookGenerator
        self.mock_content_generator = MagicMock(spec=ContentGenerator)
        self.mock_writer = MagicMock(spec=BookWriter)
        # Create the generator instance for tests
        self.generator = BookGenerator(self.mock_content_generator, self.mock_writer)

    def test_generate_toc(self):
        title = "My Awesome Book"
        toc_prompt = "Generate TOC for My Awesome Book"
        mock_toc_content = '[{"title": "Chapter 1", "subchapters": []}]'  # Valid JSON
        self.mock_content_generator.generate_content.return_value = mock_toc_content
        expected_filepath = Path("test_output/my_awesome_book.md")
        self.mock_writer.get_filepath.return_value = expected_filepath

        # Mock the TableOfContents class itself if needed, or let it run
        with patch('book_generator.TableOfContents') as MockTOC:
            mock_toc_instance = MockTOC.return_value
            toc = self.generator.generate_toc(title, toc_prompt)

            self.mock_content_generator.generate_content.assert_called_once_with(toc_prompt)
            MockTOC.assert_called_once_with(mock_toc_content) # Check TOC was initialized
            self.assertEqual(toc, mock_toc_instance) # Check returned instance
            self.assertEqual(self.generator.book_title, title)
            self.assertEqual(self.generator.filepath, expected_filepath)
            self.mock_writer.write_toc.assert_called_once_with(expected_filepath, title, mock_toc_instance)


    @patch('builtins.open', new_callable=mock_open)
    @patch('book_generator.Path.with_suffix') # Mock path manipulation
    def test_save_toc(self, mock_with_suffix, mock_file):
        # Setup
        self.generator.toc = MagicMock(spec=TableOfContents)
        self.generator.filepath = Path("test_output/my_book.md")
        mock_json_path = Path("test_output/my_book.json")
        mock_with_suffix.return_value = mock_json_path # Make with_suffix return the mock path
        self.generator.toc.to_json.return_value = '{"key": "value"}'

        # Action
        self.generator.save_toc()

        # Assertions
        mock_with_suffix.assert_called_once_with(".json")
        mock_file.assert_called_once_with(mock_json_path, "w", encoding="utf-8")
        handle = mock_file()
        handle.write.assert_called_once_with('{"key": "value"}')

    @patch('builtins.open', new_callable=mock_open)
    @patch('book_generator.Path.is_file')
    @patch('book_generator.Path.with_suffix')
    def test_load_toc(self, mock_with_suffix, mock_is_file, mock_file):
        # Setup
        self.generator.filepath = Path("test_output/my_book.md")
        self.generator.book_title = "My Awesome Book"
        # Need a real TOC instance to call update_from_json on
        self.generator.toc = TableOfContents('[{"title":"Initial","subchapters":[]}]')
        # Spy on the update method
        self.generator.toc.update_from_json = MagicMock()

        mock_json_path = Path("test_output/my_book.json")
        mock_with_suffix.return_value = mock_json_path
        mock_is_file.return_value = True # Simulate file exists
        mock_file_handle = mock_file.return_value.__enter__.return_value # Get file handle
        mock_file_handle.read.return_value = '{"title": "Loaded"}' # Content read from file

        # Action
        self.generator.load_toc()

        # Assertions
        mock_with_suffix.assert_called_once_with(".json")
        mock_is_file.assert_called_once_with()
        mock_file.assert_called_once_with(mock_json_path, "r", encoding="utf-8")
        self.generator.toc.update_from_json.assert_called_once_with('{"title": "Loaded"}')
        # Check that the main markdown TOC was rewritten
        self.mock_writer.write_toc.assert_called_once_with(
             self.generator.filepath, self.generator.book_title, self.generator.toc
        )

    # Removed test_pause_and_modify_toc

    def test_generate_book_success(self):
        # Setup
        self.generator.toc = MagicMock(spec=TableOfContents)
        self.generator.filepath = Path("test_output/my_book.md")
        self.generator.book_title = "My Awesome Book"
        chapter1 = Chapter("Chapter 1", ["Subchapter 1.1"], 1)
        chapter2 = Chapter("Chapter 2", ["Subchapter 2.1"], 2)
        self.generator.toc.chapters = [chapter1, chapter2]

        # Mock the internal method _generate_chapter
        self.generator._generate_chapter = MagicMock()

        # Action
        result = self.generator.generate_book()

        # Assertions
        self.assertEqual(result, self.generator.filepath)
        self.assertEqual(self.generator._generate_chapter.call_count, 2)
        self.generator._generate_chapter.assert_any_call(chapter1)
        self.generator._generate_chapter.assert_any_call(chapter2)

    def test_generate_book_no_toc(self):
        """Test generating a book without a TOC."""
        self.generator.toc = None # Ensure TOC is None
        self.generator.filepath = Path("test_output/my_book.md")
        self.generator.book_title = "My Awesome Book"

        with self.assertRaises(BookGenerationError) as context:
            self.generator.generate_book()
        self.assertIn("Table of Contents not generated", str(context.exception))


    def test_generate_chapter(self):
        # Setup
        self.generator.book_title = "My Awesome Book"
        self.generator.filepath = Path("test_output/my_book.md")
        chapter = Chapter("Chapter 1", ["Subchapter 1.1", "Subchapter 1.2"], 1)
        mock_intro_content = "Mock intro content"
        mock_subchapter_content = "Mock subchapter content"
        # Simulate the sequence of content generation calls
        self.mock_content_generator.generate_content.side_effect = [
            mock_intro_content,
            mock_subchapter_content, # For 1.1
            mock_subchapter_content, # For 1.2
        ]
        # Mock the TOC object held by the generator
        self.generator.toc = MagicMock(spec=TableOfContents)
        self.generator.toc.chapter_toc.return_value = "Mock chapter TOC\n\n" # Ensure newlines

        # Action
        self.generator._generate_chapter(chapter)

        # Assertions
        # Check content generation calls
        self.assertEqual(self.mock_content_generator.generate_content.call_count, 3)
        self.mock_content_generator.generate_content.assert_any_call(
            f"Write a concise introduction for Chapter {chapter.number}: '{chapter.title}' in a book titled '{self.generator.book_title}'."
        )
        self.mock_content_generator.generate_content.assert_any_call(
            f"Write a detailed section for Chapter {chapter.number}.1: 'Subchapter 1.1' within Chapter {chapter.number}: '{chapter.title}' in a book titled '{self.generator.book_title}'."
        )
        self.mock_content_generator.generate_content.assert_any_call(
            f"Write a detailed section for Chapter {chapter.number}.2: 'Subchapter 1.2' within Chapter {chapter.number}: '{chapter.title}' in a book titled '{self.generator.book_title}'."
        )
        # Check TOC generation for the chapter
        self.generator.toc.chapter_toc.assert_called_once_with(chapter)
        # Check writing calls
        self.mock_writer.write_chapter.assert_called_once_with(
            self.generator.filepath, chapter, mock_intro_content, "Mock chapter TOC\n\n"
        )
        self.assertEqual(self.mock_writer.write_subchapter.call_count, 2)
        self.mock_writer.write_subchapter.assert_any_call(
            self.generator.filepath, chapter, 1, "Subchapter 1.1", mock_subchapter_content
        )
        self.mock_writer.write_subchapter.assert_any_call(
            self.generator.filepath, chapter, 2, "Subchapter 1.2", mock_subchapter_content
        )

    # Removed test_browse_book_success
    # Removed test_browse_book_file_not_found


if __name__ == "__main__":
    # This allows running the tests directly if needed,
    # but usually you'd use 'python -m unittest src/tests/test_main.py'
    unittest.main()