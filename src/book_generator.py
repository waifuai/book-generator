"""
Book Generation Coordinator

This module coordinates the entire book generation process, managing the workflow from
table of contents creation to final book assembly. It serves as the main orchestrator
that connects all other components together.

Key responsibilities:
- Table of contents generation and parsing
- Book generation workflow management
- Progress reporting and callback handling
- Chapter and subchapter content generation
- File path management and organization
- Error handling and recovery
"""

import logging
from pathlib import Path
from typing import Optional, Callable

# Use relative imports within the src package
from .errors import BookGenerationError
from .content_generation import ContentGenerator
from .table_of_contents import TableOfContents, Chapter
from .book_writer import BookWriter

class BookGenerator:
    """Coordinates the generation of the book with progress reporting."""
    def __init__(self, content_generator: ContentGenerator, writer: BookWriter, progress_callback: Optional[Callable[[str, float], None]] = None):
        self.content_generator = content_generator
        self.writer = writer
        self.book_title: Optional[str] = None
        self.toc: Optional[TableOfContents] = None
        self.filepath: Optional[Path] = None
        self.progress_callback = progress_callback or (lambda msg, progress: None)
    
    def generate_toc(self, title: str, toc_prompt: str) -> TableOfContents:
        """Generates and parses the table of contents."""
        self.book_title = title
        toc_content = self.content_generator.generate_content(toc_prompt)
        self.toc = TableOfContents(toc_content)
        self.filepath = self.writer.get_filepath(title)
        self.writer.write_toc(self.filepath, title, self.toc)
        return self.toc
    
    def save_toc(self):
        """Saves the current table of contents to a JSON file."""
        if self.toc and self.filepath:
            toc_json_path = self.filepath.with_suffix(".json")
            with toc_json_path.open("w", encoding="utf-8") as f:
                f.write(self.toc.to_json())
            print(f"Table of Contents saved to {toc_json_path}")
    
    def load_toc(self):
        """Loads the table of contents from a JSON file."""
        if self.filepath:
            toc_json_path = self.filepath.with_suffix(".json")
            if toc_json_path.is_file():
                with toc_json_path.open("r", encoding="utf-8") as f:
                    toc_json = f.read()
                self.toc.update_from_json(toc_json)
                self.writer.write_toc(self.filepath, self.book_title, self.toc)
                print(f"Table of Contents loaded from {toc_json_path}")
            else:
                print(f"No saved Table of Contents found at {toc_json_path}")
    
    def generate_book(self):
        """Generates the entire book with progress reporting."""
        if not self.toc or not self.filepath or not self.book_title:
            raise BookGenerationError("Table of Contents not generated. Call generate_toc() first.")

        try:
            total_chapters = len(self.toc.chapters)
            total_items = sum(len(chapter.subchapters) + 1 for chapter in self.toc.chapters)  # +1 for intro per chapter
            current_item = 0

            self.progress_callback(f"Starting book generation with {total_chapters} chapters and {total_items} content items", 0.0)

            # Generate each chapter and subchapter
            for chapter_idx, chapter in enumerate(self.toc.chapters, 1):
                self.progress_callback(f"Generating Chapter {chapter_idx}/{total_chapters}: {chapter.title}", current_item / total_items)
                self._generate_chapter(chapter, current_item, total_items)
                current_item += len(chapter.subchapters) + 1  # +1 for chapter intro

                # Update progress after each chapter
                progress = current_item / total_items
                self.progress_callback(f"Completed Chapter {chapter_idx}/{total_chapters}: {chapter.title}", progress)

            self.progress_callback("Book generation completed successfully!", 1.0)
            logging.info(f"Book successfully generated at {self.filepath}")
            return self.filepath

        except BookGenerationError as e:
            self.progress_callback(f"❌ Book generation failed: {e}", -1.0)
            logging.error(f"Failed to generate book: {e}")
            return None
    
    def _generate_chapter(self, chapter: Chapter, current_item: int = 0, total_items: int = 0):
        """Generates a single chapter and its subchapters with progress reporting."""
        # Generate chapter introduction
        intro_prompt = f"Write a concise introduction for Chapter {chapter.number}: '{chapter.title}' in a book titled '{self.book_title}'."
        intro_content = self.content_generator.generate_content(intro_prompt)

        # Generate chapter TOC and write chapter
        chapter_toc = self.toc.chapter_toc(chapter)
        self.writer.write_chapter(self.filepath, chapter, intro_content, chapter_toc)

        # Generate subchapters
        for idx, subchapter_title in enumerate(chapter.subchapters, 1):
            progress = (current_item + idx) / total_items if total_items > 0 else 0
            self.progress_callback(f"  └── Subchapter {chapter.number}.{idx}: {subchapter_title}", progress)

            subchapter_prompt = (
                f"Write a detailed section for Chapter {chapter.number}.{idx}: '{subchapter_title}' "
                f"within Chapter {chapter.number}: '{chapter.title}' in a book titled '{self.book_title}'."
            )
            subchapter_content = self.content_generator.generate_content(subchapter_prompt)
            self.writer.write_subchapter(self.filepath, chapter, idx, subchapter_title, subchapter_content)