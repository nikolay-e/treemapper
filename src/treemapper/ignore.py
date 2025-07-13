# src/treemapper/ignore.py
import fnmatch
import logging
import os
from pathlib import Path

# ---> ИЗМЕНЕНИЕ: Добавляем импорты из typing <---
from typing import Dict, List, Optional, Tuple

# pathspec doesn't have type stubs
import pathspec  # type: ignore


def read_ignore_file(file_path: Path) -> List[str]:
    """Read the ignore patterns from the specified ignore file."""
    ignore_patterns = []
    if file_path.is_file():
        try:
            # Try to read directly and handle all possible errors
            with file_path.open("r", encoding="utf-8") as f:
                ignore_patterns = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            logging.info(f"Using ignore patterns from {file_path}")
            logging.debug(f"Read ignore patterns from {file_path}: {ignore_patterns}")
        except PermissionError:
            logging.warning(f"Could not read ignore file {file_path}: Permission denied")
        except IOError as e:
            logging.warning(f"Could not read ignore file {file_path}: {e}")
        except UnicodeDecodeError as e:
            logging.warning(f"Could not decode ignore file {file_path} as UTF-8: {e}")
    return ignore_patterns


def load_pathspec(patterns: List[str], syntax="gitwildmatch") -> pathspec.PathSpec:
    """Load pathspec from a list of patterns."""
    spec = pathspec.PathSpec.from_lines(syntax, patterns)
    logging.debug(f"Loaded pathspec with patterns: {patterns}")
    return spec


# ---> ИЗМЕНЕНИЕ: Заменяем | None на Optional[...] <---
def get_ignore_specs(
    root_dir: Path,
    custom_ignore_file: Optional[Path] = None,
    no_default_ignores: bool = False,
    output_file: Optional[Path] = None,
) -> Tuple[pathspec.PathSpec, Dict[Path, pathspec.PathSpec]]:
    """Get combined ignore specs and git ignore specs."""
    default_patterns = get_default_patterns(root_dir, no_default_ignores, output_file)
    # ---> CHANGE: No longer pass root_dir to get_custom_patterns.
    custom_patterns = get_custom_patterns(custom_ignore_file)

    if no_default_ignores:
        combined_patterns = custom_patterns
        if output_file:
            try:
                resolved_output = output_file.resolve()
                resolved_root = root_dir.resolve()
                if resolved_output.is_relative_to(resolved_root):
                    relative_output_str = resolved_output.relative_to(resolved_root).as_posix()
                    output_pattern = f"/{relative_output_str}"
                    if output_pattern not in combined_patterns:
                        combined_patterns.append(output_pattern)
                        logging.debug(f"Adding output file to ignores (no_default_ignores=True): {output_pattern}")
            except ValueError:
                pass
            except Exception as e:
                logging.warning(f"Could not determine relative path for output file {output_file}: {e}")
    else:
        combined_patterns = default_patterns + custom_patterns

    logging.debug(f"Ignore specs params: no_default_ignores={no_default_ignores}")
    logging.debug(f"Default patterns (used unless no_default_ignores): {default_patterns}")
    logging.debug(f"Custom patterns (-i): {custom_patterns}")
    logging.debug(f"Combined patterns for spec: {combined_patterns}")

    combined_spec = load_pathspec(combined_patterns)
    gitignore_specs = get_gitignore_specs(root_dir, no_default_ignores)

    return combined_spec, gitignore_specs


# ---> ИЗМЕНЕНИЕ: Заменяем | None на Optional[...] <---
def get_default_patterns(root_dir: Path, no_default_ignores: bool, output_file: Optional[Path]) -> List[str]:
    """Retrieve default ignore patterns ONLY IF no_default_ignores is FALSE."""
    if no_default_ignores:
        return []

    # Add common patterns to default ignores
    patterns = [
        "**/__pycache__/",
        "**/*.py[cod]",
        "**/*.so",
        "**/.pytest_cache/",
        "**/.coverage",
        "**/.mypy_cache/",
        "**/*.egg-info/",
        "**/.git/",
        "**/.eggs/",
    ]

    # ---> CHANGE: Look for .treemapperignore in the CURRENT WORKING DIRECTORY, not the root_dir.
    treemapper_ignore_file = Path.cwd() / ".treemapperignore"
    patterns.extend(read_ignore_file(treemapper_ignore_file))

    if output_file:
        try:
            # This logic correctly ignores the output file if it's inside the scanned directory.
            # It should remain as is.
            resolved_output = output_file.resolve()
            resolved_root = root_dir.resolve()
            try:
                relative_output = resolved_output.relative_to(resolved_root)
                output_pattern = f"/{relative_output.as_posix()}"
                patterns.append(output_pattern)
                logging.debug(f"Adding output file to default ignores: {output_pattern}")
            except ValueError:
                logging.debug(f"Output file {output_file} is outside root directory {root_dir}, not adding to default ignores.")
            except Exception as e:
                logging.warning(f"Could not determine relative path for output file {output_file}: {e}")
        except Exception as e:
            logging.warning(f"Could not determine relative path for output file {output_file}: {e}")

    return patterns


# ---> CHANGE: Remove the unused 'root_dir' parameter for clarity.
def get_custom_patterns(custom_ignore_file: Optional[Path]) -> List[str]:
    """Retrieve custom ignore patterns from the file specified with -i."""
    if not custom_ignore_file:
        return []

    # No need to resolve path here, cli.py already did it.
    if custom_ignore_file.is_file():
        return read_ignore_file(custom_ignore_file)
    else:
        # This case is now handled in cli.py, but we keep it as a safeguard.
        logging.warning(f"Custom ignore file '{custom_ignore_file}' not found.")
        return []


def get_gitignore_specs(root_dir: Path, no_default_ignores: bool) -> Dict[Path, pathspec.PathSpec]:
    """Retrieve gitignore specs for all .gitignore files found within root_dir."""
    if no_default_ignores:
        return {}

    # Define common directories to always ignore regardless of ignore patterns
    common_ignore_dirs = {
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        ".git",
        ".eggs",
        "*.egg-info",
        "dist",
        "build",
        ".tox",
        ".coverage",
        ".mypy_cache",
        ".venv",
        "venv",
        "env",
    }

    gitignore_specs = {}
    try:
        for dirpath_str, dirnames, filenames in os.walk(root_dir, topdown=True):
            # Filter out directories we want to skip
            for ignore_dir in list(dirnames):
                # Skip directories that match common ignore patterns
                if ignore_dir in common_ignore_dirs or any(
                    fnmatch.fnmatch(ignore_dir, pattern) for pattern in common_ignore_dirs
                ):
                    dirnames.remove(ignore_dir)
                    logging.debug(f"Skipping ignored directory: {os.path.join(dirpath_str, ignore_dir)}")

            if ".gitignore" in filenames:
                gitignore_path = Path(dirpath_str) / ".gitignore"
                patterns = read_ignore_file(gitignore_path)
                if patterns:
                    gitignore_specs[Path(dirpath_str)] = load_pathspec(patterns)
    except OSError as e:
        logging.warning(f"Error walking directory {root_dir} to find .gitignore files: {e}")

    return gitignore_specs


def should_ignore(relative_path_str: str, combined_spec: pathspec.PathSpec) -> bool:
    """Check if a file or directory should be ignored based on combined pathspec."""
    is_ignored = combined_spec.match_file(relative_path_str)
    logging.debug(f"Checking combined spec ignore for '{relative_path_str}': {is_ignored}")
    return is_ignored
