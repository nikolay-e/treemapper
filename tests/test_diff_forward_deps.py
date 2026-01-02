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


class TestFunctionCallResolution:
    def test_fwd_001_diff_calls_function_defined_elsewhere(self, diff_project):
        diff_project.add_file(
            "utils/math.py",
            """def calculate_tax(amount):
    rate = 0.15
    return amount * rate
""",
        )
        diff_project.add_file(
            "main.py",
            """def process():
    pass
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "main.py",
            """from utils.math import calculate_tax

def process():
    amount = 100
    result = calculate_tax(amount)
    return result
""",
        )
        diff_project.commit("Add tax calculation")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "main.py" in selected
        assert "math.py" in selected

    def test_fwd_002_diff_calls_method_on_imported_class(self, diff_project):
        diff_project.add_file(
            "services/user.py",
            """class UserService:
    def __init__(self):
        self.users = []

    def validate(self):
        return len(self.users) > 0

    def add_user(self, name):
        self.users.append(name)
""",
        )
        diff_project.add_file(
            "handler.py",
            """def handle():
    pass
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "handler.py",
            """from services.user import UserService

def handle():
    user = UserService()
    user.validate()
    return user
""",
        )
        diff_project.commit("Use UserService")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "handler.py" in selected
        assert "user.py" in selected

    def test_fwd_003_diff_calls_chained_methods(self, diff_project):
        diff_project.add_file(
            "database/query.py",
            """class QueryBuilder:
    def __init__(self, table):
        self.table = table
        self.filters = []
        self.limit_val = None

    def query(self, table):
        return QueryBuilder(table)

    def filter(self, **kwargs):
        self.filters.append(kwargs)
        return self

    def limit(self, n):
        self.limit_val = n
        return self
""",
        )
        diff_project.add_file(
            "query.py",
            """def run_query():
    pass
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "query.py",
            """from database.query import QueryBuilder

def run_query():
    db = QueryBuilder("users")
    result = db.query("users").filter(active=True).limit(10)
    return result
""",
        )
        diff_project.commit("Add query chain")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "query.py" in selected

    def test_fwd_004_diff_calls_function_via_alias_import(self, diff_project):
        diff_project.add_file(
            "utils/helper.py",
            """def process(data):
    return [x * 2 for x in data]
""",
        )
        diff_project.add_file(
            "app.py",
            """def run():
    pass
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "app.py",
            """from utils import helper as h

def run():
    data = [1, 2, 3]
    result = h.process(data)
    return result
""",
        )
        diff_project.commit("Use aliased helper")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "app.py" in selected

    def test_fwd_005_diff_calls_nested_inner_function(self, diff_project):
        diff_project.add_file(
            "outer.py",
            """def outer():
    def inner():
        return 42

    return 0
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "outer.py",
            """def outer():
    def inner():
        return 42

    result = inner()
    return result
""",
        )
        diff_project.commit("Call inner function")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "outer.py" in selected

    def test_fwd_006_diff_calls_through_dynamic_dispatch(self, diff_project):
        diff_project.add_file(
            "handlers/base.py",
            """class BaseHandler:
    def process(self, event):
        return f"Processing {event}"
""",
        )
        diff_project.add_file(
            "dispatcher.py",
            """def dispatch():
    pass
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "dispatcher.py",
            """from handlers.base import BaseHandler

def get_handler(event_type):
    return BaseHandler()

def dispatch():
    handler = get_handler("click")
    handler.process("click_event")
""",
        )
        diff_project.commit("Add dynamic dispatch")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "dispatcher.py" in selected


class TestTypeInterfaceUsage:
    def test_fwd_010_diff_uses_type_annotation(self, diff_project):
        diff_project.add_file(
            "models/request.py",
            """class RequestModel:
    def __init__(self, data):
        self.data = data
""",
        )
        diff_project.add_file(
            "models/response.py",
            """class ResponseModel:
    def __init__(self, result):
        self.result = result
""",
        )
        diff_project.add_file(
            "service.py",
            """def process():
    pass
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "service.py",
            """from models.request import RequestModel
from models.response import ResponseModel

def process(request: RequestModel) -> ResponseModel:
    result = request.data * 2
    return ResponseModel(result)
""",
        )
        diff_project.commit("Add typed function")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "service.py" in selected

    def test_fwd_011_diff_inherits_from_base_class(self, diff_project):
        diff_project.add_file(
            "handlers/base.py",
            """class BaseHandler:
    def handle(self):
        return "base"

    def setup(self):
        pass
""",
        )
        diff_project.add_file(
            "custom_handler.py",
            """def placeholder():
    pass
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "custom_handler.py",
            """from handlers.base import BaseHandler

class CustomHandler(BaseHandler):
    def handle(self):
        super().handle()
        return "custom"
""",
        )
        diff_project.commit("Add custom handler")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "custom_handler.py" in selected
        assert "base.py" in selected

    def test_fwd_012_diff_implements_protocol(self, diff_project):
        diff_project.add_file(
            "interfaces/repository.py",
            """from typing import Protocol

class Repository(Protocol):
    def find(self, id: int):
        ...

    def save(self, entity):
        ...
""",
        )
        diff_project.add_file(
            "impl.py",
            """def placeholder():
    pass
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "impl.py",
            """from interfaces.repository import Repository

class MyRepo(Repository):
    def find(self, id: int):
        return {"id": id}

    def save(self, entity):
        pass
""",
        )
        diff_project.commit("Implement repository")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "impl.py" in selected


class TestConstantEnumUsage:
    def test_fwd_020_diff_uses_constant_defined_elsewhere(self, diff_project):
        diff_project.add_file(
            "constants.py",
            """MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
""",
        )
        diff_project.add_file(
            "validator.py",
            """def validate():
    pass
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "validator.py",
            """from constants import MIN_PASSWORD_LENGTH

def validate(password):
    if len(password) < MIN_PASSWORD_LENGTH:
        return False
    return True
""",
        )
        diff_project.commit("Add password validation")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "validator.py" in selected
        assert "constants.py" in selected

    def test_fwd_021_diff_uses_enum_value(self, diff_project):
        diff_project.add_file(
            "enums/order.py",
            """from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
""",
        )
        diff_project.add_file(
            "order.py",
            """def create_order():
    pass
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "order.py",
            """from enums.order import OrderStatus

class Order:
    def __init__(self):
        self.status = OrderStatus.PENDING

    def complete(self):
        self.status = OrderStatus.COMPLETED
""",
        )
        diff_project.commit("Add order with status")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "order.py" in selected


class TestImportChain:
    def test_fwd_030_diff_imports_module_that_reexports(self, diff_project):
        diff_project.add_file(
            "mylib/core.py",
            """def process():
    return "processed"
""",
        )
        diff_project.add_file(
            "mylib/__init__.py",
            """from .core import process
""",
        )
        diff_project.add_file(
            "app.py",
            """def run():
    pass
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "app.py",
            """from mylib import process

def run():
    result = process()
    return result
""",
        )
        diff_project.commit("Use re-exported function")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "app.py" in selected

    def test_fwd_031_diff_uses_relative_import(self, diff_project):
        diff_project.add_file(
            "pkg/__init__.py",
            "",
        )
        diff_project.add_file(
            "pkg/utils.py",
            """def helper():
    return "help"
""",
        )
        diff_project.add_file(
            "pkg/subpkg/__init__.py",
            "",
        )
        diff_project.add_file(
            "pkg/subpkg/module.py",
            """def action():
    pass
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "pkg/subpkg/module.py",
            """from ..utils import helper

def action():
    result = helper()
    return result
""",
        )
        diff_project.commit("Use relative import")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=5000,
        )

        selected = _extract_files_from_tree(tree)
        assert "module.py" in selected
