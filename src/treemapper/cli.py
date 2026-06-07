from __future__ import annotations

import sys

from diffctx.main import main as _engine_main

from .version import __version__

_VERSION_FLAGS = frozenset({"-v", "--version"})


def _is_version_request(raw: list[str]) -> bool:
    if not raw or raw[0] == "graph":
        return False
    return any(flag in _VERSION_FLAGS for flag in raw)


def main(argv: list[str] | None = None) -> None:
    raw = list(sys.argv[1:] if argv is None else argv)

    if _is_version_request(raw):
        print(f"treemapper {__version__}")
        return

    if argv is None:
        _engine_main()
        return

    saved = sys.argv
    sys.argv = ["treemapper", *raw]
    try:
        _engine_main()
    finally:
        sys.argv = saved


if __name__ == "__main__":
    main()
