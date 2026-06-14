from __future__ import annotations

from diffctx.mcp.__main__ import main as _engine_mcp_main


def main() -> None:
    _engine_mcp_main(prog="treemapper-mcp", extra="treemapper[mcp]")


if __name__ == "__main__":
    main()
