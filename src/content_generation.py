import logging
from transformers import pipeline, set_seed
from tenacity import retry, stop_after_attempt, wait_exponential

from errors import BookGenerationError

# Set seed for reproducibility (optional, but good practice)
set_seed(42)

class ContentGenerator:
    """Generates content using a local Hugging Face transformer model."""
    def __init__(self, model_name: str = "distilgpt2"):
        """
        Initializes ContentGenerator with a local transformer model.

        Args:
            model_name: The name of the Hugging Face model to use (default: "distilgpt2").
        """
        self.model_name = model_name
        try:
            # Initialize the text generation pipeline
            # Using device=-1 forces CPU, change to 0 for default GPU if available and configured
            self.generator = pipeline('text-generation', model=self.model_name, device=-1)
            # Get the EOS token ID from the tokenizer
            self.eos_token_id = self.generator.tokenizer.eos_token_id
            # Explicitly set pad_token_id if it's None (common for GPT-2 models)
            if self.generator.tokenizer.pad_token_id is None:
                self.generator.tokenizer.pad_token_id = self.eos_token_id
                self.generator.model.config.pad_token_id = self.eos_token_id

            print(f"Hugging Face pipeline initialized with model '{self.model_name}' on CPU.")
            print(f"EOS token: '{self.generator.tokenizer.eos_token}' (ID: {self.eos_token_id})")
            print(f"Pad token ID set to: {self.generator.tokenizer.pad_token_id}")

        except Exception as e:
            raise BookGenerationError(f"Failed to initialize Hugging Face pipeline for model '{self.model_name}': {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10), # Adjusted wait times
        reraise=True
    )
    def generate_content(self, prompt: str, max_length: int = 500, min_length: int = 50) -> str:
        """
        Generates content using the initialized pipeline.

        Args:
            prompt: The input prompt for the model.
            max_length: The maximum number of tokens to generate.
            min_length: The minimum number of tokens to generate.

        Returns:
            The generated text as a string.
        """
        try:
            print(f"Generating content with local model '{self.model_name}'...")
            # Note: distilgpt2 might not be great at following complex instructions like JSON formatting.
            # The quality of generation will depend heavily on the model and prompt engineering.
            # Using eos_token_id for pad_token_id as set in __init__
            outputs = self.generator(
                prompt,
                max_length=max_length,
                min_length=min_length,
                num_return_sequences=1,
                pad_token_id=self.generator.tokenizer.pad_token_id, # Use the set pad token ID
                eos_token_id=self.eos_token_id, # Ensure generation stops correctly
                truncation=True # Ensure prompt doesn't exceed model max length
            )
            generated_text = outputs[0]['generated_text']
            print("Local generation complete.")

            # Optional: Clean up the output if the model includes the prompt
            # This depends on the specific pipeline/model behavior
            if generated_text.startswith(prompt):
                 generated_text = generated_text[len(prompt):].strip()

            # Ensure we don't return an empty string if cleaning removes everything
            if not generated_text and outputs[0]['generated_text']:
                generated_text = outputs[0]['generated_text'] # Fallback to original if cleaning failed

            # Replace the forbidden token if it appears (though unlikely with distilgpt2)
            # Using <|eos|> as per instructions
            generated_text = generated_text.replace("<|endoftext|>", "<|eos|>")

            return generated_text

        except Exception as e:
            logging.error(f"Error generating content with local model: {e}")
            # Reraise as BookGenerationError for consistent handling upstream
            raise BookGenerationError(f"Failed to generate content locally: {str(e)}")