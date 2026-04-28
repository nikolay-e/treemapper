from __future__ import annotations

from collections.abc import Iterator

from benchmarks.adapters.base import BenchmarkAdapter, BenchmarkInstance, extract_patch_files

# Best-effort language inference for Multi-SWE-bench rows that do not carry
# an explicit `language` field. Map repo namespace → language; the upstream
# dataset is partitioned this way (one repo class per language subset).
_LANG_FROM_EXTENSION: dict[str, str] = {
    "java": "java",
    "kt": "kotlin",
    "ts": "typescript",
    "tsx": "typescript",
    "js": "javascript",
    "jsx": "javascript",
    "go": "go",
    "rs": "rust",
    "c": "c",
    "h": "c",
    "cc": "cpp",
    "cpp": "cpp",
    "cxx": "cpp",
    "hpp": "cpp",
    "py": "python",
}


def _infer_language(row: dict, gold_files: frozenset[str]) -> str:
    explicit = row.get("language")
    if explicit:
        return str(explicit).lower()
    counts: dict[str, int] = {}
    for path in gold_files:
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        lang = _LANG_FROM_EXTENSION.get(ext)
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    if not counts:
        return "unknown"
    return max(counts.items(), key=lambda kv: kv[1])[0]


class _MultiSWEBenchAdapterBase(BenchmarkAdapter):
    """Adapter for ByteDance Multi-SWE-bench family.

    Three configs:
    - full (n≈1632)  — `MultiSWEBenchAdapter`
    - mini (n=400)   — `MultiSWEBenchMiniAdapter`
    - flash (n=300)  — `MultiSWEBenchFlashAdapter`

    Languages: Java, TS, JS, Go, Rust, C, C++ (and minor others). Schema is
    SWE-bench-shaped (instance_id, repo, base_commit, patch, problem_statement)
    with an optional `language` field. When `language` is missing we infer
    from the dominant gold-file extension.
    """

    hf_path = "bytedance-research/Multi-SWE-bench"
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
        patch = row.get("patch") or ""
        if not patch.strip():
            return None
        gold_files = extract_patch_files(patch)
        if not gold_files:
            return None
        return BenchmarkInstance(
            instance_id=f"{self.name}::{row['instance_id']}",
            source_benchmark=self.name,
            repo=row["repo"],
            base_commit=row["base_commit"],
            gold_patch=patch,
            gold_files=gold_files,
            language=_infer_language(row, gold_files),
            problem_statement=row.get("problem_statement"),
            gold_fragments=None,  # Multi-SWE-bench is patch-only
            difficulty=row.get("difficulty"),
            edit_scope=len(gold_files),
            extra={
                "test_patch": row.get("test_patch"),
                "hints_text": row.get("hints_text"),
            },
        )


class MultiSWEBenchAdapter(_MultiSWEBenchAdapterBase):
    name = "multi_swebench"
    config = "default"


class MultiSWEBenchMiniAdapter(_MultiSWEBenchAdapterBase):
    name = "multi_swebench_mini"
    config = "mini"


class MultiSWEBenchFlashAdapter(_MultiSWEBenchAdapterBase):
    name = "multi_swebench_flash"
    config = "flash"
