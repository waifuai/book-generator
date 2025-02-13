from dataclasses import dataclass
from pathlib import Path
import google.generativeai as genai
import os

class BookGenerationError(Exception):
    """Custom exception for book generation errors."""
    pass

class APIConfig:
    """Handles API configuration and setup."""
    def __init__(self, api_key_file: str = "../api.txt", openrouter_api_key_file: str = "../openrouter_api.txt", api_provider: str = "gemini"):
        self.api_provider = api_provider
        self.api_key = self._load_api_key(api_key_file, openrouter_api_key_file)
        self._configure_genai()
    
    def _load_api_key(self, api_key_file: str, openrouter_api_key_file: str) -> str:
        """Loads the API key based on the provider."""
        if self.api_provider == "gemini":
            api_path = Path(api_key_file)
            if not api_path.is_file():
                raise BookGenerationError(f"Error: {api_key_file} not found. Please create this file with your Gemini API key.")
            return api_path.read_text().strip()
        elif self.api_provider == "openrouter":
            api_path = Path(openrouter_api_key_file)
            if not api_path.is_file():
                raise BookGenerationError(f"Error: {openrouter_api_key_file} not found. Please create this file with your OpenRouter API key.")
            return api_path.read_text().strip()
        else:
            raise BookGenerationError(f"Invalid API provider: {self.api_provider}. Must be 'gemini' or 'openrouter'.")
    
    def _configure_genai(self):
        if self.api_provider == "gemini":
            genai.configure(api_key=self.api_key)
        elif self.api_provider == "openrouter":
            os.environ["OPENROUTER_API_KEY"] = self.api_key
        else:
            raise BookGenerationError(f"Invalid API provider: {self.api_provider}. Must be 'gemini' or 'openrouter'.")