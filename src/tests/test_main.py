"""
Test Suite Entry Point - Main Test Module

This module serves as the main entry point for the test suite. It previously contained
all test classes but they have been refactored into separate files for better
organization and maintainability.

Current status:
- All test classes have been moved to their respective module-specific files
- This file now serves as a reference and potential future integration test location
- Individual test modules are located in the same directory for better organization
- Tests can be run using pytest from the tests directory or project root

Test modules available:
- test_book_generator.py: Tests for BookGenerator coordination
- test_book_writer.py: Tests for file writing and Markdown generation
- test_config.py: Tests for API configuration and client setup
- test_content_generation.py: Tests for AI content generation
- test_table_of_contents.py: Tests for TOC parsing and management
"""

# src/tests/test_main.py
import unittest
# Note: Keep necessary imports if there were module-level fixtures or helpers,
# but in this case, the classes contained all tests.
# Imports like patch, MagicMock, Path, json etc. are now in the specific test files.

# All test classes (TestAPIConfig, TestContentGenerator, TestTableOfContents,
# TestBookWriter, TestBookGenerator) have been moved to their respective files:
# - test_content_generation.py
# - test_table_of_contents.py
# - test_book_writer.py
# - test_book_generator.py

# TestAPIConfig was removed entirely as APIConfig is no longer used.

# This file can remain minimal or be used for integration tests later if needed.

if __name__ == "__main__":
    # This allows running tests specifically from this file if needed,
    # though 'python -m pytest' in the root or 'src/tests' is preferred.
    # Since there are no tests here now, this won't do much.
    print("No tests defined directly in test_main.py. Run pytest in the tests directory.")
    # unittest.main() # No tests to run here anymore