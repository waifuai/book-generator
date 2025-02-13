import logging
import os
import requests

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from config import BookGenerationError, APIConfig

class ContentGenerator:
    """Generates content using the Generative AI model."""
    def __init__(self, model_name: str = 'gemini-1.5-flash-8b'):
        self.api_config = APIConfig()
        self.model_name = model_name
        if self.api_config.api_provider == "gemini":
            self.model = genai.GenerativeModel(model_name)
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        reraise=True
    )
    def generate_content(self, prompt: str) -> str:
        try:
            print("Calling API to generate content...")
            if self.api_config.api_provider == "gemini":
                result = self.model.generate_content(prompt)
                print("API call complete.")
                return result.text
            elif self.api_config.api_provider == "openrouter":
                # Use OpenRouter API
                api_key = os.getenv("OPENROUTER_API_KEY")
                if not api_key:
                    raise BookGenerationError("API key not found. Please set the OPENROUTER_API_KEY environment variable.")

                url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                }

                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                print("API call complete.")
                return result["choices"][0]["message"]["content"]
            else:
                raise BookGenerationError(f"Invalid API provider: {self.api_config.api_provider}")
        except Exception as e:
            logging.error(f"Error generating content: {e}")
            raise BookGenerationError(f"Failed to generate content: {str(e)}")