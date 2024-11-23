import argparse
import sys
from pathlib import Path
from typing import Tuple


def parse_args() -> Tuple[Path, Path, Path, bool, int]:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate a YAML representation of a directory structure.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="The directory to analyze")

    parser.add_argument(
        "-i", "--ignore-file",
        default=None,
        help="Path to the custom ignore file (optional)")

    parser.add_argument(
        "-o", "--output-file",
        default="./directory_tree.yaml",
        help="Path to the output YAML file")

    parser.add_argument(
        "--no-default-ignores",
        action="store_true",
        help="Disable all default ignores (including .gitignore and .treemapperignore)")

    parser.add_argument(
        "-v", "--verbosity",
        type=int,
        choices=range(0, 4),
        default=2,
        metavar="[0-3]",
        help="Set verbosity level (0: ERROR, 1: WARNING, 2: INFO, 3: DEBUG)")

    args = parser.parse_args()

    root_dir = Path(args.directory).resolve()
    if not root_dir.is_dir():
        print(f"Error: The path '{root_dir}' is not a valid directory.")
        sys.exit(1)

    output_file = Path(args.output_file)
    if not output_file.is_absolute():
        output_file = Path.cwd() / output_file

    ignore_file = Path(args.ignore_file) if args.ignore_file else None

    return root_dir, ignore_file, output_file, args.no_default_ignores, args.verbosity
