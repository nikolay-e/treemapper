import pytest

from tests.utils import DiffTestCase, DiffTestRunner

EDGE_CASE_TESTS = [
    DiffTestCase(
        name="edge_whitespace_only_changes",
        initial_files={
            "test.py": """def hello():
    x = 1
    return x
""",
        },
        changed_files={
            "test.py": """def hello():
        x = 1
        return x
""",
        },
        must_include=["test.py"],
        add_garbage_files=False,
    ),
    DiffTestCase(
        name="edge_comment_only_changes",
        initial_files={
            "test.py": """def process():
    return 42
""",
        },
        changed_files={
            "test.py": """# TODO: refactor this later
def process():
    return 42
""",
        },
        must_include=["test.py"],
        add_garbage_files=False,
    ),
    DiffTestCase(
        name="edge_single_line_change",
        initial_files={
            "test.py": """def calculate():
    return x + 1
""",
        },
        changed_files={
            "test.py": """def calculate():
    return x + 2
""",
        },
        must_include=["calculate"],
        add_garbage_files=False,
    ),
    DiffTestCase(
        name="edge_diff_introduces_syntax_error",
        initial_files={
            "test.py": """def valid():
    return 1
""",
        },
        changed_files={
            "test.py": """def broken(
    return 1
""",
        },
        must_include=["test.py"],
        add_garbage_files=False,
    ),
    DiffTestCase(
        name="edge_file_already_broken",
        initial_files={
            "broken.py": """def broken(
    x = 1
""",
        },
        changed_files={
            "broken.py": """def broken(
    x = 1
    y = 2
""",
        },
        must_include=["broken.py"],
        add_garbage_files=False,
    ),
    DiffTestCase(
        name="edge_large_diff",
        initial_files={
            "large.py": "\n".join([f"def func{i}():\n    return {i}\n" for i in range(50)]),
        },
        changed_files={
            "large.py": "\n".join([f"def func{i}():\n    return {i * 2}\n" for i in range(50)]),
        },
        must_include=["large.py"],
    ),
    DiffTestCase(
        name="edge_many_small_hunks",
        initial_files={
            "utils.py": "\n".join([f"x{i} = {i}" for i in range(100)]),
        },
        changed_files={
            "utils.py": "\n".join([f"x{i} = {i * 10}" if i % 5 == 0 else f"x{i} = {i}" for i in range(100)]),
        },
        must_include=["utils.py"],
    ),
]

CIRCULAR_IMPORT_TESTS = [
    DiffTestCase(
        name="edge_circular_import",
        initial_files={
            "src/module_a.py": """from module_b import func_b

def func_a():
    return "a"

def call_b():
    return func_b()
""",
            "src/module_b.py": """from module_a import func_a

def func_b():
    return "b"

def call_a():
    return func_a()
""",
        },
        changed_files={
            "src/module_a.py": """from module_b import func_b, new_func_b

def func_a():
    return "a_updated"

def call_b():
    return func_b()

def call_new_b():
    return new_func_b()
""",
            "src/module_b.py": """from module_a import func_a

def func_b():
    return "b"

def new_func_b():
    return "new_b"

def call_a():
    return func_a()
""",
        },
        must_include=["module_a.py"],
    ),
    DiffTestCase(
        name="edge_reexport_chain",
        initial_files={
            "src/core/utils.ts": """export function coreutils() {
    return "core";
}
""",
            "src/lib/index.ts": """export { coreutils } from '../core/utils';
""",
            "src/index.ts": """export { coreutils } from './lib';
""",
            "src/app.ts": """import { coreutils } from './index';

export function main() {
    return coreutils();
}
""",
        },
        changed_files={
            "src/core/utils.ts": """export function coreutils() {
    return "core_v2";
}

export function newCoreUtil() {
    return "new_core";
}

export const CORE_VERSION = "2.0.0";
""",
        },
        must_include=["utils.ts"],
    ),
]

GENERATED_AND_VENDOR_TESTS = [
    DiffTestCase(
        name="edge_generated_code_comment",
        initial_files={
            "codegen.yaml": """generates:
  src/generated/types.ts:
    schema: schema.graphql
    plugins:
      - typescript
""",
            "src/generated/types.ts": """// THIS FILE IS GENERATED - DO NOT EDIT
// Generated from codegen.yaml

export interface User {
    id: string;
    name: string;
}
""",
            "src/services/user.ts": """import { User } from '../generated/types';

export function processUser(user: User) {
    return user.name;
}
""",
        },
        changed_files={
            "codegen.yaml": """generates:
  src/generated/types.ts:
    schema: schema.graphql
    plugins:
      - typescript
      - typescript-operations
  src/generated/hooks.ts:
    schema: schema.graphql
    plugins:
      - typescript-react-query
""",
        },
        must_include=["codegen.yaml"],
    ),
    DiffTestCase(
        name="edge_vendor_copy",
        initial_files={
            "third_party/lodash/chunk.js": """// Copied from lodash v4.17.21
function chunk(array, size) {
    const result = [];
    for (let i = 0; i < array.length; i += size) {
        result.push(array.slice(i, i + size));
    }
    return result;
}
module.exports = chunk;
""",
            "src/utils.js": """const chunk = require('../third_party/lodash/chunk');

function processInBatches(items) {
    return chunk(items, 10);
}

module.exports = { processInBatches };
""",
        },
        changed_files={
            "third_party/lodash/chunk.js": """// Copied from lodash v4.17.21
// Modified: added type checking
function chunk(array, size) {
    if (!Array.isArray(array)) {
        throw new TypeError('Expected array');
    }
    if (typeof size !== 'number' || size < 1) {
        size = 1;
    }
    const result = [];
    for (let i = 0; i < array.length; i += size) {
        result.push(array.slice(i, i + size));
    }
    return result;
}
module.exports = chunk;
""",
        },
        must_include=["chunk.js"],
    ),
    DiffTestCase(
        name="edge_dead_code_reference",
        initial_files={
            "src/deprecated.py": """def old_function():
    '''Deprecated: use new_function instead'''
    return "old"

def new_function():
    return "new"
""",
            "src/main.py": """from deprecated import new_function

def main():
    return new_function()
""",
            "src/legacy.py": """# This file still uses old_function for backwards compatibility
from deprecated import old_function

def legacy_handler():
    return old_function()
""",
        },
        changed_files={
            "src/deprecated.py": """import warnings

def old_function():
    '''Deprecated: use new_function instead'''
    warnings.warn(
        "old_function is deprecated, use new_function",
        DeprecationWarning,
        stacklevel=2
    )
    return "old"

def new_function():
    return "new_v2"

def newer_function():
    return "newer"
""",
        },
        must_include=["deprecated.py"],
    ),
]

CROSS_FILE_PATTERN_TESTS = [
    DiffTestCase(
        name="cross_file_decorator_chain",
        initial_files={
            "decorators/logging.py": """import functools
import logging

logger = logging.getLogger(__name__)

def log_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        logger.info(f"Finished {func.__name__}")
        return result
    return wrapper

def retry(max_attempts=3):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
        return wrapper
    return decorator
""",
            "services/user_service.py": """from decorators.logging import log_calls

class UserService:
    @log_calls
    def create_user(self, name: str, email: str):
        return {"name": name, "email": email}

    @log_calls
    def delete_user(self, user_id: int):
        return {"deleted": user_id}
""",
            "services/order_service.py": """from decorators.logging import log_calls, retry

class OrderService:
    @log_calls
    @retry(max_attempts=3)
    def create_order(self, user_id: int, items: list):
        return {"user_id": user_id, "items": items}

    @log_calls
    def cancel_order(self, order_id: int):
        return {"cancelled": order_id}
""",
        },
        changed_files={
            "decorators/logging.py": """import functools
import logging
import time

logger = logging.getLogger(__name__)

def log_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"Finished {func.__name__} in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed {func.__name__} after {elapsed:.3f}s: {e}")
            raise
    return wrapper

def retry(max_attempts=3):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
        return wrapper
    return decorator
""",
        },
        must_include=["logging.py", "log_calls"],
        add_garbage_files=False,
    ),
    DiffTestCase(
        name="cross_file_mixin_method_usage",
        initial_files={
            "mixins/auditable.py": """from datetime import datetime

class AuditableMixin:
    def get_created_at(self):
        return getattr(self, '_created_at', None)

    def set_created_at(self, value: datetime):
        self._created_at = value

    def get_updated_at(self):
        return getattr(self, '_updated_at', None)

    def set_updated_at(self, value: datetime):
        self._updated_at = value

    def audit_info(self):
        return {
            'created_at': self.get_created_at(),
            'updated_at': self.get_updated_at(),
        }
""",
            "models/user.py": """from mixins.auditable import AuditableMixin

class User(AuditableMixin):
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    def save(self):
        from datetime import datetime
        if not self.get_created_at():
            self.set_created_at(datetime.now())
        self.set_updated_at(datetime.now())
        return self
""",
            "models/order.py": """from mixins.auditable import AuditableMixin

class Order(AuditableMixin):
    def __init__(self, user_id: int, total: float):
        self.user_id = user_id
        self.total = total

    def save(self):
        from datetime import datetime
        if not self.get_created_at():
            self.set_created_at(datetime.now())
        self.set_updated_at(datetime.now())
        return self

    def get_summary(self):
        return {
            'user_id': self.user_id,
            'total': self.total,
            **self.audit_info()
        }
""",
        },
        changed_files={
            "mixins/auditable.py": """from datetime import datetime

class AuditableMixin:
    def get_created_at(self):
        return getattr(self, '_created_at', None)

    def set_created_at(self, value: datetime):
        self._created_at = value

    def get_updated_at(self):
        return getattr(self, '_updated_at', None)

    def set_updated_at(self, value: datetime):
        self._updated_at = value

    def get_created_by(self):
        return getattr(self, '_created_by', None)

    def set_created_by(self, user_id: int):
        self._created_by = user_id

    def audit_info(self):
        return {
            'created_at': self.get_created_at(),
            'updated_at': self.get_updated_at(),
            'created_by': self.get_created_by(),
        }

    def track_modification(self, user_id: int | None = None):
        now = datetime.now()
        if not self.get_created_at():
            self.set_created_at(now)
            if user_id:
                self.set_created_by(user_id)
        self.set_updated_at(now)
""",
        },
        must_include=["auditable.py", "AuditableMixin"],
    ),
    DiffTestCase(
        name="cross_file_abstract_factory",
        initial_files={
            "factories/base.py": """from abc import ABC, abstractmethod

class Button(ABC):
    @abstractmethod
    def render(self) -> str:
        pass

class Input(ABC):
    @abstractmethod
    def render(self) -> str:
        pass

class UIFactory(ABC):
    @abstractmethod
    def create_button(self, label: str) -> Button:
        pass

    @abstractmethod
    def create_input(self, placeholder: str) -> Input:
        pass
""",
            "factories/material.py": """from factories.base import UIFactory, Button, Input

class MaterialButton(Button):
    def __init__(self, label: str):
        self.label = label

    def render(self) -> str:
        return f'<button class="mdc-button">{self.label}</button>'

class MaterialInput(Input):
    def __init__(self, placeholder: str):
        self.placeholder = placeholder

    def render(self) -> str:
        return f'<input class="mdc-input" placeholder="{self.placeholder}">'

class MaterialUIFactory(UIFactory):
    def create_button(self, label: str) -> Button:
        return MaterialButton(label)

    def create_input(self, placeholder: str) -> Input:
        return MaterialInput(placeholder)
""",
            "factories/bootstrap.py": """from factories.base import UIFactory, Button, Input

class BootstrapButton(Button):
    def __init__(self, label: str):
        self.label = label

    def render(self) -> str:
        return f'<button class="btn btn-primary">{self.label}</button>'

class BootstrapInput(Input):
    def __init__(self, placeholder: str):
        self.placeholder = placeholder

    def render(self) -> str:
        return f'<input class="form-control" placeholder="{self.placeholder}">'

class BootstrapUIFactory(UIFactory):
    def create_button(self, label: str) -> Button:
        return BootstrapButton(label)

    def create_input(self, placeholder: str) -> Input:
        return BootstrapInput(placeholder)
""",
        },
        changed_files={
            "factories/base.py": """from abc import ABC, abstractmethod

class Button(ABC):
    @abstractmethod
    def render(self) -> str:
        pass

    @abstractmethod
    def set_disabled(self, disabled: bool) -> None:
        pass

class Input(ABC):
    @abstractmethod
    def render(self) -> str:
        pass

    @abstractmethod
    def set_required(self, required: bool) -> None:
        pass

class Checkbox(ABC):
    @abstractmethod
    def render(self) -> str:
        pass

class UIFactory(ABC):
    @abstractmethod
    def create_button(self, label: str) -> Button:
        pass

    @abstractmethod
    def create_input(self, placeholder: str) -> Input:
        pass

    @abstractmethod
    def create_checkbox(self, label: str) -> Checkbox:
        pass
""",
        },
        must_include=["base.py", "UIFactory"],
        add_garbage_files=False,
    ),
    DiffTestCase(
        name="cross_file_strategy_pattern",
        initial_files={
            "strategies/base.py": """from abc import ABC, abstractmethod

class SortStrategy(ABC):
    @abstractmethod
    def sort(self, data: list) -> list:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass
""",
            "strategies/quicksort.py": """from strategies.base import SortStrategy

class QuickSortStrategy(SortStrategy):
    def sort(self, data: list) -> list:
        if len(data) <= 1:
            return data
        pivot = data[len(data) // 2]
        left = [x for x in data if x < pivot]
        middle = [x for x in data if x == pivot]
        right = [x for x in data if x > pivot]
        return self.sort(left) + middle + self.sort(right)

    def get_name(self) -> str:
        return "QuickSort"
""",
            "strategies/mergesort.py": """from strategies.base import SortStrategy

class MergeSortStrategy(SortStrategy):
    def sort(self, data: list) -> list:
        if len(data) <= 1:
            return data
        mid = len(data) // 2
        left = self.sort(data[:mid])
        right = self.sort(data[mid:])
        return self._merge(left, right)

    def _merge(self, left: list, right: list) -> list:
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        result.extend(left[i:])
        result.extend(right[j:])
        return result

    def get_name(self) -> str:
        return "MergeSort"
""",
            "app/sorter.py": """from strategies.base import SortStrategy

class Sorter:
    def __init__(self, strategy: SortStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: SortStrategy):
        self._strategy = strategy

    def execute(self, data: list) -> list:
        print(f"Sorting with {self._strategy.get_name()}")
        return self._strategy.sort(data)
""",
        },
        changed_files={
            "strategies/base.py": """from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')

class SortStrategy(ABC, Generic[T]):
    @abstractmethod
    def sort(self, data: list[T]) -> list[T]:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_complexity(self) -> str:
        pass

    def is_stable(self) -> bool:
        return False
""",
        },
        must_include=["base.py", "SortStrategy"],
    ),
    DiffTestCase(
        name="cross_file_observer_pattern",
        initial_files={
            "observer/subject.py": """from abc import ABC, abstractmethod
from typing import List

class Observer(ABC):
    @abstractmethod
    def update(self, subject: 'Subject') -> None:
        pass

class Subject(ABC):
    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def notify(self) -> None:
        for observer in self._observers:
            observer.update(self)
""",
            "observer/stock.py": """from observer.subject import Subject

class Stock(Subject):
    def __init__(self, symbol: str, price: float):
        super().__init__()
        self._symbol = symbol
        self._price = price

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        self._price = value
        self.notify()
""",
            "observer/observers/price_alert.py": """from observer.subject import Observer, Subject

class PriceAlertObserver(Observer):
    def __init__(self, threshold: float):
        self.threshold = threshold
        self.alerts: list[str] = []

    def update(self, subject: Subject) -> None:
        if hasattr(subject, 'price') and subject.price > self.threshold:
            self.alerts.append(
                f"ALERT: {subject.symbol} exceeded {self.threshold}"
            )
""",
        },
        changed_files={
            "observer/subject.py": """from abc import ABC, abstractmethod
from typing import List, Any
from enum import Enum, auto

class EventType(Enum):
    CREATED = auto()
    UPDATED = auto()
    DELETED = auto()

class Observer(ABC):
    @abstractmethod
    def update(self, subject: 'Subject', event_type: EventType, data: Any = None) -> None:
        pass

class Subject(ABC):
    def __init__(self):
        self._observers: List[Observer] = []
        self._event_filters: dict[Observer, set[EventType]] = {}

    def attach(self, observer: Observer, event_types: set[EventType] | None = None) -> None:
        if observer not in self._observers:
            self._observers.append(observer)
            self._event_filters[observer] = event_types or set(EventType)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)
        self._event_filters.pop(observer, None)

    def notify(self, event_type: EventType = EventType.UPDATED, data: Any = None) -> None:
        for observer in self._observers:
            allowed_events = self._event_filters.get(observer, set(EventType))
            if event_type in allowed_events:
                observer.update(self, event_type, data)

    def get_observer_count(self) -> int:
        return len(self._observers)
""",
        },
        must_include=["subject.py", "notify"],
        add_garbage_files=False,
    ),
]

CROSS_CUTTING_TESTS = [
    DiffTestCase(
        name="cross_decorator_applied_to_changed_function",
        initial_files={
            "decorators/auth.py": """def login_required(func):
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            raise ValueError("Not authenticated")
        return func(*args, **kwargs)
    return wrapper

def is_authenticated():
    return True
""",
            "decorators/rate.py": """def rate_limit(limit):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator
""",
            "api.py": """from decorators.auth import login_required
from decorators.rate import rate_limit

@login_required
@rate_limit(100)
def api_endpoint():
    return {"status": "ok"}
""",
        },
        changed_files={
            "api.py": """from decorators.auth import login_required
from decorators.rate import rate_limit

@login_required
@rate_limit(100)
def api_endpoint():
    data = fetch_data()
    return {"status": "ok", "data": data}

def fetch_data():
    return [1, 2, 3]
""",
        },
        must_include=["api.py"],
    ),
    DiffTestCase(
        name="cross_decorator_definition_changed",
        initial_files={
            "decorators.py": """def cache(ttl=60):
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
            "services.py": """from decorators import cache

@cache(ttl=300)
def expensive_computation(x):
    return x ** 2

@cache(ttl=60)
def quick_lookup(key):
    return {"key": key}
""",
        },
        changed_files={
            "decorators.py": """import time

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
        },
        must_include=["decorators.py"],
    ),
    DiffTestCase(
        name="cross_middleware_changed",
        initial_files={
            "middleware/auth.py": """class AuthMiddleware:
    def process_request(self, request):
        if not request.get("token"):
            raise ValueError("Unauthorized")
        return request
""",
            "settings.py": """MIDDLEWARE = [
    "middleware.auth.AuthMiddleware",
]
""",
        },
        changed_files={
            "middleware/auth.py": """import time

class AuthMiddleware:
    def process_request(self, request):
        if not request.get("token"):
            raise ValueError("Unauthorized")
        request["authenticated_at"] = time.time()
        return request
""",
        },
        must_include=["auth.py"],
    ),
    DiffTestCase(
        name="cross_signal_handler_changed",
        initial_files={
            "models/user.py": """class User:
    def __init__(self, name):
        self.name = name
""",
            "signals.py": """from models.user import User

def on_user_created(sender, instance):
    print(f"User created: {instance.name}")
""",
        },
        changed_files={
            "signals.py": """from models.user import User

def on_user_created(sender, instance):
    print(f"User created: {instance.name}")
    send_welcome_email(instance)

def send_welcome_email(user):
    print(f"Welcome email sent to {user.name}")
""",
        },
        must_include=["signals.py"],
    ),
    DiffTestCase(
        name="cross_custom_exception_changed",
        initial_files={
            "exceptions.py": """class ValidationError(Exception):
    pass
""",
            "validators.py": """from exceptions import ValidationError

def validate(data):
    if not data:
        raise ValidationError("Data is empty")
    return True
""",
            "handlers.py": """from exceptions import ValidationError

def handle_request(data):
    try:
        return process(data)
    except ValidationError:
        return {"error": "Validation failed"}

def process(data):
    return data
""",
        },
        changed_files={
            "exceptions.py": """class ValidationError(Exception):
    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")
""",
        },
        must_include=["exceptions.py"],
    ),
    DiffTestCase(
        name="cross_exception_raised_find_handlers",
        initial_files={
            "exceptions.py": """class InsufficientFundsError(Exception):
    def __init__(self, account_id):
        self.account_id = account_id
        super().__init__(f"Insufficient funds for account {account_id}")
""",
            "service.py": """def transfer(from_account, to_account, amount):
    return True
""",
            "api/views.py": """from exceptions import InsufficientFundsError
from service import transfer

def transfer_endpoint(request):
    try:
        result = transfer(request.from_id, request.to_id, request.amount)
        return {"success": result}
    except InsufficientFundsError as e:
        return {"error": str(e)}
""",
        },
        changed_files={
            "service.py": """from exceptions import InsufficientFundsError

def transfer(from_account, to_account, amount):
    balance = get_balance(from_account)
    if balance < amount:
        raise InsufficientFundsError(from_account)
    return True

def get_balance(account):
    return 100
""",
        },
        must_include=["service.py"],
    ),
]

INTRA_FILE_TESTS = [
    DiffTestCase(
        name="intra_helper_functions_same_file",
        initial_files={
            "processor.py": """def helper_validate(data):
    return data is not None and len(data) > 0

def helper_transform(data):
    return data.strip().lower()

def helper_format(data):
    return f"[{data}]"

def main_function(data):
    if not helper_validate(data):
        return None
    transformed = helper_transform(data)
    return helper_format(transformed)
""",
        },
        changed_files={
            "processor.py": """def helper_validate(data):
    return data is not None and len(data) > 0

def helper_transform(data):
    return data.strip().lower()

def helper_format(data):
    return f"[{data}]"

def main_function(data):
    if not helper_validate(data):
        return None
    transformed = helper_transform(data)
    formatted = helper_format(transformed)
    return f"Result: {formatted}"
""",
        },
        must_include=["main_function"],
    ),
    DiffTestCase(
        name="intra_helper_chain",
        initial_files={
            "chain.py": """def step_one(x):
    return x + 1

def step_two(x):
    return step_one(x) * 2

def step_three(x):
    return step_two(x) + 10

def process(x):
    return step_three(x)
""",
        },
        changed_files={
            "chain.py": """def step_one(x):
    return x + 1

def step_two(x):
    return step_one(x) * 2

def step_three(x):
    return step_two(x) + 10

def process(x):
    result = step_three(x)
    return result * 100
""",
        },
        must_include=["process"],
    ),
    DiffTestCase(
        name="intra_private_methods",
        initial_files={
            "service.py": """class UserService:
    def _validate_email(self, email):
        return "@" in email and "." in email

    def _hash_password(self, password):
        return f"hashed_{password}"

    def _generate_token(self):
        return "token_123"

    def create_user(self, email, password):
        if not self._validate_email(email):
            raise ValueError("Invalid email")
        hashed = self._hash_password(password)
        token = self._generate_token()
        return {"email": email, "password": hashed, "token": token}
""",
        },
        changed_files={
            "service.py": """class UserService:
    def _validate_email(self, email):
        return "@" in email and "." in email

    def _hash_password(self, password):
        return f"hashed_{password}"

    def _generate_token(self):
        return "token_123"

    def create_user(self, email, password):
        if not self._validate_email(email):
            raise ValueError("Invalid email")
        hashed = self._hash_password(password)
        token = self._generate_token()
        return {"email": email, "password": hashed, "token": token, "verified": False}
""",
        },
        must_include=["create_user"],
    ),
    DiffTestCase(
        name="intra_private_method_changed",
        initial_files={
            "cache.py": """class CacheManager:
    def __init__(self):
        self._data = {}

    def _serialize(self, value):
        return str(value)

    def _deserialize(self, data):
        return data

    def get(self, key):
        raw = self._data.get(key)
        if raw:
            return self._deserialize(raw)
        return None

    def set(self, key, value):
        self._data[key] = self._serialize(value)
""",
        },
        changed_files={
            "cache.py": """import json

class CacheManager:
    def __init__(self):
        self._data = {}

    def _serialize(self, value):
        return json.dumps(value)

    def _deserialize(self, data):
        return json.loads(data)

    def get(self, key):
        raw = self._data.get(key)
        if raw:
            return self._deserialize(raw)
        return None

    def set(self, key, value):
        self._data[key] = self._serialize(value)
""",
        },
        must_include=["_serialize", "_deserialize"],
    ),
    DiffTestCase(
        name="intra_nested_functions",
        initial_files={
            "decorator.py": """def outer_function(config):
    def inner_validator(value):
        return value is not None

    def inner_transformer(value):
        return value.upper()

    def process(data):
        if not inner_validator(data):
            return None
        return inner_transformer(data)

    return process
""",
        },
        changed_files={
            "decorator.py": """def outer_function(config):
    def inner_validator(value):
        return value is not None and len(value) > 0

    def inner_transformer(value):
        return value.upper()

    def process(data):
        if not inner_validator(data):
            return None
        return inner_transformer(data)

    return process
""",
        },
        must_include=["inner_validator"],
    ),
    DiffTestCase(
        name="intra_closure_variables",
        initial_files={
            "counter.py": """def make_counter(start=0):
    count = start

    def increment():
        nonlocal count
        count += 1
        return count

    def decrement():
        nonlocal count
        count -= 1
        return count

    def get_value():
        return count

    return increment, decrement, get_value
""",
        },
        changed_files={
            "counter.py": """def make_counter(start=0, step=1):
    count = start

    def increment():
        nonlocal count
        count += step
        return count

    def decrement():
        nonlocal count
        count -= step
        return count

    def get_value():
        return count

    return increment, decrement, get_value
""",
        },
        must_include=["make_counter"],
    ),
    DiffTestCase(
        name="intra_class_constants_usage",
        initial_files={
            "config.py": """class APIConfig:
    BASE_URL = "https://api.example.com"
    TIMEOUT = 30
    MAX_RETRIES = 3

    def get_endpoint(self, path):
        return f"{self.BASE_URL}/{path}"

    def get_with_retry(self, url):
        for i in range(self.MAX_RETRIES):
            try:
                return self._fetch(url)
            except Exception:
                if i == self.MAX_RETRIES - 1:
                    raise
        return None

    def _fetch(self, url):
        pass
""",
        },
        changed_files={
            "config.py": """class APIConfig:
    BASE_URL = "https://api.v2.example.com"
    TIMEOUT = 30
    MAX_RETRIES = 3

    def get_endpoint(self, path):
        return f"{self.BASE_URL}/{path}"

    def get_with_retry(self, url):
        for i in range(self.MAX_RETRIES):
            try:
                return self._fetch(url)
            except Exception:
                if i == self.MAX_RETRIES - 1:
                    raise
        return None

    def _fetch(self, url):
        pass
""",
        },
        must_include=["BASE_URL"],
    ),
    DiffTestCase(
        name="intra_constant_in_multiple_methods",
        initial_files={
            "limits.py": """class RateLimiter:
    MAX_REQUESTS = 100
    TIME_WINDOW = 60

    def __init__(self):
        self.requests = []

    def can_proceed(self):
        self._cleanup_old()
        return len(self.requests) < self.MAX_REQUESTS

    def record_request(self):
        if len(self.requests) >= self.MAX_REQUESTS:
            raise Exception("Rate limit exceeded")
        self.requests.append(time.time())

    def get_remaining(self):
        self._cleanup_old()
        return self.MAX_REQUESTS - len(self.requests)

    def _cleanup_old(self):
        cutoff = time.time() - self.TIME_WINDOW
        self.requests = [r for r in self.requests if r > cutoff]
""",
        },
        changed_files={
            "limits.py": """class RateLimiter:
    MAX_REQUESTS = 200
    TIME_WINDOW = 60

    def __init__(self):
        self.requests = []

    def can_proceed(self):
        self._cleanup_old()
        return len(self.requests) < self.MAX_REQUESTS

    def record_request(self):
        if len(self.requests) >= self.MAX_REQUESTS:
            raise Exception("Rate limit exceeded")
        self.requests.append(time.time())

    def get_remaining(self):
        self._cleanup_old()
        return self.MAX_REQUESTS - len(self.requests)

    def _cleanup_old(self):
        cutoff = time.time() - self.TIME_WINDOW
        self.requests = [r for r in self.requests if r > cutoff]
""",
        },
        must_include=["MAX_REQUESTS"],
    ),
    DiffTestCase(
        name="intra_module_level_variables",
        initial_files={
            "settings.py": """DEBUG = True
LOG_LEVEL = "INFO"
DATABASE_URL = "sqlite:///app.db"

def get_log_level():
    return LOG_LEVEL

def is_debug():
    return DEBUG

def get_db_connection():
    from sqlalchemy import create_engine
    return create_engine(DATABASE_URL)

def configure_logging():
    import logging
    level = getattr(logging, LOG_LEVEL)
    logging.basicConfig(level=level)
""",
        },
        changed_files={
            "settings.py": """DEBUG = False
LOG_LEVEL = "INFO"
DATABASE_URL = "sqlite:///app.db"

def get_log_level():
    return LOG_LEVEL

def is_debug():
    return DEBUG

def get_db_connection():
    from sqlalchemy import create_engine
    return create_engine(DATABASE_URL)

def configure_logging():
    import logging
    level = getattr(logging, LOG_LEVEL)
    logging.basicConfig(level=level)
""",
        },
        must_include=["DEBUG"],
    ),
    DiffTestCase(
        name="intra_multiple_module_variables",
        initial_files={
            "constants.py": """APP_NAME = "MyApp"
VERSION = "1.0.0"
AUTHOR = "Developer"

_cache = {}

def get_app_info():
    return f"{APP_NAME} v{VERSION} by {AUTHOR}"

def get_version():
    return VERSION

def cache_get(key):
    return _cache.get(key)

def cache_set(key, value):
    _cache[key] = value
""",
        },
        changed_files={
            "constants.py": """APP_NAME = "MyApp"
VERSION = "2.0.0"
AUTHOR = "Developer"

_cache = {}

def get_app_info():
    return f"{APP_NAME} v{VERSION} by {AUTHOR}"

def get_version():
    return VERSION

def cache_get(key):
    return _cache.get(key)

def cache_set(key, value):
    _cache[key] = value
""",
        },
        must_include=["VERSION"],
    ),
    DiffTestCase(
        name="intra_private_module_variable",
        initial_files={
            "registry.py": """_handlers = {}
_initialized = False

def register(name, handler):
    global _initialized
    if not _initialized:
        _initialize()
    _handlers[name] = handler

def get_handler(name):
    return _handlers.get(name)

def _initialize():
    global _initialized
    _handlers.clear()
    _initialized = True

def list_handlers():
    return list(_handlers.keys())
""",
        },
        changed_files={
            "registry.py": """_handlers = {}
_initialized = False
_default_handler = None

def register(name, handler):
    global _initialized
    if not _initialized:
        _initialize()
    _handlers[name] = handler

def get_handler(name):
    return _handlers.get(name, _default_handler)

def _initialize():
    global _initialized
    _handlers.clear()
    _initialized = True

def list_handlers():
    return list(_handlers.keys())

def set_default(handler):
    global _default_handler
    _default_handler = handler
""",
        },
        must_include=["registry.py"],
    ),
]

ALL_PATTERN_CASES = (
    EDGE_CASE_TESTS
    + CIRCULAR_IMPORT_TESTS
    + GENERATED_AND_VENDOR_TESTS
    + CROSS_FILE_PATTERN_TESTS
    + CROSS_CUTTING_TESTS
    + INTRA_FILE_TESTS
)


@pytest.mark.parametrize("case", ALL_PATTERN_CASES, ids=lambda c: c.name)
def test_pattern_cases(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
