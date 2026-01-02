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


class TestPythonSpecific:
    def test_py_001_dataclass_field_changed(self, diff_project):
        diff_project.add_file(
            "models.py",
            """from dataclasses import dataclass

@dataclass
class Order:
    id: int
    customer_id: int
    total: float
""",
        )
        diff_project.add_file(
            "services.py",
            """from models import Order

def create_order(customer_id, total):
    return Order(id=1, customer_id=customer_id, total=total)

def process_order(order: Order):
    return f"Processing order {order.id}"
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "models.py",
            """from dataclasses import dataclass

@dataclass
class Order:
    id: int
    customer_id: int
    total: float
    priority: int = 0
""",
        )
        diff_project.commit("Add priority field")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "models.py" in selected

    def test_py_002_property_changed(self, diff_project):
        diff_project.add_file(
            "user.py",
            """class User:
    def __init__(self, first, last):
        self.first = first
        self.last = last

    @property
    def full_name(self):
        return f"{self.first} {self.last}"
""",
        )
        diff_project.add_file(
            "views.py",
            """from user import User

def render_user(user):
    return f"Name: {user.full_name}"
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "user.py",
            """class User:
    def __init__(self, first, last, title=None):
        self.first = first
        self.last = last
        self.title = title

    @property
    def full_name(self):
        if self.title:
            return f"{self.title} {self.first} {self.last}"
        return f"{self.first} {self.last}"
""",
        )
        diff_project.commit("Add title to full_name")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "user.py" in selected

    def test_py_003_dunder_method_changed(self, diff_project):
        diff_project.add_file(
            "money.py",
            """class Money:
    def __init__(self, amount, currency="USD"):
        self.amount = amount
        self.currency = currency

    def __str__(self):
        return f"{self.currency} {self.amount:.2f}"
""",
        )
        diff_project.add_file(
            "calculator.py",
            """from money import Money

def sum_money(m1, m2):
    return Money(m1.amount + m2.amount)
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "money.py",
            """class Money:
    def __init__(self, amount, currency="USD"):
        self.amount = amount
        self.currency = currency

    def __str__(self):
        return f"{self.currency} {self.amount:.2f}"

    def __add__(self, other):
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")
        return Money(self.amount + other.amount, self.currency)
""",
        )
        diff_project.commit("Add __add__ method")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "money.py" in selected

    def test_py_004_context_manager_changed(self, diff_project):
        diff_project.add_file(
            "db.py",
            """from contextlib import contextmanager

@contextmanager
def transaction():
    print("Starting transaction")
    try:
        yield
        print("Committing")
    except Exception:
        print("Rolling back")
        raise
""",
        )
        diff_project.add_file(
            "service.py",
            """from db import transaction

def save_data(data):
    with transaction():
        store(data)

def store(data):
    print(f"Storing {data}")
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "db.py",
            """from contextlib import contextmanager
import time

@contextmanager
def transaction():
    start = time.time()
    print("Starting transaction")
    try:
        yield
        print(f"Committing (took {time.time() - start:.2f}s)")
    except Exception:
        print(f"Rolling back (took {time.time() - start:.2f}s)")
        raise
""",
        )
        diff_project.commit("Add timing to transaction")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "db.py" in selected


class TestAsyncPatterns:
    def test_async_function_changed(self, diff_project):
        diff_project.add_file(
            "async_utils.py",
            """async def fetch_data(url):
    await simulate_delay()
    return {"url": url, "data": "content"}

async def simulate_delay():
    import asyncio
    await asyncio.sleep(0.1)
""",
        )
        diff_project.add_file(
            "handler.py",
            """from async_utils import fetch_data

async def handle_request(url):
    data = await fetch_data(url)
    return data
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "async_utils.py",
            """import asyncio

async def fetch_data(url, timeout=30):
    try:
        await asyncio.wait_for(simulate_delay(), timeout=timeout)
        return {"url": url, "data": "content", "timeout": timeout}
    except asyncio.TimeoutError:
        return {"url": url, "error": "timeout"}

async def simulate_delay():
    await asyncio.sleep(0.1)
""",
        )
        diff_project.commit("Add timeout support")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "async_utils.py" in selected


class TestTypeAnnotations:
    def test_type_annotations_in_function(self, diff_project):
        diff_project.add_file(
            "types.py",
            """from typing import List, Optional

def process_items(items: List[str]) -> Optional[str]:
    if not items:
        return None
    return items[0]
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "types.py",
            """from typing import List, Optional, TypeVar, Generic

T = TypeVar('T')

def process_items(items: List[str]) -> Optional[str]:
    if not items:
        return None
    return items[0]

class Container(Generic[T]):
    def __init__(self, value: T):
        self.value = value

    def get(self) -> T:
        return self.value
""",
        )
        diff_project.commit("Add generic container")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "types.py" in selected
