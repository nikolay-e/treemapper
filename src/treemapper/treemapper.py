import re
import subprocess
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, TextIO, Set


def read_ignore_file(file_path: Path) -> Set[str]:
    """Read the ignore patterns from the specified ignore file."""
    ignore_patterns = set()
    if file_path.is_file():
        with file_path.open('r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    ignore_patterns.add(line)
    return ignore_patterns


def should_ignore(file: str, dir_path: str, ignore_patterns: Set[str]) -> bool:
    """Check if a file should be ignored based on ignore patterns and .gitignore."""
    # Check against ignore patterns
    if any(re.fullmatch(ignore_item.replace('*', '.*'), file) for ignore_item in ignore_patterns):
        return True

    # Check against .gitignore if present
    gitignore_path = Path(dir_path) / '.gitignore'
    if gitignore_path.is_file():
        try:
            result = subprocess.run(['git', 'check-ignore', '-q', str(Path(dir_path) / file)],
                                    check=False, capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            # Git is not installed or not found in PATH
            pass

    return False


def write_yaml_node(file: TextIO, node: Dict[str, Any], indent: str = '') -> None:
    """Write a node of the directory tree in YAML format."""
    file.write(f"{indent}- name: {node['name']}\n")
    file.write(f"{indent}  type: {node['type']}\n")

    if 'content' in node:
        file.write(f"{indent}  content: |\n")
        content_lines = node['content'].splitlines()
        for line in content_lines:
            file.write(f"{indent}    {line}\n")

    if 'children' in node:
        file.write(f"{indent}  children:\n")
        for child in node['children']:
            write_yaml_node(file, child, indent + '  ')


def build_tree(dir_path: str, base_dir: str, ignore_patterns: Set[str]) -> List[Dict[str, Any]]:
    """Build the directory tree structure."""
    tree = []
    try:
        for entry in sorted(Path(dir_path).iterdir()):
            if should_ignore(entry.name, dir_path, ignore_patterns) or not entry.exists():
                continue

            node = {
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file"
            }

            if entry.is_dir() and not entry.is_symlink():
                node["children"] = build_tree(str(entry), base_dir, ignore_patterns)
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
    parser.add_argument("-i", "--ignore-file", default=".treemapperignore",
                        help="Path to the ignore file (default: .treemapperignore in the current directory)")
    parser.add_argument("-o", "--output-file", default="directory_tree.yaml",
                        help="Path to the output YAML file (default: directory_tree.yaml in the current directory)")
    args = parser.parse_args()

    root_dir = Path(args.directory).resolve()
    if not root_dir.is_dir():
        print(f"Error: The path '{root_dir}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    # Use the current working directory for the ignore file by default
    ignore_file = Path(args.ignore_file)
    if not ignore_file.is_absolute():
        ignore_file = Path.cwd() / ignore_file

    if not ignore_file.is_file():
        print(f"Warning: Ignore file '{ignore_file}' not found. Proceeding without ignore patterns.")
        ignore_patterns = set()
    else:
        ignore_patterns = read_ignore_file(ignore_file)

    output_file = Path(args.output_file)
    if not output_file.is_absolute():
        output_file = Path.cwd() / output_file

    directory_tree = {
        "name": root_dir.name,
        "type": "directory",
        "children": build_tree(str(root_dir), str(root_dir), ignore_patterns)
    }

    try:
        with output_file.open('w', encoding='utf-8') as f:
            f.write("name: {}\n".format(directory_tree['name']))
            f.write("type: {}\n".format(directory_tree['type']))
            f.write("children:\n")
            for child in directory_tree['children']:
                write_yaml_node(f, child, '  ')
        print(f"Directory tree saved to {output_file}")
    except IOError as e:
        print(f"Error: Unable to write to file '{output_file}': {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()