# src/config.py
import os
import google.generativeai as genai
from pathlib import Path
# Use relative import within the src package
from .errors import BookGenerationError

class APIConfig:
    """Loads and configures the Google Generative AI API key."""
    def __init__(self, api_key_file: str = "~/.api-gemini"):
        """
        Initializes APIConfig and configures the genai library.

        Args:
            api_key_file: Path to the file containing the Gemini API key.
                          Defaults to '~/.api-gemini'.
        """
        self.api_key_path = Path(api_key_file).expanduser()
        self.api_key = self._load_api_key()
        self._configure_genai()

    def _load_api_key(self) -> str:
        """Loads the API key from the specified file."""
        try:
            with self.api_key_path.open("r", encoding="utf-8") as f:
                key = f.read().strip()
            if not key:
                raise BookGenerationError(f"API key file is empty: {self.api_key_path}")
            return key
        except FileNotFoundError:
            raise BookGenerationError(
                f"API key file not found: {self.api_key_path}. "
                "Please create the file and add your Gemini API key."
            )
        except Exception as e:
            raise BookGenerationError(f"Error reading API key file {self.api_key_path}: {e}")

    def _configure_genai(self):
        """Configures the google.generativeai library."""
        if not self.api_key:
            raise BookGenerationError("API key not loaded. Cannot configure genai.")
        try:
            genai.configure(api_key=self.api_key)
            print("Google Generative AI configured successfully.")
        except Exception as e:
            raise BookGenerationError(f"Failed to configure Google Generative AI: {e}")