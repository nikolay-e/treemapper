import pytest

from tests.utils import DiffTestCase, DiffTestRunner


class TestDiffInfrastructure:
    def test_basic_python_import(self, diff_test_runner: DiffTestRunner):
        case = DiffTestCase(
            name="python_import_resolution",
            initial_files={
                "utils.py": """def helper():
    return "helper result"

def unused_function():
    return "this should not be included"
""",
                "main.py": """print("initial")
""",
            },
            changed_files={
                "main.py": """from utils import helper

def main():
    result = helper()
    print(result)
""",
            },
            must_include=["def helper()", "def main()"],
            must_not_include=["unused_function"],
            commit_message="Add import and usage",
        )

        context = diff_test_runner.run_test_case(case)
        diff_test_runner.verify_assertions(context, case)

    def test_javascript_import(self, diff_test_runner: DiffTestRunner):
        case = DiffTestCase(
            name="javascript_import_resolution",
            initial_files={
                "utils.ts": """export function fetchUser(id: string) {
    return fetch(`/api/users/${id}`);
}
""",
                "garbage.ts": """export function unusedHelper() {
    return "garbage that should not be included";
}
""",
                "main.ts": """console.log("initial");
""",
            },
            changed_files={
                "main.ts": """import { fetchUser } from './utils';

async function main() {
    const user = await fetchUser('123');
    console.log(user);
}
""",
            },
            must_include=["fetchUser", "async function main"],
            must_not_include=["unusedHelper"],
            commit_message="Add fetch user functionality",
        )

        context = diff_test_runner.run_test_case(case)
        diff_test_runner.verify_assertions(context, case)

    def test_budget_calculation(self):
        case = DiffTestCase(
            name="budget_test",
            initial_files={"a.py": "x = 1"},
            changed_files={"a.py": "x = 2\ny = 3"},
            must_include=["some pattern"],
        )

        budget = case.calculate_budget()
        assert budget >= case.min_budget
        assert budget > 0


PYTHON_TEST_CASES = [
    DiffTestCase(
        name="dataclass_field_change",
        initial_files={
            "models.py": """from dataclasses import dataclass

@dataclass
class Order:
    id: int
    customer_id: int
    total: float

def unrelated_garbage_function():
    return "this is garbage that should not be in context"
""",
            "services.py": """from models import Order

def create_order(customer_id, total):
    return Order(id=1, customer_id=customer_id, total=total)

def process_order(order: Order):
    return f"Processing order {order.id}"
""",
        },
        changed_files={
            "models.py": """from dataclasses import dataclass

@dataclass
class Order:
    id: int
    customer_id: int
    total: float
    priority: int = 0

def unrelated_garbage_function():
    return "this is garbage that should not be in context"
""",
        },
        must_include=["class Order", "priority"],
        must_not_include=["unrelated_garbage_function"],
        commit_message="Add priority field",
    ),
    DiffTestCase(
        name="property_change",
        initial_files={
            "user.py": """class User:
    def __init__(self, first, last):
        self.first = first
        self.last = last

    @property
    def full_name(self):
        return f"{self.first} {self.last}"
""",
            "garbage.py": """def standalone_garbage():
    return "garbage content not related to anything"
""",
            "views.py": """from user import User

def render_user(user):
    return f"Name: {user.full_name}"
""",
        },
        changed_files={
            "user.py": """class User:
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
        },
        must_include=["def __init__", "full_name"],
        must_not_include=["standalone_garbage"],
        commit_message="Add title to full_name",
    ),
]


@pytest.mark.parametrize("case", PYTHON_TEST_CASES, ids=lambda c: c.name)
def test_python_cases(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
