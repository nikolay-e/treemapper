import logging
import os
from pathlib import Path
from typing import List, Optional

import pathspec


def read_ignore_file(file_path: Path) -> List[str]:
    ignore_patterns: List[str] = []
    if not file_path.is_file():
        return ignore_patterns

    try:
        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                stripped = line.rstrip("\n\r")
                if not stripped.strip():
                    continue
                if stripped.startswith("#"):
                    continue
                ignore_patterns.append(stripped.rstrip())
        logging.info(f"Using ignore patterns from {file_path}")
        logging.debug(f"Read ignore patterns from {file_path}: {ignore_patterns}")
    except PermissionError:
        logging.warning(f"Could not read ignore file {file_path}: Permission denied")
    except IOError as e:
        logging.warning(f"Could not read ignore file {file_path}: {e}")
    except UnicodeDecodeError as e:
        logging.warning(f"Could not decode ignore file {file_path} as UTF-8: {e}")

    return ignore_patterns


def _get_output_file_pattern(output_file: Optional[Path], root_dir: Path) -> Optional[str]:
    if not output_file:
        return None

    try:
        resolved_output = output_file.resolve()
        resolved_root = root_dir.resolve()

        if not resolved_output.is_relative_to(resolved_root):
            logging.debug(f"Output file {output_file} is outside root directory {root_dir}")
            return None

        relative_path = resolved_output.relative_to(resolved_root).as_posix()
        return f"/{relative_path}"
    except (ValueError, OSError) as e:
        logging.debug(f"Could not determine relative path for output file {output_file}: {e}")
        return None


def _aggregate_ignore_patterns(root: Path, ignore_filename: str) -> List[str]:
    out: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames.sort()
        filenames.sort()

        if ignore_filename not in filenames:
            continue

        ignore_dir = Path(dirpath)
        rel = "" if ignore_dir == root else ignore_dir.relative_to(root).as_posix()

        for line in read_ignore_file(ignore_dir / ignore_filename):
            neg = line.startswith("!")
            pat = line[1:] if neg else line

            if pat.startswith("/") or "/" in pat:
                anchored_pat = pat.lstrip("/")
                full = f"/{rel}/{anchored_pat}" if rel else f"/{anchored_pat}"
            elif rel:
                full = f"{rel}/**/{pat}"
            else:
                full = pat

            out.append(("!" + full) if neg else full)

    logging.debug(f"Aggregated {len(out)} {ignore_filename} patterns from {root}")
    return out


DEFAULT_IGNORE_PATTERNS = [
    # Version control
    "**/.git/",
    "**/.svn/",
    "**/.hg/",
    # Python
    "**/__pycache__/",
    "**/*.py[cod]",
    "**/*.so",
    "**/.coverage",
    "**/*.egg-info/",
    "**/.eggs/",
    "**/venv/",
    "**/.venv/",
    "**/.tox/",
    "**/.nox/",
    # JavaScript/Node
    "**/node_modules/",
    "**/.npm/",
    # Java/JVM
    "**/target/",
    "**/.gradle/",
    # .NET
    "**/bin/",
    "**/obj/",
    # Go
    "**/vendor/",
    # Generic build/cache
    "**/dist/",
    "**/build/",
    "**/out/",
    "**/.*_cache/",
    # IDE
    "**/.idea/",
    "**/.vscode/",
    # OS files
    "**/.DS_Store",
    "**/Thumbs.db",
]


def get_ignore_specs(
    root_dir: Path,
    custom_ignore_file: Optional[Path] = None,
    no_default_ignores: bool = False,
    output_file: Optional[Path] = None,
) -> pathspec.PathSpec:
    patterns: List[str] = []

    if not no_default_ignores:
        patterns.extend(DEFAULT_IGNORE_PATTERNS)
        patterns.extend(_aggregate_ignore_patterns(root_dir, ".gitignore"))
        patterns.extend(_aggregate_ignore_patterns(root_dir, ".treemapperignore"))

    if custom_ignore_file:
        patterns.extend(read_ignore_file(custom_ignore_file))

    output_pattern = _get_output_file_pattern(output_file, root_dir)
    if output_pattern and output_pattern not in patterns:
        patterns.append(output_pattern)
        logging.debug(f"Adding output file to ignores: {output_pattern}")

    logging.debug(f"Combined ignore patterns: {patterns}")
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def should_ignore(relative_path_str: str, combined_spec: pathspec.PathSpec) -> bool:
    is_ignored = combined_spec.match_file(relative_path_str)
    logging.debug(f"Checking ignore for '{relative_path_str}': {is_ignored}")
    return is_ignored
