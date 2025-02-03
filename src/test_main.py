import unittest
from unittest.mock import patch

from book_generator import BookGenerator, BookGenerationError
from unittest.mock import patch, mock_open
from unittest.mock import MagicMock
from book_writer import BookWriter
from table_of_contents import TableOfContents, Chapter
from config import BookGenerationError

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

"""
        self.assertEqual(toc.to_markdown(), expected_markdown)
    def test_chapter_toc(self):
        chapter = Chapter("Chapter 1", ["Subchapter 1.1", "Subchapter 1.2"], 1)
        expected_markdown = """### Chapter 1 Contents

1. [Chapter 1](#chapter-1)
    * [1.1. Subchapter 1.1](#chapter-1-1)
    * [1.2. Subchapter 1.2](#chapter-1-2)

"""
        toc = TableOfContents("[]")
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


class TestBookWriter(unittest.TestCase):
    def test_get_filepath(self):
        writer = BookWriter("test_output")
        title = "My Awesome Book"
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
        handle.write.assert_any_call(chapter_toc)
    @patch('builtins.open', new_callable=mock_open)
    def test_write_toc(self, mock_file):
        writer = BookWriter("test_output")
        filepath = Path("test_output/my_book.md")
        title = "My Awesome Book"
        toc = TableOfContents("[]")
        toc.to_markdown = MagicMock(return_value="Mock TOC Markdown")

        writer.write_toc(filepath, title, toc)

        mock_file.assert_called_once_with(filepath, "w", encoding="utf-8")
        handle = mock_file()
        handle.write.assert_any_call("# My Awesome Book\n\n")
        handle.write.assert_any_call("<a id='table-of-contents'></a>\n\n")
        handle.write.assert_any_call("Mock TOC Markdown")
        handle.write.assert_any_call(f"{content}\n\n")
        expected_filepath = Path("test_output/my_awesome_book.md")


class TestBookGenerator(unittest.TestCase):
    def test_generate_toc(self):
        mock_content_generator = MagicMock(spec=ContentGenerator)
        mock_writer = MagicMock(spec=BookWriter)
        generator = BookGenerator(mock_content_generator, mock_writer)

        title = "My Awesome Book"
        toc_prompt = "Generate TOC for My Awesome Book"
        mock_toc_content = "Mock TOC Content"
        mock_content_generator.generate_content.return_value = mock_toc_content

        toc = generator.generate_toc(title, toc_prompt)

        mock_content_generator.generate_content.assert_called_once_with(toc_prompt)
        self.assertIsInstance(toc, TableOfContents)
    @patch('builtins.open', new_callable=mock_open)
    def test_save_toc(self, mock_file):
        mock_content_generator = MagicMock(spec=ContentGenerator)
        mock_writer = MagicMock(spec=BookWriter)
        generator = BookGenerator(mock_content_generator, mock_writer)

        generator.toc = MagicMock(spec=TableOfContents)
        generator.filepath = Path("test_output/my_book.md")
        generator.toc.to_json.return_value = "{}"

        generator.save_toc()

        mock_file.assert_called_once_with(Path("test_output/my_book.json"), "w", encoding="utf-8")
        handle = mock_file()
        handle.write.assert_called_once_with("{}")
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.is_file')
    def test_load_toc(self, mock_is_file, mock_file):
        mock_content_generator = MagicMock(spec=ContentGenerator)
        mock_writer = MagicMock(spec=BookWriter)
        generator = BookGenerator(mock_content_generator, mock_writer)

        generator.filepath = Path("test_output/my_book.md")
        generator.book_title = "My Awesome Book"
        mock_is_file.return_value = True
        mock_file().read.return_value = "{}"

        generator.load_toc()

        mock_is_file.assert_called_once_with()
        mock_file.assert_called_once_with(Path("test_output/my_book.json"), "r", encoding="utf-8")
        generator.toc.update_from_json.assert_called_once_with("{}")
        mock_writer.write_toc.assert_called_once_with(generator.filepath, generator.book_title, generator.toc)
    @patch('builtins.input')
    def test_pause_and_modify_toc(self, mock_input):
        mock_content_generator = MagicMock(spec=ContentGenerator)
        mock_writer = MagicMock(spec=BookWriter)
        generator = BookGenerator(mock_content_generator, mock_writer)

        generator.save_toc = MagicMock()
        generator.load_toc = MagicMock()

        generator.pause_and_modify_toc()

        generator.save_toc.assert_called_once_with()
        mock_input.assert_called_once_with("Press Enter to continue after modifying the TOC JSON file...")
        generator.load_toc.assert_called_once_with()
        mock_writer.get_filepath.assert_called_once_with(title)
    def test_generate_book(self):
        mock_content_generator = MagicMock(spec=ContentGenerator)
        mock_writer = MagicMock(spec=BookWriter)
        generator = BookGenerator(mock_content_generator, mock_writer)

        generator.toc = TableOfContents("[]")
        generator.toc.chapters = [
            Chapter("Chapter 1", ["Subchapter 1.1"], 1),
            Chapter("Chapter 2", ["Subchapter 2.1"], 2),
        ]
        generator.filepath = Path("test_output/my_book.md")
        generator.book_title = "My Awesome Book"
        generator._generate_chapter = MagicMock()

        result = generator.generate_book()

        self.assertEqual(result, generator.filepath)
        self.assertEqual(generator._generate_chapter.call_count, 2)
        generator._generate_chapter.assert_any_call(generator.toc.chapters[0])
        generator._generate_chapter.assert_any_call(generator.toc.chapters[1])
        mock_writer.write_toc.assert_called_once_with(mock_writer.get_filepath.return_value, title, toc)
        self.assertEqual(writer.get_filepath(title), expected_filepath)
    def test_generate_chapter(self):
        mock_content_generator = MagicMock(spec=ContentGenerator)
        mock_writer = MagicMock(spec=BookWriter)
        generator = BookGenerator(mock_content_generator, mock_writer)

        generator.book_title = "My Awesome Book"
        generator.filepath = Path("test_output/my_book.md")
        chapter = Chapter("Chapter 1", ["Subchapter 1.1", "Subchapter 1.2"], 1)
        mock_intro_content = "Mock intro content"
        mock_subchapter_content = "Mock subchapter content"
        mock_content_generator.generate_content.side_effect = [
            mock_intro_content,
            mock_subchapter_content,
            mock_subchapter_content,
        ]
        generator.toc = MagicMock(spec=TableOfContents)
        generator.toc.chapter_toc.return_value = "Mock chapter TOC"

        generator._generate_chapter(chapter)

        self.assertEqual(mock_content_generator.generate_content.call_count, 3)
        mock_content_generator.generate_content.assert_any_call(
            "Write a concise introduction for Chapter 1: 'Chapter 1' in a book titled 'My Awesome Book'."
        )
        mock_content_generator.generate_content.assert_any_call(
            "Write a detailed section for Chapter 1.1: 'Subchapter 1.1' within Chapter 1: 'Chapter 1' in a book titled 'My Awesome Book'."
        )
        mock_content_generator.generate_content.assert_any_call(
            "Write a detailed section for Chapter 1.2: 'Subchapter 1.2' within Chapter 1: 'Chapter 1' in a book titled 'My Awesome Book'."
        )
        generator.toc.chapter_toc.assert_called_once_with(chapter)
        mock_writer.write_chapter.assert_called_once_with(
            generator.filepath, chapter, mock_intro_content, "Mock chapter TOC"
        )
        self.assertEqual(mock_writer.write_subchapter.call_count, 2)
        mock_writer.write_subchapter.assert_any_call(
            generator.filepath, chapter, 1, "Subchapter 1.1", mock_subchapter_content
        )
        mock_writer.write_subchapter.assert_any_call(
            generator.filepath, chapter, 2, "Subchapter 1.2", mock_subchapter_content
        )
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    @patch('pathlib.Path.is_file')
    def test_browse_book(self, mock_is_file, mock_print, mock_file):
        mock_content_generator = MagicMock(spec=ContentGenerator)
        mock_writer = MagicMock(spec=BookWriter)
        generator = BookGenerator(mock_content_generator, mock_writer)

        generator.filepath = Path("test_output/my_book.md")
        mock_is_file.return_value = True
        mock_file().read.return_value = "Mock book content"

        generator.browse_book()

        mock_is_file.assert_called_once_with()
        mock_file.assert_called_once_with(generator.filepath, "r", encoding="utf-8")
        mock_print.assert_called_once_with("Mock book content")