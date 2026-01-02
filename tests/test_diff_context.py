import pytest

from treemapper.diffctx import GitError, build_diff_context
from treemapper.diffctx.fragments import enclosing_fragment, fragment_file
from treemapper.diffctx.git import get_changed_files, is_git_repo, parse_diff
from treemapper.diffctx.graph import build_graph
from treemapper.diffctx.ppr import personalized_pagerank
from treemapper.diffctx.select import lazy_greedy_select
from treemapper.diffctx.types import Fragment, FragmentId
from treemapper.diffctx.utility import UtilityState, concepts_from_diff_text, marginal_gain


class TestGitOperations:
    def test_is_git_repo_true(self, git_repo):
        assert is_git_repo(git_repo) is True

    def test_is_git_repo_false(self, tmp_path):
        non_git = tmp_path / "not_a_repo"
        non_git.mkdir()
        assert is_git_repo(non_git) is False

    def test_parse_diff_basic(self, git_with_commits):
        git_with_commits.add_file("main.py", "def hello():\n    pass\n")
        git_with_commits.commit("Initial commit")

        git_with_commits.add_file("main.py", "def hello():\n    print('hello')\n")
        git_with_commits.commit("Update hello")

        hunks = parse_diff(git_with_commits.repo, "HEAD~1..HEAD")
        assert len(hunks) == 1
        assert hunks[0].path == git_with_commits.repo / "main.py"
        assert hunks[0].new_start == 2
        assert hunks[0].new_len == 1

    def test_get_changed_files(self, git_with_commits):
        git_with_commits.add_file("a.py", "content a")
        git_with_commits.add_file("b.py", "content b")
        git_with_commits.commit("Initial")

        git_with_commits.add_file("a.py", "modified a")
        git_with_commits.commit("Modify a")

        files = get_changed_files(git_with_commits.repo, "HEAD~1..HEAD")
        assert len(files) == 1
        assert files[0].name == "a.py"


class TestFragmentation:
    def test_fragment_python_function(self, tmp_path):
        content = """def foo():
    x = 1
    return x

def bar():
    y = 42
    return y
"""
        path = tmp_path / "test.py"
        path.write_text(content)

        fragments = fragment_file(path, content)
        assert len(fragments) == 2
        assert all(f.kind == "function" for f in fragments)
        assert {f.id.start_line for f in fragments} == {1, 5}

    def test_fragment_python_class(self, tmp_path):
        content = """class MyClass:
    def method(self):
        pass
"""
        path = tmp_path / "test.py"
        path.write_text(content)

        fragments = fragment_file(path, content)
        assert any(f.kind == "class" for f in fragments)

    def test_fragment_generic_fallback(self, tmp_path):
        content = "some plain text content\nwithout any structure\n"
        path = tmp_path / "readme.txt"
        path.write_text(content)

        fragments = fragment_file(path, content)
        assert len(fragments) == 1
        assert fragments[0].kind == "chunk"

    def test_enclosing_fragment(self, tmp_path):
        content = """def foo():
    line2
    line3
    line4

def bar():
    line7
"""
        path = tmp_path / "test.py"
        path.write_text(content)

        fragments = fragment_file(path, content)
        enclosing = enclosing_fragment(fragments, 3)
        assert enclosing is not None
        assert enclosing.id.start_line == 1


class TestGraph:
    def test_build_graph_lexical_edges(self, tmp_path):
        path = tmp_path / "test.py"

        frag1 = Fragment(
            id=FragmentId(path=path, start_line=1, end_line=3),
            kind="function",
            content="def foo():\n    helper()\n",
            identifiers=frozenset(["foo", "helper"]),
        )
        frag2 = Fragment(
            id=FragmentId(path=path, start_line=5, end_line=7),
            kind="function",
            content="def helper():\n    pass\n",
            identifiers=frozenset(["helper", "pass"]),
        )

        graph = build_graph([frag1, frag2])
        assert frag1.id in graph.nodes
        assert frag2.id in graph.nodes


class TestPPR:
    def test_ppr_seeds_get_high_scores(self, tmp_path):
        path = tmp_path / "test.py"

        frag1 = Fragment(
            id=FragmentId(path=path, start_line=1, end_line=3),
            kind="function",
            content="def seed_func():\n    pass\n",
            identifiers=frozenset(["seed_func"]),
        )
        frag2 = Fragment(
            id=FragmentId(path=path, start_line=5, end_line=7),
            kind="function",
            content="def other_func():\n    pass\n",
            identifiers=frozenset(["other_func"]),
        )

        graph = build_graph([frag1, frag2])
        scores = personalized_pagerank(graph, seeds={frag1.id}, alpha=0.55)

        assert scores[frag1.id] > scores[frag2.id]

    def test_ppr_empty_seeds(self, tmp_path):
        path = tmp_path / "test.py"
        frag = Fragment(
            id=FragmentId(path=path, start_line=1, end_line=3),
            kind="function",
            content="def foo():\n    pass\n",
            identifiers=frozenset(["foo"]),
        )

        graph = build_graph([frag])
        scores = personalized_pagerank(graph, seeds=set(), alpha=0.55)
        assert len(scores) == 1


class TestUtility:
    def test_concepts_from_diff(self):
        diff_text = """+++ b/main.py
+def new_function():
+    helper_call()
"""
        concepts = concepts_from_diff_text(diff_text)
        assert "new_function" in concepts
        assert "helper_call" in concepts

    def test_marginal_gain(self, tmp_path):
        path = tmp_path / "test.py"
        frag = Fragment(
            id=FragmentId(path=path, start_line=1, end_line=3),
            kind="function",
            content="def foo():\n    bar()\n",
            identifiers=frozenset(["foo", "bar"]),
        )

        concepts = frozenset(["foo", "bar", "baz"])
        state = UtilityState()

        gain = marginal_gain(frag, rel_score=1.0, concepts=concepts, state=state)
        assert gain > 0


class TestSelection:
    def test_lazy_greedy_respects_budget(self, tmp_path):
        path = tmp_path / "test.py"

        fragments = []
        for i in range(5):
            frag = Fragment(
                id=FragmentId(path=path, start_line=i * 10 + 1, end_line=i * 10 + 5),
                kind="function",
                content=f"def func{i}():\n    pass\n",
                identifiers=frozenset([f"func{i}"]),
                token_count=100,
            )
            fragments.append(frag)

        rel = {f.id: 1.0 for f in fragments}
        concepts = frozenset([f"func{i}" for i in range(5)])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=set(),
            rel=rel,
            concepts=concepts,
            budget_tokens=250,
            tau=0.0,
        )

        total_tokens = sum(f.token_count for f in result.selected)
        assert total_tokens <= 250

    def test_lazy_greedy_includes_core(self, tmp_path):
        path = tmp_path / "test.py"

        core_frag = Fragment(
            id=FragmentId(path=path, start_line=1, end_line=5),
            kind="function",
            content="def core():\n    pass\n",
            identifiers=frozenset(["core"]),
            token_count=50,
        )

        other_frag = Fragment(
            id=FragmentId(path=path, start_line=10, end_line=15),
            kind="function",
            content="def other():\n    pass\n",
            identifiers=frozenset(["other"]),
            token_count=50,
        )

        rel = {core_frag.id: 1.0, other_frag.id: 0.1}
        concepts = frozenset(["core", "other"])

        result = lazy_greedy_select(
            fragments=[core_frag, other_frag],
            core_ids={core_frag.id},
            rel=rel,
            concepts=concepts,
            budget_tokens=100,
            tau=0.0,
        )

        assert core_frag in result.selected


class TestBuildDiffContext:
    def test_basic_diff_context(self, git_with_commits):
        git_with_commits.add_file(
            "main.py",
            """def hello():
    pass

def world():
    pass
""",
        )
        git_with_commits.commit("Initial")

        git_with_commits.add_file(
            "main.py",
            """def hello():
    print("hello")

def world():
    pass
""",
        )
        git_with_commits.commit("Update hello")

        tree = build_diff_context(
            root_dir=git_with_commits.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        assert tree["type"] == "diff_context"
        assert "fragments" in tree

    def test_empty_diff(self, git_with_commits):
        git_with_commits.add_file("main.py", "def hello():\n    pass\n")
        git_with_commits.commit("Initial")

        tree = build_diff_context(
            root_dir=git_with_commits.repo,
            diff_range="HEAD..HEAD",
            budget_tokens=10000,
        )

        assert tree["type"] == "diff_context"
        assert tree["fragments"] == []
        assert tree.get("fragment_count", 0) == 0

    def test_not_a_git_repo(self, tmp_path):
        non_git = tmp_path / "not_git"
        non_git.mkdir()

        with pytest.raises(GitError):
            build_diff_context(
                root_dir=non_git,
                diff_range="HEAD~1..HEAD",
                budget_tokens=10000,
            )

    def test_no_content_mode(self, git_with_commits):
        git_with_commits.add_file("main.py", "def hello():\n    pass\n")
        git_with_commits.commit("Initial")

        git_with_commits.add_file("main.py", "def hello():\n    print('hi')\n")
        git_with_commits.commit("Update")

        tree = build_diff_context(
            root_dir=git_with_commits.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
            no_content=True,
        )

        def check_no_content(node):
            if node.get("type") == "fragment":
                assert node.get("content", "") == ""
            for child in node.get("children", []):
                check_no_content(child)

        check_no_content(tree)
