"""
Book Writer - File Output Management

This module handles all file writing operations for the book generator, responsible for
creating properly formatted Markdown files with navigation links and proper structure.

Key responsibilities:
- File path generation and sanitization
- Markdown file writing with proper formatting
- Chapter and subchapter content writing
- Table of contents generation in Markdown format
- Navigation link management and anchor creation
- Output directory management
"""

from pathlib import Path
from typing import Optional, TYPE_CHECKING

# Use relative import within the src package
from .table_of_contents import Chapter

if TYPE_CHECKING:
    from .table_of_contents import TableOfContents

class BookWriter:
    """Writes the book content to a file with proper file handling."""

    def __init__(self, output_dir: str = "books") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def get_filepath(self, title: str) -> Path:
        """Generates a filepath for the book based on title."""
        sanitized_title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{sanitized_title.replace(' ', '_').lower()}.md"
        return self.output_dir / filename
    
    def write_chapter(self, filepath: Path, chapter: Chapter, content: str, chapter_toc: str) -> None:
        """Writes a chapter and its content to the book file."""
        with filepath.open("a", encoding="utf-8") as file:
            file.write(f"<a id='chapter-{chapter.number}'></a>\n\n")
            file.write(f"## Chapter {chapter.number}. {chapter.title}\n\n")
            file.write(f"<a id='chapter-{chapter.number}-contents'></a>\n\n")
            file.write("[Back to Main Table of Contents](#table-of-contents)\n\n")
            file.write(chapter_toc)
            file.write(f"{content}\n\n")

    def write_subchapter(self, filepath: Path, chapter: Chapter, subchapter_num: int, title: str, content: str) -> None:
        """Writes a subchapter and its content to the book file."""
        with filepath.open("a", encoding="utf-8") as file:
            file.write(f"<a id='chapter-{chapter.number}-{subchapter_num}'></a>\n\n")
            file.write(f"### {chapter.number}.{subchapter_num}. {title}\n\n")
            file.write(f"[Back to Chapter Contents](#chapter-{chapter.number}-contents)\n")
            file.write("[Back to Main Table of Contents](#table-of-contents)\n\n")
            file.write(f"{content}\n\n")

    def write_toc(self, filepath: Path, title: str, toc: 'TableOfContents') -> None:
        """Writes the table of contents to the book file."""
        with filepath.open("w", encoding="utf-8") as file:
            file.write(f"# {title}\n\n")
            file.write("<a id='table-of-contents'></a>\n\n")
            file.write(toc.to_markdown())