from .cli import parse_args
from .ignore import get_ignore_specs
from .logger import setup_logging
from .tree import build_tree
from .writer import write_tree_to_file


def main() -> None:
    """Main function to run the TreeMapper tool."""
    # Parse command line arguments
    root_dir, ignore_file, output_file, no_default_ignores, verbosity = parse_args()

    # Setup logging
    setup_logging(verbosity)

    # Get ignore specifications
    combined_spec, gitignore_specs = get_ignore_specs(
        root_dir, ignore_file, no_default_ignores, output_file)

    # Build directory tree
    directory_tree = {
        "name": root_dir.name,
        "type": "directory",
        "children": build_tree(root_dir, root_dir, combined_spec, gitignore_specs)
    }

    # Write tree to file
    write_tree_to_file(directory_tree, output_file)


if __name__ == "__main__":
    main()
