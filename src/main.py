# src/main.py
import logging
import argparse
import sys
from pathlib import Path

# Use relative imports when running as a module
from .errors import BookGenerationError
from .config import APIConfig
from .content_generation import ContentGenerator
from .book_generator import BookGenerator
from .book_writer import BookWriter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout) # Ensure logs go to stdout
    ]
)

def create_default_toc_prompt(title: str) -> str:
    """Creates a default prompt for generating the table of contents."""
    # Prompt suitable for Gemini models
    return (
        f"Create a detailed and logical table of contents for a book titled '{title}'. "
        "Include chapter titles and several relevant subchapter titles under each chapter. "
        "Format the output as a valid JSON list of dictionaries. "
        "Each dictionary must have 'title' (string) and 'subchapters' (list of strings) keys. "
        "Output ONLY the JSON list, without any introductory text or code fences (like ```json). Example: "
        '[{"title": "Chapter 1: Introduction to Topic", "subchapters": ["Subtopic 1.1", "Subtopic 1.2", "Subtopic 1.3"]}, {"title": "Chapter 2: Core Concepts", "subchapters": ["Concept 2.1", "Concept 2.2"]}]'
    )

def parse_arguments():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Generate a book using the Gemini AI model.")
    parser.add_argument(
        "--title",
        type=str,
        required=True,
        help="The title of the book."
    )
    parser.add_argument(
        "--toc-prompt",
        type=str,
        help="A specific prompt for generating the Table of Contents. If omitted, a default prompt is used."
    )
    # Add model selection argument (optional, defaults to the desired preview model)
    parser.add_argument(
        "--model",
        type=str,
        default="models/gemini-2.5-pro-preview-03-25", # Default to the specified model
        help="The Gemini model to use (e.g., 'models/gemini-1.5-flash', 'models/gemini-pro')."
    )
    parser.add_argument(
        "--api-key-file",
        type=str,
        default="~/.api-gemini", # Default API key location
        help="Path to the file containing the Gemini API key (default: ~/.api-gemini)."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default='books',
        help="The directory to save the generated book files (default: books)."
    )
    parser.add_argument(
        "--interactive-toc",
        action='store_true',
        help="Pause execution after TOC generation to allow manual editing of the JSON file."
    )
    parser.add_argument(
        "--browse-after-toc",
        action='store_true',
        help="Display the current book content after TOC generation/loading and before generating chapters."
    )
    args = parser.parse_args()
    return args

def main():
    args = parse_arguments()

    try:
        # --- Initialization ---
        logging.info(f"Initializing with Gemini model '{args.model}'...")
        # Initialize APIConfig first
        api_config = APIConfig(api_key_file=args.api_key_file)
        # Pass config and model name to ContentGenerator
        content_generator = ContentGenerator(config=api_config, model_name=args.model)
        writer = BookWriter(output_dir=args.output_dir)
        book_generator = BookGenerator(content_generator, writer)

        # --- TOC Generation ---
        book_title = args.title
        toc_prompt = args.toc_prompt if args.toc_prompt else create_default_toc_prompt(book_title)

        logging.info(f"Generating Table of Contents for '{book_title}' using {args.model}...")
        book_generator.generate_toc(book_title, toc_prompt)
        logging.info(f"Initial Table of Contents generated and saved to Markdown.")
        book_generator.save_toc() # Always save the initial JSON TOC

        # --- Interactive TOC Modification ---
        if args.interactive_toc:
            logging.info("Pausing for interactive TOC modification.")
            print(f"\n--- INTERACTIVE TOC EDIT ---")
            print(f"The generated Table of Contents has been saved to:")
            if book_generator.filepath:
                toc_json_path = book_generator.filepath.with_suffix('.json')
                print(f"  {toc_json_path}")
                print(f"Please review and modify this JSON file if needed.")
                input("Press Enter to continue after saving your changes...")
                try:
                    book_generator.load_toc() # Reload potentially modified TOC
                    logging.info("Reloaded Table of Contents from JSON.")
                except Exception as e:
                    logging.error(f"Failed to reload TOC after interactive edit: {e}. Continuing with previous TOC.")
            else:
                logging.error("Cannot perform interactive TOC edit: Filepath not set.")


        # --- Interactive Browsing ---
        if args.browse_after_toc:
            logging.info("Browsing current book state (TOC only at this point).")
            print(f"\n--- BROWSE BOOK (TOC) ---")
            if book_generator.filepath and book_generator.filepath.is_file():
                try:
                    with book_generator.filepath.open("r", encoding="utf-8") as f:
                        print(f.read())
                    input("Press Enter to continue...")
                except Exception as e:
                    logging.error(f"Failed to read book file for browsing: {e}")
            else:
                print("Book Markdown file not found yet.")


        # --- Book Generation ---
        logging.info("Starting main book generation process...")
        result_path = book_generator.generate_book()

        if result_path:
            logging.info(f"Book successfully generated at: {result_path}")
            print(f"\nBook generation complete: {result_path}")
        else:
            logging.warning("Book generation process completed, but may have encountered errors. Check logs.")
            print("\nBook generation finished with potential issues. Please check the log output.")

    except BookGenerationError as e:
        logging.error(f"A book generation error occurred: {e}", exc_info=False)
        print(f"\nERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"\nUNEXPECTED ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()