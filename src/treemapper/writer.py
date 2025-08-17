import logging

# os is used for access permission checking
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, TextIO


def write_yaml_node(file: TextIO, node: Dict[str, Any], indent: str = "") -> None:
    """Write a node of the directory tree in YAML format."""
    # Escape filename with double quotes and handle any special characters
    # This prevents issues with filenames like 'true', 'false', numbers, or names with special chars
    name = str(node["name"]).replace('"', '\\"')  # Escape any double quotes in the name
    file.write(f'{indent}- name: "{name}"\n')
    file.write(f"{indent}  type: {node['type']}\n")

    if "content" in node:
        file.write(f"{indent}  content: |\n")
        for line in node["content"].splitlines():
            file.write(f"{indent}    {line}\n")

    if "children" in node and node["children"]:
        file.write(f"{indent}  children:\n")
        for child in node["children"]:
            write_yaml_node(file, child, indent + "  ")


def write_tree_to_file(tree: Dict[str, Any], output_file: Optional[Path]) -> None:
    """Write the complete tree to a YAML file or stdout."""

    def write_tree_content(f: TextIO) -> None:
        """Write the tree content to the given file handle."""
        # Properly quote the root name as well
        name = str(tree["name"]).replace('"', '\\"')
        f.write(f'name: "{name}"\n')
        f.write(f"type: {tree['type']}\n")
        if "children" in tree and tree["children"]:
            f.write("children:\n")
            for child in tree["children"]:
                write_yaml_node(f, child, "  ")

    if output_file is None:
        # Write to stdout with proper UTF-8 encoding
        # On Windows, sys.stdout might use cp1252 encoding which can't handle Unicode
        import io

        # Use TextIOWrapper to ensure UTF-8 encoding for stdout
        utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="")
        write_tree_content(utf8_stdout)
        utf8_stdout.flush()
        logging.info("Directory tree written to stdout")
    else:
        # Write to file
        try:
            # Create parent directories if they don't exist
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # For directories, try an early write test
            if output_file.is_dir():
                logging.error(f"Unable to write to file '{output_file}': Is a directory")
                raise IOError(f"Is a directory: {output_file}")

            # Check write permissions using os.access
            if not os.access(output_file.parent, os.W_OK):
                logging.error(f"Unable to write to file '{output_file}': Permission denied for directory")
                raise IOError(f"Permission denied for directory: {output_file.parent}")

            # Test write permissions directly by attempting to open the file
            try:
                test_handle = output_file.open("w", encoding="utf-8")
                test_handle.close()
            except (PermissionError, IOError):
                logging.error(f"Unable to write to file '{output_file}': Permission denied")
                raise IOError(f"Permission denied: {output_file}")

            with output_file.open("w", encoding="utf-8") as f:
                write_tree_content(f)
            logging.info(f"Directory tree saved to {output_file}")
        except IOError as e:
            logging.error(f"Unable to write to file '{output_file}': {e}")
            raise
