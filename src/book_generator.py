import logging
from pathlib import Path
from typing import Optional

class BookGenerationError(Exception):
    """Custom exception for book generation errors."""
    pass


from content_generation import ContentGenerator
from table_of_contents import TableOfContents, Chapter
from book_writer import BookWriter

class BookGenerator:
    """Coordinates the generation of the book."""
    def __init__(self, content_generator: ContentGenerator, writer: BookWriter):
        self.content_generator = content_generator
        self.writer = writer
        self.book_title: Optional[str] = None
        self.toc: Optional[TableOfContents] = None
        self.filepath: Optional[Path] = None
    
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
    
    def pause_and_modify_toc(self):
        """Pauses the generation process to allow TOC modification."""
        self.save_toc()
        input("Press Enter to continue after modifying the TOC JSON file...")
        self.load_toc()
    
    def generate_book(self):
        """Generates the entire book."""
        if not self.toc or not self.filepath or not self.book_title:
            raise BookGenerationError("Table of Contents not generated. Call generate_toc() first.")
        
        try:
            # Generate each chapter and subchapter
            for chapter in self.toc.chapters:
                self._generate_chapter(chapter)
            
            logging.info(f"Book successfully generated at {self.filepath}")
            return self.filepath
        
        except BookGenerationError as e:
            logging.error(f"Failed to generate book: {e}")
            return None
    
    def _generate_chapter(self, chapter: Chapter):
        """Generates a single chapter and its subchapters."""
        # Generate chapter introduction
        intro_prompt = f"Write a concise introduction for Chapter {chapter.number}: '{chapter.title}' in a book titled '{self.book_title}'."
        intro_content = self.content_generator.generate_content(intro_prompt)
        
        # Generate chapter TOC and write chapter
        chapter_toc = self.toc.chapter_toc(chapter)
        self.writer.write_chapter(self.filepath, chapter, intro_content, chapter_toc)
        
        # Generate subchapters
        for idx, subchapter_title in enumerate(chapter.subchapters, 1):
            print(f"Generating subchapter {chapter.number}.{idx}: {subchapter_title}")
            subchapter_prompt = (
                f"Write a detailed section for Chapter {chapter.number}.{idx}: '{subchapter_title}' "
                f"within Chapter {chapter.number}: '{chapter.title}' in a book titled '{self.book_title}'."
            )
            subchapter_content = self.content_generator.generate_content(subchapter_prompt)
            self.writer.write_subchapter(self.filepath, chapter, idx, subchapter_title, subchapter_content)
    
    def browse_book(self):
        """Allows the user to browse the current state of the book."""
        if self.filepath and self.filepath.is_file():
            with self.filepath.open("r", encoding="utf-8") as f:
                content = f.read()
                print(content)
            input("Press Enter to continue after browsing the book...")
        else:
            print("Book file not found. Please generate the book first.")