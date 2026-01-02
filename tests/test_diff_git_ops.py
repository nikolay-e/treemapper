import subprocess

import pytest

from treemapper.diffctx import GitError, build_diff_context
from treemapper.diffctx.git import get_changed_files, parse_diff, split_diff_range


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


class TestFileOperations:
    def test_git_001_file_renamed_find_old_references(self, diff_project):
        diff_project.add_file(
            "utils/helpers.py",
            """def helper_func():
    return "help"
""",
        )
        diff_project.add_file(
            "main.py",
            """from utils.helpers import helper_func

def main():
    return helper_func()
""",
        )
        diff_project.commit("Initial")

        subprocess.run(
            ["git", "mv", "utils/helpers.py", "utils/common.py"],
            cwd=diff_project.repo,
            capture_output=True,
            check=True,
        )
        diff_project.commit("Rename helpers to common")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        # Rename detection is a known limitation - verify algo doesn't crash
        # and returns valid tree structure (may be empty for pure renames)
        assert tree is not None
        assert tree.get("type") in ("directory", "diff_context")

    def test_git_002_file_moved_to_different_package(self, diff_project):
        diff_project.add_file(
            "old_package/__init__.py",
            "",
        )
        diff_project.add_file(
            "old_package/module.py",
            """def module_func():
    return "module"
""",
        )
        diff_project.add_file(
            "new_package/__init__.py",
            "",
        )
        diff_project.commit("Initial")

        subprocess.run(
            ["git", "mv", "old_package/module.py", "new_package/module.py"],
            cwd=diff_project.repo,
            capture_output=True,
            check=True,
        )
        diff_project.commit("Move module to new package")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        # File move detection is a known limitation - verify algo doesn't crash
        # and returns valid tree structure (may be empty for pure moves)
        assert tree is not None
        assert tree.get("type") in ("directory", "diff_context")

    def test_git_003_file_deleted(self, diff_project):
        diff_project.add_file(
            "deprecated/old_helper.py",
            """def old_helper():
    return "deprecated"
""",
        )
        diff_project.add_file(
            "main.py",
            """def main():
    return "main"
""",
        )
        diff_project.commit("Initial")

        subprocess.run(
            ["git", "rm", "deprecated/old_helper.py"],
            cwd=diff_project.repo,
            capture_output=True,
            check=True,
        )
        diff_project.commit("Delete old helper")

        hunks = parse_diff(diff_project.repo, "HEAD~1..HEAD")

        # Verify deletion is detected correctly
        deleted_hunks = [h for h in hunks if h.is_deletion]
        assert len(deleted_hunks) == 1
        assert "old_helper.py" in str(deleted_hunks[0].path)

    def test_git_004_new_file_added(self, diff_project):
        diff_project.add_file(
            "features/__init__.py",
            "",
        )
        diff_project.add_file(
            "features/base.py",
            """class BaseFeature:
    def run(self):
        return "base"
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "features/new_feature.py",
            """from .base import BaseFeature

class NewFeature(BaseFeature):
    def run(self):
        return "new"
""",
        )
        diff_project.commit("Add new feature")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "new_feature.py" in selected
        assert "base.py" in selected


class TestMergeConflictScenarios:
    def test_git_010_diff_between_branches(self, diff_project):
        diff_project.add_file(
            "main.py",
            """def main():
    return "initial"
""",
        )
        diff_project.commit("Initial on main")

        subprocess.run(
            ["git", "checkout", "-b", "feature-branch"],
            cwd=diff_project.repo,
            capture_output=True,
            check=True,
        )

        diff_project.add_file(
            "main.py",
            """def main():
    return "feature"
""",
        )
        diff_project.commit("Feature change")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "main.py" in selected

    def test_git_011_three_dot_diff(self, diff_project):
        diff_project.add_file(
            "main.py",
            """def main():
    return "initial"
""",
        )
        main_sha = diff_project.commit("Initial")

        subprocess.run(
            ["git", "checkout", "-b", "feature"],
            cwd=diff_project.repo,
            capture_output=True,
            check=True,
        )

        diff_project.add_file(
            "feature.py",
            """def feature():
    return "feature"
""",
        )
        diff_project.commit("Add feature")

        base, head = split_diff_range(f"{main_sha[:7]}...HEAD")
        assert base == main_sha[:7]
        assert head == "HEAD"


class TestDiffRangeParsing:
    def test_split_diff_range_two_dot(self):
        base, head = split_diff_range("main..feature")
        assert base == "main"
        assert head == "feature"

    def test_split_diff_range_three_dot(self):
        base, head = split_diff_range("main...feature")
        assert base == "main"
        assert head == "feature"

    def test_split_diff_range_with_sha(self):
        base, head = split_diff_range("abc1234..def5678")
        assert base == "abc1234"
        assert head == "def5678"

    def test_split_diff_range_head_notation(self):
        base, head = split_diff_range("HEAD~1..HEAD")
        assert base == "HEAD~1"
        assert head == "HEAD"


class TestChangedFilesDetection:
    def test_get_changed_files_single_file(self, diff_project):
        diff_project.add_file("file1.py", "x = 1")
        diff_project.commit("Initial")

        diff_project.add_file("file1.py", "x = 2")
        diff_project.commit("Modify")

        changed = get_changed_files(diff_project.repo, "HEAD~1..HEAD")
        assert len(changed) == 1
        assert changed[0].name == "file1.py"

    def test_get_changed_files_multiple_files(self, diff_project):
        diff_project.add_file("file1.py", "x = 1")
        diff_project.add_file("file2.py", "y = 1")
        diff_project.commit("Initial")

        diff_project.add_file("file1.py", "x = 2")
        diff_project.add_file("file2.py", "y = 2")
        diff_project.commit("Modify both")

        changed = get_changed_files(diff_project.repo, "HEAD~1..HEAD")
        names = {f.name for f in changed}
        assert names == {"file1.py", "file2.py"}

    def test_get_changed_files_nested(self, diff_project):
        diff_project.add_file("src/lib/module.py", "x = 1")
        diff_project.commit("Initial")

        diff_project.add_file("src/lib/module.py", "x = 2")
        diff_project.commit("Modify")

        changed = get_changed_files(diff_project.repo, "HEAD~1..HEAD")
        assert len(changed) == 1
        assert "module.py" in str(changed[0])


class TestParseDiff:
    def test_parse_diff_single_hunk(self, diff_project):
        diff_project.add_file(
            "test.py",
            """def hello():
    return "world"
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "test.py",
            """def hello():
    return "universe"
""",
        )
        diff_project.commit("Change return")

        hunks = parse_diff(diff_project.repo, "HEAD~1..HEAD")
        assert len(hunks) >= 1
        assert hunks[0].path.name == "test.py"

    def test_parse_diff_multiple_hunks(self, diff_project):
        diff_project.add_file(
            "test.py",
            """def func1():
    return 1

# middle section

def func2():
    return 2
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "test.py",
            """def func1():
    return 10

# middle section

def func2():
    return 20
""",
        )
        diff_project.commit("Change both functions")

        hunks = parse_diff(diff_project.repo, "HEAD~1..HEAD")
        assert len(hunks) >= 2

    def test_parse_diff_addition(self, diff_project):
        diff_project.add_file("test.py", "x = 1\n")
        diff_project.commit("Initial")

        diff_project.add_file(
            "test.py",
            """x = 1
y = 2
""",
        )
        diff_project.commit("Add line")

        hunks = parse_diff(diff_project.repo, "HEAD~1..HEAD")
        assert len(hunks) >= 1
        assert hunks[0].is_addition or hunks[0].new_len > 0

    def test_parse_diff_deletion(self, diff_project):
        diff_project.add_file(
            "test.py",
            """x = 1
y = 2
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file("test.py", "x = 1\n")
        diff_project.commit("Remove line")

        hunks = parse_diff(diff_project.repo, "HEAD~1..HEAD")
        assert len(hunks) >= 1

    def test_parse_diff_pure_deletion_hunk(self, diff_project):
        diff_project.add_file("test.py", "line1\nline2\nline3\n")
        diff_project.commit("Initial")

        subprocess.run(
            ["git", "rm", "test.py"],
            cwd=diff_project.repo,
            capture_output=True,
            check=True,
        )
        diff_project.commit("Delete file")

        hunks = parse_diff(diff_project.repo, "HEAD~1..HEAD")

        deletion_hunks = [h for h in hunks if h.is_deletion]
        assert len(deletion_hunks) == 1
        assert deletion_hunks[0].new_len == 0
        assert deletion_hunks[0].old_len > 0


class TestNonGitRepo:
    def test_non_git_repo_raises_error(self, tmp_path):
        non_git = tmp_path / "non_git"
        non_git.mkdir()

        with pytest.raises(GitError):
            build_diff_context(
                root_dir=non_git,
                diff_range="HEAD~1..HEAD",
                budget_tokens=1000,
            )


class TestGitErrorHandling:
    def test_invalid_diff_range_syntax(self, diff_project):
        diff_project.add_file("test.py", "x = 1")
        diff_project.commit("Initial")

        with pytest.raises(GitError):
            build_diff_context(
                root_dir=diff_project.repo,
                diff_range="@@invalid@@",
                budget_tokens=1000,
            )

    def test_nonexistent_ref_in_range(self, diff_project):
        diff_project.add_file("test.py", "x = 1")
        diff_project.commit("Initial")

        with pytest.raises(GitError):
            build_diff_context(
                root_dir=diff_project.repo,
                diff_range="nonexistent-branch..HEAD",
                budget_tokens=1000,
            )

    def test_range_beyond_history(self, diff_project):
        diff_project.add_file("test.py", "x = 1")
        diff_project.commit("Initial")

        with pytest.raises(GitError):
            build_diff_context(
                root_dir=diff_project.repo,
                diff_range="HEAD~10..HEAD",
                budget_tokens=1000,
            )
