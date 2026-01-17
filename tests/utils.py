# tests/utils.py
from __future__ import annotations

import subprocess
from collections.abc import Hashable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
import tiktoken
import yaml

_ENCODER = tiktoken.get_encoding("cl100k_base")

GARBAGE_FILES = {
    "unrelated_dir/garbage_utils.py": '''def completely_unrelated_garbage_function():
    """This function has nothing to do with any other code."""
    return "garbage_marker_12345"

def another_unused_helper():
    """Another garbage function that should never appear in context."""
    return "unused_marker_67890"

class UnusedGarbageClass:
    """A class with no references anywhere."""
    def useless_method(self):
        return "class_garbage_marker"
''',
    "unrelated_dir/garbage_constants.py": """GARBAGE_CONSTANT_ALPHA = "garbage_alpha_constant"
GARBAGE_CONSTANT_BETA = "garbage_beta_constant"
UNUSED_CONFIG_VALUE = 99999
""",
    "unrelated_dir/garbage_module.js": """export function unusedJsGarbage() {
    return "js_garbage_marker_abc";
}

export const GARBAGE_JS_CONST = "js_const_garbage";
""",
}


def count_tokens(text: str) -> int:
    return len(_ENCODER.encode(text))


def calculate_test_budget(content_tokens: int, overhead_ratio: float = 0.3, min_budget: int = 300) -> int:
    overhead = int(content_tokens * overhead_ratio)
    return max(min_budget, content_tokens + overhead)


def tight_budget(content_tokens: int, min_budget: int = 200) -> int:
    return max(min_budget, int(content_tokens * 1.1))


@dataclass
class DiffTestCase:
    name: str
    initial_files: dict[str, str]
    changed_files: dict[str, str]
    must_include: list[str] = field(default_factory=list)
    must_not_include: list[str] = field(default_factory=list)
    commit_message: str = "Update files"
    overhead_ratio: float = 0.3
    min_budget: int | None = None  # None = auto-calculate based on data size
    add_garbage_files: bool = False

    def calculate_budget(self) -> int:
        fragment_overhead = 18

        changed_tokens = sum(count_tokens(content) for content in self.changed_files.values())
        must_include_tokens = sum(count_tokens(pattern) for pattern in self.must_include)
        base = changed_tokens + must_include_tokens
        overhead = int(base * self.overhead_ratio)

        all_files = {**self.initial_files, **self.changed_files}
        estimated_fragments = int(len(all_files) * 1.5)
        content_tokens = sum(count_tokens(content) for content in all_files.values())
        total_with_overhead = content_tokens + estimated_fragments * fragment_overhead

        # Dynamic min_budget: 85% of total (with overhead) to leave garbage out
        dynamic_min = max(50, int(total_with_overhead * 0.85))

        return max(dynamic_min, base + overhead)

    def all_files(self) -> dict[str, str]:
        result = dict(self.initial_files)
        result.update(self.changed_files)
        return result


class DiffTestRunner:
    def __init__(self, tmp_path: Path):
        self.repo = tmp_path / "test_repo"
        self.repo.mkdir()
        subprocess.run(["git", "init"], cwd=self.repo, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=self.repo, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.repo, capture_output=True, check=True)

    def add_file(self, path: str, content: str) -> Path:
        file_path = self.repo / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def commit(self, message: str) -> str:
        subprocess.run(["git", "add", "-A"], cwd=self.repo, capture_output=True, check=True)
        result = subprocess.run(
            ["git", "commit", "-m", message, "--allow-empty"],
            cwd=self.repo,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            subprocess.run(["git", "commit", "-m", message], cwd=self.repo, capture_output=True, check=True)
        rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo, capture_output=True, text=True, check=True)
        return rev.stdout.strip()

    def run_test_case(self, case: DiffTestCase) -> dict:
        from treemapper.diffctx import build_diff_context

        if case.add_garbage_files:
            for path, content in GARBAGE_FILES.items():
                self.add_file(path, content)
            self.add_file(".treemapperignore", "unrelated_dir/\n")
            self.commit("Add unrelated garbage files")

        for path, content in case.initial_files.items():
            self.add_file(path, content)
        base_sha = self.commit("Initial commit")

        for path, content in case.changed_files.items():
            self.add_file(path, content)
        self.commit(case.commit_message)

        budget = case.calculate_budget()

        context = build_diff_context(
            root_dir=self.repo,
            diff_range=f"{base_sha}..HEAD",
            budget_tokens=budget,
        )

        return context

    def verify_assertions(self, context: dict, case: DiffTestCase) -> None:
        all_content = self._extract_all_content(context)

        for pattern in case.must_include:
            assert pattern in all_content, f"Expected '{pattern}' to be in context, but it was not found"

        for pattern in case.must_not_include:
            assert pattern not in all_content, f"Expected '{pattern}' to NOT be in context, but it was found"

    def _extract_all_content(self, context: dict) -> str:
        parts = []
        for frag in context.get("fragments", []):
            if "content" in frag:
                parts.append(frag["content"])
            if "path" in frag:
                parts.append(frag["path"])
        return "\n".join(parts)


def load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML file and return its contents."""
    try:
        with path.open("r", encoding="utf-8") as f:
            result = yaml.load(f, Loader=yaml.SafeLoader)
            return result if result is not None else {}
    except FileNotFoundError:
        pytest.fail(f"Output YAML file not found: {path}")
        return {}  # This will never execute but satisfies mypy
    except Exception as e:
        pytest.fail(f"Failed to load or parse YAML file {path}: {e}")
        return {}  # This will never execute but satisfies mypy


def get_all_files_in_tree(node: dict[str, Any]) -> set[str]:
    """Recursively get all file and directory names from the loaded tree structure."""

    names: set[str] = set()
    if not isinstance(node, dict) or "name" not in node:
        return names
    names.add(node["name"])
    if "children" in node and isinstance(node["children"], list):
        for child in node["children"]:
            if isinstance(child, dict):
                names.update(get_all_files_in_tree(child))
    return names


def find_node_by_path(tree: dict[str, Any], path_segments: list[str]) -> dict[str, Any] | None:
    """Find a node in the tree by list of path segments relative to root node."""
    current_node = tree
    for segment in path_segments:
        if current_node is None or "children" not in current_node or not isinstance(current_node["children"], list):
            return None
        found_child = None
        for child in current_node["children"]:
            if isinstance(child, dict) and child.get("name") == segment:
                found_child = child
                break
        if found_child is None:
            return None
        current_node = found_child
    return current_node


def make_hashable(obj: Any) -> Hashable:
    """Recursively convert dicts and lists to hashable tuples."""
    if isinstance(obj, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
    if isinstance(obj, list):
        return tuple(make_hashable(item) for item in obj)
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    try:
        hash(obj)
        return obj
    except TypeError:
        return repr(obj)
