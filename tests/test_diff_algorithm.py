from __future__ import annotations

from pathlib import Path

import pytest

from tests.utils import DiffTestCase, DiffTestRunner
from treemapper.diffctx.fragments import enclosing_fragment, fragment_file
from treemapper.diffctx.graph import Graph, build_graph
from treemapper.diffctx.ppr import personalized_pagerank
from treemapper.diffctx.select import lazy_greedy_select
from treemapper.diffctx.types import Fragment, FragmentId
from treemapper.diffctx.utility import UtilityState, apply_fragment, marginal_gain, utility_value


def _make_fragment(
    path: str,
    start: int,
    end: int,
    kind: str = "function",
    content: str = "",
    identifiers: frozenset[str] | None = None,
    tokens: int = 50,
) -> Fragment:
    frag = Fragment(
        id=FragmentId(Path(path), start, end),
        kind=kind,
        content=content or f"content {start}-{end}",
        identifiers=identifiers or frozenset(content.split() if content else []),
    )
    frag.token_count = tokens
    return frag


PPR_TEST_CASES = [
    DiffTestCase(
        name="ppr_disconnected_components_seed_in_first",
        initial_files={
            "component_a.py": "def a1():\n    a2()\n\ndef a2():\n    pass\n",
            "component_b.py": "def b1():\n    b2()\n\ndef b2():\n    pass\n",
        },
        changed_files={
            "component_a.py": "def a1():\n    a2()\n    return 1\n\ndef a2():\n    pass\n",
        },
        must_include=["a1", "a2"],
    ),
    DiffTestCase(
        name="ppr_circular_dependencies",
        initial_files={
            "circular.py": "def alpha():\n    beta()\n\ndef beta():\n    alpha()\n",
        },
        changed_files={
            "circular.py": "def alpha():\n    beta()\n    return 1\n\ndef beta():\n    alpha()\n",
        },
        must_include=["alpha"],
    ),
]

GRAPH_TEST_CASES = [
    DiffTestCase(
        name="graph_import_edge_from_utils",
        initial_files={
            "utils.py": "def helper():\n    return 42\n",
            "main.py": "from utils import helper\n\ndef main():\n    return helper()\n",
        },
        changed_files={
            "main.py": "from utils import helper\n\ndef main():\n    return helper() + 1\n",
        },
        must_include=["main"],
    ),
    DiffTestCase(
        name="graph_test_file_to_source",
        initial_files={
            "calculator.py": "def add(a, b):\n    return a + b\n",
            "tests/test_calculator.py": "from calculator import add\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        },
        changed_files={
            "calculator.py": "def add(a, b):\n    return float(a) + float(b)\n",
        },
        must_include=["add"],
    ),
    DiffTestCase(
        name="graph_config_yaml_key_to_code",
        initial_files={
            "config.yaml": "database_host: localhost\ndatabase_port: 5432\n",
            "db.py": 'import os\n\ndatabase_host = os.getenv("DATABASE_HOST", "localhost")\n',
        },
        changed_files={
            "config.yaml": "database_host: db.example.com\ndatabase_port: 5432\n",
        },
        must_include=["database_host"],
    ),
    DiffTestCase(
        name="graph_markdown_anchor_link",
        initial_files={
            "docs.md": "# Introduction\n\nSee [Installation](#installation).\n\n# Installation\n\nRun `pip install package`.\n",
        },
        changed_files={
            "docs.md": "# Introduction\n\nSee [Installation](#installation).\n\n# Installation\n\nRun `pip install package-v2`.\n",
        },
        must_include=["Installation"],
    ),
    DiffTestCase(
        name="graph_citation_shared_reference",
        initial_files={
            "paper.md": "# Methods\n\nAccording to [@smith2020], the approach works.\n\n# Results\n\nAs shown by [@smith2020], results are positive.\n",
        },
        changed_files={
            "paper.md": "# Methods\n\nAccording to [@smith2020], the MODIFIED approach works.\n\n# Results\n\nAs shown by [@smith2020], results are positive.\n",
        },
        must_include=["Methods"],
    ),
]

FRAGMENT_TEST_CASES = [
    DiffTestCase(
        name="fragment_decorator_included",
        initial_files={
            "decorated.py": "@decorator\ndef my_function():\n    pass\n",
        },
        changed_files={
            "decorated.py": "@decorator\ndef my_function():\n    return 42\n",
        },
        must_include=["@decorator", "my_function"],
        add_garbage_files=False,
    ),
    DiffTestCase(
        name="fragment_multiple_decorators_all_included",
        initial_files={
            "multi_dec.py": "@decorator1\n@decorator2\n@decorator3\ndef decorated_func():\n    pass\n",
        },
        changed_files={
            "multi_dec.py": "@decorator1\n@decorator2\n@decorator3\ndef decorated_func():\n    return 1\n",
        },
        must_include=["@decorator1", "@decorator2", "@decorator3", "decorated_func"],
        add_garbage_files=False,
    ),
    DiffTestCase(
        name="fragment_class_decorator_included",
        initial_files={
            "decorated_class.py": "@dataclass\nclass MyClass:\n    value: int\n",
        },
        changed_files={
            "decorated_class.py": "@dataclass\nclass MyClass:\n    value: int\n    name: str\n",
        },
        must_include=["@dataclass", "MyClass"],
        add_garbage_files=False,
    ),
    DiffTestCase(
        name="fragment_markdown_section",
        initial_files={
            "docs.md": "# Main Section\n\nThis is a large section.\nLine 1\nLine 2\n",
        },
        changed_files={
            "docs.md": "# Main Section\n\nThis is a MODIFIED section.\nLine 1\nLine 2\n",
        },
        must_include=["# Main Section"],
        add_garbage_files=False,
    ),
    DiffTestCase(
        name="fragment_env_file_change",
        initial_files={
            "app.py": 'import os\n\nDEBUG = os.getenv("DEBUG", False)\n\ndef main():\n    if DEBUG:\n        print("Debug mode")\n',
            ".env": "DEBUG=false\n",
        },
        changed_files={
            ".env": "DEBUG=true\n",
        },
        must_include=[".env"],
        add_garbage_files=False,
    ),
]

SELECTION_TEST_CASES = [
    DiffTestCase(
        name="selection_core_hunk_inside_function",
        initial_files={
            "module.py": "def long_function():\n    line1 = 1\n    line2 = 2\n    line3 = 3\n    line4 = 4\n    return line4\n",
        },
        changed_files={
            "module.py": "def long_function():\n    line1 = 1\n    modified = 'changed'\n    line3 = 3\n    line4 = 4\n    return line4\n",
        },
        must_include=["long_function"],
    ),
    DiffTestCase(
        name="selection_new_function_added",
        initial_files={
            "add_test.py": "def func1():\n    pass\n\ndef func2():\n    pass\n",
        },
        changed_files={
            "add_test.py": "def func1():\n    pass\n\ndef new_function():\n    x = 1\n    y = 2\n    return x + y\n\ndef func2():\n    pass\n",
        },
        must_include=["new_function"],
    ),
    DiffTestCase(
        name="selection_new_function_at_end",
        initial_files={
            "calculator.py": "def add(a, b):\n    return a + b\n\ndef sub(a, b):\n    return a - b\n\ndef mul(a, b):\n    return a * b\n",
        },
        changed_files={
            "calculator.py": "def add(a, b):\n    return a + b\n\ndef sub(a, b):\n    return a - b\n\ndef mul(a, b):\n    return a * b\n\ndef div(a, b):\n    if b == 0:\n        raise ValueError('division by zero')\n    return a / b\n",
        },
        must_include=["def div"],
        must_not_include=["def mul"],
    ),
    DiffTestCase(
        name="selection_rare_identifier_expansion",
        initial_files={
            "core.py": "from rare_module import unique_helper\n\ndef main():\n    return unique_helper()\n",
            "rare_module.py": "def unique_helper():\n    return 42\n",
        },
        changed_files={
            "core.py": "from rare_module import unique_helper\n\ndef main():\n    result = unique_helper()\n    return result * 2\n",
        },
        must_include=["main"],
    ),
]

OUTPUT_TEST_CASES = [
    DiffTestCase(
        name="output_required_fields_present",
        initial_files={
            "module.py": "def my_function():\n    return 42\n",
        },
        changed_files={
            "module.py": "def my_function():\n    return 100\n",
        },
        must_include=["my_function"],
        add_garbage_files=False,
    ),
    DiffTestCase(
        name="output_sorted_by_path",
        initial_files={
            "z_module.py": "def z_func():\n    pass\n",
            "a_module.py": "def a_func():\n    pass\n",
        },
        changed_files={
            "z_module.py": "def z_func():\n    return 1\n",
            "a_module.py": "def a_func():\n    return 1\n",
        },
        must_include=["z_func", "a_func"],
        add_garbage_files=False,
    ),
]

MERGING_TEST_CASES = [
    DiffTestCase(
        name="merge_adjacent_same_file",
        initial_files={
            "adjacent.py": "def func1():\n    return 1\n\ndef func2():\n    return 2\n\ndef func3():\n    return 3\n",
        },
        changed_files={
            "adjacent.py": "def func1():\n    return 10\n\ndef func2():\n    return 20\n\ndef func3():\n    return 3\n",
        },
        must_include=["func1", "func2"],
    ),
    DiffTestCase(
        name="merge_nested_class_method",
        initial_files={
            "nested.py": "class Container:\n    def method1(self):\n        pass\n\n    def method2(self):\n        pass\n",
        },
        changed_files={
            "nested.py": "class Container:\n    def method1(self):\n        return 1\n\n    def method2(self):\n        pass\n",
        },
        must_include=["method1"],
    ),
    DiffTestCase(
        name="merge_multiple_scattered_changes",
        initial_files={
            "module.py": "import os\n\nCONFIG = 'default'\n\ndef func1():\n    return 1\n\ndef func2():\n    return 2\n\ndef func3():\n    return 3\n\nclass Helper:\n    def method(self):\n        pass\n",
        },
        changed_files={
            "module.py": "import os\n\nCONFIG = 'modified'\n\ndef func1():\n    return 10\n\ndef func2():\n    return 2\n\ndef func3():\n    return 30\n\nclass Helper:\n    def method(self):\n        return True\n",
        },
        must_include=["func1", "func3"],
    ),
]

ALL_ALGORITHM_TEST_CASES = (
    PPR_TEST_CASES + GRAPH_TEST_CASES + FRAGMENT_TEST_CASES + SELECTION_TEST_CASES + OUTPUT_TEST_CASES + MERGING_TEST_CASES
)


@pytest.mark.parametrize("case", ALL_ALGORITHM_TEST_CASES, ids=lambda c: c.name)
def test_algorithm_cases(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)


class TestPPRGraphStructure:
    def test_no_path_from_core_to_candidate(self, tmp_path):
        path = tmp_path / "test.py"
        frag_a = _make_fragment(str(path), 1, 5, identifiers=frozenset(["func_a", "unique_a"]))
        path_b = tmp_path / "other.py"
        frag_b = _make_fragment(str(path_b), 1, 5, identifiers=frozenset(["func_b", "unique_b"]))

        graph = build_graph([frag_a, frag_b])
        scores = personalized_pagerank(graph, seeds={frag_a.id}, alpha=0.6)

        assert scores[frag_a.id] > scores[frag_b.id]

    def test_hub_node_dominance(self, tmp_path):
        path = tmp_path / "test.py"
        hub_frag = _make_fragment(str(path), 1, 5, identifiers=frozenset(["utils_helper"]), tokens=20)
        callers = [
            _make_fragment(str(path), 10 + i * 10, 15 + i * 10, identifiers=frozenset([f"caller{i}", "utils_helper"]), tokens=30)
            for i in range(20)
        ]

        graph = build_graph([hub_frag, *callers])
        scores = personalized_pagerank(graph, seeds={callers[0].id}, alpha=0.6)

        assert scores[callers[0].id] > 0


class TestPPRConvergence:
    def test_large_sparse_graph(self, tmp_path):
        fragments = [
            _make_fragment(
                str(tmp_path / "test.py"),
                i * 10 + 1,
                i * 10 + 5,
                identifiers=frozenset([f"func{i}", f"func{i-1}"]) if i > 0 else frozenset([f"func{i}"]),
            )
            for i in range(100)
        ]
        graph = build_graph(fragments)
        scores = personalized_pagerank(graph, seeds={fragments[0].id}, alpha=0.6, max_iter=50)

        assert len(scores) == len(fragments)
        assert all(s >= 0 for s in scores.values())

    def test_dense_small_graph(self, tmp_path):
        path = tmp_path / "dense.py"
        shared_idents = frozenset([f"shared{i}" for i in range(5)])
        fragments = [
            _make_fragment(str(path), i * 10 + 1, i * 10 + 5, identifiers=shared_idents | frozenset([f"func{i}"]))
            for i in range(20)
        ]

        graph = build_graph(fragments)
        scores = personalized_pagerank(graph, seeds={fragments[0].id}, alpha=0.6)

        assert len(scores) == len(fragments)
        assert all(s >= 0 for s in scores.values())

    def test_converges_within_tolerance(self):
        frags = [
            _make_fragment("a.py", 1, 10, identifiers=frozenset(["func_a"])),
            _make_fragment("b.py", 1, 10, identifiers=frozenset(["func_b", "func_a"])),
            _make_fragment("c.py", 1, 10, identifiers=frozenset(["func_c", "func_b"])),
        ]
        graph = build_graph(frags)
        scores = personalized_pagerank(graph, seeds={frags[0].id}, alpha=0.6, tol=1e-4, max_iter=50)

        assert len(scores) == len(frags)
        for score in scores.values():
            assert 0 <= score <= 1

    def test_max_iterations_respected(self):
        frags = [_make_fragment(f"mod{i}.py", 1, 10, identifiers=frozenset([f"func{i}"])) for i in range(10)]
        graph = build_graph(frags)
        scores = personalized_pagerank(graph, seeds={frags[0].id}, alpha=0.99, tol=1e-20, max_iter=5)

        assert len(scores) == len(frags)


class TestPPRParameters:
    def test_alpha_affects_distribution(self):
        frag_a = _make_fragment("a.py", 1, 10, identifiers=frozenset(["shared", "func_a"]))
        frag_b = _make_fragment("b.py", 1, 10, identifiers=frozenset(["shared", "func_b"]))
        frag_c = _make_fragment("c.py", 1, 10, identifiers=frozenset(["shared", "func_c"]))

        graph = Graph()
        graph.add_node(frag_a.id)
        graph.add_node(frag_b.id)
        graph.add_node(frag_c.id)
        graph.add_edge(frag_a.id, frag_b.id, 0.5)
        graph.add_edge(frag_b.id, frag_c.id, 0.5)

        scores_low_alpha = personalized_pagerank(graph, seeds={frag_a.id}, alpha=0.3)
        scores_high_alpha = personalized_pagerank(graph, seeds={frag_a.id}, alpha=0.9)

        assert scores_low_alpha[frag_a.id] != scores_high_alpha[frag_a.id]

    def test_empty_seeds_returns_uniform(self, tmp_path):
        fragments = [_make_fragment(str(tmp_path / "test.py"), i * 10 + 1, i * 10 + 5) for i in range(5)]
        graph = build_graph(fragments)
        scores = personalized_pagerank(graph, seeds=set(), alpha=0.6)

        values = list(scores.values())
        assert len({round(v, 6) for v in values}) <= 2

    def test_single_node_graph(self, tmp_path):
        frag = _make_fragment(str(tmp_path / "single.py"), 1, 5, identifiers=frozenset(["only"]))
        graph = build_graph([frag])
        scores = personalized_pagerank(graph, seeds={frag.id}, alpha=0.6)

        assert abs(scores[frag.id] - 1.0) < 1e-9

    def test_alpha_zero_pure_personalization(self):
        frags = [
            _make_fragment("seed.py", 1, 10, identifiers=frozenset(["shared"])),
            _make_fragment("other.py", 1, 10, identifiers=frozenset(["shared"])),
        ]
        graph = build_graph(frags)
        scores = personalized_pagerank(graph, seeds={frags[0].id}, alpha=0.0)

        assert scores[frags[0].id] == pytest.approx(1.0, rel=1e-6)


class TestPPRSeeds:
    def test_multiple_seeds(self, tmp_path):
        fragments = [
            _make_fragment(str(tmp_path / "multi.py"), i * 10 + 1, i * 10 + 5, identifiers=frozenset([f"func{i}"]))
            for i in range(5)
        ]
        graph = build_graph(fragments)
        seeds = {fragments[0].id, fragments[2].id}
        scores = personalized_pagerank(graph, seeds=seeds, alpha=0.6)

        assert scores[fragments[0].id] > 0
        assert scores[fragments[2].id] > 0

    def test_seeds_not_in_graph_filtered(self, tmp_path):
        frag = _make_fragment(str(tmp_path / "test.py"), 1, 5, identifiers=frozenset(["func"]))
        fake_id = FragmentId(path=Path(str(tmp_path / "test.py")), start_line=100, end_line=105)
        graph = build_graph([frag])
        scores = personalized_pagerank(graph, seeds={frag.id, fake_id}, alpha=0.6)

        assert frag.id in scores

    def test_invalid_seeds_filtered(self):
        frags = [_make_fragment("a.py", 1, 10, identifiers=frozenset(["func_a"]))]
        graph = build_graph(frags)
        invalid_seed = FragmentId(Path("nonexistent.py"), 1, 10)
        scores = personalized_pagerank(graph, seeds={invalid_seed}, alpha=0.6)

        assert len(scores) == len(frags)


class TestPPRNormalization:
    def test_scores_sum_to_one(self):
        frags = [_make_fragment(f"mod{i}.py", 1, 10, identifiers=frozenset([f"func{i}"])) for i in range(5)]
        graph = build_graph(frags)
        scores = personalized_pagerank(graph, seeds={frags[0].id, frags[2].id}, alpha=0.6)

        total = sum(scores.values())
        assert abs(total - 1.0) < 1e-6

    def test_all_scores_non_negative(self):
        frags = [_make_fragment(f"mod{i}.py", 1, 10, identifiers=frozenset([f"func{i % 3}"])) for i in range(10)]
        graph = build_graph(frags)
        scores = personalized_pagerank(graph, seeds={frags[0].id}, alpha=0.6)

        for score in scores.values():
            assert score >= 0


class TestPPRDeterminism:
    def test_same_input_same_output(self):
        frags = [
            _make_fragment("a.py", 1, 10, identifiers=frozenset(["shared", "func_a"])),
            _make_fragment("b.py", 1, 10, identifiers=frozenset(["shared", "func_b"])),
            _make_fragment("c.py", 1, 10, identifiers=frozenset(["func_c"])),
        ]
        graph = build_graph(frags)
        seeds = {frags[0].id}

        results = [personalized_pagerank(graph, seeds, alpha=0.6, tol=1e-6) for _ in range(5)]
        for result in results[1:]:
            assert result == results[0]


class TestPPREmptyGraph:
    def test_empty_graph_returns_empty(self):
        graph = Graph()
        scores = personalized_pagerank(graph, seeds=set(), alpha=0.6)
        assert scores == {}

    def test_single_node_graph_self_reference(self):
        frag = _make_fragment("single.py", 1, 10)
        graph = Graph()
        graph.add_node(frag.id)
        scores = personalized_pagerank(graph, {frag.id}, alpha=0.6)

        assert len(scores) == 1
        assert scores[frag.id] == pytest.approx(1.0, rel=1e-6)


class TestPPRDanglingNodes:
    def test_no_outgoing_edges(self):
        frag_hub = _make_fragment("hub.py", 1, 10, identifiers=frozenset(["hub"]))
        frag_leaf1 = _make_fragment("leaf1.py", 1, 10, identifiers=frozenset(["hub"]))
        frag_leaf2 = _make_fragment("leaf2.py", 1, 10, identifiers=frozenset(["hub"]))

        graph = Graph()
        graph.add_node(frag_hub.id)
        graph.add_node(frag_leaf1.id)
        graph.add_node(frag_leaf2.id)
        graph.add_edge(frag_hub.id, frag_leaf1.id, 1.0)
        graph.add_edge(frag_hub.id, frag_leaf2.id, 1.0)

        scores = personalized_pagerank(graph, {frag_hub.id}, alpha=0.6)

        assert len(scores) == 3
        assert abs(sum(scores.values()) - 1.0) < 1e-6

    def test_all_dangling(self):
        frags = [_make_fragment(f"isolated{i}.py", 1, 10) for i in range(3)]
        graph = Graph()
        for frag in frags:
            graph.add_node(frag.id)

        scores = personalized_pagerank(graph, {frags[0].id}, alpha=0.6)

        assert len(scores) == 3
        assert abs(sum(scores.values()) - 1.0) < 1e-6


class TestPPRCircularDependencies:
    def test_cycle_handled(self):
        frag_a = _make_fragment("a.py", 1, 10, identifiers=frozenset(["func_b"]))
        frag_b = _make_fragment("b.py", 1, 10, identifiers=frozenset(["func_c"]))
        frag_c = _make_fragment("c.py", 1, 10, identifiers=frozenset(["func_a"]))

        graph = Graph()
        graph.add_node(frag_a.id)
        graph.add_node(frag_b.id)
        graph.add_node(frag_c.id)
        graph.add_edge(frag_a.id, frag_b.id, 0.5)
        graph.add_edge(frag_b.id, frag_c.id, 0.5)
        graph.add_edge(frag_c.id, frag_a.id, 0.5)

        scores = personalized_pagerank(graph, {frag_a.id}, alpha=0.6)

        assert len(scores) == 3
        assert abs(sum(scores.values()) - 1.0) < 1e-6


class TestPPRDisconnectedComponents:
    def test_separate_components(self):
        comp1 = [
            _make_fragment("comp1_a.py", 1, 10, identifiers=frozenset(["shared1"])),
            _make_fragment("comp1_b.py", 1, 10, identifiers=frozenset(["shared1"])),
        ]
        comp2 = [
            _make_fragment("comp2_a.py", 1, 10, identifiers=frozenset(["shared2"])),
            _make_fragment("comp2_b.py", 1, 10, identifiers=frozenset(["shared2"])),
        ]

        all_frags = comp1 + comp2
        graph = build_graph(all_frags)
        scores = personalized_pagerank(graph, seeds={comp1[0].id}, alpha=0.6)

        comp1_total = sum(scores.get(f.id, 0) for f in comp1)
        comp2_total = sum(scores.get(f.id, 0) for f in comp2)
        assert comp1_total >= comp2_total


class TestPPRWeightedEdges:
    def test_higher_weight_more_flow(self):
        frag_src = _make_fragment("src.py", 1, 10)
        frag_high = _make_fragment("high.py", 1, 10)
        frag_low = _make_fragment("low.py", 1, 10)

        graph = Graph()
        graph.add_node(frag_src.id)
        graph.add_node(frag_high.id)
        graph.add_node(frag_low.id)
        graph.add_edge(frag_src.id, frag_high.id, 0.9)
        graph.add_edge(frag_src.id, frag_low.id, 0.1)

        scores = personalized_pagerank(graph, {frag_src.id}, alpha=0.8)

        assert scores[frag_high.id] > scores[frag_low.id]


class TestPPRLargeGraph:
    def test_scalability(self):
        n = 100
        frags = [_make_fragment(f"mod{i}.py", 1, 10, identifiers=frozenset([f"func{i % 10}"])) for i in range(n)]
        graph = build_graph(frags)
        scores = personalized_pagerank(graph, seeds={frags[0].id, frags[50].id}, alpha=0.6, max_iter=50)

        assert len(scores) == n
        assert abs(sum(scores.values()) - 1.0) < 1e-5


class TestGraphEdges:
    def test_function_call_creates_edge(self):
        caller = _make_fragment(
            "caller.py", 1, 10, content="def main():\n    helper()\n", identifiers=frozenset(["main", "helper"])
        )
        callee = _make_fragment("callee.py", 1, 10, content="def helper():\n    return 42\n", identifiers=frozenset(["helper"]))

        graph = build_graph([caller, callee])

        assert caller.id in graph.nodes
        assert callee.id in graph.nodes

    def test_method_call_creates_edge(self):
        caller = _make_fragment(
            "caller.py",
            1,
            10,
            content="def use_service():\n    service.process()\n",
            identifiers=frozenset(["use_service", "service", "process"]),
        )
        service = _make_fragment(
            "service.py",
            1,
            10,
            content="class Service:\n    def process(self):\n        pass\n",
            identifiers=frozenset(["Service", "process"]),
        )

        graph = build_graph([caller, service])

        assert caller.id in graph.nodes
        assert service.id in graph.nodes

    def test_variable_reference(self):
        definer = _make_fragment("constants.py", 1, 5, content="CONFIG_VALUE = 42\n", identifiers=frozenset(["CONFIG_VALUE"]))
        user = _make_fragment(
            "app.py", 1, 10, content="def main():\n    x = CONFIG_VALUE\n", identifiers=frozenset(["main", "CONFIG_VALUE"])
        )

        graph = build_graph([definer, user])

        assert definer.id in graph.nodes
        assert user.id in graph.nodes

    def test_no_self_reference(self):
        frag = _make_fragment("module.py", 1, 10, content="def func():\n    func()\n", identifiers=frozenset(["func"]))
        graph = build_graph([frag])
        neighbors = graph.neighbors(frag.id)
        assert frag.id not in neighbors


class TestFragmentFile:
    def test_nested_function_creates_separate_fragment(self, tmp_path):
        code = "def outer():\n    x = 1\n    def inner():\n        return x\n    return inner()\n"
        file_path = tmp_path / "nested.py"
        file_path.write_text(code)

        fragments = fragment_file(file_path, code)
        function_frags = [f for f in fragments if f.kind == "function"]
        assert len(function_frags) >= 2

    def test_deeply_nested_functions(self, tmp_path):
        code = "def level1():\n    def level2():\n        def level3():\n            return 42\n        return level3()\n    return level2()\n"
        file_path = tmp_path / "deep_nested.py"
        file_path.write_text(code)

        fragments = fragment_file(file_path, code)
        function_frags = [f for f in fragments if f.kind == "function"]
        assert len(function_frags) >= 3

    def test_module_gap_before_first_def(self, tmp_path):
        code = 'import os\nimport sys\n\nCONFIG_PATH = "/etc/app.conf"\nDEBUG = True\n\ndef main():\n    pass\n'
        file_path = tmp_path / "with_gap.py"
        file_path.write_text(code)

        fragments = fragment_file(file_path, code)
        chunk_frags = [f for f in fragments if f.kind == "chunk"]
        assert len(chunk_frags) >= 1
        assert "import os" in chunk_frags[0].content

    def test_syntax_error_fallback_to_generic(self, tmp_path):
        code = "def broken(:\n    x = [1, 2\n    return x\n"
        file_path = tmp_path / "broken.py"
        file_path.write_text(code)

        fragments = fragment_file(file_path, code)
        assert len(fragments) >= 1
        assert fragments[0].kind == "chunk"

    def test_async_function_handled(self, tmp_path):
        code = "async def async_handler():\n    await something()\n    return result\n"
        file_path = tmp_path / "async_code.py"
        file_path.write_text(code)

        fragments = fragment_file(file_path, code)
        async_frags = [f for f in fragments if f.kind == "function"]
        assert len(async_frags) >= 1
        assert "async def" in async_frags[0].content

    def test_async_with_decorator(self, tmp_path):
        code = "@async_decorator\nasync def decorated_async():\n    await other()\n"
        file_path = tmp_path / "async_decorated.py"
        file_path.write_text(code)

        fragments = fragment_file(file_path, code)
        async_frags = [f for f in fragments if f.kind == "function"]
        assert len(async_frags) >= 1
        assert "@async_decorator" in async_frags[0].content

    def test_generic_chunk_200_lines(self, tmp_path):
        lines = [f"line {i}" for i in range(1, 251)]
        code = "\n".join(lines)
        file_path = tmp_path / "large.tex"
        file_path.write_text(code)

        fragments = fragment_file(file_path, code)
        assert len(fragments) >= 2
        first_frag = fragments[0]
        assert first_frag.kind == "chunk"
        assert first_frag.start_line == 1

    def test_yaml_top_level_keys(self, tmp_path):
        code = "database:\n  host: localhost\n  port: 5432\n\nserver:\n  port: 8080\n  debug: true\n"
        file_path = tmp_path / "config.yaml"
        file_path.write_text(code)

        fragments = fragment_file(file_path, code)
        assert len(fragments) >= 2

    def test_toml_sections(self, tmp_path):
        code = '[database]\nhost = "localhost"\nport = 5432\n\n[server]\nport = 8080\ndebug = true\n'
        file_path = tmp_path / "config.toml"
        file_path.write_text(code)

        fragments = fragment_file(file_path, code)
        assert len(fragments) >= 2


class TestEnclosingFragment:
    def test_find_smallest_covering(self, tmp_path):
        code = "class MyClass:\n    def method1(self):\n        pass\n\n    def method2(self):\n        x = 1\n        y = 2\n        return x + y\n\n    def method3(self):\n        pass\n"
        file_path = tmp_path / "enclosing.py"
        file_path.write_text(code)

        fragments = fragment_file(file_path, code)
        enclosing = enclosing_fragment(fragments, 7)
        assert enclosing is not None
        assert "method2" in enclosing.content

    def test_no_match_returns_none(self, tmp_path):
        code = "def func():\n    pass\n"
        file_path = tmp_path / "small.py"
        file_path.write_text(code)

        fragments = fragment_file(file_path, code)
        enclosing = enclosing_fragment(fragments, 100)
        assert enclosing is None


class TestLazyGreedySelect:
    def test_respects_token_limit(self):
        fragments = [
            _make_fragment("a.py", 1, 10, content="func_a code", tokens=500),
            _make_fragment("b.py", 1, 10, content="func_b code", tokens=500),
            _make_fragment("c.py", 1, 10, content="func_c code", tokens=500),
        ]
        core_ids = {fragments[0].id}
        rel = {f.id: 1.0 for f in fragments}
        concepts = frozenset(["func_a", "func_b", "func_c"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=core_ids,
            rel=rel,
            concepts=concepts,
            budget_tokens=800,
            tau=0.0,
        )

        total_tokens = sum(f.token_count for f in result.selected)
        assert total_tokens <= 800

    def test_core_larger_than_budget_partial(self):
        fragments = [
            _make_fragment("big.py", 1, 100, content="huge_function", tokens=2000),
            _make_fragment("small.py", 1, 10, content="tiny_func", tokens=100),
        ]
        core_ids = {fragments[0].id}
        rel = {f.id: 1.0 for f in fragments}
        concepts = frozenset(["huge_function", "tiny_func"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=core_ids,
            rel=rel,
            concepts=concepts,
            budget_tokens=500,
            tau=0.0,
        )

        assert result.reason in ("budget_exhausted", "no_candidates", "best_singleton")

    def test_zero_tau_no_early_stop(self):
        fragments = [
            _make_fragment("a.py", 1, 10, content="high_value code", tokens=100),
            _make_fragment("b.py", 1, 10, content="medium_value code", tokens=100),
            _make_fragment("c.py", 1, 10, content="low_value code", tokens=100),
        ]
        core_ids = set()
        rel = {
            fragments[0].id: 1.0,
            fragments[1].id: 0.5,
            fragments[2].id: 0.1,
        }
        concepts = frozenset(["high_value", "medium_value", "low_value"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=core_ids,
            rel=rel,
            concepts=concepts,
            budget_tokens=10000,
            tau=0.0,
        )

        assert result.reason != "stopped_by_tau"

    def test_no_candidates_empty_input(self):
        result = lazy_greedy_select(
            fragments=[],
            core_ids=set(),
            rel={},
            concepts=frozenset(),
            budget_tokens=10000,
            tau=0.0,
        )

        assert result.reason == "no_candidates"
        assert len(result.selected) == 0

    def test_budget_exhausted(self):
        fragments = [
            _make_fragment("a.py", 1, 10, content="func_a", tokens=200),
            _make_fragment("b.py", 1, 10, content="func_b", tokens=200),
            _make_fragment("c.py", 1, 10, content="func_c", tokens=200),
            _make_fragment("d.py", 1, 10, content="func_d", tokens=200),
        ]
        core_ids = {fragments[0].id}
        rel = {f.id: 1.0 for f in fragments}
        concepts = frozenset(["func_a", "func_b", "func_c", "func_d"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=core_ids,
            rel=rel,
            concepts=concepts,
            budget_tokens=500,
            tau=0.0,
        )

        assert result.reason in ("budget_exhausted", "no_candidates")
        assert len(result.selected) >= 1
        assert sum(f.token_count for f in result.selected) <= 500

    def test_budget_fully_exhausted(self):
        fragments = [
            _make_fragment("a.py", 1, 10, content="func_a", tokens=250),
            _make_fragment("b.py", 1, 10, content="func_b", tokens=250),
            _make_fragment("c.py", 1, 10, content="func_c", tokens=250),
        ]
        core_ids = {fragments[0].id, fragments[1].id}
        rel = {f.id: 1.0 for f in fragments}
        concepts = frozenset(["func_a", "func_b", "func_c"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=core_ids,
            rel=rel,
            concepts=concepts,
            budget_tokens=500,
            tau=0.0,
        )

        assert result.reason == "budget_exhausted"
        assert result.used_tokens == 500
        assert len(result.selected) == 2


class TestUtilityFunctions:
    def test_marginal_gain_diminishes(self):
        frag = _make_fragment("a.py", 1, 10, content="concept_a concept_b", tokens=100)
        concepts = frozenset(["concept_a", "concept_b"])
        state = UtilityState()

        gain1 = marginal_gain(frag, 1.0, concepts, state)
        apply_fragment(frag, 1.0, concepts, state)

        gain2 = marginal_gain(frag, 1.0, concepts, state)

        assert gain2 < gain1

    def test_utility_value_accumulates(self):
        frag1 = _make_fragment("a.py", 1, 10, content="concept_a", tokens=100)
        frag2 = _make_fragment("b.py", 1, 10, content="concept_b", tokens=100)
        concepts = frozenset(["concept_a", "concept_b"])
        state = UtilityState()

        val0 = utility_value(state)
        apply_fragment(frag1, 1.0, concepts, state)
        val1 = utility_value(state)
        apply_fragment(frag2, 1.0, concepts, state)
        val2 = utility_value(state)

        assert val0 < 1e-9
        assert val1 > val0
        assert val2 > val1

    def test_empty_concepts_fallback(self):
        frag = _make_fragment("a.py", 1, 10, content="some content", tokens=100)
        concepts = frozenset()
        state = UtilityState()

        gain = marginal_gain(frag, 0.5, concepts, state)

        assert gain == pytest.approx(0.05, rel=0.01)


class TestMergingFragments:
    def test_function_class_separate(self, tmp_path):
        code = "def standalone_function():\n    return 1\n\nclass MyClass:\n    def method(self):\n        pass\n"
        file_path = tmp_path / "mixed.py"
        file_path.write_text(code)

        fragments = fragment_file(file_path, code)

        function_frags = [f for f in fragments if f.kind == "function"]
        class_frags = [f for f in fragments if f.kind == "class"]

        assert len(function_frags) >= 1
        assert len(class_frags) >= 1

    def test_no_partial_overlap(self, tmp_path):
        code = "class BigClass:\n    def method1(self):\n        x = 1\n        y = 2\n        return x + y\n\n    def method2(self):\n        a = 1\n        b = 2\n        return a * b\n"
        file_path = tmp_path / "overlapping.py"
        file_path.write_text(code)

        fragments = fragment_file(file_path, code)

        for i, f1 in enumerate(fragments):
            for f2 in fragments[i + 1 :]:
                if f1.path == f2.path:
                    f1_range = set(range(f1.start_line, f1.end_line + 1))
                    f2_range = set(range(f2.start_line, f2.end_line + 1))
                    overlap = f1_range & f2_range
                    assert not (
                        overlap and f1_range != overlap and f2_range != overlap
                    ), f"Partial overlap detected: {f1.id} and {f2.id}"

    def test_yaml_sections_separate(self, tmp_path):
        code = "database:\n  host: localhost\n  port: 5432\n  name: mydb\n\nlogging:\n  level: INFO\n  format: json\n\nserver:\n  port: 8080\n  workers: 4\n"
        file_path = tmp_path / "config.yaml"
        file_path.write_text(code)

        fragments = fragment_file(file_path, code)
        assert len(fragments) >= 2

    def test_markdown_heading_hierarchy(self, tmp_path):
        code = "# Level 1\n\nContent under level 1.\n\n## Level 2\n\nContent under level 2.\n\n### Level 3\n\nContent under level 3.\n\n## Another Level 2\n\nMore content.\n"
        file_path = tmp_path / "hierarchy.md"
        file_path.write_text(code)

        fragments = fragment_file(file_path, code)
        assert len(fragments) >= 1

    def test_single_line_gap(self, tmp_path):
        code = "def func1():\n    pass\n\ndef func2():\n    pass\n"
        file_path = tmp_path / "single_gap.py"
        file_path.write_text(code)

        fragments = fragment_file(file_path, code)
        function_frags = [f for f in fragments if f.kind == "function"]
        assert len(function_frags) >= 2

    def test_no_gap(self, tmp_path):
        code = "def func1():\n    pass\ndef func2():\n    pass\n"
        file_path = tmp_path / "no_gap.py"
        file_path.write_text(code)

        fragments = fragment_file(file_path, code)
        function_frags = [f for f in fragments if f.kind == "function"]
        assert len(function_frags) >= 2


class TestBestSingletonSelection:
    def test_greedy_prefers_multiple_small_over_single_large(self):
        small_frags = [_make_fragment(f"small{i}.py", 1, 10, content=f"small_concept_{i}", tokens=50) for i in range(10)]
        big_frag = _make_fragment("big.py", 1, 100, content="big_valuable_concept", tokens=400)

        fragments = [*small_frags, big_frag]
        core_ids: set[FragmentId] = set()
        rel = {f.id: 0.1 for f in small_frags}
        rel[big_frag.id] = 1.0
        concepts = frozenset([f"small_concept_{i}" for i in range(10)] + ["big_valuable_concept"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=core_ids,
            rel=rel,
            concepts=concepts,
            budget_tokens=500,
            tau=0.0,
        )

        assert len(result.selected) >= 5
        assert result.utility > 0

    def test_singleton_path_with_constrained_budget(self):
        core = _make_fragment("core.py", 1, 10, content="core_concept", tokens=200)
        greedy_candidate = _make_fragment("small.py", 1, 10, content="small_concept", tokens=50)
        singleton_candidate = _make_fragment("single.py", 1, 10, content="single_concept", tokens=150)

        fragments = [core, greedy_candidate, singleton_candidate]
        core_ids = {core.id}
        rel = {core.id: 1.0, greedy_candidate.id: 0.1, singleton_candidate.id: 0.9}
        concepts = frozenset(["core_concept", "small_concept", "single_concept"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=core_ids,
            rel=rel,
            concepts=concepts,
            budget_tokens=400,
            tau=0.0,
        )

        assert core in result.selected
        assert result.utility > 0

    def test_singleton_not_better_than_greedy(self):
        fragments = [
            _make_fragment("a.py", 1, 10, content="concept_a", tokens=100),
            _make_fragment("b.py", 1, 10, content="concept_b", tokens=100),
            _make_fragment("c.py", 1, 10, content="concept_c", tokens=100),
        ]
        core_ids: set[FragmentId] = set()
        rel = {f.id: 1.0 for f in fragments}
        concepts = frozenset(["concept_a", "concept_b", "concept_c"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=core_ids,
            rel=rel,
            concepts=concepts,
            budget_tokens=1000,
            tau=0.0,
        )

        assert result.reason != "best_singleton"
        assert len(result.selected) == 3


class TestNoUtilityReason:
    def test_zero_relevance_all_fragments(self):
        fragments = [
            _make_fragment("a.py", 1, 10, content="concept_a", tokens=100),
            _make_fragment("b.py", 1, 10, content="concept_b", tokens=100),
        ]
        core_ids: set[FragmentId] = set()
        rel = {f.id: 0.0 for f in fragments}
        concepts = frozenset(["concept_a", "concept_b"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=core_ids,
            rel=rel,
            concepts=concepts,
            budget_tokens=1000,
            tau=0.0,
        )

        assert len(result.selected) >= 0


class TestSubsetFragmentHandling:
    def test_subset_fragment_excluded_from_core(self):
        outer = _make_fragment("file.py", 1, 100, content="outer_class", tokens=150)
        inner = _make_fragment("file.py", 10, 50, content="inner_method", tokens=50)

        fragments = [outer, inner]
        core_ids = {outer.id, inner.id}
        rel = {f.id: 1.0 for f in fragments}
        concepts = frozenset(["outer_class", "inner_method"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=core_ids,
            rel=rel,
            concepts=concepts,
            budget_tokens=1000,
            tau=0.0,
        )

        assert outer in result.selected
        outer_count = sum(1 for f in result.selected if f.id == outer.id)
        inner_count = sum(1 for f in result.selected if f.id == inner.id)
        assert outer_count == 1
        assert inner_count <= 1

    def test_non_overlapping_fragments_both_selected(self):
        frag1 = _make_fragment("file.py", 1, 50, content="func_first", tokens=100)
        frag2 = _make_fragment("file.py", 60, 100, content="func_second", tokens=100)

        fragments = [frag1, frag2]
        core_ids = {frag1.id, frag2.id}
        rel = {f.id: 1.0 for f in fragments}
        concepts = frozenset(["func_first", "func_second"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=core_ids,
            rel=rel,
            concepts=concepts,
            budget_tokens=1000,
            tau=0.0,
        )

        assert len(result.selected) == 2


class TestComputeDensityEdgeCases:
    def test_zero_token_count_returns_zero(self):
        from treemapper.diffctx.utility import UtilityState, compute_density

        frag = _make_fragment("a.py", 1, 10, content="concept", tokens=0)
        state = UtilityState()

        density = compute_density(frag, 1.0, frozenset(["concept"]), state)

        assert density == 0.0

    def test_high_relevance_with_many_concepts(self):
        from treemapper.diffctx.utility import UtilityState, compute_density

        concepts = frozenset([f"concept_{i}" for i in range(20)])
        frag = _make_fragment("a.py", 1, 10, content=" ".join(concepts), tokens=100, identifiers=concepts)
        state = UtilityState()

        density = compute_density(frag, 1.0, concepts, state)

        assert density > 0


class TestPPRAllNodesAsSeeds:
    def test_all_nodes_as_seeds_uniform(self):
        frags = [_make_fragment(f"mod{i}.py", 1, 10, identifiers=frozenset([f"func{i}"])) for i in range(5)]
        graph = build_graph(frags)
        all_seeds = {f.id for f in frags}

        scores = personalized_pagerank(graph, seeds=all_seeds, alpha=0.6)

        values = list(scores.values())
        for v in values:
            assert v > 0
        assert abs(sum(values) - 1.0) < 1e-6


class TestPPRAlphaExtremes:
    def test_alpha_one_pure_random_walk(self):
        frags = [
            _make_fragment("a.py", 1, 10, identifiers=frozenset(["shared", "func_a"])),
            _make_fragment("b.py", 1, 10, identifiers=frozenset(["shared", "func_b"])),
            _make_fragment("c.py", 1, 10, identifiers=frozenset(["shared", "func_c"])),
        ]
        graph = build_graph(frags)

        scores = personalized_pagerank(graph, seeds={frags[0].id}, alpha=1.0, max_iter=100)

        assert len(scores) == 3
        assert abs(sum(scores.values()) - 1.0) < 1e-6

    def test_very_small_alpha(self):
        frags = [
            _make_fragment("a.py", 1, 10, identifiers=frozenset(["shared"])),
            _make_fragment("b.py", 1, 10, identifiers=frozenset(["shared"])),
        ]
        graph = build_graph(frags)

        scores = personalized_pagerank(graph, seeds={frags[0].id}, alpha=0.01)

        assert scores[frags[0].id] > scores[frags[1].id]


class TestSelectionWithMixedSizes:
    def test_prefers_smaller_equal_value_fragments(self):
        small_frag = _make_fragment("small.py", 1, 5, content="concept", tokens=50)
        large_frag = _make_fragment("large.py", 1, 100, content="concept", tokens=500)

        fragments = [small_frag, large_frag]
        core_ids: set[FragmentId] = set()
        rel = {small_frag.id: 1.0, large_frag.id: 1.0}
        concepts = frozenset(["concept"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=core_ids,
            rel=rel,
            concepts=concepts,
            budget_tokens=100,
            tau=0.0,
        )

        assert small_frag in result.selected
        assert large_frag not in result.selected

    def test_fills_budget_efficiently(self):
        fragments = [
            _make_fragment("a.py", 1, 10, content="concept_a", tokens=100),
            _make_fragment("b.py", 1, 10, content="concept_b", tokens=100),
            _make_fragment("c.py", 1, 10, content="concept_c", tokens=100),
            _make_fragment("d.py", 1, 10, content="concept_d", tokens=50),
            _make_fragment("e.py", 1, 10, content="concept_e", tokens=50),
        ]
        core_ids: set[FragmentId] = set()
        rel = {f.id: 1.0 for f in fragments}
        concepts = frozenset([f"concept_{c}" for c in "abcde"])

        result = lazy_greedy_select(
            fragments=fragments,
            core_ids=core_ids,
            rel=rel,
            concepts=concepts,
            budget_tokens=300,
            tau=0.0,
        )

        assert result.used_tokens <= 300
        assert len(result.selected) >= 2
