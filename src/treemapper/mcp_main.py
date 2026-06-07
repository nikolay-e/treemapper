from __future__ import annotations

from diffctx.mcp.__main__ import main as _engine_mcp_main


def main() -> None:
    try:
        _engine_mcp_main(prog="treemapper-mcp", extra="treemapper[mcp]")
    except TypeError:  # diffctx < 1.8 — no injectable identity
        _engine_mcp_main()


if __name__ == "__main__":
    main()
