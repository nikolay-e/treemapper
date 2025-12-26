import errno
import os
import sys
from contextlib import contextmanager
from typing import Generator


@contextmanager
def _handle_broken_pipe() -> Generator[None, None, None]:
    try:
        yield
        sys.stdout.flush()
    except BrokenPipeError:
        _suppress_broken_pipe()
    except ValueError:
        _suppress_broken_pipe()
    except OSError as e:
        if e.errno in (errno.EINVAL, errno.EPIPE):
            _suppress_broken_pipe()
        raise


def _suppress_broken_pipe() -> None:
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        try:
            os.dup2(devnull, sys.stdout.fileno())
        finally:
            os.close(devnull)
    except Exception:
        pass
    sys.exit(0)


def main() -> None:
    from .cli import parse_args
    from .ignore import get_ignore_specs
    from .logger import setup_logging
    from .tree import TreeBuildContext, build_tree
    from .writer import write_tree_to_file

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

    if args.output_file is None:
        with _handle_broken_pipe():
            write_tree_to_file(directory_tree, args.output_file, args.output_format)
    else:
        write_tree_to_file(directory_tree, args.output_file, args.output_format)


if __name__ == "__main__":
    main()
