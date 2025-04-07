import logging
import google.generativeai as genai
# Removed Tool and GoogleSearchRetrieval imports
from tenacity import retry, stop_after_attempt, wait_exponential

# Use absolute imports relative to src
from errors import BookGenerationError
from config import APIConfig # Import APIConfig
class ContentGenerator:
    """Generates content using the Google Generative AI API."""
    def __init__(self, config: APIConfig, model_name: str = "models/gemini-2.0-flash"):
        """
        Initializes ContentGenerator with the Gemini API.

        Args:
            config: An instance of APIConfig containing the configured API key.
            model_name: The name of the Gemini model to use.
                        Defaults to "models/gemini-2.0-flash".
        """
        self.model_name = model_name
        self.config = config
        # Removed self.enable_search

        try:
            print(f"Initializing Gemini model '{self.model_name}'...")
            # Initialize the Gemini model without tools
            self.model = genai.GenerativeModel(
                model_name=self.model_name
                # Removed tools parameter
            )
            print(f"Gemini model '{self.model_name}' initialized successfully.")

        except Exception as e:
            # Catch potential errors during initialization
            logging.error(f"Failed to initialize Gemini model '{self.model_name}': {e}", exc_info=True)
            raise BookGenerationError(f"Failed to initialize Gemini model '{self.model_name}': {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def generate_content(self, prompt: str) -> str:
        """
        Generates content using the initialized Gemini model.

        Args:
            prompt: The input prompt for the model.

        Returns:
            The generated text as a string.
        """
        try:
            print(f"Generating content with Gemini model '{self.model_name}'...")
            # Generate content using the Gemini API
            # If search tool was enabled during init, the model may use it.
            response = self.model.generate_content(
                prompt,
                # generation_config=genai.types.GenerationConfig(...) # Add config if needed
                # request_options={'timeout': 600} # Example timeout
            )

            # Accessing the text part of the response
            # Handle potential errors or empty responses
            if not response.candidates or not response.candidates[0].content.parts:
                feedback = getattr(response, 'prompt_feedback', 'No feedback available')
                logging.warning(f"Gemini response was empty or blocked. Feedback: {feedback}")
                if hasattr(feedback, 'block_reason'):
                     raise BookGenerationError(f"Content generation blocked. Reason: {feedback.block_reason}. Details: {getattr(feedback, 'block_reason_message', 'N/A')}")
                raise BookGenerationError("Received an empty response from the Gemini API.")

            generated_text = response.text

            # Removed search tool usage check


            print("Gemini generation complete.")
            return generated_text

        except Exception as e:
            logging.error(f"Error generating content with Gemini model: {e}", exc_info=True)
            raise BookGenerationError(f"Failed to generate content with Gemini: {str(e)}")