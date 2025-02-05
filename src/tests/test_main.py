import unittest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import json
import google.generativeai as genai

from book_generator import BookGenerator, BookGenerationError
from book_writer import BookWriter
from table_of_contents import TableOfContents, Chapter
from content_generation import ContentGenerator
from config import APIConfig, BookGenerationError


class TestAPIConfig(unittest.TestCase):

    @patch('config.genai.configure')
    def test_api_config_init_success(self, mock_configure):
        """Test successful API key loading and configuration."""
        mock_api_key = "test_api_key"
        with patch("builtins.open", mock_open(read_data=mock_api_key)):
            api_config = APIConfig("dummy_path.txt")
            self.assertEqual(api_config.api_key, mock_api_key)
            mock_configure.assert_called_once_with(api_key=mock_api_key)

    def test_api_config_file_not_found(self):
        """Test handling of missing API key file."""
        with self.assertRaises(BookGenerationError) as context:
            APIConfig("nonexistent_file.txt")
        self.assertIn("nonexistent_file.txt not found", str(context.exception))


class TestContentGenerator(unittest.TestCase):

    @patch('content_generation.genai.GenerativeModel')
    def test_generate_content_success(self, MockGenerativeModel):
        """Test successful content generation."""
        mock_model = MockGenerativeModel.return_value
        mock_response = MagicMock()
        mock_response.text = "Generated content"
        mock_model.generate_content.return_value = mock_response

        generator = ContentGenerator(model_name="test_model")
        result = generator.generate_content("Test prompt")

        self.assertEqual(result, "Generated content")
        mock_model.generate_content.assert_called_once_with("Test prompt")

    @patch('content_generation.genai.GenerativeModel')
    @patch('content_generation.retry')
    def test_generate_content_retry(self, mock_retry, MockGenerativeModel):
        """Test that the retry decorator is applied."""
        mock_model = MockGenerativeModel.return_value

        # Configure the mock retry decorator to just call the original function
        def call_through(*args, **kwargs):
            fn = kwargs['f']
            return fn(*args, **kwargs)

        mock_retry.side_effect = call_through

        generator = ContentGenerator()
        # Make the generate_content call fail
        mock_model.generate_content.side_effect = Exception("API error")

        with self.assertRaises(BookGenerationError) as context:
            generator.generate_content("test prompt")
        self.assertIn("Failed to generate content", str(context.exception))
        # Check that retry and generate_content were called
        mock_retry.assert_called()
        mock_model.generate_content.assert_called()



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
        self.assertEqual(toc.chapters[0].subchapters, ["Subchapter 1.1", "Subchapter 1.2")
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
                "subchapters": ["Subchapter 2.1"
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

"""
        self.assertEqual(toc.to_markdown(), expected_markdown)

    def test_chapter_toc(self):
        chapter = Chapter("Chapter 1", ["Subchapter 1.1", "Subchapter 1.2"], 1)
        expected_markdown = """### Chapter 1 Contents

1. [Chapter 1](#chapter-1)
    * [1.1. Subchapter 1.1](#chapter-1-1)
    * [1.2. Subchapter 1.2](#chapter-1-2)

"""
        toc = TableOfContents("[")  # to make chapter_toc accessible
        self.assertEqual(toc.chapter_toc(chapter), expected_markdown)

    def test_to_json(self):
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
        expected_json = json.dumps(json.loads(toc_json), indent=4)
        self.assertEqual(toc.to_json(), expected_json)

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

    def test_get_filepath(self):
        writer = BookWriter("test_output")
        title = "My Awesome Book"
        expected_filepath = Path("test_output/my_awesome_book.md")
        self.assertEqual(writer.get_filepath(title), expected_filepath)

    @patch('builtins.open', new_callable=mock_open)
    def test_write_chapter(self, mock_file):
        writer = BookWriter("test_output")
        filepath = Path("test_output/my_book.md")
        chapter = Chapter("Chapter 1", ["Subchapter 1.1"], 1)
        content = "This is the content of Chapter 1."
        chapter_toc = "Chapter 1 TOC"

        writer.write_chapter(filepath, chapter, content, chapter_toc)

        mock_file.assert_called_once_with(filepath, "a", encoding="utf-8")
        handle = mock_file()
        handle.write.assert_any_call("<a id='chapter-1'></a>\n\n")
        handle.write.assert_any_call("## Chapter 1. Chapter 1\n\n")
        handle.write.assert_any_call("<a id='chapter-1-contents'></a>\n\n")
        handle.write.assert_any_call("[Back to Main Table of Contents](#table-of-contents)\n\n")
        handle.write.assert_any_call(chapter_toc)
        handle.write.assert_any_call(f"{content}\n\n")


    @patch('builtins.open', new_callable=mock_open)
    def test_write_subchapter(self, mock_file):
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
    def test_write_toc(self, mock_file):
        writer = BookWriter("test_output")
        filepath = Path("test_output/my_book.md")
        title = "My Awesome Book"
        toc = TableOfContents("[]")  # Initialize with empty data
        toc.to_markdown = MagicMock(return_value="Mock TOC Markdown") # Mock to_markdown

        writer.write_toc(filepath, title, toc)

        mock_file.assert_called_once_with(filepath, "w", encoding="utf-8")
        handle = mock_file()
        handle.write.assert_any_call("# My Awesome Book\n\n")
        handle.write.assert_any_call("<a id='table-of-contents'></a>\n\n")
        handle.write.assert_any_call("Mock TOC Markdown")



class TestBookGenerator(unittest.TestCase):

    def setUp(self):
        self.mock_content_generator = MagicMock(spec=ContentGenerator)
        self.mock_writer = MagicMock(spec=BookWriter)
        self.generator = BookGenerator(self.mock_content_generator, self.mock_writer)

    def test_generate_toc(self):
        title = "My Awesome Book"
        toc_prompt = "Generate TOC for My Awesome Book"
        mock_toc_content = "[{\"title\": \"Chapter 1\", \"subchapters\": []}]"  # Valid JSON
        self.mock_content_generator.generate_content.return_value = mock_toc_content
        expected_filepath = Path("test_output/my_awesome_book.md")
        self.mock_writer.get_filepath.return_value = expected_filepath

        toc = self.generator.generate_toc(title, toc_prompt)

        self.mock_content_generator.generate_content.assert_called_once_with(toc_prompt)
        self.assertIsInstance(toc, TableOfContents)
        self.assertEqual(self.generator.book_title, title)
        self.assertEqual(self.generator.filepath, expected_filepath)
        self.mock_writer.write_toc.assert_called_once_with(expected_filepath, title, toc)


    @patch('builtins.open', new_callable=mock_open)
    def test_save_toc(self, mock_file):
        self.generator.toc = MagicMock(spec=TableOfContents)
        self.generator.filepath = Path("test_output/my_book.md")
        self.generator.toc.to_json.return_value = "{}"

        self.generator.save_toc()

        mock_file.assert_called_once_with(Path("test_output/my_book.json"), "w", encoding="utf-8")
        handle = mock_file()
        handle.write.assert_called_once_with("{}")

    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.is_file')
    def test_load_toc(self, mock_is_file, mock_file):

        self.generator.filepath = Path("test_output/my_book.md")
        self.generator.book_title = "My Awesome Book"
        self.generator.toc = MagicMock(spec=TableOfContents) # Initialize toc
        mock_is_file.return_value = True
        mock_file().read.return_value = "{}"

        self.generator.load_toc()

        mock_is_file.assert_called_once_with()
        mock_file.assert_called_once_with(Path("test_output/my_book.json"), "r", encoding="utf-8")
        self.generator.toc.update_from_json.assert_called_once_with("{}")
        self.mock_writer.write_toc.assert_called_once_with(self.generator.filepath, self.generator.book_title, self.generator.toc)


    @patch('builtins.input')
    def test_pause_and_modify_toc(self, mock_input):
        self.generator.save_toc = MagicMock()
        self.generator.load_toc = MagicMock()

        self.generator.pause_and_modify_toc()

        self.generator.save_toc.assert_called_once()
        mock_input.assert_called_once_with("Press Enter to continue after modifying the TOC JSON file...")
        self.generator.load_toc.assert_called_once()

    def test_generate_book_success(self):
        self.generator.toc = MagicMock(spec=TableOfContents)
        self.generator.filepath = Path("test_output/my_book.md")
        self.generator.book_title = "My Awesome Book"
        self.generator.toc.chapters = [
            Chapter("Chapter 1", ["Subchapter 1.1"], 1),
            Chapter("Chapter 2", ["Subchapter 2.1"], 2),
        
        self.generator._generate_chapter = MagicMock()

        result = self.generator.generate_book()

        self.assertEqual(result, self.generator.filepath)
        self.assertEqual(self.generator._generate_chapter.call_count, 2)
        self.generator._generate_chapter.assert_any_call(self.generator.toc.chapters[0])
        self.generator._generate_chapter.assert_any_call(self.generator.toc.chapters[1)

    def test_generate_book_no_toc(self):
        """Test generating a book without a TOC."""
        self.generator.toc = None
        self.generator.filepath = Path("test_output/my_book.md")
        self.generator.book_title = "My Awesome Book"

        with self.assertRaises(BookGenerationError) as context:
            self.generator.generate_book()
        self.assertIn("Table of Contents not generated", str(context.exception))


    def test_generate_chapter(self):
        self.generator.book_title = "My Awesome Book"
        self.generator.filepath = Path("test_output/my_book.md")
        chapter = Chapter("Chapter 1", ["Subchapter 1.1", "Subchapter 1.2"], 1)
        mock_intro_content = "Mock intro content"
        mock_subchapter_content = "Mock subchapter content"
        self.mock_content_generator.generate_content.side_effect = [
            mock_intro_content,
            mock_subchapter_content,
            mock_subchapter_content,
        ]
        self.generator.toc = MagicMock(spec=TableOfContents)
        self.generator.toc.chapter_toc.return_value = "Mock chapter TOC"

        self.generator._generate_chapter(chapter)

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
        self.generator.toc.chapter_toc.assert_called_once_with(chapter)
        self.mock_writer.write_chapter.assert_called_once_with(
            self.generator.filepath, chapter, mock_intro_content, "Mock chapter TOC"
        )
        self.assertEqual(self.mock_writer.write_subchapter.call_count, 2)
        self.mock_writer.write_subchapter.assert_any_call(
            self.generator.filepath, chapter, 1, "Subchapter 1.1", mock_subchapter_content
        )
        self.mock_writer.write_subchapter.assert_any_call(
            self.generator.filepath, chapter, 2, "Subchapter 1.2", mock_subchapter_content
        )

    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    @patch('pathlib.Path.is_file')
    def test_browse_book_success(self, mock_is_file, mock_print, mock_file):
        self.generator.filepath = Path("test_output/my_book.md")
        mock_is_file.return_value = True
        mock_file().read.return_value = "Mock book content"
        mock_input = MagicMock()
        with patch('builtins.input', mock_input):
           self.generator.browse_book()

        mock_is_file.assert_called_once_with()
        mock_file.assert_called_once_with(self.generator.filepath, "r", encoding="utf-8")
        mock_print.assert_called_with("Mock book content")
        mock_input.assert_called_with("Press Enter to continue after browsing the book...")

    @patch('pathlib.Path.is_file')
    def test_browse_book_file_not_found(self, mock_is_file):
        self.generator.filepath = Path("test_output/nonexistent_book.md")
        mock_is_file.return_value = False
        mock_print = MagicMock()

        with patch('builtins.print', mock_print):
            self.generator.browse_book()
        mock_is_file.assert_called_once()
        mock_print.assert_called_with("Book file not found. Please generate the book first.")

if __name__ == "__main__":
    unittest.main()