import logging

from config import APIConfig, BookGenerationError
from content_generation import ContentGenerator
from book_generator import BookGenerator
from book_writer import BookWriter
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    # Example usage
    try:
        # Initialize API configuration
        api_provider = "openrouter"  # or "gemini"
        APIConfig(api_provider=api_provider)
        
        # Initialize content generator and writer
        content_generator = ContentGenerator()
        writer = BookWriter()
        
        # Create book generator
        book_generator = BookGenerator(content_generator, writer)
        
        # Book title and TOC prompt
        book_title = (
            "string theory industries. The new generation of technologies that become possible after string theory is solved. "
        )
        
        toc_prompt = (
            f"Create a detailed table of contents for a book titled '{book_title}', "
            "including chapter titles and subchapter titles. Format the output as a valid "
            "JSON list of dictionaries, where each dictionary represents a chapter and contains "
            "'title' and 'subchapters' keys. 'subchapters' should be a list of strings."
        )
        
        # Generate the initial table of contents
        book_generator.generate_toc(book_title, toc_prompt)
        
        # Pause to allow TOC modification
        book_generator.pause_and_modify_toc()
        
        # Allow browsing of current book state
        book_generator.browse_book()
        
        # Generate the rest of the book
        result = book_generator.generate_book()
        
        if result:
            print(f"Book successfully generated at: {result}")
        else:
            print("Failed to generate book. Check the logs for details.")
    
    except BookGenerationError as e:
        logging.error(f"Failed to initialize book generation: {e}")

if __name__ == "__main__":
    main()