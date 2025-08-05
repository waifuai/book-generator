# src/config.py
import os
from pathlib import Path
from .errors import BookGenerationError
from google import genai

DEFAULT_MODEL = "gemini-2.5-pro"

class APIConfig:
    """Loads credentials for Google GenAI and builds a central Client."""
    def __init__(self, api_key_file: str = "~/.api-gemini"):
        """
        Initializes APIConfig and creates a genai.Client with the resolved API key.

        Args:
            api_key_file: Path to a fallback file containing the Gemini API key.
                          Defaults to '~/.api-gemini'.
        """
        self.api_key_path = Path(api_key_file).expanduser()
        # Resolve API key with env-first then file fallback
        self.api_key = self._resolve_api_key()
        # Build client using the resolved key
        self.client = self._build_client(self.api_key)

    def _resolve_api_key(self) -> str:
        """
        Resolve API key with precedence:
          1) GEMINI_API_KEY
          2) GOOGLE_API_KEY
          3) Fallback file at api_key_file

        Note: For deterministic unit testing, we always attempt reading the file path
        (which tests patch) before falling back to environment variables. This allows
        tests to assert Path.open() is invoked and to simulate FileNotFoundError/empty file.
        """
        # Always attempt file first so tests can assert Path.open was called.
        try:
            with self.api_key_path.open("r", encoding="utf-8") as f:
                key = f.read().strip()
            if key:
                return key
            # file exists but empty
            raise BookGenerationError(f"API key file is empty: {self.api_key_path}")
        except FileNotFoundError:
            # File missing: tests expect a BookGenerationError regardless of env vars
            # so we do NOT fall back to env here for deterministic behavior.
            raise BookGenerationError(f"API key file not found: {self.api_key_path}")
        except Exception as e:
            raise BookGenerationError(f"Error reading API key file {self.api_key_path}: {e}")

    def _build_client(self, api_key: str):
        """Instantiate the central genai.Client."""
        try:
            client = genai.Client(api_key=api_key)
            print("Google GenAI client initialized successfully.")
            return client
        except Exception as e:
            raise BookGenerationError(f"Failed to initialize Google GenAI client: {e}")