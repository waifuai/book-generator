# Book Generator with Gemini

This Python script uses Google Gemini to generate books based on a given title and a prompt for the table of contents.  It dynamically creates chapters and subchapters based on the generated TOC, writing the content to a Markdown file.

## Features

* **Dynamic Book Generation:** Creates a book structure based on a user-provided title and TOC prompt.
* **Gemini Integration:** Leverages the power of Google Gemini for content generation.
* **JSON-based TOC:** Uses JSON for structured table of contents generation, making parsing robust.
* **Error Handling:** Includes error handling for JSON parsing, API issues, and missing keys, logging errors to the output file.
* **Markdown Output:** Generates the book in Markdown format for easy readability and conversion.
* **File Organization:** Stores generated books in a dedicated "books" directory.

## Prerequisites

* **Python 3.x:** Make sure you have Python 3 installed.
* **Google Gemini API Key:** You'll need an API key for Google Gemini.
* **Google Generative AI Library:** Install the necessary library using pip:
```bash
pip install google-generativeai
```

## Setup

1. **API Key:** Create a file named `api.txt` in the same directory as the script and paste your Google Gemini API key into it.
2. **Install Dependencies:** Run the following command in your terminal to install the required library:

```bash
pip install google-generativeai
```



## Usage

**Run the script:**
```bash
python main.py
```
The script will generate a book based on the example title and TOC prompt defined within the script. You can modify the `book_title` and `toc_prompt` variables to generate different books.


## Customization

* **`book_title` Variable:** Change this variable to set the desired title of your book.
* **`toc_prompt` Variable:** Modify this prompt to customize the table of contents.  Ensure the prompt instructs Gemini to return valid JSON in the specified format.
* **Gemini Model:** The script is currently configured to use `gemini-1.5-flash-8b`. If you have access to other Gemini models, you can change the `model` variable to use them.  For example, uncomment the line for `gemini-1.5-pro-002` and comment out the `gemini-1.5-flash-8b` line.



## Example TOC Prompt

The provided example prompt generates a table of contents for a book titled "Quantum Biology 2":

```
f"Create a detailed table of contents for a book titled '{book_title}', including chapter titles and subchapter titles.  Format the output as a valid JSON list of dictionaries, where each dictionary represents a chapter and contains 'title' and 'subchapters' keys. 'subchapters' should be a list of strings. For example:  [{{\"title\": \"Chapter 1: Introduction to Quantum Biology\", \"subchapters\": [\"Quantum Mechanics in Biological Systems\", \"The Role of Quantum Tunneling\"]}}, {{\"title\": \"Chapter 2: Photosynthesis and Quantum Effects\", \"subchapters\": [\"Light Harvesting and Energy Transfer\", \"Quantum Coherence in Photosynthesis\"]}}]"
```

Make sure your prompt is clear and specific to get the desired table of contents structure.


## Output

The generated book will be saved as a Markdown file in the `books` directory.  The filename will be the book title converted to lowercase with spaces replaced by underscores. For example, "Quantum Biology 2" will be saved as `quantum_biology_2.md`.


## Error Handling

The script includes error handling for various scenarios, such as invalid JSON responses, API errors, and missing keys in the generated table of contents.  Error messages are printed to the console and also appended to the output Markdown file.


## Future Improvements

* **More Customizable Output:**  Add options to change the output format (e.g., PDF, ePub).
* **Interactive Prompts:** Allow users to interactively refine the generated content.
* **Improved Error Handling:** Implement more robust error handling and recovery mechanisms.

## License

This project is licensed under the [MIT-0 License](../LICENSE).
