import re
import subprocess

import pytest

from tests.utils import DiffTestCase, DiffTestRunner
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


OPERATIONS_TEST_CASES = [
    DiffTestCase(
        name="git_new_file_with_inheritance",
        initial_files={
            "features/__init__.py": "",
            "features/base.py": """class BaseFeature:
    def run(self):
        return "base"
""",
        },
        changed_files={
            "features/new_feature.py": """from .base import BaseFeature

class NewFeature(BaseFeature):
    def run(self):
        return "new"
""",
        },
        must_include=["new_feature.py", "BaseFeature"],
        commit_message="Add new feature",
    ),
    DiffTestCase(
        name="ignore_node_modules",
        initial_files={
            "main.py": "x = 1",
            "node_modules/pkg/index.js": "module.exports = {}",
        },
        changed_files={
            "main.py": "x = 2",
            "node_modules/pkg/index.js": "module.exports = {v: 1}",
        },
        must_include=["main.py"],
        must_not_include=["index.js", "node_modules"],
        commit_message="Modify both",
    ),
    DiffTestCase(
        name="ignore_venv",
        initial_files={
            "main.py": "x = 1",
            ".venv/lib/site.py": "x = 1",
        },
        changed_files={
            "main.py": "x = 2",
            ".venv/lib/site.py": "x = 2",
        },
        must_include=["main.py"],
        must_not_include=["site.py"],
        commit_message="Modify files",
    ),
    DiffTestCase(
        name="ignore_pycache",
        initial_files={
            "main.py": "x = 1",
            "__pycache__/main.cpython-311.pyc": "binary",
        },
        changed_files={
            "main.py": "x = 2",
        },
        must_include=["main.py"],
        must_not_include=["cpython-311.pyc"],
        commit_message="Modify main",
    ),
    DiffTestCase(
        name="treemapperignore_excludes_file",
        initial_files={
            ".treemapperignore": "*.tmp\n",
            "main.py": "x = 1",
            "cache.tmp": "temp data",
        },
        changed_files={
            "main.py": "x = 2",
            "cache.tmp": "new temp data",
        },
        must_include=["main.py"],
        must_not_include=["cache.tmp"],
        commit_message="Modify files",
    ),
    DiffTestCase(
        name="full_mode_all_changed_files",
        initial_files={
            "a.py": "def func_a():\n    return 1\n",
            "b.py": "def func_b():\n    return 2\n",
            "c.py": "def func_c():\n    return 3\n",
        },
        changed_files={
            "a.py": "def func_a():\n    return 10\n",
            "b.py": "def func_b():\n    return 20\n",
            "c.py": "def func_c():\n    return 30\n",
        },
        must_include=["a.py", "b.py", "c.py"],
        commit_message="Modify all",
    ),
]


@pytest.mark.parametrize("case", OPERATIONS_TEST_CASES, ids=lambda c: c.name)
def test_operations_cases(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)


@pytest.fixture
def diff_project(git_with_commits):
    return git_with_commits


class TestGitFileOperations:
    def test_file_renamed(self, diff_project):
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

        assert tree is not None
        assert tree.get("type") in ("directory", "diff_context")

    def test_file_moved_to_different_package(self, diff_project):
        diff_project.add_file("old_package/__init__.py", "")
        diff_project.add_file(
            "old_package/module.py",
            """def module_func():
    return "module"
""",
        )
        diff_project.add_file("new_package/__init__.py", "")
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

        assert tree is not None
        assert tree.get("type") in ("directory", "diff_context")

    def test_file_deleted(self, diff_project):
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

        deleted_hunks = [h for h in hunks if h.is_deletion]
        assert len(deleted_hunks) == 1
        assert "old_helper.py" in str(deleted_hunks[0].path)


class TestBranchOperations:
    def test_diff_between_branches(self, diff_project):
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

    def test_three_dot_diff_parsing(self, diff_project):
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
    def test_split_two_dot(self):
        base, head = split_diff_range("main..feature")
        assert base == "main"
        assert head == "feature"

    def test_split_three_dot(self):
        base, head = split_diff_range("main...feature")
        assert base == "main"
        assert head == "feature"

    def test_split_with_sha(self):
        base, head = split_diff_range("abc1234..def5678")
        assert base == "abc1234"
        assert head == "def5678"

    def test_split_head_notation(self):
        base, head = split_diff_range("HEAD~1..HEAD")
        assert base == "HEAD~1"
        assert head == "HEAD"


class TestChangedFilesDetection:
    def test_single_file(self, diff_project):
        diff_project.add_file("file1.py", "x = 1")
        diff_project.commit("Initial")

        diff_project.add_file("file1.py", "x = 2")
        diff_project.commit("Modify")

        changed = get_changed_files(diff_project.repo, "HEAD~1..HEAD")
        assert len(changed) == 1
        assert changed[0].name == "file1.py"

    def test_multiple_files(self, diff_project):
        diff_project.add_file("file1.py", "x = 1")
        diff_project.add_file("file2.py", "y = 1")
        diff_project.commit("Initial")

        diff_project.add_file("file1.py", "x = 2")
        diff_project.add_file("file2.py", "y = 2")
        diff_project.commit("Modify both")

        changed = get_changed_files(diff_project.repo, "HEAD~1..HEAD")
        names = {f.name for f in changed}
        assert names == {"file1.py", "file2.py"}

    def test_nested_files(self, diff_project):
        diff_project.add_file("src/lib/module.py", "x = 1")
        diff_project.commit("Initial")

        diff_project.add_file("src/lib/module.py", "x = 2")
        diff_project.commit("Modify")

        changed = get_changed_files(diff_project.repo, "HEAD~1..HEAD")
        assert len(changed) == 1
        assert "module.py" in str(changed[0])


class TestParseDiff:
    def test_single_hunk(self, diff_project):
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

    def test_multiple_hunks(self, diff_project):
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

    def test_addition(self, diff_project):
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

    def test_deletion(self, diff_project):
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

    def test_pure_deletion_hunk(self, diff_project):
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


class TestGitErrorHandling:
    def test_non_git_repo_raises_error(self, tmp_path):
        non_git = tmp_path / "non_git"
        non_git.mkdir()

        with pytest.raises(GitError):
            build_diff_context(
                root_dir=non_git,
                diff_range="HEAD~1..HEAD",
                budget_tokens=1000,
            )

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


class TestFullMode:
    def test_full_mode_ignores_budget(self, diff_project):
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


class TestOutputStructure:
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
