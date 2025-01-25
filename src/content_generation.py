import logging

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from config import BookGenerationError

class ContentGenerator:
    """Generates content using the Generative AI model."""
    def __init__(self, model_name: str = 'gemini-1.5-flash-8b'):
        self.model = genai.GenerativeModel(model_name)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        reraise=True
    )
    def generate_content(self, prompt: str) -> str:
        try:
            print("Calling API to generate content...")
            result = self.model.generate_content(prompt)
            print("API call complete.")
            return result.text
        except Exception as e:
            logging.error(f"Error generating content: {e}")
            raise BookGenerationError(f"Failed to generate content: {str(e)}")