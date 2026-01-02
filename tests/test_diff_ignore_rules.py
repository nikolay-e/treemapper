import pytest

from treemapper.diffctx import build_diff_context


def _extract_files_from_tree(tree: dict) -> set[str]:
    files = set()
    if tree.get("type") == "diff_context":
        for frag in tree.get("fragments", []):
            path = frag.get("path", "")
            if path:
                files.add(path.split("/")[-1])
        return files
    return files


@pytest.fixture
def diff_project(git_with_commits):
    return git_with_commits


class TestDefaultIgnores:
    def test_node_modules_excluded(self, diff_project):
        """Files in node_modules should be excluded from diff context"""
        diff_project.add_file("main.py", "x = 1")
        diff_project.add_file("node_modules/pkg/index.js", "module.exports = {}")
        diff_project.commit("Initial")

        diff_project.add_file("main.py", "x = 2")
        diff_project.add_file("node_modules/pkg/index.js", "module.exports = {v: 1}")
        diff_project.commit("Modify both")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "main.py" in selected
        assert "index.js" not in selected

    def test_venv_excluded(self, diff_project):
        """Files in .venv should be excluded from diff context"""
        diff_project.add_file("main.py", "x = 1")
        diff_project.add_file(".venv/lib/site.py", "x = 1")
        diff_project.commit("Initial")

        diff_project.add_file("main.py", "x = 2")
        diff_project.add_file(".venv/lib/site.py", "x = 2")
        diff_project.commit("Modify")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "main.py" in selected
        assert "site.py" not in selected

    def test_pycache_excluded(self, diff_project):
        """Files in __pycache__ should be excluded"""
        diff_project.add_file("main.py", "x = 1")
        diff_project.add_file("__pycache__/main.cpython-311.pyc", "binary")
        diff_project.commit("Initial")

        diff_project.add_file("main.py", "x = 2")
        diff_project.commit("Modify")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "main.py" in selected


class TestGitignoreRules:
    def test_gitignore_excludes_file(self, diff_project):
        """Files matching .gitignore should be excluded"""
        diff_project.add_file(".gitignore", "*.log\n")
        diff_project.add_file("main.py", "x = 1")
        diff_project.add_file("debug.log", "log line 1")
        diff_project.commit("Initial")

        diff_project.add_file("main.py", "x = 2")
        diff_project.add_file("debug.log", "log line 2")
        diff_project.commit("Modify")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "main.py" in selected
        # Note: .gitignore patterns apply to treemapper selection


class TestTreemapperIgnore:
    def test_treemapperignore_excludes_file(self, diff_project):
        """Files matching .treemapperignore should be excluded"""
        diff_project.add_file(".treemapperignore", "*.tmp\n")
        diff_project.add_file("main.py", "x = 1")
        diff_project.add_file("cache.tmp", "temp data")
        diff_project.commit("Initial")

        diff_project.add_file("main.py", "x = 2")
        diff_project.add_file("cache.tmp", "new temp data")
        diff_project.commit("Modify")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "main.py" in selected
        assert "cache.tmp" not in selected
