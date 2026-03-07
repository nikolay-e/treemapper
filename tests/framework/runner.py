from __future__ import annotations

import subprocess
from pathlib import Path

from tests.conftest import GARBAGE_FILES, GARBAGE_MARKERS
from tests.framework.types import YamlTestCase


def _match_path(candidate: str, target: str) -> bool:
    return candidate == target or candidate.endswith(f"/{target}")


def _format_fragment_summary(context: dict) -> str:
    lines = []
    for frag in context.get("fragments", []):
        path = frag.get("path", "?")
        kind = frag.get("kind", "?")
        symbol = frag.get("symbol", "")
        frag_lines = frag.get("lines", "?")
        content = frag.get("content", "")
        tokens = len(content.split())
        label = f"  {path}:{frag_lines} ({kind}"
        if symbol:
            label += f" {symbol}"
        label += f", ~{tokens}w)"
        lines.append(label)
    return "\n".join(lines)


class YamlTestRunner:
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

    def run_test_case(self, case: YamlTestCase) -> dict:
        from treemapper.diffctx import build_diff_context

        if case.add_garbage_files:
            for path, content in GARBAGE_FILES.items():
                self.add_file(path, content)
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

    def verify_assertions(self, context: dict, case: YamlTestCase) -> None:
        fragments = context.get("fragments", [])
        fragment_paths = self._extract_fragment_paths(context)
        all_content = self._extract_all_content(context)
        content_by_file = self._extract_content_by_file(context)
        unique_files = sorted(set(fragment_paths))

        def diag():
            return f"Selected fragments:\n{_format_fragment_summary(context)}"

        for pattern in case.must_include:
            assert pattern in all_content, (
                f"[{case.name}] Expected pattern not found in context.\n" f"Pattern: '{pattern}'\n" f"{diag()}"
            )

        for file_path in case.must_include_files:
            assert any(_match_path(p, file_path) for p in fragment_paths), (
                f"[{case.name}] Expected file '{file_path}' in fragments.\n" f"{diag()}"
            )

        for content_block in case.must_include_content:
            normalized_block = content_block.rstrip("\n")
            assert normalized_block in all_content, (
                f"[{case.name}] Expected content block not found.\n" f"Expected:\n  {normalized_block[:300]}\n" f"{diag()}"
            )

        self._verify_content_from(case, content_by_file, diag)

        for pattern in case.must_not_include:
            assert pattern not in all_content, f"[{case.name}] Unwanted pattern found in context: '{pattern}'\n" f"{diag()}"

        for file_path in case.must_not_include_files:
            assert not any(_match_path(p, file_path) for p in fragment_paths), (
                f"[{case.name}] File '{file_path}' should NOT be in fragments.\n" f"{diag()}"
            )

        if case.max_fragments is not None:
            assert len(fragments) <= case.max_fragments, (
                f"[{case.name}] Too many fragments: {len(fragments)} > {case.max_fragments}\n" f"{diag()}"
            )

        if case.max_files is not None:
            assert len(unique_files) <= case.max_files, (
                f"[{case.name}] Too many files: {len(unique_files)} > {case.max_files}\n" f"{diag()}"
            )

        if case.add_garbage_files and not case.skip_garbage_check:
            for marker in GARBAGE_MARKERS:
                assert marker not in all_content, f"[{case.name}] Garbage marker '{marker}' leaked into context.\n" f"{diag()}"

    def _verify_content_from(self, case: YamlTestCase, content_by_file: dict[str, str], diag) -> None:
        for file_path, snippets in case.must_include_content_from.items():
            file_content = None
            for p, c in content_by_file.items():
                if _match_path(p, file_path):
                    file_content = c
                    break
            if file_content is None:
                raise AssertionError(
                    f"[{case.name}] File '{file_path}' not in selected fragments "
                    f"(needed for must_include_content_from).\n"
                    f"{diag()}"
                )
            for snippet in snippets:
                normalized = snippet.rstrip("\n")
                assert normalized in file_content, (
                    f"[{case.name}] Content from '{file_path}' missing expected snippet.\n"
                    f"Expected:\n  {normalized[:300]}\n"
                    f"File content (first 500 chars):\n  {file_content[:500]}\n"
                    f"{diag()}"
                )

    def _extract_all_content(self, context: dict) -> str:
        parts = []
        for frag in context.get("fragments", []):
            if "content" in frag:
                parts.append(frag["content"])
            if "path" in frag:
                parts.append(frag["path"])
        return "\n".join(parts)

    def _extract_fragment_paths(self, context: dict) -> list[str]:
        return [frag["path"] for frag in context.get("fragments", []) if "path" in frag]

    def _extract_content_by_file(self, context: dict) -> dict[str, str]:
        by_file: dict[str, list[str]] = {}
        for frag in context.get("fragments", []):
            path = frag.get("path", "")
            if path not in by_file:
                by_file[path] = []
            if "content" in frag:
                by_file[path].append(frag["content"])
        return {path: "\n".join(parts) for path, parts in by_file.items()}
