# TreeMapper

TreeMapper is a Python tool designed to represent directory structures in YAML format. 

## Features

- Generates YAML representation of directory structures
- Includes file contents in the output
- Respects `.gitignore` files and a custom ignore list (`.treemapperignore`)

## Installation

You can install TreeMapper using pip:

```
pip install treemapper
```

## Usage

After installation, you can run TreeMapper from the command line:

```
treemapper [directory_path] [-i IGNORE_FILE] [-o OUTPUT_FILE]
```

- `directory_path`: The directory to analyze (default: current directory)
- `-i IGNORE_FILE, --ignore-file IGNORE_FILE`: Path to the ignore file (default: `.treemapperignore` in the current directory)
- `-o OUTPUT_FILE, --output-file OUTPUT_FILE`: Path to the output YAML file (default: `directory_tree.yaml` in the current directory)

If no directory path is provided, TreeMapper will analyze the current directory.

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

TreeMapper uses a `.treemapperignore` file to exclude certain files and directories from the analysis. The format is similar to `.gitignore`. You can create this file in the directory you're analyzing or specify a custom ignore file using the `-i` option.

Example `.treemapperignore`:
```
*.log
node_modules
__pycache__
```

## Contact

Nikolay Eremeev - nikolay.eremeev@outlook.com

Project Link: [https://github.com/nikolay-e/TreeMapper](https://github.com/nikolay-e/TreeMapper)