from __future__ import annotations

from typing import Any

from _diffctx import (
    coupling_metrics as _rust_coupling_metrics,
    detect_cycles as _rust_detect_cycles,
    hotspots as _rust_hotspots,
    quotient_graph as _rust_quotient_graph,
    to_mermaid as _rust_to_mermaid,
)

QuotientGraph = Any  # opaque PyQuotientGraph from the Rust extension


def detect_cycles(
    pg: Any,
    level: str = "directory",
    edge_types: set[str] | None = None,
) -> list[list[str]]:
    types = sorted(edge_types) if edge_types else None
    return _rust_detect_cycles(pg, level, types)


def hotspots(
    pg: Any,
    top: int = 10,
    edge_types: set[str] | None = None,
) -> list[tuple[str, float, dict[str, int]]]:
    types = sorted(edge_types) if edge_types else None
    return _rust_hotspots(pg, top, types)


def coupling_metrics(
    pg: Any,
    level: str = "directory",
    edge_types: set[str] | None = None,
) -> list[Any]:
    types = sorted(edge_types) if edge_types else None
    return _rust_coupling_metrics(pg, level, types)


def quotient_graph(pg: Any, level: str = "directory") -> QuotientGraph:
    return _rust_quotient_graph(pg, level)


def to_mermaid(qg: Any, top_n: int = 50) -> str:
    return _rust_to_mermaid(qg, top_n)
