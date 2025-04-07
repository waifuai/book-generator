# Book Generator with Google Gemini

This Python script uses the Google Gemini API (specifically `models/gemini-2.0-flash` by default) to generate books based on a given title and a prompt for the table of contents. It dynamically creates chapters and subchapters based on the generated TOC, writing the content to a Markdown file.
## Features

*   **Dynamic Book Generation:** Creates a book structure based on a user-provided title and TOC prompt.
*   **Gemini API Integration:** Leverages the power of Google Gemini models (using `models/gemini-2.0-flash` by default) for content generation.
*   **Command-Line Interface:** Allows customization of book title, prompts, model, API key location, and output via CLI arguments.
*   **JSON-based TOC:** Uses JSON for structured table of contents generation.
*   **Interactive TOC Editing:** Option to pause and manually edit the generated Table of Contents JSON file.
*   **Error Handling:** Includes error handling for API issues, JSON parsing, and missing keys, logging errors.
*   **Markdown Output:** Generates the book in Markdown format for easy readability and conversion.
*   **File Organization:** Stores generated books in a dedicated "books" directory (customizable via CLI).

## Prerequisites

*   **Python 3.x:** Make sure you have Python 3 installed.
*   **Virtual Environment Tool (`uv`):** This project uses `uv` for environment management. Install it if you haven't already (e.g., `pip install --user uv`).
*   **Gemini API Key:** You need an API key from Google AI Studio (or Google Cloud).
*   **Required Libraries:** The necessary libraries (`google-generativeai`, `pytest`, `tenacity`) will be installed into a virtual environment.

## Setup

1.  **Create API Key File:** Create a file named `.api-gemini` in your home directory (`~/.api-gemini`) and paste your Gemini API key into it. Ensure the file has restrictive permissions. Alternatively, you can specify a different path using the `--api-key-file` argument.

2.  **Create Virtual Environment:** Navigate to the project root directory in your terminal and create a `uv` environment:
    ```bash
    python -m uv venv .venv
    ```

3.  **Install Dependencies:** Install the required packages into the virtual environment using `uv`. This command ensures `pip` is available, installs `uv` inside the venv, and then installs the project dependencies:
    ```bash
    .venv/Scripts/python.exe -m ensurepip ; .venv/Scripts/python.exe -m pip install uv ; .venv/Scripts/python.exe -m uv pip install google-generativeai pytest tenacity
    ```

## Usage

The script is run from the command line using the Python interpreter within the virtual environment.

**Basic Example (using default model and API key path):**

```bash
.venv/Scripts/python.exe -m src.main --title "My Gemini Generated Book"
```

**Example with a custom TOC prompt, specific model, and interactive editing:**

```bash
.venv/Scripts/python.exe -m src.main --title "Interactive Gemini Book" --toc-prompt "Create a 5-chapter TOC about advanced AI..." --model "models/gemini-2.0-flash" --interactive-toc
```

**Command-Line Arguments:**

*   `--title` (str, **required**): The title of the book.
*   `--toc-prompt` (str, optional): A specific prompt for generating the Table of Contents. If omitted, a default prompt is used.
*   `--model` (str, optional, default='models/gemini-2.0-flash'): The Gemini model to use (e.g., 'models/gemini-2.0-flash', 'models/gemini-pro').
*   `--api-key-file` (str, optional, default='~/.api-gemini'): Path to the file containing the Gemini API key.
*   `--output-dir` (str, optional, default='books'): The directory to save the generated book files.
*   `--interactive-toc` (flag, optional): Pause execution after TOC generation to allow manual editing of the `<book_title>.json` file before proceeding.
*   `--browse-after-toc` (flag, optional): Display the current book content (if any) after TOC generation/loading and before generating chapters.

## Customization

Most customization is handled via the command-line arguments described in the **Usage** section. You can change the book title, output directory, Gemini model, API key location, and control interactive steps without modifying the Python code.

## Example TOC Prompt Structure

Ensure your `--toc-prompt` (if provided) instructs the AI to return valid JSON in the specified format: a list of dictionaries, where each dictionary represents a chapter and contains 'title' (string) and 'subchapters' (list of strings) keys. Instruct the model to output *only* the JSON list.

Example snippet for a prompt:
```
... Format the output as a valid JSON list of dictionaries. Each dictionary must have 'title' and 'subchapters' keys. 'subchapters' should be a list of strings. Output ONLY the JSON list, without any introductory text or code fences. For example:  [{\"title\": \"Chapter 1: ...\", \"subchapters\": [\"Sub 1.1\", \"Sub 1.2\"]}, {\"title\": \"Chapter 2: ...\", \"subchapters\": [\"Sub 2.1\"]}]
```

## Output

The generated book will be saved as a Markdown file in the directory specified by `--output-dir` (defaulting to `books`). The filename will be the book title converted to lowercase with spaces replaced by underscores (e.g., `my_gemini_generated_book.md`). A corresponding JSON file containing the final Table of Contents structure will also be saved (e.g., `my_gemini_generated_book.json`).

## Error Handling

The script includes error handling for various scenarios, such as invalid JSON responses, API errors (including rate limits and content blocking), file not found errors for the API key, and missing keys in the generated table of contents. Error messages are printed to the console and logged.

## Future Improvements

*   **More Output Formats:** Add options to generate PDF, ePub, etc.
*   **Content Refinement:** Allow interactive refinement of generated chapter/subchapter content.
*   **Advanced Error Handling:** Implement more robust error recovery and specific handling for different API error types.
*   **Configuration File:** Optionally load settings from a config file instead of only CLI args.

## License

This project is licensed under the [MIT-0 License](LICENSE).
