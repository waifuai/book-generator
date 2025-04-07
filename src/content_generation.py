import logging
import google.generativeai as genai
# Import Tool and GoogleSearchRetrieval for enabling search
from google.ai.generativelanguage import Tool, GoogleSearchRetrieval
from tenacity import retry, stop_after_attempt, wait_exponential

from .errors import BookGenerationError
from .config import APIConfig # Import APIConfig

class ContentGenerator:
    """Generates content using the Google Generative AI API with search tool."""
    def __init__(self, config: APIConfig, model_name: str = "models/gemini-2.5-pro-exp-03-25", enable_search: bool = False):
        """
        Initializes ContentGenerator with the Gemini API.

        Args:
            config: An instance of APIConfig containing the configured API key.
            model_name: The name of the Gemini model to use.
                        Defaults to "models/gemini-2.5-pro-exp-03-25".
            enable_search: Whether to enable the Google Search tool. Defaults to False.
                           Note: Requires a model known to support the search tool if enabled.
        """
        self.model_name = model_name
        self.config = config
        self.enable_search = enable_search

        try:
            tools_config = []
            if self.enable_search:
                # Define the Google Search tool configuration only if enabled
                search_tool = Tool(google_search_retrieval=GoogleSearchRetrieval())
                tools_config = [search_tool]
                print(f"Initializing Gemini model '{self.model_name}' with search tool enabled...")
            else:
                print(f"Initializing Gemini model '{self.model_name}' without search tool...")

            # Initialize the Gemini model
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                tools=tools_config # Pass the tool config (empty list if search disabled)
            )
            print(f"Gemini model '{self.model_name}' initialized successfully.")

        except Exception as e:
            # Catch potential errors during initialization
            search_status = "with search tool" if self.enable_search else "without search tool"
            logging.error(f"Failed to initialize Gemini model '{self.model_name}' {search_status}: {e}", exc_info=True)
            raise BookGenerationError(f"Failed to initialize Gemini model '{self.model_name}' {search_status}: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def generate_content(self, prompt: str) -> str:
        """
        Generates content using the initialized Gemini model. The model may use
        the enabled search tool if needed based on the prompt.

        Args:
            prompt: The input prompt for the model.

        Returns:
            The generated text as a string.
        """
        try:
            search_status = "(search enabled)" if self.enable_search else "(search disabled)"
            print(f"Generating content with Gemini model '{self.model_name}' {search_status}...")
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

            # Check if the model actually used the search tool (only relevant if enabled)
            if self.enable_search:
                try:
                    if response.candidates[0].citation_metadata:
                         logging.info(f"Gemini used the search tool. Citations found: {len(response.candidates[0].citation_metadata.citation_sources)}")
                         # You could potentially process citations here if needed
                except (AttributeError, IndexError):
                     logging.info("Gemini did not report using the search tool for this request (or search was disabled).")


            print("Gemini generation complete.")
            return generated_text

        except Exception as e:
            logging.error(f"Error generating content with Gemini model: {e}", exc_info=True)
            raise BookGenerationError(f"Failed to generate content with Gemini: {str(e)}")