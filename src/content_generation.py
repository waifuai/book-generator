import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from .errors import BookGenerationError
from .config import APIConfig

# Keep a local default to satisfy type hints and legacy imports;
# actual runtime default is decided in main.py via ~/.model-gemini or CLI.
DEFAULT_MODEL = "gemini-2.5-pro"

class ContentGenerator:
    """Generates content using the Google GenAI SDK."""
    def __init__(self, config: APIConfig, model_name: str = DEFAULT_MODEL):
        """
        Initializes ContentGenerator with the GenAI client.

        Args:
            config: An instance of APIConfig containing the initialized genai.Client.
            model_name: The name of the Gemini model to use. Defaults to "gemini-2.5-pro".
        """
        self.model_name = model_name
        self.config = config
        self.client = config.client  # central client
        print(f"Using GenAI model '{self.model_name}' with central client.")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def generate_content(self, prompt: str) -> str:
        """
        Generates content using the GenAI client.

        Args:
            prompt: The input prompt for the model.

        Returns:
            The generated text as a string.
        """
        try:
            print(f"Generating content with model '{self.model_name}' via genai.Client...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )

            # google-genai responses expose text directly similar to legacy, but ensure candidates presence
            text = getattr(response, "text", None)
            if not text:
                # best-effort checks in case structure differs
                candidates = getattr(response, "candidates", None)
                if not candidates:
                    raise BookGenerationError("Received an empty response from the GenAI API.")
            print("GenAI generation complete.")
            return text or ""

        except Exception as e:
            logging.error(f"Error generating content with GenAI: {e}", exc_info=True)
            raise BookGenerationError(f"Failed to generate content with Gemini: {str(e)}")