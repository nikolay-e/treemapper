import pytest

from treemapper.diffctx import build_diff_context


@pytest.fixture
def diff_project(git_with_commits):
    return git_with_commits


class TestFullMode:
    def test_full_mode_includes_all_changed_code(self, diff_project):
        """--full should include all fragments from changed files"""
        diff_project.add_file("a.py", "def func_a():\n    return 1\n")
        diff_project.add_file("b.py", "def func_b():\n    return 2\n")
        diff_project.add_file("c.py", "def func_c():\n    return 3\n")
        diff_project.commit("Initial")

        diff_project.add_file("a.py", "def func_a():\n    return 10\n")
        diff_project.add_file("b.py", "def func_b():\n    return 20\n")
        diff_project.add_file("c.py", "def func_c():\n    return 30\n")
        diff_project.commit("Modify all")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=100,
            full=True,
        )

        fragments = tree.get("fragments", [])
        paths = {f["path"].split("/")[-1] for f in fragments}
        assert "a.py" in paths
        assert "b.py" in paths
        assert "c.py" in paths

    def test_full_mode_ignores_budget(self, diff_project):
        """--full should ignore budget constraint"""
        content = "\n".join([f"def func{i}():\n    return {i}\n" for i in range(20)])
        diff_project.add_file("large.py", content)
        diff_project.commit("Initial")

        modified = "\n".join([f"def func{i}():\n    return {i*10}\n" for i in range(20)])
        diff_project.add_file("large.py", modified)
        diff_project.commit("Modify")

        full_tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=50,
            full=True,
        )

        smart_tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=50,
            full=False,
        )

        full_count = len(full_tree.get("fragments", []))
        smart_count = len(smart_tree.get("fragments", []))

        assert full_count >= smart_count


class TestOutputTreeStructure:
    def test_output_type_is_diff_context(self, diff_project):
        diff_project.add_file("test.py", "x = 1")
        diff_project.commit("Initial")
        diff_project.add_file("test.py", "x = 2")
        diff_project.commit("Modify")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=1000,
        )

        assert tree.get("type") == "diff_context"

    def test_fragment_lines_format(self, diff_project):
        diff_project.add_file("test.py", "def foo():\n    return 1\n")
        diff_project.commit("Initial")
        diff_project.add_file("test.py", "def foo():\n    return 2\n")
        diff_project.commit("Modify")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=1000,
        )

        import re

        for frag in tree.get("fragments", []):
            if "lines" in frag:
                assert re.match(r"^\d+-\d+$", frag["lines"])

    def test_no_content_removes_content(self, diff_project):
        diff_project.add_file("test.py", "def foo():\n    return 1\n")
        diff_project.commit("Initial")
        diff_project.add_file("test.py", "def foo():\n    return 2\n")
        diff_project.commit("Modify")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=1000,
            no_content=True,
        )

        for frag in tree.get("fragments", []):
            content = frag.get("content", "")
            assert content == "" or content is None
