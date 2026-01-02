import pytest

from treemapper.diffctx import build_diff_context
from treemapper.diffctx.fragments import fragment_file


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


class TestContainmentParentChild:
    def test_struct_001_method_changed_include_class_signature(self, diff_project):
        diff_project.add_file(
            "service.py",
            """class PaymentService:
    def __init__(self):
        self.payments = []

    def process_payment(self):
        return "processed"
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "service.py",
            """class PaymentService:
    def __init__(self):
        self.payments = []

    def process_payment(self):
        self.validate()
        return "processed with validation"

    def validate(self):
        return True
""",
        )
        diff_project.commit("Add validation to payment")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "service.py" in selected

    def test_struct_002_nested_function_changed_include_outer(self, diff_project):
        diff_project.add_file(
            "decorators.py",
            """def retry(max_attempts):
    def decorator(func):
        def wrapper(*args):
            for i in range(max_attempts):
                try:
                    return func(*args)
                except Exception:
                    if i == max_attempts - 1:
                        raise
            return None
        return wrapper
    return decorator
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "decorators.py",
            """import time

def retry(max_attempts):
    def decorator(func):
        def wrapper(*args):
            for i in range(max_attempts):
                try:
                    return func(*args)
                except Exception:
                    if i == max_attempts - 1:
                        raise
                    time.sleep(0.1 * (i + 1))
            return None
        return wrapper
    return decorator
""",
        )
        diff_project.commit("Add exponential backoff")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "decorators.py" in selected

    def test_struct_003_code_inside_with_block_changed(self, diff_project):
        diff_project.add_file(
            "db.py",
            """class Transaction:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

def transaction():
    return Transaction()

def save(data):
    with transaction():
        try:
            db_insert(data)
        except Exception:
            pass

def db_insert(data):
    pass
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "db.py",
            """class Transaction:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

def transaction():
    return Transaction()

def save(data):
    with transaction():
        try:
            validate(data)
            db_insert(data)
        except Exception:
            rollback()

def validate(data):
    return True

def db_insert(data):
    pass

def rollback():
    pass
""",
        )
        diff_project.commit("Add validation and rollback")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "db.py" in selected


class TestSiblingRelationships:
    def test_struct_010_one_function_changed_related_functions(self, diff_project):
        diff_project.add_file(
            "validators.py",
            """import re

def validate_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email))

def validate_phone(phone):
    pattern = r'^\\+?[0-9]{10,14}$'
    return bool(re.match(pattern, phone))

def validate_address(addr):
    return len(addr) > 5
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "validators.py",
            """import re

def validate_email(email):
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email))

def validate_phone(phone):
    pattern = r'^\\+?[0-9]{10,14}$'
    return bool(re.match(pattern, phone))

def validate_address(addr):
    return len(addr) > 5
""",
        )
        diff_project.commit("Add null check to email validation")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "validators.py" in selected

    def test_struct_011_files_in_same_package(self, diff_project):
        diff_project.add_file(
            "utils/__init__.py",
            """from .strings import slugify
from .numbers import round_up
""",
        )
        diff_project.add_file(
            "utils/strings.py",
            """def slugify(text):
    return text.lower().replace(" ", "-")
""",
        )
        diff_project.add_file(
            "utils/numbers.py",
            """def round_up(n):
    return int(n) + 1
""",
        )
        diff_project.add_file(
            "utils/dates.py",
            """def format_date(d):
    return d.strftime("%Y-%m-%d")
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "utils/strings.py",
            """import re

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')
""",
        )
        diff_project.commit("Improve slugify")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "strings.py" in selected


class TestModuleLevelDependencies:
    def test_struct_020_import_at_top_include_imported(self, diff_project):
        diff_project.add_file(
            "helpers.py",
            """def normalize(data):
    return [x.strip() for x in data]

def validate(data):
    return all(x for x in data)
""",
        )
        diff_project.add_file(
            "processor.py",
            """def process(data):
    return data
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "processor.py",
            """from helpers import normalize, validate

def process(data):
    data = normalize(data)
    if validate(data):
        return data
    return []
""",
        )
        diff_project.commit("Use helpers")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "processor.py" in selected
        assert "helpers.py" in selected

    def test_struct_021_init_changed_find_exports(self, diff_project):
        diff_project.add_file(
            "mypackage/__init__.py",
            """from .old_module import OldClass
""",
        )
        diff_project.add_file(
            "mypackage/old_module.py",
            """class OldClass:
    pass
""",
        )
        diff_project.add_file(
            "mypackage/new_module.py",
            """class NewClass:
    def __init__(self):
        self.value = 42
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "mypackage/__init__.py",
            """from .old_module import OldClass
from .new_module import NewClass
""",
        )
        diff_project.commit("Export NewClass")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "__init__.py" in selected
        assert "new_module.py" in selected


class TestDocumentationRelationships:
    def test_doc_001_function_changed_include_docstring(self, tmp_path):
        path = tmp_path / "utils.py"
        content = '''def complex_algorithm(data):
    """
    Implements the X algorithm.

    Args:
        data: input dataset

    Returns:
        processed result
    """
    result = []
    for item in data:
        result.append(item * 2)
    return result
'''
        path.write_text(content)

        fragments = fragment_file(path, content)

        assert len(fragments) >= 1
        func_frag = next((f for f in fragments if f.kind == "function"), None)
        assert func_frag is not None
        assert "complex_algorithm" in func_frag.content
