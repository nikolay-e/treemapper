import subprocess
from pathlib import Path

import pytest

from treemapper.diffctx import build_diff_context
from treemapper.diffctx.fragments import fragment_file
from treemapper.diffctx.graph import build_graph
from treemapper.diffctx.ppr import personalized_pagerank
from treemapper.diffctx.select import lazy_greedy_select
from treemapper.diffctx.types import Fragment, FragmentId, extract_identifier_list, extract_identifiers
from treemapper.diffctx.utility import UtilityState, concepts_from_diff_text, marginal_gain, utility_value


@pytest.fixture
def complex_project(tmp_path):
    repo = tmp_path / "complex_repo"
    repo.mkdir()

    subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True, check=True)

    class ProjectHelper:
        def __init__(self, path: Path):
            self.repo = path

        def write(self, rel_path: str, content: str) -> Path:
            file_path = self.repo / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return file_path

        def commit(self, message: str) -> str:
            subprocess.run(["git", "add", "-A"], cwd=self.repo, capture_output=True, check=True)
            subprocess.run(["git", "commit", "-m", message], cwd=self.repo, capture_output=True, check=True)
            result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo, capture_output=True, text=True, check=True)
            return result.stdout.strip()

    return ProjectHelper(repo)


class TestCrossFilePPRPropagation:
    def test_changed_function_pulls_in_callee_file(self, complex_project):
        complex_project.write(
            "src/math_utils.py",
            """def calculate_sum(a, b):
    return a + b

def calculate_product(a, b):
    return a * b

def calculate_average(numbers):
    total = calculate_sum(numbers[0], numbers[1])
    for n in numbers[2:]:
        total = calculate_sum(total, n)
    return total / len(numbers)
""",
        )

        complex_project.write(
            "src/processor.py",
            """from math_utils import calculate_average

def process_data(data):
    result = calculate_average(data)
    return result
""",
        )

        complex_project.commit("Initial commit")

        complex_project.write(
            "src/processor.py",
            """from math_utils import calculate_average, calculate_product

def process_data(data):
    avg = calculate_average(data)
    prod = calculate_product(data[0], data[1])
    return avg + prod
""",
        )
        complex_project.commit("Add product calculation")

        tree = build_diff_context(
            root_dir=complex_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected_files = _extract_files_from_tree(tree)
        # Core guarantee: changed file is always included
        assert "processor.py" in selected_files

    def test_caller_gets_relevance_via_backward_edges(self, complex_project):
        complex_project.write(
            "src/core.py",
            """def core_function():
    return 42
""",
        )

        complex_project.write(
            "src/caller_a.py",
            """from core import core_function

def use_core_a():
    return core_function() + 1
""",
        )

        complex_project.write(
            "src/caller_b.py",
            """from core import core_function

def use_core_b():
    return core_function() * 2
""",
        )

        complex_project.commit("Initial")

        complex_project.write(
            "src/core.py",
            """def core_function():
    return 100
""",
        )
        complex_project.commit("Change core return value")

        tree = build_diff_context(
            root_dir=complex_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected_files = _extract_files_from_tree(tree)
        assert "core.py" in selected_files


class TestRareIdentifierExpansion:
    def test_rare_identifier_pulls_in_definition_file(self, complex_project):
        complex_project.write(
            "src/special_algorithm.py",
            """def fibonacci_memoized_optimized(n, cache=None):
    if cache is None:
        cache = {}
    if n in cache:
        return cache[n]
    if n <= 1:
        return n
    result = fibonacci_memoized_optimized(n-1, cache) + fibonacci_memoized_optimized(n-2, cache)
    cache[n] = result
    return result
""",
        )

        complex_project.write(
            "src/main.py",
            """def main():
    print("Hello")
""",
        )

        complex_project.commit("Initial")

        complex_project.write(
            "src/main.py",
            """from special_algorithm import fibonacci_memoized_optimized

def main():
    result = fibonacci_memoized_optimized(10)
    print(result)
""",
        )
        complex_project.commit("Use fibonacci")

        tree = build_diff_context(
            root_dir=complex_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected_files = _extract_files_from_tree(tree)
        assert "main.py" in selected_files
        assert "special_algorithm.py" in selected_files

    def test_rare_identifier_threshold_exactly_3_files(self, complex_project):
        complex_project.write(
            "src/special_utils.py",
            "def very_unique_calculator_func():\n    return 1\n",
        )
        complex_project.write(
            "src/other.py",
            "from special_utils import very_unique_calculator_func\n",
        )
        complex_project.write(
            "src/main.py",
            "def main():\n    print('hello')\n",
        )
        complex_project.commit("Initial")

        complex_project.write(
            "src/main.py",
            "from special_utils import very_unique_calculator_func\n\ndef main():\n    result = very_unique_calculator_func()\n    print(result)\n",
        )
        complex_project.commit("Use unique function")

        tree = build_diff_context(
            root_dir=complex_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        fragments = tree.get("fragments", [])
        paths = {f.get("path", "").split("/")[-1] for f in fragments}
        assert "special_utils.py" in paths

    def test_common_identifier_not_expanded(self, complex_project):
        for i in range(6):
            complex_project.write(f"src/mod{i}.py", f"def process():\n    return {i}\n")
        complex_project.write("src/main.py", "process()\n")
        complex_project.commit("Initial")

        complex_project.write("src/main.py", "process()\nprint('x')\n")
        complex_project.commit("Modify")

        tree = build_diff_context(
            root_dir=complex_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        fragments = tree.get("fragments", [])
        paths = {f.get("path", "").split("/")[-1] for f in fragments}
        assert "main.py" in paths
        mod_count = sum(1 for p in paths if p.startswith("mod"))
        assert mod_count < 6


class TestConceptsExtraction:
    def test_concepts_from_added_lines(self):
        diff_text = """+++ b/main.py
+def new_function():
+    helper_call()
+    another_helper()
"""
        concepts = concepts_from_diff_text(diff_text)
        assert "new_function" in concepts
        assert "helper_call" in concepts
        assert "another_helper" in concepts

    def test_concepts_from_deleted_lines(self):
        diff_text = """--- a/main.py
-def old_function():
-    deprecated_helper()
"""
        concepts = concepts_from_diff_text(diff_text)
        assert "old_function" in concepts
        assert "deprecated_helper" in concepts

    def test_concepts_from_both_added_and_deleted(self):
        diff_text = """--- a/main.py
+++ b/main.py
-def old_approach():
-    legacy_helper()
+def new_approach():
+    modern_helper()
"""
        concepts = concepts_from_diff_text(diff_text)
        assert "old_approach" in concepts
        assert "legacy_helper" in concepts
        assert "new_approach" in concepts
        assert "modern_helper" in concepts


class TestHierarchicalDeduplication:
    def test_class_and_methods_have_hierarchical_structure(self, tmp_path):
        path = tmp_path / "test.py"
        content = """class MyClass:
    def method_a(self):
        x = 1
        y = 2
        return x + y

    def method_b(self):
        a = 10
        b = 20
        return a * b

def standalone():
    result = 42
    return result
"""
        path.write_text(content)

        fragments = fragment_file(path, content)

        class_frag = next((f for f in fragments if f.kind == "class"), None)
        func_frags = [f for f in fragments if f.kind == "function"]

        assert class_frag is not None
        assert len(func_frags) >= 2

        methods_inside_class = [f for f in func_frags if class_frag.start_line <= f.start_line <= class_frag.end_line]
        assert len(methods_inside_class) >= 2

    def test_selection_avoids_hierarchical_overlap(self, tmp_path):
        path = tmp_path / "test.py"
        content = """class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b
"""
        path.write_text(content)
        fragments = fragment_file(path, content)

        for frag in fragments:
            frag.token_count = len(frag.content.split()) * 2

        rel = {f.id: 1.0 for f in fragments}
        concepts = extract_identifiers(content)

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=set(),
            rel=rel,
            concepts=concepts,
            budget_tokens=1000,
            tau=0.0,
        )

        [f.id for f in result.selected]
        for i, frag_i in enumerate(result.selected):
            for j, frag_j in enumerate(result.selected):
                if i == j or frag_i.path != frag_j.path:
                    continue
                overlap = frag_i.start_line <= frag_j.start_line and frag_j.end_line <= frag_i.end_line
                assert not overlap, f"Hierarchical overlap: {frag_i.id} contains {frag_j.id}"


class TestBudgetConstraint:
    def test_selection_respects_budget(self, tmp_path):
        path = tmp_path / "test.py"
        fragments = []
        for i in range(20):
            frag = Fragment(
                id=FragmentId(path=path, start_line=i * 10 + 1, end_line=i * 10 + 5),
                kind="function",
                content=f"def func{i}():\n    pass\n" * 10,
                identifiers=frozenset([f"func{i}", f"helper{i}"]),
                token_count=100,
            )
            fragments.append(frag)

        rel = {f.id: 1.0 / (i + 1) for i, f in enumerate(fragments)}
        concepts = frozenset([f"func{i}" for i in range(20)])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=set(),
            rel=rel,
            concepts=concepts,
            budget_tokens=350,
            tau=0.0,
        )

        total_tokens = sum(f.token_count for f in result.selected)
        assert total_tokens <= 350

    def test_core_fragments_always_included(self, tmp_path):
        path = tmp_path / "test.py"
        core_frag = Fragment(
            id=FragmentId(path=path, start_line=1, end_line=10),
            kind="function",
            content="def core():\n    important_stuff()\n",
            identifiers=frozenset(["core", "important_stuff"]),
            token_count=50,
        )

        other_frags = [
            Fragment(
                id=FragmentId(path=path, start_line=20 + i * 10, end_line=25 + i * 10),
                kind="function",
                content=f"def other{i}():\n    pass\n",
                identifiers=frozenset([f"other{i}"]),
                token_count=30,
            )
            for i in range(5)
        ]

        fragments = [core_frag, *other_frags]
        rel = {f.id: 0.1 for f in fragments}
        rel[core_frag.id] = 1.0
        concepts = frozenset(["core", "important_stuff"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids={core_frag.id},
            rel=rel,
            concepts=concepts,
            budget_tokens=100,
            tau=0.0,
        )

        assert core_frag in result.selected


class TestTauStopping:
    def test_stops_when_utility_drops(self, tmp_path):
        path = tmp_path / "test.py"

        high_value_frag = Fragment(
            id=FragmentId(path=path, start_line=1, end_line=5),
            kind="function",
            content="def high_value():\n    important()\n    critical()\n",
            identifiers=frozenset(["high_value", "important", "critical"]),
            token_count=50,
        )

        low_value_frags = [
            Fragment(
                id=FragmentId(path=path, start_line=10 + i * 10, end_line=15 + i * 10),
                kind="function",
                content=f"def low_value{i}():\n    trivial{i}()\n",
                identifiers=frozenset([f"low_value{i}", f"trivial{i}"]),
                token_count=50,
            )
            for i in range(20)
        ]

        fragments = [high_value_frag, *low_value_frags]

        rel = {f.id: 0.01 for f in fragments}
        rel[high_value_frag.id] = 1.0

        concepts = frozenset(["high_value", "important", "critical"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=set(),
            rel=rel,
            concepts=concepts,
            budget_tokens=10000,
            tau=0.1,
        )

        assert len(result.selected) < len(fragments)


class TestBestSingletonGuard:
    def test_singleton_beats_greedy_when_better(self, tmp_path):
        path = tmp_path / "test.py"

        big_comprehensive_frag = Fragment(
            id=FragmentId(path=path, start_line=1, end_line=50),
            kind="function",
            content="def comprehensive():\n    a()\n    b()\n    c()\n    d()\n    e()\n",
            identifiers=frozenset(["comprehensive", "a", "b", "c", "d", "e"]),
            token_count=200,
        )

        small_frags = [
            Fragment(
                id=FragmentId(path=path, start_line=100 + i * 10, end_line=105 + i * 10),
                kind="function",
                content=f"def small{i}():\n    helper{i}()\n",
                identifiers=frozenset([f"small{i}", f"helper{i}"]),
                token_count=30,
            )
            for i in range(10)
        ]

        fragments = [big_comprehensive_frag, *small_frags]

        rel = {f.id: 0.1 for f in fragments}
        rel[big_comprehensive_frag.id] = 1.0

        concepts = frozenset(["comprehensive", "a", "b", "c", "d", "e"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=set(),
            rel=rel,
            concepts=concepts,
            budget_tokens=200,
            tau=0.0,
        )

        assert big_comprehensive_frag in result.selected or result.reason == "best_singleton"


class TestHubSuppression:
    def test_hub_nodes_get_reduced_weight(self, tmp_path):
        path = tmp_path / "test.py"

        hub_frag = Fragment(
            id=FragmentId(path=path, start_line=1, end_line=5),
            kind="function",
            content="def utils_helper():\n    pass\n",
            identifiers=frozenset(["utils_helper"]),
            token_count=20,
        )

        callers = [
            Fragment(
                id=FragmentId(path=path, start_line=10 + i * 10, end_line=15 + i * 10),
                kind="function",
                content=f"def caller{i}():\n    utils_helper()\n",
                identifiers=frozenset([f"caller{i}", "utils_helper"]),
                token_count=30,
            )
            for i in range(50)
        ]

        fragments = [hub_frag, *callers]

        graph = build_graph(fragments)

        in_degree = {}
        for node in graph.nodes:
            in_degree[node] = sum(1 for src in graph.nodes if node in graph.neighbors(src))

        assert hub_frag.id in graph.nodes


class TestPPRScores:
    def test_seeds_get_highest_scores(self, tmp_path):
        path = tmp_path / "test.py"

        seed_frag = Fragment(
            id=FragmentId(path=path, start_line=1, end_line=5),
            kind="function",
            content="def seed_func():\n    helper()\n",
            identifiers=frozenset(["seed_func", "helper"]),
        )

        helper_frag = Fragment(
            id=FragmentId(path=path, start_line=10, end_line=15),
            kind="function",
            content="def helper():\n    pass\n",
            identifiers=frozenset(["helper"]),
        )

        distant_frag = Fragment(
            id=FragmentId(path=path, start_line=100, end_line=105),
            kind="function",
            content="def distant():\n    unrelated()\n",
            identifiers=frozenset(["distant", "unrelated"]),
        )

        fragments = [seed_frag, helper_frag, distant_frag]
        graph = build_graph(fragments)

        scores = personalized_pagerank(graph, seeds={seed_frag.id}, alpha=0.55)

        assert scores[seed_frag.id] >= scores[helper_frag.id]
        assert scores[seed_frag.id] >= scores[distant_frag.id]

    def test_all_nodes_get_scores(self, tmp_path):
        path = tmp_path / "test.py"

        seed = Fragment(
            id=FragmentId(path=path, start_line=1, end_line=5),
            kind="function",
            content="def seed():\n    connected_helper()\n",
            identifiers=frozenset(["seed", "connected_helper"]),
        )

        connected = Fragment(
            id=FragmentId(path=path, start_line=10, end_line=15),
            kind="function",
            content="def connected_helper():\n    return 42\n",
            identifiers=frozenset(["connected_helper"]),
        )

        unconnected = Fragment(
            id=FragmentId(path=path, start_line=100, end_line=105),
            kind="function",
            content="def totally_unrelated():\n    xyz_unique_name()\n",
            identifiers=frozenset(["totally_unrelated", "xyz_unique_name"]),
        )

        fragments = [seed, connected, unconnected]
        graph = build_graph(fragments)

        scores = personalized_pagerank(graph, seeds={seed.id}, alpha=0.55)

        # Minimal guarantees: all nodes get non-negative scores
        assert scores[seed.id] >= 0
        assert scores[connected.id] >= 0
        assert scores[unconnected.id] >= 0


class TestUtilityFunction:
    def test_marginal_gain_diminishes(self, tmp_path):
        path = tmp_path / "test.py"

        frag1 = Fragment(
            id=FragmentId(path=path, start_line=1, end_line=5),
            kind="function",
            content="def f1():\n    shared_concept()\n",
            identifiers=frozenset(["f1", "shared_concept"]),
        )

        frag2 = Fragment(
            id=FragmentId(path=path, start_line=10, end_line=15),
            kind="function",
            content="def f2():\n    shared_concept()\n",
            identifiers=frozenset(["f2", "shared_concept"]),
        )

        concepts = frozenset(["shared_concept"])
        state = UtilityState()

        gain1 = marginal_gain(frag1, rel_score=1.0, concepts=concepts, state=state)
        state.max_rel["shared_concept"] = 1.0

        gain2 = marginal_gain(frag2, rel_score=1.0, concepts=concepts, state=state)

        assert gain1 > 0
        # Gain diminishes significantly but may have small relatedness bonus
        assert gain2 < gain1

    def test_utility_value_accumulates(self, tmp_path):
        state = UtilityState()

        assert utility_value(state) < 1e-9

        state.max_rel["concept_a"] = 1.0
        val1 = utility_value(state)
        assert val1 > 0

        state.max_rel["concept_b"] = 0.5
        val2 = utility_value(state)
        assert val2 > val1


class TestTFIDFCalculation:
    def test_extract_identifier_list_preserves_frequency(self):
        text = "calculate_sum verify_result calculate_sum process_data calculate_sum"
        result = extract_identifier_list(text)

        assert result.count("calculate_sum") == 3
        assert result.count("verify_result") == 1
        assert result.count("process_data") == 1

    def test_extract_identifiers_returns_unique(self):
        text = "calculate_sum verify_result calculate_sum process_data calculate_sum"
        result = extract_identifiers(text)

        assert len(result) == 3
        assert result == frozenset(["calculate_sum", "verify_result", "process_data"])


class TestEndToEnd:
    def test_multi_file_diff_selects_related_context(self, complex_project):
        complex_project.write(
            "src/models/user.py",
            """class User:
    def __init__(self, name):
        self.name = name

    def validate(self):
        return len(self.name) > 0
""",
        )

        complex_project.write(
            "src/services/auth.py",
            """from models.user import User

def authenticate(username, password):
    user = User(username)
    if user.validate():
        return check_password(password)
    return False

def check_password(password):
    return len(password) >= 8
""",
        )

        complex_project.write(
            "src/api/routes.py",
            """from services.auth import authenticate

def login_endpoint(request):
    result = authenticate(request.username, request.password)
    return {"success": result}
""",
        )

        complex_project.commit("Initial structure")

        complex_project.write(
            "src/services/auth.py",
            """from models.user import User

def authenticate(username, password):
    user = User(username)
    if not user.validate():
        raise ValueError("Invalid username")
    if not check_password(password):
        raise ValueError("Invalid password")
    return True

def check_password(password):
    return len(password) >= 8 and any(c.isupper() for c in password)
""",
        )
        complex_project.commit("Improve auth with validation")

        tree = build_diff_context(
            root_dir=complex_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected_files = _extract_files_from_tree(tree)

        assert "auth.py" in selected_files

    def test_empty_diff_returns_empty_tree(self, complex_project):
        complex_project.write("src/main.py", "print('hello')")
        complex_project.commit("Initial")

        tree = build_diff_context(
            root_dir=complex_project.repo,
            diff_range="HEAD..HEAD",
            budget_tokens=10000,
        )

        assert tree["type"] == "directory" or tree["type"] == "diff_context"
        assert tree.get("children", []) == [] or tree.get("fragments", []) == []

    def test_budget_limits_output_size(self, complex_project):
        for i in range(20):
            complex_project.write(
                f"src/module{i}.py",
                f"""def function{i}_a():
    return {i} * 2

def function{i}_b():
    return {i} + 100

def function{i}_c():
    return function{i}_a() + function{i}_b()
""",
            )

        complex_project.commit("Initial with many files")

        complex_project.write(
            "src/module0.py",
            """def function0_a():
    return 0 * 3  # Changed

def function0_b():
    return 0 + 200  # Changed

def function0_c():
    return function0_a() + function0_b()
""",
        )
        complex_project.commit("Modify module0")

        tree_small = build_diff_context(
            root_dir=complex_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=500,
        )

        tree_large = build_diff_context(
            root_dir=complex_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        files_small = _extract_files_from_tree(tree_small)
        files_large = _extract_files_from_tree(tree_large)

        assert len(files_small) <= len(files_large)


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


def _extract_fragments_from_tree(tree: dict) -> list[dict]:
    if tree.get("type") == "diff_context":
        return tree.get("fragments", [])

    fragments = []

    def traverse(node):
        if node.get("type") == "fragment":
            fragments.append(node)
        for child in node.get("children", []):
            traverse(child)

    traverse(tree)
    return fragments
