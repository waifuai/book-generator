import json
from dataclasses import dataclass
from typing import List

from .errors import BookGenerationError

@dataclass
class Chapter:
    """Represents a chapter in the book."""
    title: str
    subchapters: List[str]
    number: int = 0

class TableOfContents:
    """Parses and holds the table of contents."""
    def __init__(self, content: str):
        self.chapters = self._parse_toc(content)
        self._assign_numbers()
    
    def _parse_toc(self, content: str) -> List[Chapter]:
        content = self._clean_response(content)
        try:
            toc_data = json.loads(content)
            return [
                Chapter(
                    title=chapter.get('title', ''),
                    subchapters=chapter.get('subchapters', [])
                )
                for chapter in toc_data
            ]
        except json.JSONDecodeError as e:
            raise BookGenerationError(f"Invalid TOC format: {e}")
    
    @staticmethod
    def _clean_response(content: str) -> str:
        """Cleans the API response from any wrapper tokens and surrounding whitespace."""
        import re
        # Regex to find optional ```json, ```python, or ```, capture the content, and match optional ``` at the end
        # It handles leading/trailing whitespace around the fences and the content itself.
        # Using re.DOTALL so '.' matches newline characters.
        match = re.match(r'^\s*(?:```(?:json|python)?\s*)?(.*?)(?:\s*```\s*)?$', content, re.DOTALL | re.IGNORECASE)
        if match:
            # Return the captured group (the content inside), stripped of leading/trailing whitespace
            return match.group(1).strip()
        else:
            # If no fences are found, just strip the original content
            return content.strip()
    
    def _assign_numbers(self):
        """Assigns chapter numbers to all chapters."""
        for idx, chapter in enumerate(self.chapters, 1):
            chapter.number = idx
    
    def to_markdown(self) -> str:
        """Generates the markdown table of contents."""
        lines = ["# Table of Contents\n"]
        for chapter in self.chapters:
            lines.append(f"{chapter.number}. [{chapter.title}](#chapter-{chapter.number})")
            for idx, subchapter in enumerate(chapter.subchapters, 1):
                lines.append(f"    * [{chapter.number}.{idx}. {subchapter}](#chapter-{chapter.number}-{idx})")
        return "\n".join(lines) + "\n\n"
    
    def chapter_toc(self, chapter: Chapter) -> str:
        """Generates the table of contents for a single chapter."""
        lines = [f"### Chapter {chapter.number} Contents\n"]
        lines.append(f"{chapter.number}. [{chapter.title}](#chapter-{chapter.number})")
        for idx, subchapter in enumerate(chapter.subchapters, 1):
            lines.append(f"    * [{chapter.number}.{idx}. {subchapter}](#chapter-{chapter.number}-{idx})")
        return "\n".join(lines) + "\n\n"
    
    def to_json(self) -> str:
        """Converts the table of contents to JSON format."""
        toc_data = [
            {
                'title': chapter.title,
                'subchapters': chapter.subchapters,
                'number': chapter.number
            }
            for chapter in self.chapters
        ]
        return json.dumps(toc_data, indent=4)
    
    def update_from_json(self, json_data: str):
        """Updates the table of contents from JSON data."""
        try:
            toc_data = json.loads(json_data)
            self.chapters = [
                Chapter(
                    title=chapter.get('title', ''),
                    subchapters=chapter.get('subchapters', []),
                    number=chapter.get('number', 0)
                )
                for chapter in toc_data
            ]
        except json.JSONDecodeError as e:
            raise BookGenerationError(f"Invalid TOC JSON format: {e}")