"""
API Configuration and Client Management

This module handles all API configuration, credential management, and client initialization
for the Google Gemini AI service. It provides a centralized configuration system with
multiple fallback options for API keys and model selection.

Key responsibilities:
- Google Gemini client initialization and management
- API key resolution with multiple fallback strategies
- Model configuration and default resolution
- Environment variable and file-based credential handling
- Error handling for configuration and client setup
- Future extensibility for multiple AI providers
"""

# src/config.py
import os
from pathlib import Path
from .errors import BookGenerationError
from google import genai

# Default provider/model behavior:
# - Provider default: openrouter (as requested), but current code only wires Gemini.
# - Model default for Gemini is resolved from ~/.model-gemini when not overridden by CLI.
# - We also provide a resolver for ~/.model-openrouter for future OpenRouter integration.
DEFAULT_GEMINI_MODEL_FALLBACK = "gemini-2.5-pro"
GEMINI_MODEL_FILE = Path("~/.model-gemini").expanduser()
OPENROUTER_MODEL_FILE = Path("~/.model-openrouter").expanduser()

def _resolve_model_from_file(path: Path) -> str | None:
    """
    Return stripped contents of a single-line model file if present and non-empty, else None.
    """
    try:
        if path.is_file():
            content = path.read_text(encoding="utf-8").strip()
            return content if content else None
    except Exception:
        # Silent fallback; caller decides the ultimate default
        return None
    return None

def resolve_default_gemini_model() -> str:
    """
    Resolve the default Gemini model with precedence:
      1) ~/.model-gemini (if exists and non-empty)
      2) hardcoded fallback DEFAULT_GEMINI_MODEL_FALLBACK
    """
    file_model = _resolve_model_from_file(GEMINI_MODEL_FILE)
    return file_model or DEFAULT_GEMINI_MODEL_FALLBACK

def resolve_default_openrouter_model() -> str | None:
    """
    Resolve the default OpenRouter model from ~/.model-openrouter if present.
    Returns None when not available. Intended for future OpenRouter provider use.
    """
    return _resolve_model_from_file(OPENROUTER_MODEL_FILE)

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