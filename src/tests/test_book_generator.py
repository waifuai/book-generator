# src/tests/test_book_generator.py
import unittest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import json
import logging

# Add src to path if necessary (handled by pytest.ini)
# import sys
# sys.path.insert(0, str(Path(__file__).parent.parent))

from book_generator import BookGenerator
from book_writer import BookWriter
from table_of_contents import TableOfContents, Chapter
from content_generation import ContentGenerator # Keep this import for mocking
from errors import BookGenerationError

# Suppress logging during tests
logging.disable(logging.CRITICAL)

class TestBookGenerator(unittest.TestCase):

    def setUp(self):
        # Mock dependencies passed to BookGenerator
        # Mock ContentGenerator (now assumed to be Gemini-based)
        self.mock_content_generator = MagicMock(spec=ContentGenerator)
        self.mock_writer = MagicMock(spec=BookWriter)
        # Create the generator instance for tests
        self.generator = BookGenerator(self.mock_content_generator, self.mock_writer)

    def test_generate_toc_success(self):
        """Test successful generation and writing of TOC."""
        title = "My Awesome Book"
        toc_prompt = "Generate TOC for My Awesome Book"
        # Simulate a simple, valid JSON response (expected from Gemini)
        mock_toc_content = '[{"title": "Chapter 1", "subchapters": ["Intro"]}]'
        self.mock_content_generator.generate_content.return_value = mock_toc_content
        expected_filepath = Path("test_output/my_awesome_book.md")
        self.mock_writer.get_filepath.return_value = expected_filepath

        # Patch TableOfContents to control its instance and methods
        with patch('book_generator.TableOfContents') as MockTOC:
            mock_toc_instance = MockTOC.return_value
            toc = self.generator.generate_toc(title, toc_prompt)

            # Assertions
            self.mock_content_generator.generate_content.assert_called_once_with(toc_prompt)
            MockTOC.assert_called_once_with(mock_toc_content) # Check TOC was initialized
            self.assertEqual(toc, mock_toc_instance) # Check returned instance
            self.assertEqual(self.generator.book_title, title)
            self.assertEqual(self.generator.filepath, expected_filepath)
            # Check that the writer was called to write the TOC markdown
            self.mock_writer.write_toc.assert_called_once_with(expected_filepath, title, mock_toc_instance)

    def test_generate_toc_failure_parsing(self):
        """Test TOC generation failure due to invalid JSON."""
        title = "My Failing Book"
        toc_prompt = "Generate failing TOC"
        mock_toc_content = 'invalid json content' # Simulate invalid response
        self.mock_content_generator.generate_content.return_value = mock_toc_content
        expected_filepath = Path("test_output/my_failing_book.md")
        self.mock_writer.get_filepath.return_value = expected_filepath

        # Expect BookGenerationError during TableOfContents initialization
        with self.assertRaises(BookGenerationError):
            self.generator.generate_toc(title, toc_prompt)

        self.mock_content_generator.generate_content.assert_called_once_with(toc_prompt)
        # write_toc should not be called if parsing fails
        self.mock_writer.write_toc.assert_not_called()


    @patch('book_generator.Path.open', new_callable=mock_open) # Patch Path.open in book_generator module
    @patch('book_generator.Path.with_suffix')
    def test_save_toc(self, mock_with_suffix, mock_open_method):
        """Test saving the table of contents to a JSON file."""
        # Setup
        self.generator.toc = MagicMock(spec=TableOfContents)
        self.generator.filepath = Path("test_output/my_book.md")
        mock_json_path = Path("test_output/my_book.json")
        mock_with_suffix.return_value = mock_json_path # Make with_suffix return the mock path
        self.generator.toc.to_json.return_value = '{"title": "Saved Chapter", "subchapters": [], "number": 1}'

        # Action
        self.generator.save_toc()

        # Assertions
        mock_with_suffix.assert_called_once_with(".json")
        mock_open_method.assert_called_once_with("w", encoding="utf-8")
        handle = mock_open_method() # Get the handle from the mock
        handle.write.assert_called_once_with('{"title": "Saved Chapter", "subchapters": [], "number": 1}')
        self.generator.toc.to_json.assert_called_once()

    @patch('book_generator.Path.open', new_callable=mock_open) # Patch Path.open in book_generator module
    @patch('book_generator.Path.is_file')
    @patch('book_generator.Path.with_suffix')
    def test_load_toc_success(self, mock_with_suffix, mock_is_file, mock_open_method):
        """Test loading the table of contents from a JSON file."""
        # Setup
        self.generator.filepath = Path("test_output/my_book.md")
        self.generator.book_title = "My Awesome Book"
        # Use a real TOC instance to test update_from_json
        self.generator.toc = TableOfContents('[{"title":"Initial","subchapters":[]}]')
        # Spy on the update method
        update_spy = MagicMock(side_effect=self.generator.toc.update_from_json)
        self.generator.toc.update_from_json = update_spy

        mock_json_path = Path("test_output/my_book.json")
        mock_with_suffix.return_value = mock_json_path
        mock_is_file.return_value = True # Simulate file exists
        mock_file_handle = mock_open_method.return_value.__enter__.return_value # Get file handle
        loaded_json_content = '[{"title": "Loaded Chapter", "subchapters": ["Loaded Sub"], "number": 1}]'
        mock_file_handle.read.return_value = loaded_json_content

        # Action
        self.generator.load_toc()

        # Assertions
        mock_with_suffix.assert_called_once_with(".json")
        mock_is_file.assert_called_once_with()
        mock_open_method.assert_called_once_with("r", encoding="utf-8")
        # Check update_from_json was called with the loaded content
        update_spy.assert_called_once_with(loaded_json_content)
        # Verify the content was actually updated
        self.assertEqual(len(self.generator.toc.chapters), 1)
        self.assertEqual(self.generator.toc.chapters[0].title, "Loaded Chapter")
        # Check that the main markdown TOC was rewritten by the writer
        self.mock_writer.write_toc.assert_called_once_with(
             self.generator.filepath, self.generator.book_title, self.generator.toc
        )

    @patch('book_generator.Path.is_file')
    @patch('book_generator.Path.with_suffix')
    def test_load_toc_file_not_found(self, mock_with_suffix, mock_is_file):
        """Test loading TOC when the JSON file doesn't exist."""
        self.generator.filepath = Path("test_output/my_book.md")
        mock_json_path = Path("test_output/my_book.json")
        mock_with_suffix.return_value = mock_json_path
        mock_is_file.return_value = False # Simulate file does not exist

        # Action
        self.generator.load_toc() # Should execute without error, just print

        # Assertions
        mock_with_suffix.assert_called_once_with(".json")
        mock_is_file.assert_called_once_with()
        # Ensure update_from_json and write_toc were NOT called
        if hasattr(self.generator.toc, 'update_from_json') and isinstance(self.generator.toc.update_from_json, MagicMock):
             self.generator.toc.update_from_json.assert_not_called()
        self.mock_writer.write_toc.assert_not_called()


    def test_generate_book_success(self):
        """Test successful generation of the entire book."""
        # Setup
        self.generator.toc = MagicMock(spec=TableOfContents)
        self.generator.filepath = Path("test_output/my_book.md")
        self.generator.book_title = "My Awesome Book"
        chapter1 = MagicMock(spec=Chapter)
        chapter2 = MagicMock(spec=Chapter)
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
        """Test the generation of a single chapter and its subchapters."""
        # Setup
        self.generator.book_title = "My Awesome Book"
        self.generator.filepath = Path("test_output/my_book.md")
        chapter = Chapter(title="Chapter 1", subchapters=["Subchapter 1.1", "Subchapter 1.2"], number=1)
        mock_intro_content = "Mock intro content for chapter 1"
        mock_sub1_content = "Mock content for subchapter 1.1"
        mock_sub2_content = "Mock content for subchapter 1.2"
        # Simulate the sequence of content generation calls (now from Gemini mock)
        self.mock_content_generator.generate_content.side_effect = [
            mock_intro_content,
            mock_sub1_content,
            mock_sub2_content,
        ]
        self.generator.toc = MagicMock(spec=TableOfContents)
        self.generator.toc.chapter_toc.return_value = "Mock chapter 1 TOC\n\n"

        # Action
        self.generator._generate_chapter(chapter)

        # Assertions
        # Check content generation calls (prompts remain the same)
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
            self.generator.filepath, chapter, mock_intro_content, "Mock chapter 1 TOC\n\n"
        )
        self.assertEqual(self.mock_writer.write_subchapter.call_count, 2)
        self.mock_writer.write_subchapter.assert_any_call(
            self.generator.filepath, chapter, 1, "Subchapter 1.1", mock_sub1_content
        )
        self.mock_writer.write_subchapter.assert_any_call(
            self.generator.filepath, chapter, 2, "Subchapter 1.2", mock_sub2_content
        )

    # Removed tests for pause_and_modify_toc and browse_book as they moved to main.py


if __name__ == "__main__":
    # Restore logging level if running tests directly
    logging.disable(logging.NOTSET)
    unittest.main()