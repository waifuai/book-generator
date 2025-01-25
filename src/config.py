from dataclasses import dataclass
from pathlib import Path
import google.generativeai as genai

class BookGenerationError(Exception):
    """Custom exception for book generation errors."""
    pass

class APIConfig:
    """Handles API configuration and setup."""
    def __init__(self, api_key_file: str = "../api.txt"):
        self.api_key = self._load_api_key(api_key_file)
        self._configure_genai()
    
    def _load_api_key(self, api_key_file: str) -> str:
        api_path = Path(api_key_file)
        if not api_path.is_file():
            raise BookGenerationError(f"Error: {api_key_file} not found. Please create this file with your API key.")
        return api_path.read_text().strip()
    
    def _configure_genai(self):
        genai.configure(api_key=self.api_key)