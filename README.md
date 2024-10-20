# TreeMapper

TreeMapper is a Python tool designed to convert directory structures into a YAML format, primarily for use with Large Language Models (LLMs).

## Motivation

The main motivation behind TreeMapper is to provide a simple way to convert code repositories or directory structures into a format that can be easily parsed and understood by LLMs. This allows for more effective code analysis, project structure understanding, and potentially more accurate code generation or modification suggestions from AI models.

## Features

- Generates YAML representation of directory structures
- Includes file contents in the output
- Respects `.gitignore` files and a custom ignore list (`.treemapperignore`)
- Provides a format suitable for input to LLMs

## Installation

Install TreeMapper using pip:

```
pip install treemapper
```

## Usage

Basic usage:

```
treemapper [directory_path] [-i IGNORE_FILE] [-o OUTPUT_FILE]
```

- `directory_path`: The directory to analyze (default: current directory)
- `-i IGNORE_FILE, --ignore-file IGNORE_FILE`: Path to a custom ignore file
- `-o OUTPUT_FILE, --output-file OUTPUT_FILE`: Path for the output YAML file

## Example Output

```yaml
name: example_directory
type: directory
children:
  - name: file1.txt
    type: file
    content: |
      This is the content of file1.txt
  - name: subdirectory
    type: directory
    children:
      - name: file2.py
        type: file
        content: |
          def hello_world():
              print("Hello, World!")
```

## Configuration

Use a `.treemapperignore` file in your project directory to exclude specific files or directories. The format is similar to `.gitignore`.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Contact

Nikolay Eremeev - nikolay.eremeev@outlook.com

Project Link: [https://github.com/nikolay-e/TreeMapper](https://github.com/nikolay-e/TreeMapper)