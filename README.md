# Book Generator with Local AI

This Python script uses a local Hugging Face `transformers` model (specifically `distilgpt2` by default) to generate books based on a given title and a prompt for the table of contents. It dynamically creates chapters and subchapters based on the generated TOC, writing the content to a Markdown file.

## Features

*   **Dynamic Book Generation:** Creates a book structure based on a user-provided title and TOC prompt.
*   **Local AI Integration:** Leverages the power of Hugging Face `transformers` (using `distilgpt2` by default) for content generation, running entirely offline after the model is downloaded.
*   **Command-Line Interface:** Allows customization of book title, prompts, and output via CLI arguments.
*   **JSON-based TOC:** Uses JSON for structured table of contents generation, making parsing robust (though generation quality depends on the model).
*   **Interactive TOC Editing:** Option to pause and manually edit the generated Table of Contents JSON file.
*   **Error Handling:** Includes error handling for JSON parsing, model issues, and missing keys, logging errors.
*   **Markdown Output:** Generates the book in Markdown format for easy readability and conversion.
*   **File Organization:** Stores generated books in a dedicated "books" directory (customizable via CLI).

## Prerequisites

*   **Python 3.x:** Make sure you have Python 3 installed.
*   **Virtual Environment Tool (`uv`):** This project uses `uv` for environment management. Install it if you haven't already (e.g., `pip install --user uv`).
*   **Required Libraries:** The necessary libraries (`transformers`, `torch`, `pytest`, `tenacity`) will be installed into a virtual environment.

## Setup

1.  **Create Virtual Environment:** Navigate to the project root directory in your terminal and create a `uv` environment:
    ```bash
    python -m uv venv .venv
    ```

2.  **Install Dependencies:** Install the required packages into the virtual environment using `uv`. This command ensures `pip` is available, installs `uv` inside the venv, and then installs the project dependencies:
    ```bash
    .venv/Scripts/python.exe -m ensurepip ; .venv/Scripts/python.exe -m pip install uv ; .venv/Scripts/python.exe -m uv pip install transformers torch pytest tenacity
    ```
    *(Note: The first time you run the script or tests, the `distilgpt2` model will be downloaded automatically by the `transformers` library.)*

## Usage

The script is run from the command line using the Python interpreter within the virtual environment.

**Basic Example:**

```bash
.venv/Scripts/python.exe src/main.py --title "My Locally Generated Book"
```

**Example with a custom TOC prompt and interactive editing:**

```bash
.venv/Scripts/python.exe src/main.py --title "Interactive Local Book" --toc-prompt "Create a 3-chapter TOC about local AI models..." --interactive-toc
```

**Command-Line Arguments:**

*   `--title` (str, **required**): The title of the book.
*   `--toc-prompt` (str, optional): A specific prompt for generating the Table of Contents. If omitted, a default prompt is used. *Note: The default `distilgpt2` model may struggle with complex JSON generation; keep prompts simple or be prepared to edit the TOC interactively.*
*   `--output-dir` (str, optional, default='books'): The directory to save the generated book files.
*   `--interactive-toc` (flag, optional): Pause execution after TOC generation to allow manual editing of the `<book_title>.json` file before proceeding.
*   `--browse-after-toc` (flag, optional): Display the current book content (if any) after TOC generation/loading and before generating chapters.

## Customization

Most customization is handled via the command-line arguments described in the **Usage** section. You can change the book title, output directory, and control interactive steps without modifying the Python code. The underlying AI model (`distilgpt2`) can be changed by modifying the `model_name` default in `src/content_generation.py`.

## Example TOC Prompt Structure

Ensure your `--toc-prompt` (if provided) instructs the AI to return valid JSON in the specified format: a list of dictionaries, where each dictionary represents a chapter and contains 'title' (string) and 'subchapters' (list of strings) keys. Keep the structure simple for better results with smaller models like `distilgpt2`.

Example snippet for a prompt:
```
... Format the output as a valid JSON list of dictionaries. Each dictionary must have 'title' and 'subchapters' keys. 'subchapters' should be a list of strings. Output ONLY the JSON list. For example:  [{\"title\": \"Chapter 1: ...\", \"subchapters\": [\"Sub 1.1\", \"Sub 1.2\"]}, {\"title\": \"Chapter 2: ...\", \"subchapters\": [\"Sub 2.1\"]}]
```

## Output

The generated book will be saved as a Markdown file in the directory specified by `--output-dir` (defaulting to `books`). The filename will be the book title converted to lowercase with spaces replaced by underscores (e.g., `my_locally_generated_book.md`). A corresponding JSON file containing the final Table of Contents structure will also be saved (e.g., `my_locally_generated_book.json`).

## Error Handling

The script includes error handling for various scenarios, such as invalid JSON responses, model loading/generation errors, and missing keys in the generated table of contents. Error messages are printed to the console and logged.

## Future Improvements

*   **More Output Formats:** Add options to generate PDF, ePub, etc.
*   **Content Refinement:** Allow interactive refinement of generated chapter/subchapter content.
*   **Advanced Error Handling:** Implement more robust error recovery.
*   **Model Selection:** Re-introduce CLI argument to select different local models.
*   **GPU Support:** Add option/detection for running inference on GPU if available.

## License

This project is licensed under the [MIT-0 License](LICENSE).
