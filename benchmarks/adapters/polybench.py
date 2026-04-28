from __future__ import annotations

from collections.abc import Iterator

from benchmarks.adapters.base import (
    BenchmarkAdapter,
    BenchmarkInstance,
    GoldenFragment,
    extract_patch_files,
)


class _PolyBenchAdapterBase(BenchmarkAdapter):
    """Adapter for amazon-science SWE-PolyBench (Java / JS / TS / Python).

    PolyBench ships CST node-level annotations alongside the gold patch when
    available. The annotations live in `gold_nodes` (or `cst_nodes`) and are
    optional; instances without them still expose file-level recall via the
    patch.

    Three configs exist upstream:
    - full (n≈2110)         — `--config default`, uses subclass `PolyBenchAdapter`
    - polybench500 (n=500)  — `PolyBench500Adapter`
    - verified (n=382)      — `PolyBenchVerifiedAdapter`
    """

    hf_path = "AmazonScience/SWE-PolyBench"
    config: str
    revision: str = "main"

    def dataset_revision(self) -> str:
        return f"{self.hf_path}[{self.config}]@{self.revision}"

    def _load_raw(self) -> Iterator[dict]:
        from datasets import load_dataset

        ds = load_dataset(self.hf_path, self.config, split="test", revision=self.revision)
        for row in ds:
            yield dict(row)

    def _normalize(self, row: dict) -> BenchmarkInstance | None:
        patch = row.get("patch") or row.get("gold_patch") or ""
        if not patch.strip():
            return None
        gold_files_from_patch = extract_patch_files(patch)
        if not gold_files_from_patch:
            return None

        fragments = self._extract_cst_fragments(row)
        gold_files = gold_files_from_patch | frozenset(f.path for f in fragments)

        language = (row.get("language") or "unknown").lower()
        return BenchmarkInstance(
            instance_id=f"{self.name}::{row['instance_id']}",
            source_benchmark=self.name,
            repo=row["repo"],
            base_commit=row["base_commit"],
            gold_patch=patch,
            gold_files=gold_files,
            language=language,
            problem_statement=row.get("problem_statement"),
            gold_fragments=tuple(fragments) if fragments else None,
            difficulty=row.get("difficulty"),
            edit_scope=len(gold_files_from_patch),
            extra={
                "test_patch": row.get("test_patch"),
                "hints_text": row.get("hints_text"),
            },
        )

    @staticmethod
    def _extract_cst_fragments(row: dict) -> list[GoldenFragment]:
        """PolyBench CST nodes carry (file, start_line, end_line, node_type).

        The exact field name varies by upstream snapshot; we accept several
        common spellings and tolerate missing or malformed entries.
        """
        raw = row.get("gold_nodes") or row.get("cst_nodes") or row.get("retrieval_targets") or []
        if isinstance(raw, str):
            import json

            try:
                raw = json.loads(raw)
            except (ValueError, TypeError):
                return []
        if not isinstance(raw, list):
            return []
        out: list[GoldenFragment] = []
        for n in raw:
            if not isinstance(n, dict):
                continue
            path = n.get("file") or n.get("path")
            start = n.get("start_line") or n.get("start")
            end = n.get("end_line") or n.get("end")
            if not path or start is None or end is None:
                continue
            out.append(
                GoldenFragment(
                    path=str(path),
                    start_line=int(start),
                    end_line=int(end),
                    kind=str(n.get("node_type") or n.get("kind") or "node"),
                )
            )
        return out


class PolyBenchAdapter(_PolyBenchAdapterBase):
    name = "polybench"
    config = "default"


class PolyBench500Adapter(_PolyBenchAdapterBase):
    name = "polybench500"
    config = "polybench500"


class PolyBenchVerifiedAdapter(_PolyBenchAdapterBase):
    name = "polybench_verified"
    config = "verified"
