# src/tests/test_book_writer.py
import unittest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

# Add src to path if necessary (handled by pytest.ini)
# import sys
# sys.path.insert(0, str(Path(__file__).parent.parent))

from ..book_writer import BookWriter
# Need Chapter for type hinting in tests, even if not directly instantiated here
from ..table_of_contents import Chapter, TableOfContents

class TestBookWriter(unittest.TestCase):

    @patch('src.book_writer.Path.mkdir') # Mock mkdir in src.book_writer
    def test_init_and_get_filepath(self, mock_mkdir):
        """Test initialization creates directory and get_filepath works."""
        writer = BookWriter("test_output_dir")
        mock_mkdir.assert_called_once_with(exist_ok=True)
        self.assertEqual(writer.output_dir, Path("test_output_dir"))

        title = "My Test Book! Title?"
        # Expected: lowercase, spaces to underscores, remove non-alnum/-/_
        expected_filepath = Path("test_output_dir/my_test_book_title.md")
        self.assertEqual(writer.get_filepath(title), expected_filepath)

        title_with_trailing = "Another Book   "
        expected_filepath_trailing = Path("test_output_dir/another_book.md")
        self.assertEqual(writer.get_filepath(title_with_trailing), expected_filepath_trailing)


    @patch('src.book_writer.Path.open', new_callable=mock_open) # Patch Path.open in src.book_writer module
    @patch('src.book_writer.Path.mkdir') # Still need to mock mkdir for init
    def test_write_chapter(self, mock_mkdir, mock_open_method): # Renamed mock_file -> mock_open_method
        """Test writing a chapter to the file."""
        writer = BookWriter("test_output")
        filepath = Path("test_output/my_book.md")
        # Use MagicMock for Chapter to avoid needing a full TOC instance here
        mock_chapter = MagicMock(spec=Chapter)
        mock_chapter.number = 1
        mock_chapter.title = "Chapter One Title"
        content = "This is the content of Chapter 1."
        chapter_toc = "### Chapter 1 Contents\n\n1. [Link](#link)\n\n" # Example TOC

        writer.write_chapter(filepath, mock_chapter, content, chapter_toc)

        mock_open_method.assert_called_once_with("a", encoding="utf-8") # Removed filepath
        handle = mock_open_method() # Get handle from mock
        # Check specific calls with expected formatting
        handle.write.assert_any_call("<a id='chapter-1'></a>\n\n")
        handle.write.assert_any_call("## Chapter 1. Chapter One Title\n\n")
        handle.write.assert_any_call("<a id='chapter-1-contents'></a>\n\n")
        handle.write.assert_any_call("[Back to Main Table of Contents](#table-of-contents)\n\n")
        handle.write.assert_any_call(chapter_toc) # Already has newlines
        handle.write.assert_any_call(f"{content}\n\n")


    @patch('src.book_writer.Path.open', new_callable=mock_open) # Patch Path.open in src.book_writer module
    @patch('src.book_writer.Path.mkdir')
    def test_write_subchapter(self, mock_mkdir, mock_open_method): # Renamed mock_file -> mock_open_method
        """Test writing a subchapter to the file."""
        writer = BookWriter("test_output")
        filepath = Path("test_output/my_book.md")
        mock_chapter = MagicMock(spec=Chapter)
        mock_chapter.number = 2
        subchapter_num = 3
        title = "Subchapter Two Point Three"
        content = "This is the content of Subchapter 2.3."

        writer.write_subchapter(filepath, mock_chapter, subchapter_num, title, content)

        mock_open_method.assert_called_once_with("a", encoding="utf-8") # Removed filepath
        handle = mock_open_method() # Get handle from mock
        handle.write.assert_any_call("<a id='chapter-2-3'></a>\n\n")
        handle.write.assert_any_call("### 2.3. Subchapter Two Point Three\n\n")
        handle.write.assert_any_call("[Back to Chapter Contents](#chapter-2-contents)\n")
        handle.write.assert_any_call("[Back to Main Table of Contents](#table-of-contents)\n\n")
        handle.write.assert_any_call(f"{content}\n\n")

    @patch('src.book_writer.Path.open', new_callable=mock_open) # Patch Path.open in src.book_writer module
    @patch('src.book_writer.Path.mkdir')
    def test_write_toc(self, mock_mkdir, mock_open_method): # Renamed mock_file -> mock_open_method
        """Test writing the main table of contents."""
        writer = BookWriter("test_output")
        filepath = Path("test_output/my_book.md")
        title = "My Awesome Book"
        # Mock the TOC object and its method
        mock_toc = MagicMock(spec=TableOfContents)
        mock_toc.to_markdown.return_value = "# Table of Contents\n\n1. [Mock Chapter](#mock)\n\n"

        writer.write_toc(filepath, title, mock_toc)

        # Check file opened in write mode ('w')
        mock_open_method.assert_called_once_with("w", encoding="utf-8") # Removed filepath
        handle = mock_open_method() # Get handle from mock
        handle.write.assert_any_call("# My Awesome Book\n\n")
        handle.write.assert_any_call("<a id='table-of-contents'></a>\n\n")
        # Check it wrote the markdown returned by the mock
        handle.write.assert_any_call(mock_toc.to_markdown.return_value)
        mock_toc.to_markdown.assert_called_once() # Ensure the method was called


if __name__ == "__main__":
    unittest.main()