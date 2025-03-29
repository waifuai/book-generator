# Book Generator with AI

This Python script uses Google Gemini or other models via OpenRouter to generate books based on a given title and a prompt for the table of contents. It dynamically creates chapters and subchapters based on the generated TOC, writing the content to a Markdown file.

## Features

*   **Dynamic Book Generation:** Creates a book structure based on a user-provided title and TOC prompt.
*   **AI Integration:** Leverages the power of Google Gemini or models available through OpenRouter for content generation.
*   **Flexible Configuration:** Uses environment variables for API keys.
*   **Command-Line Interface:** Allows customization of book title, prompts, AI provider, model, and output via CLI arguments.
*   **JSON-based TOC:** Uses JSON for structured table of contents generation, making parsing robust.
*   **Interactive TOC Editing:** Option to pause and manually edit the generated Table of Contents JSON file.
*   **Error Handling:** Includes error handling for JSON parsing, API issues, and missing keys, logging errors to the output file.
*   **Markdown Output:** Generates the book in Markdown format for easy readability and conversion.
*   **File Organization:** Stores generated books in a dedicated "books" directory (customizable via CLI).

## Prerequisites

*   **Python 3.x:** Make sure you have Python 3 installed.
*   **API Keys:** You'll need an API key for either Google Gemini or OpenRouter, depending on the provider you choose.
*   **Required Libraries:** Install the necessary libraries using pip:
    ```bash
    pip install --user google-generativeai python-dotenv requests tenacity
    ```
    *(Note: `google-generativeai` is only strictly needed if using the 'gemini' provider, and `requests` for 'openrouter'. `tenacity` is used for retries.)*

## Setup

1.  **Environment Variables:**
    *   Copy the `.env.example` file to a new file named `.env` in the project root directory.
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file and add your API keys:
        ```dotenv
        GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
        OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY_HERE
        ```
        *(Only the key for the provider you intend to use is required)*.
    *   **Important:** The `.env` file is included in `.gitignore` to prevent accidentally committing your keys.

2.  **Install Dependencies:** If you haven't already, run the following command in your terminal:
    ```bash
    pip install --user google-generativeai python-dotenv requests tenacity
    ```

## Usage

The script is run from the command line, allowing for various customizations.

**Basic Example (using default OpenRouter provider):**

```bash
python src/main.py --title "My Awesome Book Title"
```

**Example using Gemini:**

```bash
python src/main.py --title "Another Book" --provider gemini --model gemini-1.5-flash-latest
```

**Example with a custom TOC prompt and interactive editing:**

```bash
python src/main.py --title "Interactive Book" --toc-prompt "Create a 5-chapter TOC about..." --interactive-toc
```

**Command-Line Arguments:**

*   `--title` (str, **required**): The title of the book.
*   `--toc-prompt` (str, optional): A specific prompt for generating the Table of Contents. If omitted, a default prompt will be constructed using the title.
*   `--provider` (str, optional, choices=['gemini', 'openrouter'], default='openrouter'): The AI provider to use.
*   `--model` (str, optional): The specific model name for the chosen provider (e.g., 'gemini-1.5-flash-latest', 'google/gemini-flash-1.5', 'mistralai/mistral-7b-instruct'). Check provider documentation for available models.
*   `--output-dir` (str, optional, default='books'): The directory to save the generated book files.
*   `--interactive-toc` (flag, optional): Pause execution after TOC generation to allow manual editing of the `<book_title>.json` file before proceeding.
*   `--browse-after-toc` (flag, optional): Display the current book content (if any) after TOC generation/loading and before generating chapters.

## Customization

Most customization is now handled via the command-line arguments described in the **Usage** section. You can easily change the book title, AI provider, specific model, output directory, and control interactive steps without modifying the Python code.

## Example TOC Prompt Structure

Ensure your `--toc-prompt` (if provided) instructs the AI to return valid JSON in the specified format: a list of dictionaries, where each dictionary represents a chapter and contains 'title' (string) and 'subchapters' (list of strings) keys.

Example snippet for a prompt:
```
... Format the output as a valid JSON list of dictionaries, where each dictionary represents a chapter and contains 'title' and 'subchapters' keys. 'subchapters' should be a list of strings. For example:  [{\"title\": \"Chapter 1: ...\", \"subchapters\": [\"Sub 1.1\", \"Sub 1.2\"]}, {\"title\": \"Chapter 2: ...\", \"subchapters\": [\"Sub 2.1\", \"Sub 2.2\"]}]
```

## Output

The generated book will be saved as a Markdown file in the directory specified by `--output-dir` (defaulting to `books`). The filename will be the book title converted to lowercase with spaces replaced by underscores (e.g., `my_awesome_book_title.md`). A corresponding JSON file containing the final Table of Contents structure will also be saved (e.g., `my_awesome_book_title.json`).

## Error Handling

The script includes error handling for various scenarios, such as invalid JSON responses, API errors, missing environment variables, and missing keys in the generated table of contents. Error messages are printed to the console and logged.

## Future Improvements

*   **More Output Formats:** Add options to generate PDF, ePub, etc.
*   **Content Refinement:** Allow interactive refinement of generated chapter/subchapter content.
*   **Advanced Error Handling:** Implement more robust error recovery.
*   **Configuration File:** Optionally support a configuration file (e.g., YAML) in addition to CLI args.

## License

This project is licensed under the [MIT-0 License](LICENSE).
