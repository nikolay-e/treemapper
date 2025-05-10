# src/treemapper/tree.py
import logging

# os is used for permission checking
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# pathspec doesn't have type stubs
from pathspec import pathspec  # type: ignore

from .ignore import should_ignore


def build_tree(
    dir_path: Path, base_dir: Path, combined_spec: pathspec.PathSpec, gitignore_specs: Dict[Path, pathspec.PathSpec]
) -> List[Dict[str, Any]]:
    """Build the directory tree structure."""
    tree = []
    try:
        for entry in sorted(dir_path.iterdir()):
            try:
                relative_path = entry.relative_to(base_dir).as_posix()
                is_dir_entry = entry.is_dir()
            except OSError as e:
                logging.warning(f"Could not process path for entry {entry}: {e}")
                continue

            if is_dir_entry:
                relative_path_check = relative_path + "/"
            else:
                relative_path_check = relative_path

            if should_ignore(relative_path_check, combined_spec):
                continue

            if should_ignore_git(entry, relative_path_check, gitignore_specs, base_dir):
                continue

            if not entry.exists() or entry.is_symlink():
                logging.debug(f"Skipping '{relative_path_check}': not exists or is symlink")
                continue

            node = create_node(entry, base_dir, combined_spec, gitignore_specs)
            if node:
                tree.append(node)

    except PermissionError:
        logging.warning(f"Permission denied accessing directory {dir_path}")
    except OSError as e:
        logging.warning(f"Error accessing directory {dir_path}: {e}")

    return tree


def should_ignore_git(
    entry: Path, relative_path_check: str, gitignore_specs: Dict[Path, pathspec.PathSpec], base_dir: Path
) -> bool:
    """Check if entry should be ignored based on applicable gitignore specs."""
    if not gitignore_specs:
        return False

    # Track the path's ignore status through the hierarchy - start with not ignored
    is_ignored = False
    closest_rule_path = None
    closest_rule_distance = float("inf")

    # Process in hierarchical order from root to most specific directory
    # Sort gitignore_specs by path length to process parent directories first
    sorted_specs = sorted(gitignore_specs.items(), key=lambda x: len(str(x[0])))

    for git_dir_path, git_spec in sorted_specs:
        try:
            # Only process if this gitignore applies to the entry (entry is in/under gitignore dir)
            if entry == git_dir_path or entry.is_relative_to(git_dir_path):
                # Calculate distance between entry and this gitignore (0 = same dir, 1 = immediate child, etc.)
                try:
                    distance = len(entry.relative_to(git_dir_path).parts)
                except ValueError:
                    continue  # Skip if entry is not relative to git_dir_path

                # Get path relative to the gitignore directory
                rel_path_to_git_dir = entry.relative_to(git_dir_path).as_posix()
                if entry.is_dir() and not rel_path_to_git_dir.endswith("/"):
                    rel_path_to_git_dir += "/"

                # If this is root dir and rel_path is empty, it should be "."
                if not rel_path_to_git_dir:
                    rel_path_to_git_dir = "."

                # Check for special handling of root-anchored patterns
                if git_dir_path == base_dir:
                    # Also check with leading slash for root-anchored patterns
                    anchored_path = "/" + rel_path_to_git_dir if not rel_path_to_git_dir.startswith("/") else rel_path_to_git_dir
                    logging.debug(f"Checking root .gitignore with anchored path '{anchored_path}'")
                    match_anchored = git_spec.match_file(anchored_path)
                    if match_anchored:
                        logging.debug(f"Path '{anchored_path}' matches root-anchored pattern")
                        is_ignored = True
                        closest_rule_path = git_dir_path
                        closest_rule_distance = distance

                # Regular gitignore match
                logging.debug(f"Checking '{rel_path_to_git_dir}' against .gitignore in '{git_dir_path}'")
                match_regular = git_spec.match_file(rel_path_to_git_dir)

                # Update status if this is a more specific rule (closer to the file)
                if match_regular and distance <= closest_rule_distance:
                    # Check if this contains a negation pattern (negative patterns start with !)
                    has_negation = False
                    try:
                        has_negation = any(
                            hasattr(pattern, "pattern") and pattern.pattern.startswith("!") for pattern in git_spec.patterns
                        )
                    except Exception:
                        # Ignore errors when checking for negation patterns
                        pass

                    is_ignored = match_regular
                    closest_rule_path = git_dir_path
                    closest_rule_distance = distance

                    if has_negation:
                        logging.debug(f"Path '{rel_path_to_git_dir}' handled by negation pattern in {git_dir_path}")

                logging.debug(
                    f"After checking .gitignore in '{git_dir_path}', path '{relative_path_check}' is_ignored={is_ignored}"
                )
        except Exception as e:
            logging.warning(f"Error checking gitignore spec from {git_dir_path} against {entry}: {e}")
            continue

    if is_ignored and closest_rule_path is not None:
        try:
            gitignore_location = closest_rule_path.relative_to(base_dir).as_posix() or "."
        except ValueError:
            gitignore_location = str(closest_rule_path)
        logging.debug(f"Ignoring '{relative_path_check}' based on .gitignore in '{gitignore_location}'")

    return is_ignored


def create_node(
    entry: Path, base_dir: Path, combined_spec: pathspec.PathSpec, gitignore_specs: Dict[Path, pathspec.PathSpec]
) -> Optional[Dict[str, Any]]:
    """Create a node for the tree structure. Returns None if node creation fails."""
    try:
        node_type = "directory" if entry.is_dir() else "file"

        node: Dict[str, Any] = {"name": entry.name, "type": node_type}

        if node_type == "directory":
            children = build_tree(entry, base_dir, combined_spec, gitignore_specs)
            if children:
                node["children"] = children
        elif node_type == "file":

            node_content: Optional[str] = None
            try:
                # Try to read the file directly, and handle all possible errors
                # Check permissions first using os.access
                if not os.access(entry, os.R_OK):
                    logging.error(f"Could not read {entry.name}: Permission denied")
                    node_content = "<unreadable content>"
                else:
                    node_content = entry.read_text(encoding="utf-8")
                    if isinstance(node_content, str):
                        cleaned_content = node_content.replace("\x00", "")
                        if cleaned_content != node_content:
                            logging.warning(f"Removed NULL bytes from content of {entry.name}")
                            node_content = cleaned_content
            except PermissionError:
                # Explicitly handle permission errors
                logging.error(f"Could not read {entry.name}: Permission denied")
                node_content = "<unreadable content>"
            except UnicodeDecodeError:
                logging.warning(f"Cannot decode {entry.name} as UTF-8. Marking as unreadable.")
                node_content = "<unreadable content: not utf-8>"
            except IOError as e_read:
                logging.error(f"Could not read {entry.name}: {e_read}")
                node_content = "<unreadable content>"
            except Exception as e_other:
                logging.error(f"Unexpected error reading {entry.name}: {e_other}")
                node_content = "<unreadable content: unexpected error>"

            node["content"] = node_content if node_content is not None else ""

        return node

    except Exception as e:
        logging.error(f"Failed to create node for {entry.name}: {e}")
        return None
