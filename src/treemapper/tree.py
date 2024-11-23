import logging
from pathlib import Path
from typing import Dict, List, Any

from pathspec import pathspec

from .ignore import should_ignore


def build_tree(dir_path: Path,
               base_dir: Path,
               combined_spec: pathspec.PathSpec,
               gitignore_specs: Dict[Path, pathspec.PathSpec]) -> List[Dict[str, Any]]:
    """Build the directory tree structure."""
    tree = []
    try:
        for entry in sorted(dir_path.iterdir()):
            relative_path = entry.relative_to(base_dir).as_posix()
            if entry.is_dir():
                relative_path += '/'

            # Skip .git directory
            if entry.name == '.git':
                logging.debug(f"Skipping .git directory: {relative_path}")
                continue

            # Check combined ignore patterns
            if should_ignore(relative_path, combined_spec):
                logging.debug(f"Ignoring '{relative_path}' based on combined_spec")
                continue

            # Check gitignore patterns
            if should_ignore_git(entry, relative_path, gitignore_specs):
                continue

            if not entry.exists() or entry.is_symlink():
                logging.debug(f"Skipping '{relative_path}': not exists or is symlink")
                continue

            node = create_node(entry, base_dir, combined_spec, gitignore_specs)
            if node:
                tree.append(node)

    except (PermissionError, OSError) as e:
        logging.warning(f"Error accessing {dir_path}: {e}")

    return tree


def should_ignore_git(entry: Path, relative_path: str,
                      gitignore_specs: Dict[Path, pathspec.PathSpec]) -> bool:
    """Check if entry should be ignored based on gitignore specs."""
    for git_dir, git_spec in gitignore_specs.items():
        try:
            if entry.is_relative_to(git_dir):
                rel_path = entry.relative_to(git_dir).as_posix()
                if entry.is_dir():
                    rel_path += '/'
                if git_spec.match_file(rel_path):
                    logging.debug(
                        f"Ignoring '{relative_path}' based on .gitignore in '{git_dir}'")
                    return True
        except ValueError:
            continue
    return False


def create_node(entry: Path, base_dir: Path, combined_spec: pathspec.PathSpec,
                gitignore_specs: Dict[Path, pathspec.PathSpec]) -> Dict[str, Any]:
    """Create a node for the tree structure."""
    node = {
        "name": entry.name,
        "type": "directory" if entry.is_dir() else "file"
    }

    if entry.is_dir():
        children = build_tree(entry, base_dir, combined_spec, gitignore_specs)
        if children:
            node["children"] = children
    elif entry.is_file():
        try:
            node["content"] = entry.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            node["content"] = entry.read_bytes().decode('utf-8', errors='replace')
        except IOError:
            node["content"] = "<unreadable content>"

    return node
