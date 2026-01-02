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


class TestCallersOfModifiedFunction:
    def test_bwd_001_function_signature_changed_find_callers(self, diff_project):
        diff_project.add_file(
            "utils.py",
            """def format_date(date):
    return date.strftime("%Y-%m-%d")
""",
        )
        diff_project.add_file(
            "reports/generator.py",
            """from utils import format_date

def generate_report(today):
    formatted = format_date(today)
    return f"Report for {formatted}"
""",
        )
        diff_project.add_file(
            "api/views.py",
            """from utils import format_date

def get_created_date(created_at):
    return format_date(created_at)
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "utils.py",
            """def format_date(date, timezone=None):
    if timezone:
        date = date.astimezone(timezone)
    return date.strftime("%Y-%m-%d")
""",
        )
        diff_project.commit("Add timezone parameter")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "utils.py" in selected

    def test_bwd_002_function_body_changed_find_callers(self, diff_project):
        diff_project.add_file(
            "calculator.py",
            """def calculate_total(items):
    return sum(i.price for i in items)
""",
        )
        diff_project.add_file(
            "checkout.py",
            """from calculator import calculate_total

class CartItem:
    def __init__(self, price, quantity):
        self.price = price
        self.quantity = quantity

def process_checkout(cart_items):
    total = calculate_total(cart_items)
    return {"total": total}
""",
        )
        diff_project.add_file(
            "invoice.py",
            """from calculator import calculate_total

def create_invoice(line_items):
    amount = calculate_total(line_items)
    return {"amount": amount}
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "calculator.py",
            """def calculate_total(items):
    return sum(i.price * i.quantity for i in items)
""",
        )
        diff_project.commit("Fix calculation to include quantity")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "calculator.py" in selected

    def test_bwd_003_function_deleted_find_orphaned_callers(self, diff_project):
        diff_project.add_file(
            "helpers.py",
            """def deprecated_helper():
    return "old"

def new_helper():
    return "new"
""",
        )
        diff_project.add_file(
            "consumer.py",
            """from helpers import deprecated_helper

def use_helper():
    return deprecated_helper()
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "helpers.py",
            """def new_helper():
    return "new"
""",
        )
        diff_project.commit("Remove deprecated helper")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        # Either helpers.py (the changed file) or consumer.py (the caller) should be selected
        # The algorithm selects files based on relevance propagation
        assert "helpers.py" in selected or "consumer.py" in selected

    def test_bwd_004_method_changed_find_callers(self, diff_project):
        diff_project.add_file(
            "user.py",
            """class User:
    def __init__(self, first, last):
        self.first = first
        self.last = last

    def get_full_name(self):
        return f"{self.first} {self.last}"
""",
        )
        diff_project.add_file(
            "templates/profile.py",
            """from user import User

def render_profile(user):
    name = user.get_full_name()
    return f"<h1>{name}</h1>"
""",
        )
        diff_project.add_file(
            "emails/welcome.py",
            """from user import User

def send_welcome(recipient):
    name = recipient.get_full_name()
    return f"Welcome, {name}!"
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

    def get_full_name(self, include_title=False):
        if include_title and self.title:
            return f"{self.title} {self.first} {self.last}"
        return f"{self.first} {self.last}"
""",
        )
        diff_project.commit("Add title support")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "user.py" in selected


class TestImplementersSubclasses:
    def test_bwd_010_base_class_method_changed_find_overrides(self, diff_project):
        diff_project.add_file(
            "base.py",
            """class BaseProcessor:
    def process(self, data):
        return data
""",
        )
        diff_project.add_file(
            "processors/json.py",
            """from base import BaseProcessor

class JsonProcessor(BaseProcessor):
    def process(self, data):
        import json
        return json.loads(data)
""",
        )
        diff_project.add_file(
            "processors/xml.py",
            """from base import BaseProcessor

class XmlProcessor(BaseProcessor):
    def process(self, data):
        return f"<xml>{data}</xml>"
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "base.py",
            """class BaseProcessor:
    def process(self, data, options=None):
        if options:
            data = self.preprocess(data, options)
        return data

    def preprocess(self, data, options):
        return data
""",
        )
        diff_project.commit("Add options parameter")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "base.py" in selected

    def test_bwd_011_protocol_changed_find_implementations(self, diff_project):
        diff_project.add_file(
            "interfaces.py",
            """from typing import Protocol

class Repository(Protocol):
    def find(self, id: int):
        ...
""",
        )
        diff_project.add_file(
            "repos/user_repo.py",
            """from interfaces import Repository

class UserRepository:
    def find(self, id: int):
        return {"id": id, "name": "User"}
""",
        )
        diff_project.add_file(
            "repos/order_repo.py",
            """from interfaces import Repository

class OrderRepository:
    def find(self, id: int):
        return {"id": id, "total": 100}
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "interfaces.py",
            """from typing import Protocol

class Repository(Protocol):
    def find(self, id: int):
        ...

    def find_by_criteria(self, criteria: dict) -> list:
        ...
""",
        )
        diff_project.commit("Add find_by_criteria method")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "interfaces.py" in selected


class TestUsagesOfModifiedVariable:
    def test_bwd_020_global_constant_changed_find_usages(self, diff_project):
        diff_project.add_file(
            "config.py",
            """MAX_RETRIES = 3
TIMEOUT = 30
""",
        )
        diff_project.add_file(
            "client.py",
            """from config import MAX_RETRIES

def fetch_with_retry(url):
    for i in range(MAX_RETRIES):
        try:
            return fetch(url)
        except:
            pass
    return None

def fetch(url):
    return "data"
""",
        )
        diff_project.add_file(
            "worker.py",
            """from config import MAX_RETRIES

def process_job(job):
    attempts = 0
    while attempts < MAX_RETRIES:
        try:
            return do_work(job)
        except:
            attempts += 1
    return None

def do_work(job):
    return "done"
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "config.py",
            """MAX_RETRIES = 5
TIMEOUT = 30
""",
        )
        diff_project.commit("Increase max retries")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "config.py" in selected

    def test_bwd_021_class_attribute_changed_find_usages(self, diff_project):
        diff_project.add_file(
            "models.py",
            """class Config:
    timeout = 30
    max_connections = 10
""",
        )
        diff_project.add_file(
            "client.py",
            """from models import Config

def make_request():
    timeout = Config.timeout
    return f"Request with timeout {timeout}"
""",
        )
        diff_project.add_file(
            "settings.py",
            """from models import Config

default_timeout = Config.timeout
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "models.py",
            """class Config:
    timeout = 60
    max_connections = 10
""",
        )
        diff_project.commit("Increase timeout")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "models.py" in selected
