import logging
import os
from pathlib import Path
from typing import List, Dict, Tuple

import pathspec


def read_ignore_file(file_path: Path) -> List[str]:
    """Read the ignore patterns from the specified ignore file."""
    ignore_patterns = []
    if file_path.is_file():
        with file_path.open('r') as f:
            ignore_patterns = [line.strip() for line in f
                               if line.strip() and not line.startswith('#')]
        logging.info(f"Using ignore patterns from {file_path}")
        logging.debug(f"Read ignore patterns from {file_path}: {ignore_patterns}")
    return ignore_patterns


def load_pathspec(patterns: List[str], syntax='gitwildmatch') -> pathspec.PathSpec:
    """Load pathspec from a list of patterns."""
    spec = pathspec.PathSpec.from_lines(syntax, patterns)
    logging.debug(f"Loaded pathspec with patterns: {patterns}")
    return spec


def get_ignore_specs(
    root_dir: Path,
    custom_ignore_file: Path = None,
    no_default_ignores: bool = False,
    output_file: Path = None
) -> Tuple[pathspec.PathSpec, Dict[Path, pathspec.PathSpec]]:
    """Get combined ignore specs and git ignore specs."""
    default_patterns = get_default_patterns(root_dir, no_default_ignores, output_file)
    custom_patterns = get_custom_patterns(root_dir, custom_ignore_file)
    combined_patterns = custom_patterns if no_default_ignores else default_patterns + custom_patterns
    combined_spec = load_pathspec(combined_patterns)
    gitignore_specs = get_gitignore_specs(root_dir, no_default_ignores)

    return combined_spec, gitignore_specs

def get_default_patterns(root_dir: Path, no_default_ignores: bool, output_file: Path) -> List[str]:
    """Retrieve default ignore patterns."""
    if no_default_ignores:
        return []

    patterns = []
    # Add .treemapperignore patterns
    treemapper_ignore_file = root_dir / ".treemapperignore"
    patterns.extend(read_ignore_file(treemapper_ignore_file))

    # Add default git patterns
    patterns.extend([".git/", ".git/**"])

    # Add the output file to ignore patterns
    if output_file:
        try:
            relative_output = output_file.resolve().relative_to(root_dir.resolve())
            patterns.append(str(relative_output))
            if str(relative_output.parent) != ".":
                patterns.append(str(relative_output.parent) + "/")
        except ValueError:
            pass  # Output file is outside root_dir; no need to add to ignores

    return patterns

def get_custom_patterns(root_dir: Path, custom_ignore_file: Path) -> List[str]:
    """Retrieve custom ignore patterns."""
    if not custom_ignore_file:
        return []

    custom_ignore_file = custom_ignore_file if custom_ignore_file.is_absolute() else root_dir / custom_ignore_file
    if custom_ignore_file.is_file():
        return read_ignore_file(custom_ignore_file)

    logging.warning(f"Custom ignore file '{custom_ignore_file}' not found.")
    return []

def get_gitignore_specs(root_dir: Path, no_default_ignores: bool) -> Dict[Path, pathspec.PathSpec]:
    """Retrieve gitignore specs for all .gitignore files in the directory."""
    if no_default_ignores:
        return {}

    gitignore_specs = {}
    for dirpath, _, filenames in os.walk(root_dir):
        if ".gitignore" in filenames:
            gitignore_path = Path(dirpath) / ".gitignore"
            patterns = read_ignore_file(gitignore_path)
            gitignore_specs[Path(dirpath)] = load_pathspec(patterns)

    return gitignore_specs



def should_ignore(file_path: str, combined_spec: pathspec.PathSpec) -> bool:
    """Check if a file or directory should be ignored based on combined pathspec."""
    paths_to_check = [file_path]

    # Add path variations for checking
    if file_path.endswith('/'):
        paths_to_check.append(file_path)

    # Add parent directories with trailing slash
    for part in Path(file_path).parents:
        if part != Path('.'):
            paths_to_check.append(part.as_posix() + '/')

    result = any(combined_spec.match_file(path) for path in paths_to_check)
    logging.debug(
        f"Should ignore '{file_path}': {result} (checking paths: {paths_to_check})")
    return result
