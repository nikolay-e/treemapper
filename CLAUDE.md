# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TreeMapper is a Python tool that converts directory structures to YAML format, designed specifically for use with Large Language Models (LLMs). It maps entire codebases into structured YAML files, making it easy to analyze code, document projects, and work with AI tools.

## Development Environment

- Python 3.9+ required
- Package dependencies: pathspec, pyyaml

## Building and Installation

```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# Build distribution package
python -m build

# Install from PyPI
pip install treemapper
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_basic.py

# Run specific test
pytest tests/test_basic.py::test_basic_mapping

# Run tests with coverage
pytest --cov=src/treemapper

# Run tests in verbose mode
pytest -v
```

## Linting and Formatting

```bash
# Run flake8 linter
flake8 src/treemapper

# Run black formatter
black src/treemapper

# Run type checking with mypy
mypy src/treemapper

# Run autoflake to remove unused imports
autoflake --remove-all-unused-imports -i src/treemapper/*.py
```

## Project Architecture

The codebase is organized as follows:

- `src/treemapper/`: Main package
  - `treemapper.py`: Entry point and main orchestration
  - `cli.py`: Command-line argument parsing
  - `ignore.py`: Logic for handling ignore patterns (gitignore, treemapperignore)
  - `tree.py`: Core tree building functionality
  - `writer.py`: YAML output formatting and file writing
  - `logger.py`: Logging configuration

The application flow is:
1. Parse command-line arguments (`cli.py`)
2. Set up logging based on verbosity level (`logger.py`)
3. Load ignore patterns from various sources (`ignore.py`)
4. Build the directory tree structure (`tree.py`)
5. Write the tree structure to a YAML file (`writer.py`)

## Running the Application

```bash
# Map current directory
treemapper .

# Map specific directory
treemapper /path/to/dir

# Custom output file
treemapper . -o my-tree.yaml

# Custom ignore patterns
treemapper . -i ignore.txt

# Disable all default ignores
treemapper . --no-default-ignores

# Set verbosity level (0=ERROR, 1=WARNING, 2=INFO, 3=DEBUG)
treemapper . -v 3
```

## Creating a Distribution Package

```bash
# Build package
python -m build

# Create executable with PyInstaller
pyinstaller treemapper.spec
```
