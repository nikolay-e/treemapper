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


class TestDecoratorUsage:
    def test_cross_001_decorator_applied_to_changed_function(self, diff_project):
        diff_project.add_file(
            "decorators/auth.py",
            """def login_required(func):
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            raise ValueError("Not authenticated")
        return func(*args, **kwargs)
    return wrapper

def is_authenticated():
    return True
""",
        )
        diff_project.add_file(
            "decorators/rate.py",
            """def rate_limit(limit):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator
""",
        )
        diff_project.add_file(
            "api.py",
            """from decorators.auth import login_required
from decorators.rate import rate_limit

@login_required
@rate_limit(100)
def api_endpoint():
    return {"status": "ok"}
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "api.py",
            """from decorators.auth import login_required
from decorators.rate import rate_limit

@login_required
@rate_limit(100)
def api_endpoint():
    data = fetch_data()
    return {"status": "ok", "data": data}

def fetch_data():
    return [1, 2, 3]
""",
        )
        diff_project.commit("Add data fetching")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "api.py" in selected

    def test_cross_002_decorator_definition_changed(self, diff_project):
        diff_project.add_file(
            "decorators.py",
            """def cache(ttl=60):
    def decorator(func):
        cache_store = {}
        def wrapper(*args):
            if args in cache_store:
                return cache_store[args]
            result = func(*args)
            cache_store[args] = result
            return result
        return wrapper
    return decorator
""",
        )
        diff_project.add_file(
            "services.py",
            """from decorators import cache

@cache(ttl=300)
def expensive_computation(x):
    return x ** 2

@cache(ttl=60)
def quick_lookup(key):
    return {"key": key}
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "decorators.py",
            """import time

def cache(ttl=60):
    def decorator(func):
        cache_store = {}
        cache_times = {}
        def wrapper(*args):
            now = time.time()
            if args in cache_store:
                if now - cache_times[args] < ttl:
                    return cache_store[args]
            result = func(*args)
            cache_store[args] = result
            cache_times[args] = now
            return result
        return wrapper
    return decorator
""",
        )
        diff_project.commit("Add TTL expiration")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "decorators.py" in selected


class TestMiddlewareHooks:
    def test_cross_010_middleware_changed(self, diff_project):
        diff_project.add_file(
            "middleware/auth.py",
            """class AuthMiddleware:
    def process_request(self, request):
        if not request.get("token"):
            raise ValueError("Unauthorized")
        return request
""",
        )
        diff_project.add_file(
            "settings.py",
            """MIDDLEWARE = [
    "middleware.auth.AuthMiddleware",
]
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "middleware/auth.py",
            """import time

class AuthMiddleware:
    def process_request(self, request):
        if not request.get("token"):
            raise ValueError("Unauthorized")
        request["authenticated_at"] = time.time()
        return request
""",
        )
        diff_project.commit("Add auth timestamp")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "auth.py" in selected

    def test_cross_011_signal_handler_changed(self, diff_project):
        diff_project.add_file(
            "models/user.py",
            """class User:
    def __init__(self, name):
        self.name = name
""",
        )
        diff_project.add_file(
            "signals.py",
            """from models.user import User

def on_user_created(sender, instance):
    print(f"User created: {instance.name}")
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "signals.py",
            """from models.user import User

def on_user_created(sender, instance):
    print(f"User created: {instance.name}")
    send_welcome_email(instance)

def send_welcome_email(user):
    print(f"Welcome email sent to {user.name}")
""",
        )
        diff_project.commit("Add welcome email")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "signals.py" in selected


class TestExceptionHandling:
    def test_cross_020_custom_exception_changed(self, diff_project):
        diff_project.add_file(
            "exceptions.py",
            """class ValidationError(Exception):
    pass
""",
        )
        diff_project.add_file(
            "validators.py",
            """from exceptions import ValidationError

def validate(data):
    if not data:
        raise ValidationError("Data is empty")
    return True
""",
        )
        diff_project.add_file(
            "handlers.py",
            """from exceptions import ValidationError

def handle_request(data):
    try:
        return process(data)
    except ValidationError:
        return {"error": "Validation failed"}

def process(data):
    return data
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "exceptions.py",
            """class ValidationError(Exception):
    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")
""",
        )
        diff_project.commit("Add field to ValidationError")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "exceptions.py" in selected

    def test_cross_021_exception_raised_find_handlers(self, diff_project):
        diff_project.add_file(
            "exceptions.py",
            """class InsufficientFundsError(Exception):
    def __init__(self, account_id):
        self.account_id = account_id
        super().__init__(f"Insufficient funds for account {account_id}")
""",
        )
        diff_project.add_file(
            "service.py",
            """def transfer(from_account, to_account, amount):
    return True
""",
        )
        diff_project.add_file(
            "api/views.py",
            """from exceptions import InsufficientFundsError
from service import transfer

def transfer_endpoint(request):
    try:
        result = transfer(request.from_id, request.to_id, request.amount)
        return {"success": result}
    except InsufficientFundsError as e:
        return {"error": str(e)}
""",
        )
        diff_project.commit("Initial")

        diff_project.add_file(
            "service.py",
            """from exceptions import InsufficientFundsError

def transfer(from_account, to_account, amount):
    balance = get_balance(from_account)
    if balance < amount:
        raise InsufficientFundsError(from_account)
    return True

def get_balance(account):
    return 100
""",
        )
        diff_project.commit("Add balance check")

        tree = build_diff_context(
            root_dir=diff_project.repo,
            diff_range="HEAD~1..HEAD",
            budget_tokens=10000,
        )

        selected = _extract_files_from_tree(tree)
        assert "service.py" in selected
