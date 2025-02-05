# Test Suite for Book Generation (`test_main.py`)

This document provides an overview of the test suite (`test_main.py`) for the book generation project.  It covers the tests for the core components, including API configuration, content generation, table of contents management, book writing, and the overall book generation process.  The tests heavily utilize mocking to isolate units of code and ensure reliable testing.

## Overview

The `test_main.py` file contains unit tests for the following classes and their methods:

-   **`APIConfig`**:  Handles loading and configuring the Google Generative AI API key.
-   **`ContentGenerator`**:  Responsible for generating text content using the Google Generative AI API.
-   **`TableOfContents`**:  Manages the structure and representation of the book's table of contents.
-   **`BookWriter`**:  Handles writing the generated content to a Markdown file.
-   **`BookGenerator`**:  Orchestrates the entire book generation process, from creating the table of contents to writing the final book.

The tests are designed to verify:

-   Successful execution of each component's core functionality.
-   Proper error handling for various scenarios (e.g., missing files, invalid JSON, API errors).
-   Correct interaction between different components.
-   Adherence to expected output formats (Markdown, JSON).
-   Correct usage of the `retry` decorator for handling API errors.

## Test Cases and Descriptions

### `TestAPIConfig`

| Test Case                           | Description                                                                                       |
| ------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `test_api_config_init_success`        | Verifies that the API key is loaded correctly from a file and that `genai.configure` is called. |
| `test_api_config_file_not_found`      | Checks for correct error handling (raising `BookGenerationError`) when the API key file is missing. |

### `TestContentGenerator`

| Test Case                           | Description                                                                                                            |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `test_generate_content_success`      | Verifies that `generate_content` successfully returns generated text from a mocked `GenerativeModel`.              |
| `test_generate_content_retry`        | Checks that the `retry` decorator is correctly applied to `generate_content` and that a `BookGenerationError` is raised upon failure. |

### `TestTableOfContents`

| Test Case                                 | Description                                                                                                               |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `test_parse_toc`                          | Verifies the correct parsing of a valid JSON string into `Chapter` objects.                                                   |
| `test_parse_toc_invalid_json`             | Checks for correct error handling (raising `BookGenerationError`) when parsing invalid JSON.                              |
| `test_clean_response`                     | Tests the `_clean_response` method, ensuring correct removal of Markdown code block delimiters.                          |
| `test_assign_numbers`                     | Verifies that chapter numbers are assigned correctly.                                                                     |
| `test_to_markdown`                       | Checks the correct generation of the table of contents in Markdown format.                                                 |
| `test_chapter_toc`                       | Tests the generation of a chapter-specific table of contents in Markdown format.                                       |
| `test_to_json`                           | Verifies the correct conversion of the table of contents to a JSON string.                                                  |
| `test_update_from_json`                  | Checks the updating of the `TableOfContents` object from a JSON string.                                                     |
| `test_update_from_json_invalid_json`      | Checks error handling (raising `BookGenerationError`) when updating from invalid JSON.                                     |

### `TestBookWriter`

| Test Case                           | Description                                                                                                                 |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `test_get_filepath`                  | Verifies the correct generation of the output file path based on the book title.                                           |
| `test_write_chapter`                 | Tests writing a chapter to the Markdown file, including chapter title, content, and chapter-specific table of contents.    |
| `test_write_subchapter`              | Tests writing a subchapter to the Markdown file, including subchapter title, content, and links back to the chapter contents. |
| `test_write_toc`                     | Tests writing the main table of contents to the Markdown file.                                                              |

### `TestBookGenerator`

| Test Case                           | Description                                                                                                                                            |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `test_generate_toc`                  | Tests the successful generation of the table of contents, including writing the TOC to the file.                                                       |
| `test_save_toc`                      | Verifies saving the table of contents to a JSON file.                                                                                                |
| `test_load_toc`                      | Tests loading the table of contents from a JSON file and updating the Markdown file.                                                                   |
| `test_pause_and_modify_toc`          | Checks the functionality for pausing execution, allowing manual TOC modification, and then reloading the modified TOC.                               |
| `test_generate_book_success`        | Tests the successful generation of the entire book, including generating all chapters and subchapters.                                                    |
| `test_generate_book_no_toc`         | Checks for correct error handling (raising `BookGenerationError`) when attempting to generate a book without a table of contents.                    |
| `test_generate_chapter`              | Verifies the generation of a single chapter, including its introduction and all subchapters, and writing the content to the file.                 |
| `test_browse_book_success`          | Tests the successful browsing of the generated book content (reading from the Markdown file).                                                        |
| `test_browse_book_file_not_found`   | Checks for the correct handling of the case where the book file does not exist (displaying an appropriate message to the user).                       |

## Dependencies

The tests rely on the following:

-   `unittest`: Python's built-in unit testing framework.
-   `unittest.mock`:  For creating mock objects and patching dependencies (e.g., `genai`, file I/O).
-   `pathlib`:  For working with file paths in a more object-oriented way.
-   `json`: For handling JSON data.
-   `google.generativeai`:  The Google Generative AI library (though it's heavily mocked in the tests).
-   The project's own modules: `book_generator`, `book_writer`, `table_of_contents`, `content_generation`, and `config`.

## Running the Tests

To run the tests, navigate to the `src/tests` directory in your terminal and execute:

```bash
python -m unittest test_main.py
```

This will run all the test cases defined in `test_main.py` and report the results.