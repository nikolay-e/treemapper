from __future__ import annotations

import pytest

from tests.utils import DiffTestCase, DiffTestRunner

MONOREPO_TEST_CASES = [
    DiffTestCase(
        name="monorepo_workspace_packages",
        initial_files={
            "package.json": '{\n    "name": "monorepo",\n    "workspaces": ["packages/*"]\n}\n',
            "packages/core/package.json": '{\n    "name": "@myorg/core",\n    "version": "1.0.0"\n}\n',
            "packages/core/src/index.ts": 'export function coreFunction() {\n    return "core";\n}\n',
            "packages/web/package.json": '{\n    "name": "@myorg/web",\n    "dependencies": {\n        "@myorg/core": "workspace:*"\n    }\n}\n',
        },
        changed_files={
            "packages/api/package.json": '{\n    "name": "@myorg/api",\n    "version": "1.0.0",\n    "dependencies": {\n        "@myorg/core": "workspace:*"\n    }\n}\n',
            "packages/api/src/index.ts": "import { coreFunction } from '@myorg/core';\n\nexport function apiHandler() {\n    return coreFunction();\n}\n",
        },
        must_include=["index.ts"],
        commit_message="Add api package",
    ),
    DiffTestCase(
        name="monorepo_shared_lib_change",
        initial_files={
            "packages/shared/src/utils.ts": "export function formatDate(date: Date): string {\n    return date.toISOString();\n}\n",
            "packages/web/src/components/DateDisplay.tsx": "import { formatDate } from '@myorg/shared';\n\nexport function DateDisplay({ date }: { date: Date }) {\n    return <span>{formatDate(date)}</span>;\n}\n",
            "packages/api/src/handlers/report.ts": "import { formatDate } from '@myorg/shared';\n\nexport function generateReport(date: Date) {\n    return { generatedAt: formatDate(date) };\n}\n",
        },
        changed_files={
            "packages/shared/src/utils.ts": "export function formatDate(date: Date, format: string = 'iso'): string {\n    if (format === 'iso') {\n        return date.toISOString();\n    }\n    if (format === 'locale') {\n        return date.toLocaleDateString();\n    }\n    return date.toString();\n}\n\nexport function parseDate(str: string): Date {\n    return new Date(str);\n}\n",
        },
        must_include=["utils.ts"],
        commit_message="Add format option and parseDate to shared utils",
    ),
    DiffTestCase(
        name="monorepo_internal_package",
        initial_files={
            "internal/logger/index.ts": "export class Logger {\n    log(message: string) {\n        console.log(message);\n    }\n}\n",
            "packages/api/src/server.ts": "import { Logger } from '../../internal/logger';\n\nconst logger = new Logger();\n\nexport function startServer() {\n    logger.log('Server started');\n}\n",
            "packages/worker/src/main.ts": "import { Logger } from '../../internal/logger';\n\nconst logger = new Logger();\n\nexport function runWorker() {\n    logger.log('Worker started');\n}\n",
        },
        changed_files={
            "internal/logger/index.ts": "export enum LogLevel {\n    DEBUG,\n    INFO,\n    WARN,\n    ERROR,\n}\n\nexport class Logger {\n    constructor(private level: LogLevel = LogLevel.INFO) {}\n\n    log(message: string, level: LogLevel = LogLevel.INFO) {\n        if (level >= this.level) {\n            console.log(`[${LogLevel[level]}] ${message}`);\n        }\n    }\n\n    debug(message: string) {\n        this.log(message, LogLevel.DEBUG);\n    }\n\n    error(message: string) {\n        this.log(message, LogLevel.ERROR);\n    }\n}\n",
        },
        must_include=["index.ts"],
        commit_message="Add log levels to internal logger",
    ),
    DiffTestCase(
        name="monorepo_cross_package_type",
        initial_files={
            "packages/types/src/user.ts": "export interface User {\n    id: string;\n    name: string;\n}\n",
            "packages/api/src/routes/users.ts": "import { User } from '@myorg/types';\n\nexport function getUser(id: string): User {\n    return { id, name: 'John' };\n}\n",
            "packages/web/src/hooks/useUser.ts": "import { User } from '@myorg/types';\n\nexport function useUser(id: string): User | null {\n    return { id, name: 'John' };\n}\n",
        },
        changed_files={
            "packages/types/src/user.ts": "export interface User {\n    id: string;\n    name: string;\n    email: string;\n    role: UserRole;\n    createdAt: Date;\n}\n\nexport enum UserRole {\n    USER = 'user',\n    ADMIN = 'admin',\n    MODERATOR = 'moderator',\n}\n\nexport type UserCreateInput = Omit<User, 'id' | 'createdAt'>;\nexport type UserUpdateInput = Partial<UserCreateInput>;\n",
        },
        must_include=["user.ts"],
        commit_message="Add email, role and utility types to User",
    ),
    DiffTestCase(
        name="monorepo_root_config_extends",
        initial_files={
            "tsconfig.base.json": '{\n    "compilerOptions": {\n        "target": "ES2020",\n        "module": "commonjs",\n        "strict": true\n    }\n}\n',
            "packages/core/tsconfig.json": '{\n    "extends": "../../tsconfig.base.json",\n    "compilerOptions": {\n        "outDir": "./dist"\n    }\n}\n',
            "packages/web/tsconfig.json": '{\n    "extends": "../../tsconfig.base.json",\n    "compilerOptions": {\n        "jsx": "react",\n        "outDir": "./dist"\n    }\n}\n',
        },
        changed_files={
            "tsconfig.base.json": '{\n    "compilerOptions": {\n        "target": "ES2022",\n        "module": "ESNext",\n        "moduleResolution": "bundler",\n        "strict": true,\n        "skipLibCheck": true,\n        "esModuleInterop": true,\n        "paths": {\n            "@myorg/*": ["packages/*/src"]\n        }\n    }\n}\n',
        },
        must_include=["tsconfig.base.json"],
        commit_message="Update base tsconfig with ESNext and paths",
    ),
    DiffTestCase(
        name="monorepo_turborepo_depends_on",
        initial_files={
            "turbo.json": '{\n    "$schema": "https://turbo.build/schema.json",\n    "pipeline": {\n        "build": {\n            "dependsOn": ["^build"],\n            "outputs": ["dist/**"]\n        },\n        "test": {\n            "dependsOn": ["build"]\n        }\n    }\n}\n',
            "packages/core/src/index.ts": "export const VERSION = '1.0.0';\n",
            "packages/app/src/index.ts": "import { VERSION } from '@myorg/core';\nconsole.log(VERSION);\n",
        },
        changed_files={
            "turbo.json": '{\n    "$schema": "https://turbo.build/schema.json",\n    "pipeline": {\n        "build": {\n            "dependsOn": ["^build"],\n            "outputs": ["dist/**"],\n            "env": ["NODE_ENV"]\n        },\n        "test": {\n            "dependsOn": ["build"],\n            "outputs": ["coverage/**"]\n        },\n        "lint": {\n            "outputs": []\n        },\n        "typecheck": {\n            "dependsOn": ["^build"],\n            "outputs": []\n        },\n        "deploy": {\n            "dependsOn": ["build", "test", "lint"],\n            "outputs": []\n        }\n    }\n}\n',
        },
        must_include=["turbo.json"],
        commit_message="Add lint, typecheck and deploy pipelines",
    ),
]


STRUCTURAL_TEST_CASES = [
    DiffTestCase(
        name="structural_method_changed_include_class",
        initial_files={
            "service.py": 'class PaymentService:\n    def __init__(self):\n        self.payments = []\n\n    def process_payment(self):\n        return "processed"\n',
        },
        changed_files={
            "service.py": 'class PaymentService:\n    def __init__(self):\n        self.payments = []\n\n    def process_payment(self):\n        self.validate()\n        return "processed with validation"\n\n    def validate(self):\n        return True\n',
        },
        must_include=["service.py"],
        commit_message="Add validation to payment",
    ),
    DiffTestCase(
        name="structural_nested_function_changed",
        initial_files={
            "decorators.py": "def retry(max_attempts):\n    def decorator(func):\n        def wrapper(*args):\n            for i in range(max_attempts):\n                try:\n                    return func(*args)\n                except Exception:\n                    if i == max_attempts - 1:\n                        raise\n            return None\n        return wrapper\n    return decorator\n",
        },
        changed_files={
            "decorators.py": "import time\n\ndef retry(max_attempts):\n    def decorator(func):\n        def wrapper(*args):\n            for i in range(max_attempts):\n                try:\n                    return func(*args)\n                except Exception:\n                    if i == max_attempts - 1:\n                        raise\n                    time.sleep(0.1 * (i + 1))\n            return None\n        return wrapper\n    return decorator\n",
        },
        must_include=["decorators.py"],
        commit_message="Add exponential backoff",
    ),
    DiffTestCase(
        name="structural_code_inside_with_block",
        initial_files={
            "db.py": "class Transaction:\n    def __enter__(self):\n        return self\n\n    def __exit__(self, *args):\n        pass\n\ndef transaction():\n    return Transaction()\n\ndef save(data):\n    with transaction():\n        try:\n            db_insert(data)\n        except Exception:\n            pass\n\ndef db_insert(data):\n    pass\n",
        },
        changed_files={
            "db.py": "class Transaction:\n    def __enter__(self):\n        return self\n\n    def __exit__(self, *args):\n        pass\n\ndef transaction():\n    return Transaction()\n\ndef save(data):\n    with transaction():\n        try:\n            validate(data)\n            db_insert(data)\n        except Exception:\n            rollback()\n\ndef validate(data):\n    return True\n\ndef db_insert(data):\n    pass\n\ndef rollback():\n    pass\n",
        },
        must_include=["db.py"],
        commit_message="Add validation and rollback",
    ),
    DiffTestCase(
        name="structural_import_include_imported",
        initial_files={
            "helpers.py": "def normalize(data):\n    return [x.strip() for x in data]\n\ndef validate(data):\n    return all(x for x in data)\n",
            "processor.py": "def process(data):\n    return data\n",
        },
        changed_files={
            "processor.py": "from helpers import normalize, validate\n\ndef process(data):\n    data = normalize(data)\n    if validate(data):\n        return data\n    return []\n",
        },
        must_include=["processor.py", "helpers.py"],
        commit_message="Use helpers",
    ),
    DiffTestCase(
        name="structural_init_changed_find_exports",
        initial_files={
            "mypackage/__init__.py": "from .old_module import OldClass\n",
            "mypackage/old_module.py": "class OldClass:\n    pass\n",
            "mypackage/new_module.py": "class NewClass:\n    def __init__(self):\n        self.value = 42\n",
        },
        changed_files={
            "mypackage/__init__.py": "from .old_module import OldClass\nfrom .new_module import NewClass\n",
        },
        must_include=["__init__.py", "new_module.py"],
        commit_message="Export NewClass",
    ),
    DiffTestCase(
        name="structural_files_in_same_package",
        initial_files={
            "utils/__init__.py": "from .strings import slugify\nfrom .numbers import round_up\n",
            "utils/strings.py": 'def slugify(text):\n    return text.lower().replace(" ", "-")\n',
            "utils/numbers.py": "def round_up(n):\n    return int(n) + 1\n",
            "utils/dates.py": 'def format_date(d):\n    return d.strftime("%Y-%m-%d")\n',
        },
        changed_files={
            "utils/strings.py": "import re\n\ndef slugify(text):\n    text = text.lower()\n    text = re.sub(r'[^a-z0-9]+', '-', text)\n    return text.strip('-')\n",
        },
        must_include=["strings.py"],
        commit_message="Improve slugify",
    ),
]


CONTEXT_TEST_CASES = [
    DiffTestCase(
        name="context_basic_diff",
        initial_files={
            "main.py": "def hello():\n    pass\n\ndef world():\n    pass\n",
        },
        changed_files={
            "main.py": 'def hello():\n    print("hello")\n\ndef world():\n    pass\n',
        },
        must_include=["hello"],
        commit_message="Update hello",
    ),
    DiffTestCase(
        name="context_cross_file_ppr_callee",
        initial_files={
            "src/math_utils.py": "def calculate_sum(a, b):\n    return a + b\n\ndef calculate_product(a, b):\n    return a * b\n\ndef calculate_average(numbers):\n    total = calculate_sum(numbers[0], numbers[1])\n    for n in numbers[2:]:\n        total = calculate_sum(total, n)\n    return total / len(numbers)\n",
            "src/processor.py": "from math_utils import calculate_average\n\ndef process_data(data):\n    result = calculate_average(data)\n    return result\n",
        },
        changed_files={
            "src/processor.py": "from math_utils import calculate_average, calculate_product\n\ndef process_data(data):\n    avg = calculate_average(data)\n    prod = calculate_product(data[0], data[1])\n    return avg + prod\n",
        },
        must_include=["processor.py"],
        commit_message="Add product calculation",
    ),
    DiffTestCase(
        name="context_caller_backward_edges",
        initial_files={
            "src/core.py": "def core_function():\n    return 42\n",
            "src/caller_a.py": "from core import core_function\n\ndef use_core_a():\n    return core_function() + 1\n",
            "src/caller_b.py": "from core import core_function\n\ndef use_core_b():\n    return core_function() * 2\n",
        },
        changed_files={
            "src/core.py": "def core_function():\n    return 100\n",
        },
        must_include=["core.py"],
        commit_message="Change core return value",
    ),
    DiffTestCase(
        name="context_rare_identifier_pulls_definition",
        initial_files={
            "src/special_algorithm.py": "def fibonacci_memoized_optimized(n, cache=None):\n    if cache is None:\n        cache = {}\n    if n in cache:\n        return cache[n]\n    if n <= 1:\n        return n\n    result = fibonacci_memoized_optimized(n-1, cache) + fibonacci_memoized_optimized(n-2, cache)\n    cache[n] = result\n    return result\n",
            "src/main.py": 'def main():\n    print("Hello")\n',
        },
        changed_files={
            "src/main.py": "from special_algorithm import fibonacci_memoized_optimized\n\ndef main():\n    result = fibonacci_memoized_optimized(10)\n    print(result)\n",
        },
        must_include=["main.py", "special_algorithm.py"],
        commit_message="Use fibonacci",
    ),
    DiffTestCase(
        name="context_multi_file_selects_related",
        initial_files={
            "src/models/user.py": "class User:\n    def __init__(self, name):\n        self.name = name\n\n    def validate(self):\n        return len(self.name) > 0\n",
            "src/services/auth.py": "from models.user import User\n\ndef authenticate(username, password):\n    user = User(username)\n    if user.validate():\n        return check_password(password)\n    return False\n\ndef check_password(password):\n    return len(password) >= 8\n",
            "src/api/routes.py": 'from services.auth import authenticate\n\ndef login_endpoint(request):\n    result = authenticate(request.username, request.password)\n    return {"success": result}\n',
        },
        changed_files={
            "src/services/auth.py": 'from models.user import User\n\ndef authenticate(username, password):\n    user = User(username)\n    if not user.validate():\n        raise ValueError("Invalid username")\n    if not check_password(password):\n        raise ValueError("Invalid password")\n    return True\n\ndef check_password(password):\n    return len(password) >= 8 and any(c.isupper() for c in password)\n',
        },
        must_include=["auth.py"],
        commit_message="Improve auth with validation",
    ),
]


QUALITY_TEST_CASES = [
    DiffTestCase(
        name="quality_pytest_function",
        initial_files={
            "calculator.py": "def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a - b\n",
            "test_calculator.py": "def test_placeholder():\n    pass\n",
        },
        changed_files={
            "test_calculator.py": "from calculator import add\n\ndef test_add_positive():\n    assert add(2, 3) == 5\n\ndef test_add_negative():\n    assert add(-1, -1) == -2\n",
        },
        must_include=["def add"],
        commit_message="Add calculator tests",
    ),
    DiffTestCase(
        name="quality_pytest_fixture",
        initial_files={
            "models.py": 'class User:\n    def __init__(self, name, email):\n        self.name = name\n        self.email = email\n\n    def display_name(self):\n        return f"{self.name} <{self.email}>"\n',
            "test_models.py": "def test_placeholder():\n    pass\n",
        },
        changed_files={
            "test_models.py": 'import pytest\nfrom models import User\n\n@pytest.fixture\ndef sample_user():\n    return User("Alice", "alice@example.com")\n\ndef test_display_name(sample_user):\n    assert sample_user.display_name() == "Alice <alice@example.com>"\n',
        },
        must_include=["class User"],
        commit_message="Add fixture and test",
    ),
    DiffTestCase(
        name="quality_mock_patch",
        initial_files={
            "api_client.py": 'import requests\n\ndef fetch_user(user_id):\n    response = requests.get(f"https://api.example.com/users/{user_id}")\n    return response.json()\n',
            "test_api.py": "def test_placeholder():\n    pass\n",
        },
        changed_files={
            "test_api.py": 'from unittest import mock\nfrom api_client import fetch_user\n\n@mock.patch(\'api_client.requests.get\')\ndef test_fetch_user(mock_get):\n    mock_get.return_value.json.return_value = {"id": 1, "name": "Alice"}\n    result = fetch_user(1)\n    assert result["name"] == "Alice"\n',
        },
        must_include=["def fetch_user"],
        commit_message="Add mock.patch test",
    ),
    DiffTestCase(
        name="quality_simple_function_call",
        initial_files={
            "utils.py": "def foo(x):\n    return x * 2\n",
            "main.py": "def bar():\n    pass\n",
        },
        changed_files={
            "main.py": "from utils import foo\n\ndef bar():\n    return foo(42)\n",
        },
        must_include=["def foo"],
        commit_message="Add foo call",
    ),
    DiffTestCase(
        name="quality_method_call_on_object",
        initial_files={
            "service.py": "class DataService:\n    def process(self, data):\n        return data.upper()\n",
            "main.py": "def run(): pass\n",
        },
        changed_files={
            "main.py": 'from service import DataService\n\ndef run():\n    svc = DataService()\n    return svc.process("hello")\n',
        },
        must_include=["class DataService"],
        commit_message="Add service call",
    ),
    DiffTestCase(
        name="quality_decorator_function",
        initial_files={
            "decorators.py": 'def log_calls(func):\n    def wrapper(*args, **kwargs):\n        print(f"Calling {func.__name__}")\n        return func(*args, **kwargs)\n    return wrapper\n',
            "main.py": "def greet(): pass\n",
        },
        changed_files={
            "main.py": 'from decorators import log_calls\n\n@log_calls\ndef greet():\n    return "Hello"\n',
        },
        must_include=["def log_calls"],
        commit_message="Add decorator",
    ),
    DiffTestCase(
        name="quality_context_manager",
        initial_files={
            "managers.py": 'class DatabaseConnection:\n    def __enter__(self):\n        self.conn = "connected"\n        return self\n\n    def __exit__(self, *args):\n        self.conn = None\n\n    def query(self, sql):\n        return f"Result of {sql}"\n',
            "main.py": "data = None\n",
        },
        changed_files={
            "main.py": 'from managers import DatabaseConnection\n\nwith DatabaseConnection() as db:\n    data = db.query("SELECT *")\n',
        },
        must_include=["class DatabaseConnection"],
        commit_message="Use context manager",
    ),
    DiffTestCase(
        name="quality_chained_method_calls",
        initial_files={
            "builder.py": 'class QueryBuilder:\n    def __init__(self):\n        self.query = ""\n\n    def select(self, fields):\n        self.query += f"SELECT {fields}"\n        return self\n\n    def where(self, condition):\n        self.query += f" WHERE {condition}"\n        return self\n\n    def build(self):\n        return self.query\n',
            "main.py": "query = ''\n",
        },
        changed_files={
            "main.py": 'from builder import QueryBuilder\n\nquery = QueryBuilder().select("*").where("id=1").build()\n',
        },
        must_include=["class QueryBuilder"],
        commit_message="Use builder",
    ),
    DiffTestCase(
        name="quality_multiple_function_calls",
        initial_files={
            "utils.py": 'def validate(x):\n    return x > 0\n\ndef transform(x):\n    return x * 2\n\ndef save(x):\n    return f"saved: {x}"\n',
            "main.py": "def process(): pass\n",
        },
        changed_files={
            "main.py": "from utils import validate, transform, save\n\ndef process(data):\n    if validate(data):\n        result = transform(data)\n        return save(result)\n",
        },
        must_include=["def validate"],
        commit_message="Add processing",
        add_garbage_files=False,
    ),
    DiffTestCase(
        name="quality_imported_function_from_package",
        initial_files={
            "pkg/__init__.py": "",
            "pkg/helpers.py": "def compute(x):\n    return x ** 2\n",
            "main.py": "result = 0\n",
        },
        changed_files={
            "main.py": "from pkg.helpers import compute\n\nresult = compute(5)\n",
        },
        must_include=["def compute"],
        commit_message="Use compute",
    ),
]


COMPREHENSIVE_TEST_CASES = MONOREPO_TEST_CASES + STRUCTURAL_TEST_CASES + CONTEXT_TEST_CASES + QUALITY_TEST_CASES


@pytest.mark.parametrize("case", COMPREHENSIVE_TEST_CASES, ids=lambda c: c.name)
def test_comprehensive_cases(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
