from __future__ import annotations

import diffctx

from .version import __version__


def main(argv: list[str] | None = None) -> None:
    diffctx.run(argv, prog="treemapper", version=__version__)


if __name__ == "__main__":
    main()
