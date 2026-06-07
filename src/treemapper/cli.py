from __future__ import annotations

import sys

from .version import __version__

try:
    from diffctx.main import run as _engine_run
except ImportError:  # diffctx < 1.8 — no injectable-identity entry yet
    _engine_run = None

_VERSION_FLAGS = frozenset({"-v", "--version"})


def _is_version_request(raw: list[str]) -> bool:
    if not raw or raw[0] == "graph":
        return False
    return any(flag in _VERSION_FLAGS for flag in raw)


def _run_via_fallback(argv: list[str] | None) -> None:
    from diffctx.main import main as _engine_main

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


def main(argv: list[str] | None = None) -> None:
    if _engine_run is not None:
        _engine_run(argv, prog="treemapper", version=__version__)
        return
    _run_via_fallback(argv)


if __name__ == "__main__":
    main()
