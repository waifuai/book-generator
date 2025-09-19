# src/tests/test_table_of_contents.py
import unittest
import json

# Add src to path if necessary (handled by pytest.ini)
# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).parent.parent))

from ..table_of_contents import TableOfContents, Chapter
from ..errors import BookGenerationError

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
            TableOfContents("invalid json {") # Make it clearly invalid

    def test_parse_toc_missing_keys(self):
        # Test robustness if keys are missing in the JSON
        toc_json_missing_subchapters = '[{"title": "Chapter 1"}]'
        toc = TableOfContents(toc_json_missing_subchapters)
        self.assertEqual(len(toc.chapters), 1)
        self.assertEqual(toc.chapters[0].title, "Chapter 1")
        self.assertEqual(toc.chapters[0].subchapters, []) # Should default to empty list

        toc_json_missing_title = '[{"subchapters": ["Sub 1.1"]}]'
        toc = TableOfContents(toc_json_missing_title)
        self.assertEqual(len(toc.chapters), 1)
        self.assertEqual(toc.chapters[0].title, "Untitled Chapter") # Should default to placeholder title
        self.assertEqual(toc.chapters[0].subchapters, ["Sub 1.1"])


    def test_clean_response(self):
        test_cases = [
            ("```python\nhello\n```", "hello"),
            ("```json\n{\"key\": \"value\"}\n```", "{\"key\": \"value\"}"),
            ("```\nworld\n```", "world"),
            ("no wrappers here", "no wrappers here"),
            ("  ```json\n  indented\n  ```  ", "indented"), # Test stripping
            ("```json{\"key\": \"value\"}```", "{\"key\": \"value\"}"), # No newlines
        ]
        for input_str, expected_output in test_cases:
            # Access static method via class
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
            toc.update_from_json("invalid json {") # Make it clearly invalid

if __name__ == "__main__":
    unittest.main()