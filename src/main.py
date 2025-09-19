"""
Book Generator Main Entry Point

This module serves as the main entry point and command-line interface for the book generator application.
It handles argument parsing, initialization of all components, and orchestrates the complete book
generation workflow from table of contents creation to final book output.

Key responsibilities:
- Command-line argument parsing and validation
- Application initialization and component setup
- Table of contents generation and management
- Book generation process coordination
- Error handling and user feedback
- Progress reporting and user interaction
"""

# src/main.py
import logging
import argparse
import sys
from pathlib import Path
from typing import Optional

# Use relative imports when running as a module
from .errors import BookGenerationError
from .config import APIConfig
from .config import resolve_default_gemini_model
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

def progress_callback(message: str, progress: float) -> None:
    """Progress callback function for book generation."""
    if progress < 0:
        # Error state
        print(f"❌ {message}")
    elif progress == 0:
        # Starting
        print(f"📋 {message}")
    elif progress == 1.0:
        # Completed
        print(f"✅ {message}")
    elif progress < 1.0:
        # In progress
        percentage = int(progress * 100)
        bar_length = 30
        filled_length = int(bar_length * progress)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        print(f"🔄 [{bar}] {percentage}% - {message}")
    else:
        # General message
        print(f"ℹ️  {message}")


def create_default_toc_prompt(title: str) -> str:
    """Creates a default prompt for generating the table of contents."""
    # Prompt suitable for Gemini models
    return (
        f"Create a detailed and logical table of contents for a book titled '{title}'. "
        "Include 4-6 chapter titles with 2-4 relevant subchapter titles under each chapter. "
        "Format the output as a valid JSON list of dictionaries. "
        "Each dictionary must have 'title' (string) and 'subchapters' (list of strings) keys. "
        "Output ONLY the JSON list, without any introductory text or code fences. Example: "
        '[{"title": "Chapter 1: Introduction to Topic", "subchapters": ["Subtopic 1.1", "Subtopic 1.2", "Subtopic 1.3"]}, {"title": "Chapter 2: Core Concepts", "subchapters": ["Concept 2.1", "Concept 2.2"]}]'
    )

def parse_arguments():
    """Parses command-line arguments with validation."""
    parser = argparse.ArgumentParser(
        description="Generate a book using the Gemini AI model.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --title "My Book Title"
  %(prog)s --title "Advanced AI" --model "gemini-2.5-pro" --interactive-toc
  %(prog)s --title "Custom Book" --toc-prompt "Create a TOC about machine learning..." --output-dir ./my-books
        """
    )

    # Required arguments
    parser.add_argument(
        "--title",
        type=str,
        required=True,
        help="The title of the book to generate (required)."
    )

    # Optional content arguments
    parser.add_argument(
        "--toc-prompt",
        type=str,
        help="A specific prompt for generating the Table of Contents. If omitted, a default prompt is used based on the book title."
    )

    # Model and API configuration
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="The Gemini model to use (e.g., 'gemini-2.5-pro'). If not provided, uses ~/.model-gemini or falls back to 'gemini-2.5-pro'."
    )
    parser.add_argument(
        "--api-key-file",
        type=str,
        default="~/.api-gemini",
        help="Path to the file containing the Gemini API key (default: ~/.api-gemini)."
    )

    # Output configuration
    parser.add_argument(
        "--output-dir",
        type=str,
        default='books',
        help="The directory to save the generated book files (default: books)."
    )

    # Interactive features
    parser.add_argument(
        "--interactive-toc",
        action='store_true',
        help="Pause execution after TOC generation to allow manual editing of the JSON file before proceeding."
    )
    parser.add_argument(
        "--browse-after-toc",
        action='store_true',
        help="Display the current book content (TOC only) after generation/loading and before generating chapters."
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.title.strip():
        parser.error("Book title cannot be empty.")

    if args.toc_prompt and not args.toc_prompt.strip():
        parser.error("TOC prompt cannot be empty if provided.")

    if args.model and not args.model.strip():
        parser.error("Model name cannot be empty if provided.")

    return args
def main():
    """Main entry point for the book generator application."""
    args = parse_arguments()

    try:
        # --- Initialization ---
        print(f"📖 Initializing Book Generator for: '{args.title}'")
        print("=" * 60)

        # Determine model with precedence:
        # 1) CLI --model
        # 2) ~/.model-gemini
        # 3) hardcoded fallback
        chosen_model = args.model or resolve_default_gemini_model()
        logging.info(f"Initializing with Gemini model '{chosen_model}'...")

        print(f"🤖 Using Gemini model: {chosen_model}")
        print(f"🔑 API key file: {args.api_key_file}")
        print(f"📁 Output directory: {args.output_dir}")

        # Initialize APIConfig first
        try:
            api_config = APIConfig(api_key_file=args.api_key_file)
            print("✅ API configuration loaded successfully")
        except BookGenerationError as e:
            print(f"❌ API Configuration Error: {e}")
            print("\n💡 Troubleshooting tips:")
            print("   - Ensure your API key file exists and contains a valid Gemini API key")
            print("   - Check file permissions (should be readable)")
            print("   - Verify the API key is not expired")
            raise

        # Pass config and chosen model name to ContentGenerator
        content_generator = ContentGenerator(config=api_config, model_name=chosen_model)
        writer = BookWriter(output_dir=args.output_dir)
        book_generator = BookGenerator(content_generator, writer, progress_callback=progress_callback)

        # --- TOC Generation ---
        book_title = args.title
        toc_prompt = args.toc_prompt if args.toc_prompt else create_default_toc_prompt(book_title)

        print(f"\n📋 Generating Table of Contents for '{book_title}'...")
        if args.toc_prompt:
            print("Using custom TOC prompt provided via --toc-prompt")
        else:
            print("Using default TOC prompt")

        logging.info(f"Generating Table of Contents for '{book_title}' using {chosen_model}...")
        book_generator.generate_toc(book_title, toc_prompt)
        logging.info("Initial Table of Contents generated and saved to Markdown.")
        book_generator.save_toc() # Always save the initial JSON TOC

        toc_json_path = book_generator.filepath.with_suffix('.json') if book_generator.filepath else None
        if toc_json_path:
            print(f"✅ TOC generated and saved to: {toc_json_path}")

        # --- Interactive TOC Modification ---
        if args.interactive_toc:
            print(f"\n🔧 INTERACTIVE TOC EDIT MODE")
            print("=" * 40)
            print("The generated Table of Contents has been saved to:")
            if book_generator.filepath:
                toc_json_path = book_generator.filepath.with_suffix('.json')
                print(f"  📄 {toc_json_path}")
                print("\n📝 Instructions:")
                print("   1. Open the JSON file above in a text editor")
                print("   2. Review and modify the structure as needed")
                print("   3. Save your changes")
                print("   4. Return here and press Enter to continue")
                input("\nPress Enter to continue after saving your changes...")

                try:
                    book_generator.load_toc() # Reload potentially modified TOC
                    logging.info("Reloaded Table of Contents from JSON.")
                    print("✅ TOC reloaded from JSON file")
                except Exception as e:
                    logging.error(f"Failed to reload TOC after interactive edit: {e}. Continuing with previous TOC.")
                    print(f"⚠️  Warning: Failed to reload TOC from JSON: {e}")
                    print("   Continuing with the previously generated TOC...")
            else:
                logging.error("Cannot perform interactive TOC edit: Filepath not set.")
                print("❌ Error: Cannot perform interactive TOC edit - filepath not set")

        # --- Interactive Browsing ---
        if args.browse_after_toc:
            print(f"\n👀 BROWSE MODE - Current Book Content")
            print("=" * 40)
            if book_generator.filepath and book_generator.filepath.is_file():
                try:
                    with book_generator.filepath.open("r", encoding="utf-8") as f:
                        content = f.read()
                        print(content)
                        print("\n" + "=" * 40)
                    input("Press Enter to continue with book generation...")
                except Exception as e:
                    logging.error(f"Failed to read book file for browsing: {e}")
                    print(f"❌ Error reading book file: {e}")
            else:
                print("📝 No book content available yet (TOC only generated)")

        # --- Book Generation ---
        print("
🚀 Starting main book generation process..."        print("=" * 60)

        result_path = book_generator.generate_book()

        if result_path:
            logging.info(f"Book successfully generated at: {result_path}")
            print("
✅ BOOK GENERATION COMPLETE!"            print("=" * 60)
            print(f"📖 Book saved to: {result_path}")
            print(f"📊 File size: {result_path.stat().st_size if result_path.exists() else 'Unknown'} bytes")

            # Show additional info
            toc_file = result_path.with_suffix('.json')
            if toc_file.exists():
                print(f"📋 TOC file: {toc_file}")

            print("
🎉 Your book has been successfully generated!"        else:
            logging.warning("Book generation process completed, but may have encountered errors. Check logs.")
            print("\n⚠️  Book generation finished with potential issues.")
            print("   Please check the log output above for details.")

    except BookGenerationError as e:
        logging.error(f"A book generation error occurred: {e}", exc_info=False)
        print(f"\n❌ BOOK GENERATION ERROR")
        print("=" * 40)
        print(f"Error: {e}")
        print("\n🔍 Troubleshooting:")
        if "API key" in str(e).lower():
            print("   • Check that your API key file exists and is readable")
            print("   • Verify the API key is valid and not expired")
            print("   • Ensure you have proper internet connection")
        elif "json" in str(e).lower():
            print("   • The AI model returned invalid JSON format")
            print("   • Try running again - this is usually temporary")
            print("   • Consider using a custom TOC prompt with --toc-prompt")
        else:
            print("   • Check the logs above for more detailed error information")
            print("   • Ensure all dependencies are properly installed")
        sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n\n🛑 Book generation interrupted by user")
        print("   Partial files may have been created in the output directory")
        sys.exit(130)

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"\n💥 UNEXPECTED ERROR")
        print("=" * 40)
        print(f"Error: {e}")
        print("\n🐛 This appears to be a bug. Please report this issue with the error details above.")
        print("   Include the full command you ran and any relevant log output.")
        sys.exit(1)


if __name__ == "__main__":
    main()