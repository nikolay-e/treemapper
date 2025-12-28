import logging
import sys


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    return f"{size_bytes / 1024:.1f} KB"


def main() -> None:
    from .cli import parse_args
    from .clipboard import ClipboardError, copy_to_clipboard
    from .ignore import get_ignore_specs
    from .logger import setup_logging
    from .tree import TreeBuildContext, build_tree
    from .writer import tree_to_string, write_string_to_file, write_tree_to_file

    args = parse_args()
    setup_logging(args.verbosity)

    ctx = TreeBuildContext(
        base_dir=args.root_dir,
        combined_spec=get_ignore_specs(args.root_dir, args.ignore_file, args.no_default_ignores, args.output_file),
        output_file=args.output_file,
        max_depth=args.max_depth,
        no_content=args.no_content,
        max_file_bytes=args.max_file_bytes,
    )

    directory_tree = {
        "name": args.root_dir.name,
        "type": "directory",
        "children": build_tree(args.root_dir, ctx),
    }

    output_content = None
    if args.copy:
        output_content = tree_to_string(directory_tree, args.output_format)
        try:
            byte_size = copy_to_clipboard(output_content)
            print(f"Copied to clipboard ({_format_size(byte_size)})", file=sys.stderr)
        except ClipboardError as e:
            logging.warning(f"Clipboard: {e}")

    if args.copy_only and args.output_file is None:
        return

    if output_content is not None:
        write_string_to_file(output_content, args.output_file, args.output_format)
    else:
        write_tree_to_file(directory_tree, args.output_file, args.output_format)


if __name__ == "__main__":
    main()
