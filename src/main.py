# src/main.py
import logging
import argparse
import sys
from pathlib import Path

# Assuming src is in the python path (e.g., via pytest.ini or running as module)
# Removed APIConfig import
from errors import BookGenerationError
from content_generation import ContentGenerator
from book_generator import BookGenerator
from book_writer import BookWriter

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
    # Note: distilgpt2 might struggle with complex JSON generation.
    # Keep the prompt simple or expect potential parsing issues.
    return (
        f"Create a simple table of contents for a book titled '{title}'. "
        "List chapter titles and a few subchapter titles under each. "
        "Format the output as a valid JSON list of dictionaries. "
        "Each dictionary must have 'title' (string) and 'subchapters' (list of strings) keys. "
        "Output ONLY the JSON list. Example: "
        '[{"title": "Chapter 1: Start", "subchapters": ["Topic 1.1", "Topic 1.2"]}, {"title": "Chapter 2: Middle", "subchapters": ["Topic 2.1"]}]'
    )

def parse_arguments():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Generate a book using a local AI model.")
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
    # Removed --provider and --model arguments
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
    # Removed model validation logic based on provider
    args = parser.parse_args()
    return args

def main():
    args = parse_arguments()

    try:
        # --- Initialization ---
        logging.info(f"Initializing with local model...")
        # Initialize ContentGenerator directly (uses default 'distilgpt2')
        content_generator = ContentGenerator()
        writer = BookWriter(output_dir=args.output_dir)
        book_generator = BookGenerator(content_generator, writer)

        # --- TOC Generation ---
        book_title = args.title
        toc_prompt = args.toc_prompt if args.toc_prompt else create_default_toc_prompt(book_title)

        logging.info(f"Generating Table of Contents for '{book_title}'...")
        # Note: TOC generation might be less reliable with distilgpt2.
        # Consider increasing max_length or adjusting the prompt if issues occur.
        book_generator.generate_toc(book_title, toc_prompt)
        logging.info(f"Initial Table of Contents generated and saved to Markdown.")
        book_generator.save_toc() # Always save the initial JSON TOC

        # --- Interactive TOC Modification ---
        if args.interactive_toc:
            logging.info("Pausing for interactive TOC modification.")
            print(f"\n--- INTERACTIVE TOC EDIT ---")
            print(f"The generated Table of Contents has been saved to:")
            # Ensure filepath exists before accessing methods
            if book_generator.filepath:
                print(f"  {book_generator.filepath.with_suffix('.json')}")
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
        logging.error(f"A book generation error occurred: {e}", exc_info=False) # Keep log cleaner
        print(f"\nERROR: {e}")
        sys.exit(1) # Exit with error code
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True) # Log full trace for unexpected
        print(f"\nUNEXPECTED ERROR: {e}")
        sys.exit(1) # Exit with error code


if __name__ == "__main__":
    main()