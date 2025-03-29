import logging
import os
import requests

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from config import APIConfig
from errors import BookGenerationError

class ContentGenerator:
    """Generates content using the Generative AI model."""
    def __init__(self, api_config: APIConfig, model_name: str):
        """
        Initializes ContentGenerator.

        Args:
            api_config: An initialized APIConfig instance.
            model_name: The name of the model to use for generation.
        """
        self.api_config = api_config
        self.model_name = model_name
        self.model = None # Initialize model attribute

        if self.api_config.api_provider == "gemini":
            if not self.model_name:
                 raise BookGenerationError("Model name must be provided for Gemini provider.")
            try:
                # Initialize the Gemini model
                self.model = genai.GenerativeModel(self.model_name)
                print(f"Gemini model '{self.model_name}' initialized.")
            except Exception as e:
                 raise BookGenerationError(f"Failed to initialize Gemini model '{self.model_name}': {e}")
        elif self.api_config.api_provider == "openrouter":
             # For OpenRouter using requests, model initialization isn't done here.
             # The model name is used directly in the API call payload.
             if not self.model_name:
                 raise BookGenerationError("Model name must be provided for OpenRouter provider.")
             print(f"OpenRouter model set to '{self.model_name}'.")
        # No need for an else here as APIConfig already validated the provider

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