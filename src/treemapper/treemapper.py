import fnmatch
import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Set
import pathspec


def read_ignore_file(file_path: Path) -> List[str]:
    """Read the ignore patterns from the specified ignore file."""
    ignore_patterns = []
    if file_path.is_file():
        with file_path.open('r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    ignore_patterns.append(line)
    return ignore_patterns


def load_pathspec(patterns: List[str], syntax='gitwildmatch') -> pathspec.PathSpec:
    """Load pathspec from a list of patterns."""
    return pathspec.PathSpec.from_lines(syntax, patterns)


def should_ignore(file_path: str, combined_spec: pathspec.PathSpec) -> bool:
    """Check if a file or directory should be ignored based on combined pathspec."""
    return combined_spec.match_file(file_path)


def write_yaml_node(file, node: Dict[str, Any], indent: str = '') -> None:
    """Write a node of the directory tree in YAML format."""
    file.write(f"{indent}- name: {node['name']}\n")
    file.write(f"{indent}  type: {node['type']}\n")

    if 'content' in node:
        file.write(f"{indent}  content: |\n")
        content_lines = node['content'].splitlines()
        for line in content_lines:
            file.write(f"{indent}    {line}\n")

    if 'children' in node and node['children']:
        file.write(f"{indent}  children:\n")
        for child in node['children']:
            write_yaml_node(file, child, indent + '  ')


def build_tree(dir_path: Path, base_dir: Path, combined_spec: pathspec.PathSpec) -> List[Dict[str, Any]]:
    """Build the directory tree structure."""
    tree = []
    try:
        for entry in sorted(dir_path.iterdir()):
            relative_path = entry.relative_to(base_dir).as_posix()
            if should_ignore(relative_path, combined_spec) or not entry.exists():
                continue

            node = {
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file"
            }

            if entry.is_dir() and not entry.is_symlink():
                children = build_tree(entry, base_dir, combined_spec)
                if children:
                    node["children"] = children
            elif entry.is_file():
                try:
                    node["content"] = entry.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    node["content"] = entry.read_bytes().decode('utf-8', errors='replace')
                except IOError:
                    node["content"] = "<unreadable content>"

            tree.append(node)
    except (PermissionError, OSError) as e:
        print(f"Error accessing {dir_path}: {e}", file=sys.stderr)

    return tree


def main():
    parser = argparse.ArgumentParser(description="Generate a YAML representation of a directory structure.")
    parser.add_argument("directory", nargs="?", default=".",
                        help="The directory to analyze (default: current directory)")
    parser.add_argument("-i", "--ignore-file", default=None,
                        help="Path to the custom ignore file (optional)")
    parser.add_argument("-o", "--output-file", default="directory_tree.yaml",
                        help="Path to the output YAML file (default: directory_tree.yaml in the current directory)")
    args = parser.parse_args()

    root_dir = Path(args.directory).resolve()
    if not root_dir.is_dir():
        print(f"Error: The path '{root_dir}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    # Read default .treemapperignore
    default_ignore_file = root_dir / '.treemapperignore'
    default_patterns = read_ignore_file(default_ignore_file)

    # Read custom ignore file if provided
    if args.ignore_file:
        custom_ignore_file = Path(args.ignore_file)
        if not custom_ignore_file.is_absolute():
            custom_ignore_file = root_dir / custom_ignore_file
        if custom_ignore_file.is_file():
            custom_patterns = read_ignore_file(custom_ignore_file)
        else:
            print(f"Warning: Custom ignore file '{custom_ignore_file}' not found. Proceeding without custom ignore patterns.", file=sys.stderr)
            custom_patterns = []
    else:
        custom_patterns = []

    # Read .gitignore patterns
    gitignore_file = root_dir / '.gitignore'
    gitignore_patterns = read_ignore_file(gitignore_file) if gitignore_file.is_file() else []

    # Combine all patterns
    combined_patterns = default_patterns + custom_patterns + gitignore_patterns

    # Load pathspec with combined patterns
    combined_spec = load_pathspec(combined_patterns)

    output_file = Path(args.output_file)
    if not output_file.is_absolute():
        output_file = Path.cwd() / output_file

    directory_tree = {
        "name": root_dir.name,
        "type": "directory",
        "children": build_tree(root_dir, root_dir, combined_spec)
    }

    try:
        with output_file.open('w', encoding='utf-8') as f:
            f.write("name: {}\n".format(directory_tree['name']))
            f.write("type: {}\n".format(directory_tree['type']))
            if 'children' in directory_tree and directory_tree['children']:
                f.write("children:\n")
                for child in directory_tree['children']:
                    write_yaml_node(f, child, '  ')
        print(f"Directory tree saved to {output_file}")
    except IOError as e:
        print(f"Error: Unable to write to file '{output_file}': {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
