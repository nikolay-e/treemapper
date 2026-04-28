from __future__ import annotations

from collections.abc import Iterator

from benchmarks.adapters.base import BenchmarkAdapter, BenchmarkInstance, extract_patch_files


class _SWEBenchAdapterBase(BenchmarkAdapter):
    """Shared logic for princeton-nlp SWE-bench Lite and Verified.

    Both share the same row schema: instance_id, repo, base_commit, patch,
    test_patch, problem_statement, hints_text. They differ only in dataset
    path and revision.
    """

    hf_path: str
    hf_split: str = "test"
    revision: str = "main"

    def dataset_revision(self) -> str:
        return f"{self.hf_path}@{self.revision}"

    def _load_raw(self) -> Iterator[dict]:
        from datasets import load_dataset

        ds = load_dataset(self.hf_path, split=self.hf_split, revision=self.revision)
        for row in ds:
            yield dict(row)

    def _normalize(self, row: dict) -> BenchmarkInstance | None:
        patch = row.get("patch") or ""
        if not patch.strip():
            return None
        gold_files = extract_patch_files(patch)
        if not gold_files:
            return None
        repo = row["repo"]
        return BenchmarkInstance(
            instance_id=f"{self.name}::{row['instance_id']}",
            source_benchmark=self.name,
            repo=repo,
            base_commit=row["base_commit"],
            gold_patch=patch,
            gold_files=gold_files,
            language="python",
            problem_statement=row.get("problem_statement"),
            gold_fragments=None,  # Lite/Verified do not ship fragment-level annotations
            difficulty=row.get("difficulty"),
            edit_scope=len(gold_files),
            extra={"hints_text": row.get("hints_text"), "test_patch": row.get("test_patch")},
        )


class SWEBenchLiteAdapter(_SWEBenchAdapterBase):
    name = "swebench_lite"
    hf_path = "princeton-nlp/SWE-bench_Lite"
    revision = "main"


class SWEBenchVerifiedAdapter(_SWEBenchAdapterBase):
    name = "swebench_verified"
    hf_path = "princeton-nlp/SWE-bench_Verified"
    revision = "main"
