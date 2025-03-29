from dataclasses import dataclass
from pathlib import Path
import google.generativeai as genai
import os
from dotenv import load_dotenv

from errors import BookGenerationError

# Load environment variables from .env file
load_dotenv()

class APIConfig:
    """Handles API configuration and setup using environment variables."""
    def __init__(self, api_provider: str = "gemini"):
        """
        Initializes APIConfig.

        Args:
            api_provider: The API provider to use ('gemini' or 'openrouter').
                          Defaults to 'gemini'.

        Raises:
            BookGenerationError: If the specified provider is invalid or the
                                 required API key environment variable is not set.
        """
        self.api_provider = api_provider.lower()
        if self.api_provider not in ["gemini", "openrouter"]:
            raise BookGenerationError(f"Invalid API provider: {self.api_provider}. Must be 'gemini' or 'openrouter'.")

        self.api_key = self._load_api_key()
        self._configure_provider()

    def _load_api_key(self) -> str:
        """Loads the API key from environment variables based on the provider."""
        if self.api_provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise BookGenerationError("Error: GEMINI_API_KEY environment variable not found. Please set it in your .env file or environment.")
            return api_key
        elif self.api_provider == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise BookGenerationError("Error: OPENROUTER_API_KEY environment variable not found. Please set it in your .env file or environment.")
            # The key is already set in the environment by load_dotenv,
            # but we return it for consistency and potential direct use.
            return api_key
        # This part should ideally not be reached due to the check in __init__
        else:
             raise BookGenerationError(f"Invalid API provider: {self.api_provider}") # Should not happen

    def _configure_provider(self):
        """Configures the generative AI provider."""
        if self.api_provider == "gemini":
            try:
                genai.configure(api_key=self.api_key)
                print("Gemini API configured successfully.")
            except Exception as e:
                 raise BookGenerationError(f"Failed to configure Gemini API: {e}")
        elif self.api_provider == "openrouter":
            # The key is already set in the environment by load_dotenv()
            # and _load_api_key ensures it exists.
            # No specific configuration step needed here for OpenRouter via requests.
             print("OpenRouter API key loaded from environment.")
        # This part should ideally not be reached
        else:
            raise BookGenerationError(f"Invalid API provider: {self.api_provider}") # Should not happen