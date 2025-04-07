import logging
import google.generativeai as genai
from google.generativeai.types import Tool, FunctionDeclaration # Import necessary types
from tenacity import retry, stop_after_attempt, wait_exponential

from .errors import BookGenerationError
from .config import APIConfig # Import APIConfig

# Define the search tool using the helper
# Note: As of early 2024, the exact method might evolve.
# Using a placeholder structure based on common patterns.
# If this specific helper isn't available, direct FunctionDeclaration might be needed.
# Assuming a simple search query tool for demonstration.
# A more robust implementation might require specific function declarations.
# For now, let's represent the intent to use the built-in search grounding.
# The actual enabling might happen via model arguments or specific API features.
# Let's structure the code assuming model initialization handles search enablement.

class ContentGenerator:
    """Generates content using the Google Generative AI API."""
    def __init__(self, config: APIConfig, model_name: str = "models/gemini-2.5-pro-preview-03-25"):
        """
        Initializes ContentGenerator with the Gemini API.

        Args:
            config: An instance of APIConfig containing the configured API key.
            model_name: The name of the Gemini model to use.
                        Defaults to "models/gemini-2.5-pro-preview-03-25".
        """
        self.model_name = model_name
        self.config = config # Store config for potential future use (though key is already configured)

        try:
            # Define the search tool - This tells the model it *can* use search.
            # The actual triggering depends on the prompt and model capabilities.
            # For models supporting automatic search grounding, just specifying the model
            # might be enough, but explicitly defining the tool is clearer intent.
            # Note: The exact API for enabling search might change.
            # This represents enabling the capability.
            search_tool = Tool(function_declarations=[
                # Placeholder: In some Gemini versions, a specific function like
                # 'search_tool_fn' or similar might be expected, or just enabling
                # search in model parameters. Let's assume the model name implies search capability
                # for now, or that the API handles it implicitly when available.
                # If direct tool definition is needed:
                # FunctionDeclaration(name="web_search", description="Search the web for information.")
            ])

            # Initialize the Gemini model with the search tool enabled
            # The 'tools' parameter might be the way to enable specific tools like search.
            # Check the latest google-generativeai documentation for the correct method.
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                # tools=[search_tool] # Enable the search tool capability if required by API
                # Or, search might be enabled via generation_config or implicitly
            )
            print(f"Gemini model '{self.model_name}' initialized successfully.")
            # If search needs explicit enabling via tools, uncomment the line above.
            # For models like preview with built-in search, this might not be needed.

        except Exception as e:
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
            # Safety settings can be added here if needed
            response = self.model.generate_content(
                prompt,
                # generation_config=genai.types.GenerationConfig(...) # Add config if needed
                # request_options={'timeout': 600} # Example timeout
            )

            # Accessing the text part of the response
            # Handle potential errors or empty responses
            if not response.candidates or not response.candidates[0].content.parts:
                 # Attempt to get feedback if available
                feedback = getattr(response, 'prompt_feedback', 'No feedback available')
                logging.warning(f"Gemini response was empty or blocked. Feedback: {feedback}")
                # Check for block reason specifically
                if hasattr(feedback, 'block_reason'):
                     raise BookGenerationError(f"Content generation blocked. Reason: {feedback.block_reason}. Details: {getattr(feedback, 'block_reason_message', 'N/A')}")
                raise BookGenerationError("Received an empty response from the Gemini API.")

            generated_text = response.text # Use the convenient .text attribute

            print("Gemini generation complete.")
            return generated_text

        except Exception as e:
            # Catch potential API errors, rate limits, etc.
            logging.error(f"Error generating content with Gemini model: {e}")
            # Reraise as BookGenerationError for consistent handling upstream
            raise BookGenerationError(f"Failed to generate content with Gemini: {str(e)}")