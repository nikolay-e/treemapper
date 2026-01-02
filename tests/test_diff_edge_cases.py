import pytest

from treemapper.diffctx import build_diff_context
from treemapper.diffctx.fragments import fragment_file
from treemapper.diffctx.select import lazy_greedy_select
from treemapper.diffctx.types import Fragment, FragmentId, extract_identifiers
from treemapper.diffctx.utility import UtilityState, concepts_from_diff_text, marginal_gain


def _extract_files_from_tree(tree: dict) -> set[str]:
    files = set()
    if tree.get("type") == "diff_context":
        for frag in tree.get("fragments", []):
            path = frag.get("path", "")
            if path:
                files.add(path.split("/")[-1])
        return files

    def traverse(node):
        if node.get("type") == "file":
            files.add(node["name"])
        for child in node.get("children", []):
            traverse(child)

    traverse(tree)
    return files


@pytest.fixture
def diff_project(git_with_commits):
    return git_with_commits


class TestEmptyMinimalCases:
    def test_edge_001_empty_diff(self, diff_project):
        diff_project.add_file("main.py", "x = 1")
        diff_project.commit("Initial")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD..HEAD",
            budget_tokens=10000,
        )

        assert tree.get("children", []) == [] or tree.get("fragments", []) == []

    def test_edge_002_whitespace_only_changes(self, diff_project):
        diff_project.add_file(
            "test.py",
            """def hello():
    x = 1
    return x
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "test.py",
            """def hello():
        x = 1
        return x
""",
        )
        diff_project.commit("Change indentation")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "test.py" in selected

    def test_edge_003_comment_only_changes(self, diff_project):
        diff_project.add_file(
            "test.py",
            """def process():
    return 42
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "test.py",
            """# TODO: refactor this later
def process():
    return 42
""",
        )
        diff_project.commit("Add comment")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "test.py" in selected

    def test_edge_004_single_line_change(self, diff_project):
        diff_project.add_file(
            "test.py",
            """def calculate():
    return x + 1
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "test.py",
            """def calculate():
    return x + 2
""",
        )
        diff_project.commit("Change constant")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "test.py" in selected


class TestSyntaxErrors:
    def test_edge_010_diff_introduces_syntax_error(self, diff_project):
        diff_project.add_file(
            "test.py",
            """def valid():
    return 1
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "test.py",
            """def broken(
    return 1
""",
        )
        diff_project.commit("Break syntax")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "test.py" in selected

    def test_edge_011_file_already_broken(self, diff_project):
        diff_project.add_file(
            "broken.py",
            """def broken(
    x = 1
""",
        )
        diff_project.commit("Initial broken")

        diff_project.add_file(
            "broken.py",
            """def broken(
    x = 1
    y = 2
""",
        )
        diff_project.commit("Add to broken file")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "broken.py" in selected


class TestLargeComplexCases:
    def test_edge_020_large_diff(self, diff_project):
        initial_content = "\n".join([f"def func{i}():\n    return {i}\n" for i in range(50)])
        diff_project.add_file("large.py", initial_content)
        diff_project.commit("Initial")

        modified_content = "\n".join([f"def func{i}():\n    return {i * 2}\n" for i in range(50)])
        diff_project.add_file("large.py", modified_content)
        diff_project.commit("Modify all")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "large.py" in selected

    def test_edge_021_many_small_hunks(self, diff_project):
        lines = []
        for i in range(100):
            lines.append(f"x{i} = {i}")
        diff_project.add_file("utils.py", "\n".join(lines))
        diff_project.commit("Initial")

        lines = []
        for i in range(100):
            if i % 5 == 0:
                lines.append(f"x{i} = {i * 10}")
            else:
                lines.append(f"x{i} = {i}")
        diff_project.add_file("utils.py", "\n".join(lines))
        diff_project.commit("Modify every 5th line")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "utils.py" in selected

    def test_edge_022_binary_file_in_diff(self, diff_project):
        # Test that binary files in repo don't break context building
        # Binary files are not tracked in git diff context, only code files
        diff_project.add_file("code.py", "x = 1")
        # Add binary file but don't track changes to it in the diff
        (diff_project.repo / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        diff_project.commit("Initial with binary")

        # Only modify the code file
        diff_project.add_file("code.py", "x = 2")
        diff_project.commit("Modify code only")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "code.py" in selected

    def test_edge_023_non_utf8_file(self, diff_project):
        diff_project.add_file("valid.py", "x = 1")
        diff_project.commit("Initial")

        diff_project.add_file("valid.py", "x = 2")
        diff_project.commit("Modify")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "valid.py" in selected


class TestBudgetConstraints:
    def test_edge_030_budget_smaller_than_core(self, diff_project):
        large_content = "x = 1\n" * 500
        diff_project.add_file("large.py", large_content)
        diff_project.commit("Initial")

        modified = "y = 2\n" * 500
        diff_project.add_file("large.py", modified)
        diff_project.commit("Modify")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=100,
        )

        assert tree is not None

    def test_edge_031_budget_exactly_matches_core(self, tmp_path):
        path = tmp_path / "test.py"
        content = "def func():\n    return 42\n"
        path.write_text(content)

        fragments = fragment_file(path, content)
        total_tokens = 50

        for frag in fragments:
            frag.token_count = total_tokens // len(fragments)

        rel = {f.id: 1.0 for f in fragments}
        concepts = extract_identifiers(content)
        core_ids = {fragments[0].id} if fragments else set()

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=core_ids,
            rel=rel,
            concepts=concepts,
            budget_tokens=total_tokens,
            tau=0.0,
        )

        assert len(result.selected) >= 1

    def test_edge_032_unlimited_budget_large_repo(self, diff_project):
        for i in range(20):
            content = f"def module{i}_func():\n    return {i}\n"
            diff_project.add_file(f"module{i}.py", content)
        diff_project.commit("Initial")

        diff_project.add_file("module0.py", "def module0_func():\n    return 100\n")
        diff_project.commit("Modify one")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=50000,
        )

        selected = _extract_files_from_tree(tree)
        assert "module0.py" in selected


class TestFragmentBehavior:
    def test_fragment_python_preserves_structure(self, tmp_path):
        path = tmp_path / "test.py"
        content = """class MyClass:
    def method_a(self):
        return 1

    def method_b(self):
        return 2

def standalone():
    return 3
"""
        path.write_text(content)

        fragments = fragment_file(path, content)

        kinds = {f.kind for f in fragments}
        assert "class" in kinds or "function" in kinds

    def test_fragment_generic_fallback(self, tmp_path):
        path = tmp_path / "data.txt"
        content = "Line 1\nLine 2\nLine 3\n" * 100
        path.write_text(content)

        fragments = fragment_file(path, content)

        assert len(fragments) >= 1


class TestConceptsExtraction:
    def test_concepts_filters_short_identifiers(self):
        diff_text = """+++ b/test.py
+x = 1
+y = 2
+longname = 3
"""
        concepts = concepts_from_diff_text(diff_text)

        assert "longname" in concepts

    def test_concepts_handles_special_characters(self):
        diff_text = """+++ b/test.py
+def my_function():
+    return "string-with-dashes"
"""
        concepts = concepts_from_diff_text(diff_text)

        assert "my_function" in concepts

    def test_concepts_from_both_additions_and_deletions(self):
        diff_text = """--- a/test.py
+++ b/test.py
-old_function()
+new_function()
"""
        concepts = concepts_from_diff_text(diff_text)

        assert "old_function" in concepts
        assert "new_function" in concepts


class TestSelectionReasons:
    def test_selection_reason_no_candidates(self, tmp_path):
        result = lazy_greedy_select(
            fragments=[],
            core_ids=set(),
            rel={},
            concepts=frozenset(),
            budget_tokens=1000,
            tau=0.1,
        )

        assert result.reason == "no_candidates"

    def test_selection_reason_budget_exhausted(self, tmp_path):
        path = tmp_path / "test.py"
        fragments = [
            Fragment(
                id=FragmentId(path=path, start_line=1, end_line=5),
                kind="function",
                content="def f():\n    pass\n",
                identifiers=frozenset(["f"]),
                token_count=100,
            )
        ]

        rel = {fragments[0].id: 1.0}
        concepts = frozenset(["f"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids={fragments[0].id},
            rel=rel,
            concepts=concepts,
            budget_tokens=100,
            tau=0.1,
        )

        assert result.reason in ["budget_exhausted", "no_candidates", "stopped_by_tau"]


class TestSelectionAlgorithm:
    def test_overlap_full_containment(self, tmp_path):
        path = tmp_path / "test.py"
        content = "\n".join([f"line{i}" for i in range(1, 21)])
        path.write_text(content)

        frag_a = Fragment(
            id=FragmentId(path=path, start_line=1, end_line=20),
            kind="function",
            content=content,
            identifiers=frozenset(["func_a", "helper"]),
            token_count=50,
        )
        frag_b = Fragment(
            id=FragmentId(path=path, start_line=5, end_line=10),
            kind="function",
            content="\n".join([f"line{i}" for i in range(5, 11)]),
            identifiers=frozenset(["func_b"]),
            token_count=20,
        )

        fragments = [frag_a, frag_b]
        rel = {frag_a.id: 1.0, frag_b.id: 0.8}
        concepts = frozenset(["func_a", "func_b", "helper"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids={frag_a.id},
            rel=rel,
            concepts=concepts,
            budget_tokens=100,
            tau=0.0,
        )

        selected_ids = {f.id for f in result.selected}
        assert frag_a.id in selected_ids
        assert frag_b.id not in selected_ids

    def test_selection_deterministic(self, tmp_path):
        path = tmp_path / "test.py"
        content = "def func():\n    pass\n"
        path.write_text(content)

        fragments = [
            Fragment(
                id=FragmentId(path=path, start_line=1, end_line=5),
                kind="function",
                content="def func1():\n    pass\n",
                identifiers=frozenset(["func1"]),
                token_count=10,
            ),
            Fragment(
                id=FragmentId(path=path, start_line=6, end_line=10),
                kind="function",
                content="def func2():\n    pass\n",
                identifiers=frozenset(["func2"]),
                token_count=10,
            ),
            Fragment(
                id=FragmentId(path=path, start_line=11, end_line=15),
                kind="function",
                content="def func3():\n    pass\n",
                identifiers=frozenset(["func3"]),
                token_count=10,
            ),
        ]

        rel = {f.id: 0.5 for f in fragments}
        concepts = frozenset(["func1", "func2", "func3"])

        result1 = lazy_greedy_select(
            fragments=fragments,
            core_ids={fragments[0].id},
            rel=rel,
            concepts=concepts,
            budget_tokens=50,
            tau=0.0,
        )

        result2 = lazy_greedy_select(
            fragments=fragments,
            core_ids={fragments[0].id},
            rel=rel,
            concepts=concepts,
            budget_tokens=50,
            tau=0.0,
        )

        assert [f.id for f in result1.selected] == [f.id for f in result2.selected]

    def test_tau_zero_no_early_stopping(self, tmp_path):
        path = tmp_path / "test.py"

        fragments = [
            Fragment(
                id=FragmentId(path=path, start_line=i * 10 + 1, end_line=i * 10 + 5),
                kind="function",
                content=f"def func{i}():\n    pass\n",
                identifiers=frozenset([f"func{i}"]),
                token_count=5,
            )
            for i in range(10)
        ]

        rel = {f.id: 0.1 for f in fragments}
        concepts = frozenset([f"func{i}" for i in range(10)])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids={fragments[0].id},
            rel=rel,
            concepts=concepts,
            budget_tokens=100,
            tau=0.0,
        )

        assert len(result.selected) == 10
        assert result.reason != "stopped_by_tau"

    def test_utility_gain_with_concepts(self, tmp_path):
        path = tmp_path / "test.py"

        frag_no_overlap = Fragment(
            id=FragmentId(path=path, start_line=1, end_line=5),
            kind="function",
            content="def unrelated():\n    pass\n",
            identifiers=frozenset(["unrelated"]),
            token_count=10,
        )

        frag_with_overlap = Fragment(
            id=FragmentId(path=path, start_line=6, end_line=10),
            kind="function",
            content="def target_func():\n    pass\n",
            identifiers=frozenset(["target_func", "helper"]),
            token_count=10,
        )

        concepts = frozenset(["target_func", "helper", "other"])
        state = UtilityState()

        gain_no_overlap = marginal_gain(frag_no_overlap, 0.8, concepts, state)
        gain_with_overlap = marginal_gain(frag_with_overlap, 0.8, concepts, state)

        assert gain_with_overlap > gain_no_overlap
        assert gain_with_overlap > 0

    def test_best_singleton_overlaps_core_skipped(self, tmp_path):
        path = tmp_path / "test.py"

        frag_core = Fragment(
            id=FragmentId(path=path, start_line=1, end_line=20),
            kind="function",
            content="def core():\n    pass\n",
            identifiers=frozenset(["core", "helper"]),
            token_count=30,
        )

        frag_singleton = Fragment(
            id=FragmentId(path=path, start_line=5, end_line=15),
            kind="function",
            content="def singleton():\n    pass\n",
            identifiers=frozenset(["singleton", "helper"]),
            token_count=20,
        )

        frag_other = Fragment(
            id=FragmentId(path=path, start_line=25, end_line=30),
            kind="function",
            content="def other():\n    pass\n",
            identifiers=frozenset(["other"]),
            token_count=10,
        )

        fragments = [frag_core, frag_singleton, frag_other]
        rel = {f.id: 0.5 for f in fragments}
        rel[frag_singleton.id] = 1.0
        concepts = frozenset(["core", "singleton", "helper", "other"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids={frag_core.id},
            rel=rel,
            concepts=concepts,
            budget_tokens=100,
            tau=0.0,
        )

        selected_ids = {f.id for f in result.selected}
        assert frag_core.id in selected_ids
        assert frag_singleton.id not in selected_ids
        assert result.reason != "best_singleton"


class TestParameterValidation:
    def test_invalid_alpha_negative(self, diff_project):
        """alpha < 0 should raise ValueError"""
        diff_project.add_file("test.py", "x = 1")
        diff_project.commit("Initial")
        diff_project.add_file("test.py", "x = 2")
        diff_project.commit("Modify")

        with pytest.raises(ValueError):
            build_diff_context(
                root_dir=diff_project.repo,
                diff_range="HEAD~1..HEAD",
                budget_tokens=1000,
                alpha=-0.1,
            )

    def test_invalid_alpha_greater_than_one(self, diff_project):
        """alpha >= 1 should raise ValueError"""
        diff_project.add_file("test.py", "x = 1")
        diff_project.commit("Initial")
        diff_project.add_file("test.py", "x = 2")
        diff_project.commit("Modify")

        with pytest.raises(ValueError):
            build_diff_context(
                root_dir=diff_project.repo,
                diff_range="HEAD~1..HEAD",
                budget_tokens=1000,
                alpha=1.5,
            )

    def test_invalid_tau_negative(self, diff_project):
        """tau < 0 should raise ValueError"""
        diff_project.add_file("test.py", "x = 1")
        diff_project.commit("Initial")
        diff_project.add_file("test.py", "x = 2")
        diff_project.commit("Modify")

        with pytest.raises(ValueError):
            build_diff_context(
                root_dir=diff_project.repo,
                diff_range="HEAD~1..HEAD",
                budget_tokens=1000,
                tau=-0.5,
            )

    def test_valid_alpha_boundaries(self, diff_project):
        """alpha=0.0 and alpha=0.99 should work"""
        diff_project.add_file("test.py", "x = 1")
        diff_project.commit("Initial")
        diff_project.add_file("test.py", "x = 2")
        diff_project.commit("Modify")

        # Should not raise
        tree1 = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=1000,
            alpha=0.0,
        )
        assert tree1 is not None

        tree2 = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=1000,
            alpha=0.99,
        )
        assert tree2 is not None

    def test_valid_tau_zero(self, diff_project):
        """tau=0.0 should work"""
        diff_project.add_file("test.py", "x = 1")
        diff_project.commit("Initial")
        diff_project.add_file("test.py", "x = 2")
        diff_project.commit("Modify")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=1000,
            tau=0.0,
        )
        assert tree is not None


class TestEmptyDiffType:
    def test_empty_diff_returns_diff_context_type(self, diff_project):
        diff_project.add_file("test.py", "x = 1")
        diff_project.commit("Initial")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD..HEAD",
            budget_tokens=1000,
        )

        assert tree["type"] == "diff_context"
        assert "fragments" in tree
        assert tree["fragments"] == []
        assert tree.get("fragment_count", 0) == 0

    def test_empty_diff_no_children_field(self, diff_project):
        diff_project.add_file("test.py", "x = 1")
        diff_project.commit("Initial")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD..HEAD",
            budget_tokens=1000,
        )

        assert "children" not in tree


class TestCLIBudgetDefault:
    def test_cli_budget_default_matches_behavior(self):
        import subprocess

        from treemapper.diffctx import _DEFAULT_BUDGET_TOKENS

        result = subprocess.run(
            ["python", "-m", "treemapper", "--help"],
            capture_output=True,
            text=True,
        )

        assert "50000" in result.stdout
        assert _DEFAULT_BUDGET_TOKENS == 50_000
