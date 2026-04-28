from __future__ import annotations

import json

import pytest

from benchmarks.adapters import (
    BenchmarkAdapter,
    BenchmarkInstance,
    ContaminationDetector,
    ContextBenchAdapter,
    GoldenFragment,
    SWEBenchLiteAdapter,
    SWEBenchVerifiedAdapter,
)

_SAMPLE_PATCH = """\
diff --git a/src/auth.py b/src/auth.py
index 1234567..89abcde 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -10,3 +10,5 @@ def login(user):
     return token
+
+def logout(user):
+    user.token = None
diff --git a/tests/test_auth.py b/tests/test_auth.py
index aaaaaaa..bbbbbbb 100644
--- a/tests/test_auth.py
+++ b/tests/test_auth.py
@@ -5,3 +5,5 @@ def test_login():
     assert login(u) is not None
+
+def test_logout():
+    pass
"""


def _swebench_row(instance_id: str = "owner__repo-1", repo: str = "owner/repo") -> dict:
    return {
        "instance_id": instance_id,
        "repo": repo,
        "base_commit": "deadbeef" * 5,
        "patch": _SAMPLE_PATCH,
        "test_patch": "",
        "problem_statement": "Add logout method to auth module.",
        "hints_text": "",
    }


class _StubLiteAdapter(SWEBenchLiteAdapter):
    """Lite adapter with HF fetch replaced by an in-memory row list."""

    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def _load_raw(self):
        yield from self._rows


class _StubVerifiedAdapter(SWEBenchVerifiedAdapter):
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def _load_raw(self):
        yield from self._rows


class _StubContextBenchAdapter(ContextBenchAdapter):
    def __init__(self, rows: list[dict], config: str = "default") -> None:
        super().__init__(config=config)
        self._rows = rows

    def _load_raw(self):
        yield from self._rows


def test_swebench_lite_normalizes_row_to_instance():
    adapter = _StubLiteAdapter([_swebench_row()])
    instances = list(adapter.load())
    assert len(instances) == 1
    inst = instances[0]
    assert inst.source_benchmark == "swebench_lite"
    assert inst.instance_id == "swebench_lite::owner__repo-1"
    assert inst.repo == "owner/repo"
    assert inst.language == "python"
    assert inst.gold_files == frozenset({"src/auth.py", "tests/test_auth.py"})
    assert inst.edit_scope == 2
    assert inst.problem_statement == "Add logout method to auth module."
    assert inst.gold_fragments is None  # Lite has no fragment annotations


def test_swebench_verified_uses_distinct_namespace():
    lite = _StubLiteAdapter([_swebench_row()])
    verified = _StubVerifiedAdapter([_swebench_row()])
    lite_inst = next(iter(lite.load()))
    ver_inst = next(iter(verified.load()))
    assert lite_inst.instance_id != ver_inst.instance_id
    assert lite_inst.source_benchmark == "swebench_lite"
    assert ver_inst.source_benchmark == "swebench_verified"


def test_swebench_skips_rows_with_empty_patch():
    row = _swebench_row()
    row["patch"] = ""
    adapter = _StubLiteAdapter([row])
    assert list(adapter.load()) == []


def test_contextbench_extracts_fragments_from_gold_context():
    row = {
        "instance_id": "ctxb-001",
        "repo": "owner/repo",
        "repo_url": "https://github.com/owner/repo",
        "base_commit": "cafebabe" * 5,
        "patch": _SAMPLE_PATCH,
        "language": "python",
        "gold_context": json.dumps(
            [
                {"file": "src/auth.py", "start_line": 10, "end_line": 20, "kind": "hunk"},
                {"file": "src/utils.py", "start_line": 1, "end_line": 30, "kind": "function"},
            ]
        ),
    }
    adapter = _StubContextBenchAdapter([row])
    inst = next(iter(adapter.load()))
    assert inst.source_benchmark == "contextbench"
    assert inst.gold_fragments is not None
    assert len(inst.gold_fragments) == 2
    assert inst.gold_fragments[0] == GoldenFragment(path="src/auth.py", start_line=10, end_line=20, kind="hunk")
    # Gold files include patch-derived plus fragment-derived (utils.py from context).
    assert "src/utils.py" in inst.gold_files
    assert "src/auth.py" in inst.gold_files


def test_contextbench_verified_config_uses_dedicated_name():
    adapter = _StubContextBenchAdapter([], config="contextbench_verified")
    assert adapter.name == "contextbench_verified"


def test_contamination_detector_finds_cross_benchmark_twins():
    shared_repo = "owner/repo"
    lite = _StubLiteAdapter([_swebench_row(repo=shared_repo)])
    verified = _StubVerifiedAdapter([_swebench_row(repo=shared_repo)])
    detector = ContaminationDetector([lite, verified])
    stats = detector.stats()
    assert stats["keys"] == 1, "shared (repo, base_commit) must collapse to one key"
    assert stats["instances"] == 2
    assert stats["collisions"] == 1
    lite_inst = next(iter(lite.load()))
    duplicates = detector.find_duplicates(lite_inst)
    assert duplicates == {"swebench_verified::owner__repo-1"}


def test_contamination_detector_filters_calibration_pool():
    shared_sha = "f00dface" * 5
    held_out_row = _swebench_row(instance_id="held-1")
    held_out_row["base_commit"] = shared_sha
    twin_row = _swebench_row(instance_id="twin-1")
    twin_row["base_commit"] = shared_sha
    safe_row = _swebench_row(instance_id="safe-1")
    safe_row["base_commit"] = "11111111" * 5

    held_out_adapter = _StubVerifiedAdapter([held_out_row])
    pool_adapter = _StubLiteAdapter([twin_row, safe_row])

    detector = ContaminationDetector([held_out_adapter, pool_adapter])
    held_out_ids = {inst.instance_id for inst in held_out_adapter.load()}

    candidates = list(pool_adapter.load())
    safe = detector.filter_calibration_pool(candidates, held_out_ids)
    safe_ids = {c.instance_id for c in safe}
    assert "swebench_lite::safe-1" in safe_ids
    assert "swebench_lite::twin-1" not in safe_ids


def test_dataset_revision_includes_pinned_identifier():
    assert "@" in SWEBenchLiteAdapter().dataset_revision()
    assert "@" in SWEBenchVerifiedAdapter().dataset_revision()
    assert "@" in ContextBenchAdapter().dataset_revision()


def test_benchmark_adapter_is_abstract():
    with pytest.raises(TypeError):
        BenchmarkAdapter()  # type: ignore[abstract]


def test_eval_result_dataclass_carries_optional_fragment_metrics():
    from benchmarks.adapters import EvalResult

    r = EvalResult(
        instance_id="x::1",
        source_benchmark="x",
        file_recall=0.5,
        file_precision=0.5,
    )
    assert r.fragment_recall is None
    assert r.line_f1 is None
    assert r.elapsed_seconds == 0.0


def test_benchmark_instance_is_immutable():
    inst = BenchmarkInstance(
        instance_id="x::1",
        source_benchmark="x",
        repo="o/r",
        base_commit="abc",
        gold_patch="",
        gold_files=frozenset(),
        language="python",
    )
    with pytest.raises(Exception):  # FrozenInstanceError
        inst.repo = "other/repo"  # type: ignore[misc]
