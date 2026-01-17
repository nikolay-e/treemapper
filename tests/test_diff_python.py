import pytest

from tests.utils import DiffTestCase, DiffTestRunner

PYTHON_BASIC_CASES = [
    DiffTestCase(
        name="python_001_dataclass_field_changed",
        initial_files={
            "models.py": """from dataclasses import dataclass

@dataclass
class Order:
    id: int
    customer_id: int
    total: float
""",
            "services.py": """from models import Order

def create_order(customer_id, total):
    return Order(id=1, customer_id=customer_id, total=total)

def process_order(order: Order):
    return f"Processing order {order.id}"
""",
            "garbage_unused.py": """garbage_marker_12345 = "never used"
unused_marker_67890 = "also never used"
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
""",
        },
        must_include=["@dataclass", "class Order", "priority"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_002_property_changed",
        initial_files={
            "user.py": """class User:
    def __init__(self, first, last):
        self.first = first
        self.last = last

    @property
    def full_name(self):
        return f"{self.first} {self.last}"
""",
            "views.py": """from user import User

def render_user(user):
    return f"Name: {user.full_name}"
""",
            "garbage_file.py": """garbage_marker_12345 = True
unused_marker_67890 = False
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
        must_include=["@property", "full_name", "title"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_003_dunder_method_changed",
        initial_files={
            "money.py": """class Money:
    def __init__(self, amount, currency="USD"):
        self.amount = amount
        self.currency = currency

    def __str__(self):
        return f"{self.currency} {self.amount:.2f}"
""",
            "calculator.py": """from money import Money

def sum_money(m1, m2):
    return Money(m1.amount + m2.amount)
""",
            "unrelated.py": """garbage_marker_12345 = "test"
unused_marker_67890 = 123
""",
        },
        changed_files={
            "money.py": """class Money:
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
        },
        must_include=["__add__", "class Money"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_004_context_manager_changed",
        initial_files={
            "db.py": """from contextlib import contextmanager

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
            "service.py": """from db import transaction

def save_data(data):
    with transaction():
        store(data)

def store(data):
    print(f"Storing {data}")
""",
            "garbage.py": """garbage_marker_12345 = None
unused_marker_67890 = []
""",
        },
        changed_files={
            "db.py": """from contextlib import contextmanager
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
        },
        must_include=["@contextmanager", "transaction"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]


PYTHON_ASYNC_CASES = [
    DiffTestCase(
        name="python_005_async_function_with_timeout",
        initial_files={
            "async_utils.py": """async def fetch_data(url):
    await simulate_delay()
    return {"url": url, "data": "content"}

async def simulate_delay():
    import asyncio
    await asyncio.sleep(0.1)
""",
            "handler.py": """from async_utils import fetch_data

async def handle_request(url):
    data = await fetch_data(url)
    return data
""",
            "garbage.py": """garbage_marker_12345 = "async garbage"
unused_marker_67890 = "not used"
""",
        },
        changed_files={
            "async_utils.py": """import asyncio

async def fetch_data(url, timeout=30):
    try:
        await asyncio.wait_for(simulate_delay(), timeout=timeout)
        return {"url": url, "data": "content", "timeout": timeout}
    except asyncio.TimeoutError:
        return {"url": url, "error": "timeout"}

async def simulate_delay():
    await asyncio.sleep(0.1)
""",
        },
        must_include=["async def fetch_data", "timeout"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]


PYTHON_TYPE_ANNOTATION_CASES = [
    DiffTestCase(
        name="python_006_generic_container_added",
        initial_files={
            "types.py": """from typing import List, Optional

def process_items(items: List[str]) -> Optional[str]:
    if not items:
        return None
    return items[0]
""",
            "garbage.py": """garbage_marker_12345 = {}
unused_marker_67890 = set()
""",
        },
        changed_files={
            "types.py": """from typing import List, Optional, TypeVar, Generic

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
        },
        must_include=["TypeVar", "Generic", "Container"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]


PYTHON_FUNCTION_CALL_CASES = [
    DiffTestCase(
        name="python_007_function_from_module",
        initial_files={
            "utils/tax.py": """def calculate_tax(income: float) -> float:
    if income < 10000:
        return 0
    return income * 0.2
""",
            "services/billing.py": """def get_total():
    return 100
""",
            "garbage.py": """garbage_marker_12345 = 1
unused_marker_67890 = 2
""",
        },
        changed_files={
            "services/billing.py": """from utils.tax import calculate_tax

def get_total(income: float) -> float:
    tax = calculate_tax(income)
    return income - tax
""",
        },
        must_include=["def calculate_tax"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_008_method_call_on_object",
        initial_files={
            "models/user.py": """class User:
    def __init__(self, name: str):
        self.name = name
        self.active = True

    def update_profile(self, data: dict):
        self.name = data.get("name", self.name)
""",
            "handlers/profile.py": """def handle_update():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "unused"
unused_marker_67890 = "also unused"
""",
        },
        changed_files={
            "handlers/profile.py": """from models.user import User

def handle_update(user: User, data: dict):
    user.update_profile(data)
    return user
""",
        },
        must_include=["def update_profile"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_009_decorator_usage",
        initial_files={
            "decorators.py": """import functools
import time

def rate_limit(calls_per_second: int):
    def decorator(func):
        last_call = [0.0]
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]
            if elapsed < 1.0 / calls_per_second:
                time.sleep(1.0 / calls_per_second - elapsed)
            last_call[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator
""",
            "api.py": """def call_api():
    return "response"
""",
            "garbage.py": """garbage_marker_12345 = "decorator garbage"
unused_marker_67890 = "unused decorator"
""",
        },
        changed_files={
            "api.py": """from decorators import rate_limit

@rate_limit(100)
def call_api():
    return "response"
""",
        },
        must_include=["def rate_limit"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_010_super_init_call",
        initial_files={
            "base.py": """class BaseConfig:
    def __init__(self, config: dict):
        self.debug = config.get("debug", False)
        self.timeout = config.get("timeout", 30)
""",
            "app.py": """class AppConfig:
    pass
""",
            "garbage.py": """garbage_marker_12345 = "base garbage"
unused_marker_67890 = "unused base"
""",
        },
        changed_files={
            "app.py": """from base import BaseConfig

class AppConfig(BaseConfig):
    def __init__(self, config: dict):
        super().__init__(config)
        self.app_name = config.get("name", "app")
""",
        },
        must_include=["BaseConfig"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_011_override_method",
        initial_files={
            "base_processor.py": """class BaseProcessor:
    def process(self, data: list) -> list:
        return [item.strip() for item in data]

    def validate(self, item: str) -> bool:
        return len(item) > 0
""",
            "custom_processor.py": """class CustomProcessor:
    pass
""",
            "garbage.py": """garbage_marker_12345 = "processor garbage"
unused_marker_67890 = "unused processor"
""",
        },
        changed_files={
            "custom_processor.py": """from base_processor import BaseProcessor

class CustomProcessor(BaseProcessor):
    def process(self, data: list) -> list:
        validated = [item for item in data if self.validate(item)]
        return super().process(validated)
""",
        },
        must_include=["def process", "BaseProcessor"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_012_context_manager_usage",
        initial_files={
            "db.py": """class DatabaseConnection:
    def __init__(self, url: str):
        self.url = url
        self.conn = None

    def __enter__(self):
        self.conn = self._connect()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
        return False

    def _connect(self):
        return {"url": self.url}
""",
            "service.py": """def run_query():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "db garbage"
unused_marker_67890 = "unused db"
""",
        },
        changed_files={
            "service.py": """from db import DatabaseConnection

def run_query(url: str, query: str):
    with DatabaseConnection(url) as db:
        return db.execute(query)
""",
        },
        must_include=["__enter__"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_013_async_await_function",
        initial_files={
            "fetcher.py": """import aiohttp

async def fetch_user_data(user_id: int) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"/users/{user_id}") as resp:
            return await resp.json()
""",
            "handlers.py": """async def handle_request():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "fetcher garbage"
unused_marker_67890 = "unused fetcher"
""",
        },
        changed_files={
            "handlers.py": """from fetcher import fetch_user_data

async def handle_request(user_id: int):
    data = await fetch_user_data(user_id)
    return {"user": data}
""",
        },
        must_include=["async def fetch_user_data"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_014_generator_usage",
        initial_files={
            "batching.py": """def data_batches(records: list, batch_size: int = 100):
    for i in range(0, len(records), batch_size):
        yield records[i:i + batch_size]
""",
            "processor.py": """def process_all():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "batch garbage"
unused_marker_67890 = "unused batch"
""",
        },
        changed_files={
            "processor.py": """from batching import data_batches

def process_all(records: list):
    results = []
    for batch in data_batches(records):
        results.extend(process_batch(batch))
    return results

def process_batch(batch: list):
    return [item.upper() for item in batch]
""",
        },
        must_include=["yield"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_015_property_access",
        initial_files={
            "models/person.py": """class Person:
    def __init__(self, first: str, last: str):
        self.first = first
        self.last = last

    @property
    def full_name(self) -> str:
        return f"{self.first} {self.last}"
""",
            "views.py": """def render():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "person garbage"
unused_marker_67890 = "unused person"
""",
        },
        changed_files={
            "views.py": """from models.person import Person

def render(person: Person) -> str:
    name = person.full_name
    return f"<h1>{name}</h1>"
""",
        },
        must_include=["@property"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_016_classmethod_call",
        initial_files={
            "models/config.py": """import json

class Config:
    def __init__(self, data: dict):
        self.data = data

    @classmethod
    def from_json(cls, json_str: str) -> "Config":
        data = json.loads(json_str)
        return cls(data)

    @classmethod
    def from_file(cls, path: str) -> "Config":
        with open(path) as f:
            return cls.from_json(f.read())
""",
            "loader.py": """def load():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "config garbage"
unused_marker_67890 = "unused config"
""",
        },
        changed_files={
            "loader.py": """from models.config import Config

def load(json_data: str) -> Config:
    return Config.from_json(json_data)
""",
        },
        must_include=["@classmethod"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_017_staticmethod_call",
        initial_files={
            "validators.py": r"""import re

class Validator:
    @staticmethod
    def is_email(text: str) -> bool:
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return bool(re.match(pattern, text))

    @staticmethod
    def is_phone(text: str) -> bool:
        return text.isdigit() and len(text) >= 10
""",
            "forms.py": """def validate_form():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "validator garbage"
unused_marker_67890 = "unused validator"
""",
        },
        changed_files={
            "forms.py": """from validators import Validator

def validate_form(email: str, phone: str) -> bool:
    valid_email = Validator.is_email(email)
    valid_phone = Validator.is_phone(phone)
    return valid_email and valid_phone
""",
        },
        must_include=["@staticmethod"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_018_dunder_add_operator",
        initial_files={
            "cart.py": """class Cart:
    def __init__(self, items: list):
        self.items = items

    def __add__(self, other: "Cart") -> "Cart":
        return Cart(self.items + other.items)

    def total(self) -> float:
        return sum(item.price for item in self.items)
""",
            "checkout.py": """def process():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "cart garbage"
unused_marker_67890 = "unused cart"
""",
        },
        changed_files={
            "checkout.py": """from cart import Cart

def merge_carts(cart1: Cart, cart2: Cart) -> Cart:
    combined = cart1 + cart2
    return combined
""",
        },
        must_include=["__add__"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_019_getitem_access",
        initial_files={
            "cache.py": """class Cache:
    def __init__(self):
        self._data = {}

    def __getitem__(self, key: str):
        return self._data.get(key)

    def __setitem__(self, key: str, value):
        self._data[key] = value
""",
            "service.py": """def get_value():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "cache garbage"
unused_marker_67890 = "unused cache"
""",
        },
        changed_files={
            "service.py": """from cache import Cache

cache = Cache()

def get_value(key: str):
    return cache[key]
""",
        },
        must_include=["__getitem__"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_020_lambda_variable_usage",
        initial_files={
            "transforms.py": """transformer = lambda x: x.upper()
normalizer = lambda x: x.strip().lower()
""",
            "processor.py": """def process():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "lambda garbage"
unused_marker_67890 = "unused lambda"
""",
        },
        changed_files={
            "processor.py": """from transforms import transformer

def process(data: str) -> str:
    result = transformer(data)
    return result
""",
        },
        must_include=["lambda"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_021_partial_function_usage",
        initial_files={
            "formatters.py": """import functools

def format_number(value: float, precision: int = 2, prefix: str = "") -> str:
    return f"{prefix}{value:.{precision}f}"

format_currency = functools.partial(format_number, precision=2, prefix="$")
format_percent = functools.partial(format_number, precision=1, prefix="")
""",
            "reports.py": """def generate():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "format garbage"
unused_marker_67890 = "unused format"
""",
        },
        changed_files={
            "reports.py": """from formatters import format_currency

def generate(amount: float) -> str:
    return format_currency(amount)
""",
        },
        must_include=["def format_number"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_022_callable_class_usage",
        initial_files={
            "processor.py": """class TextProcessor:
    def __init__(self, uppercase: bool = False):
        self.uppercase = uppercase

    def __call__(self, text: str) -> str:
        result = text.strip()
        if self.uppercase:
            result = result.upper()
        return result
""",
            "handler.py": """def handle():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "text garbage"
unused_marker_67890 = "unused text"
""",
        },
        changed_files={
            "handler.py": """from processor import TextProcessor

processor = TextProcessor(uppercase=True)

def handle(text: str) -> str:
    return processor(text)
""",
        },
        must_include=["__call__"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_023_mixin_method_call",
        initial_files={
            "mixins.py": """import logging

class LoggingMixin:
    logger = logging.getLogger(__name__)

    def log_action(self, action: str):
        self.logger.info(f"Action: {action}")

    def log_error(self, error: str):
        self.logger.error(f"Error: {error}")
""",
            "service.py": """class UserService:
    pass
""",
            "garbage.py": """garbage_marker_12345 = "mixin garbage"
unused_marker_67890 = "unused mixin"
""",
        },
        changed_files={
            "service.py": """from mixins import LoggingMixin

class UserService(LoggingMixin):
    def create_user(self, name: str):
        self.log_action(f"Creating user: {name}")
        return {"name": name}
""",
        },
        must_include=["def log_action"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_024_abstract_method_implementation",
        initial_files={
            "base.py": """from abc import ABC, abstractmethod

class BaseHandler(ABC):
    @abstractmethod
    def execute(self, data: dict) -> dict:
        pass

    @abstractmethod
    def validate(self, data: dict) -> bool:
        pass
""",
            "handlers.py": """class Handler:
    pass
""",
            "garbage.py": """garbage_marker_12345 = "abstract garbage"
unused_marker_67890 = "unused abstract"
""",
        },
        changed_files={
            "handlers.py": """from base import BaseHandler

class ConcreteHandler(BaseHandler):
    def execute(self, data: dict) -> dict:
        return {"processed": data}

    def validate(self, data: dict) -> bool:
        return "id" in data
""",
        },
        must_include=["@abstractmethod"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_025_protocol_implementation",
        initial_files={
            "protocols.py": """from typing import Protocol

class Serializable(Protocol):
    def to_dict(self) -> dict: ...
    def from_dict(self, data: dict) -> None: ...

class Comparable(Protocol):
    def __lt__(self, other) -> bool: ...
    def __eq__(self, other) -> bool: ...
""",
            "models.py": """class User:
    pass
""",
            "garbage.py": """garbage_marker_12345 = "protocol garbage"
unused_marker_67890 = "unused protocol"
""",
        },
        changed_files={
            "models.py": """class User:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def to_dict(self) -> dict:
        return {"name": self.name, "age": self.age}

    def from_dict(self, data: dict) -> None:
        self.name = data["name"]
        self.age = data["age"]
""",
        },
        must_include=["to_dict", "from_dict"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_026_getattr_dynamic_call",
        initial_files={
            "actions.py": """class ActionHandler:
    def process(self, data):
        return {"action": "process", "data": data}

    def validate(self, data):
        return {"action": "validate", "data": data}

    def transform(self, data):
        return {"action": "transform", "data": data}
""",
            "dispatcher.py": """def dispatch():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "action garbage"
unused_marker_67890 = "unused action"
""",
        },
        changed_files={
            "dispatcher.py": """from actions import ActionHandler

handler = ActionHandler()

def dispatch(action: str, data: dict):
    method = getattr(handler, action, None)
    if method:
        return method(data)
    return None
""",
        },
        must_include=["def process"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]


PYTHON_TYPE_HINT_CASES = [
    DiffTestCase(
        name="python_027_type_hint_parameter",
        initial_files={
            "models/user.py": """class UserModel:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
""",
            "services.py": """def process():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "model garbage"
unused_marker_67890 = "unused model"
""",
        },
        changed_files={
            "services.py": """from models.user import UserModel

def process(user: UserModel) -> dict:
    return {"id": user.id, "name": user.name}
""",
        },
        must_include=["class UserModel"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_028_return_type_annotation",
        initial_files={
            "models/order.py": """class Order:
    def __init__(self, id: int, total: float):
        self.id = id
        self.total = total
""",
            "repository.py": """def get_orders():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "order garbage"
unused_marker_67890 = "unused order"
""",
        },
        changed_files={
            "repository.py": """from models.order import Order

def get_orders() -> list[Order]:
    return [Order(1, 100.0), Order(2, 200.0)]
""",
        },
        must_include=["class Order"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_029_generic_type_usage",
        initial_files={
            "containers.py": """from typing import Generic, TypeVar

K = TypeVar('K')
V = TypeVar('V')

class Cache(Generic[K, V]):
    def __init__(self):
        self._data: dict[K, V] = {}

    def get(self, key: K) -> V | None:
        return self._data.get(key)

    def set(self, key: K, value: V) -> None:
        self._data[key] = value
""",
            "service.py": """def run():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "container garbage"
unused_marker_67890 = "unused container"
""",
        },
        changed_files={
            "service.py": """from containers import Cache

cache: Cache[str, dict] = Cache()

def run(key: str, data: dict):
    cache.set(key, data)
    return cache.get(key)
""",
        },
        must_include=["class Cache"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_030_typevar_with_bound",
        initial_files={
            "base.py": """class BaseModel:
    def validate(self) -> bool:
        return True

    def to_dict(self) -> dict:
        return {}
""",
            "repository.py": """def save():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "typevar garbage"
unused_marker_67890 = "unused typevar"
""",
        },
        changed_files={
            "repository.py": """from typing import TypeVar
from base import BaseModel

T = TypeVar('T', bound=BaseModel)

def save(model: T) -> T:
    if model.validate():
        return model
    raise ValueError("Invalid model")
""",
        },
        must_include=["class BaseModel"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_031_typeddict_usage",
        initial_files={
            "types.py": """from typing import TypedDict

class AppConfig(TypedDict):
    debug: bool
    timeout: int
    host: str
    port: int
""",
            "loader.py": """def load_config():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "typeddict garbage"
unused_marker_67890 = "unused typeddict"
""",
        },
        changed_files={
            "loader.py": """from types import AppConfig

def load_config() -> AppConfig:
    return {
        "debug": True,
        "timeout": 30,
        "host": "localhost",
        "port": 8080
    }
""",
        },
        must_include=["class AppConfig"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_032_namedtuple_usage",
        initial_files={
            "geometry.py": """from typing import NamedTuple

class Point(NamedTuple):
    x: float
    y: float

    def distance(self, other: "Point") -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
""",
            "renderer.py": """def draw():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "geometry garbage"
unused_marker_67890 = "unused geometry"
""",
        },
        changed_files={
            "renderer.py": """from geometry import Point

def draw(start: Point, end: Point) -> float:
    point = Point(x=start.x, y=end.y)
    return point.distance(end)
""",
        },
        must_include=["class Point"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_033_dataclass_usage",
        initial_files={
            "models.py": """from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int
    email: str = ""
""",
            "service.py": """def create():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "dataclass garbage"
unused_marker_67890 = "unused dataclass"
""",
        },
        changed_files={
            "service.py": """from models import User

def create(name: str, age: int) -> User:
    return User(name=name, age=age)
""",
        },
        must_include=["@dataclass"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_034_pydantic_model_usage",
        initial_files={
            "schemas.py": """from pydantic import BaseModel, EmailStr

class UserSchema(BaseModel):
    name: str
    email: EmailStr
    age: int

    class Config:
        orm_mode = True
""",
            "api.py": """def validate():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "pydantic garbage"
unused_marker_67890 = "unused pydantic"
""",
        },
        changed_files={
            "api.py": """from schemas import UserSchema

def validate(data: dict) -> UserSchema:
    return UserSchema(**data)
""",
        },
        must_include=["class UserSchema"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_035_enum_usage",
        initial_files={
            "enums.py": """from enum import Enum, auto

class OrderStatus(Enum):
    PENDING = auto()
    PROCESSING = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()
""",
            "orders.py": """def update_status():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "enum garbage"
unused_marker_67890 = "unused enum"
""",
        },
        changed_files={
            "orders.py": """from enums import OrderStatus

def update_status(order_id: int) -> OrderStatus:
    return OrderStatus.PENDING
""",
        },
        must_include=["class OrderStatus"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_036_newtype_usage",
        initial_files={
            "types.py": """from typing import NewType

UserId = NewType('UserId', int)
OrderId = NewType('OrderId', int)
""",
            "service.py": """def get_user():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "newtype garbage"
unused_marker_67890 = "unused newtype"
""",
        },
        changed_files={
            "service.py": """from types import UserId

def get_user(user_id: UserId) -> dict:
    return {"id": user_id}
""",
        },
        must_include=["UserId = NewType"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]


PYTHON_IMPORT_CASES = [
    DiffTestCase(
        name="python_037_from_import",
        initial_files={
            "utils/helpers.py": """def format_date(dt) -> str:
    return dt.strftime("%Y-%m-%d")

def format_time(dt) -> str:
    return dt.strftime("%H:%M:%S")
""",
            "views.py": """def render():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "helper garbage"
unused_marker_67890 = "unused helper"
""",
        },
        changed_files={
            "views.py": """from utils.helpers import format_date

def render(event):
    return f"Date: {format_date(event.date)}"
""",
        },
        must_include=["def format_date"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_038_import_alias",
        initial_files={
            "data_utils.py": """def process_dataframe(df):
    return df.dropna()
""",
            "analysis.py": """def analyze():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "data garbage"
unused_marker_67890 = "unused data"
""",
        },
        changed_files={
            "analysis.py": """import pandas as pd
from data_utils import process_dataframe

def analyze(path: str):
    df = pd.read_csv(path)
    df = process_dataframe(df)
    return df.describe()
""",
        },
        must_include=["def process_dataframe"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_039_relative_import",
        initial_files={
            "package/models/user.py": """class User:
    def __init__(self, name: str):
        self.name = name
""",
            "package/services/user_service.py": """class UserService:
    pass
""",
            "garbage.py": """garbage_marker_12345 = "relative garbage"
unused_marker_67890 = "unused relative"
""",
        },
        changed_files={
            "package/services/user_service.py": """from ..models.user import User

class UserService:
    def create(self, name: str) -> User:
        return User(name)
""",
        },
        must_include=["class User"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_040_init_reexport",
        initial_files={
            "mypackage/helpers.py": """class HelperClass:
    def help(self):
        return "helping"
""",
            "mypackage/__init__.py": """from .helpers import HelperClass

__all__ = ["HelperClass"]
""",
            "app.py": """def run():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "init garbage"
unused_marker_67890 = "unused init"
""",
        },
        changed_files={
            "app.py": """from mypackage import HelperClass

def run():
    helper = HelperClass()
    return helper.help()
""",
        },
        must_include=["class HelperClass"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_041_type_checking_import",
        initial_files={
            "models.py": """from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services import UserService

class User:
    def __init__(self, name: str):
        self.name = name
""",
            "services.py": """from models import User

class UserService:
    def create(self, name: str) -> User:
        return User(name)
""",
            "garbage.py": """garbage_marker_12345 = "type checking garbage"
unused_marker_67890 = "unused type checking"
""",
        },
        changed_files={
            "models.py": """from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services import UserService

class User:
    def __init__(self, name: str, service: "UserService | None" = None):
        self.name = name
        self.service = service
""",
        },
        must_include=["class User", "UserService"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_042_dynamic_import",
        initial_files={
            "plugins/plugin_a.py": """def execute():
    return "A"
""",
            "plugins/plugin_b.py": """def execute():
    return "B"
""",
            "loader.py": """def load():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "dynamic garbage"
unused_marker_67890 = "unused dynamic"
""",
        },
        changed_files={
            "loader.py": """import importlib

def load(plugin_name: str):
    module = importlib.import_module(f"plugins.{plugin_name}")
    return module.execute()
""",
        },
        must_include=["importlib.import_module"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_043_conditional_import",
        initial_files={
            "compat.py": """import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib
""",
            "config.py": """def load():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "compat garbage"
unused_marker_67890 = "unused compat"
""",
        },
        changed_files={
            "config.py": """from compat import tomllib

def load(path: str) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)
""",
        },
        must_include=["tomllib"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_044_star_import",
        initial_files={
            "constants.py": """MAX_RETRIES = 3
TIMEOUT = 30
BASE_URL = "https://api.example.com"

__all__ = ["MAX_RETRIES", "TIMEOUT", "BASE_URL"]
""",
            "client.py": """def call():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "constant garbage"
unused_marker_67890 = "unused constant"
""",
        },
        changed_files={
            "client.py": """from constants import *

def call(endpoint: str):
    url = f"{BASE_URL}/{endpoint}"
    return url
""",
        },
        must_include=["__all__"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_045_package_all_export",
        initial_files={
            "mylib/foo.py": """def foo_func():
    return "foo"
""",
            "mylib/bar.py": """def bar_func():
    return "bar"
""",
            "mylib/__init__.py": """from .foo import foo_func
from .bar import bar_func
""",
            "garbage.py": """garbage_marker_12345 = "package garbage"
unused_marker_67890 = "unused package"
""",
        },
        changed_files={
            "mylib/__init__.py": """from .foo import foo_func
from .bar import bar_func

__all__ = ["foo_func", "bar_func"]
""",
        },
        must_include=["__all__"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_046_lazy_import",
        initial_files={
            "heavy.py": """import time

def expensive_init():
    time.sleep(0.1)
    return {"initialized": True}

data = expensive_init()

def get_data():
    return data
""",
            "service.py": """def process():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "heavy garbage"
unused_marker_67890 = "unused heavy"
""",
        },
        changed_files={
            "service.py": """def get_heavy():
    import heavy
    return heavy.get_data()

def process():
    data = get_heavy()
    return data
""",
        },
        must_include=["def get_data"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]


PYTHON_EXCEPTION_CASES = [
    DiffTestCase(
        name="python_047_custom_exception_raise",
        initial_files={
            "exceptions.py": """class ValidationError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class NotFoundError(Exception):
    pass
""",
            "service.py": """def validate():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "exception garbage"
unused_marker_67890 = "unused exception"
""",
        },
        changed_files={
            "service.py": """from exceptions import ValidationError

def validate(data: dict):
    if "email" not in data:
        raise ValidationError("email", "is required")
    return True
""",
        },
        must_include=["ValidationError"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_048_exception_handler",
        initial_files={
            "errors.py": """class DatabaseError(Exception):
    pass

class ConnectionError(DatabaseError):
    pass
""",
            "handler.py": """def handle():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "error garbage"
unused_marker_67890 = "unused error"
""",
        },
        changed_files={
            "handler.py": """from errors import DatabaseError, ConnectionError

def handle():
    try:
        connect()
    except ConnectionError as e:
        return {"error": "connection", "detail": str(e)}
    except DatabaseError as e:
        return {"error": "database", "detail": str(e)}

def connect():
    pass
""",
        },
        must_include=["DatabaseError"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_049_exception_chaining",
        initial_files={
            "exceptions.py": """class AppError(Exception):
    pass

class DataError(AppError):
    pass
""",
            "parser.py": """def parse():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "chain garbage"
unused_marker_67890 = "unused chain"
""",
        },
        changed_files={
            "parser.py": """from exceptions import DataError

def parse(data: str):
    try:
        return eval(data)
    except SyntaxError as e:
        raise DataError("Invalid syntax") from e
""",
        },
        must_include=["class DataError"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]


PYTHON_FLASK_CASES = [
    DiffTestCase(
        name="python_050_flask_blueprint_route",
        initial_files={
            "routes.py": """from flask import Blueprint

bp = Blueprint("api", __name__)

@bp.route("/users")
def get_users():
    return {"users": []}
""",
            "app.py": """from flask import Flask
""",
            "garbage.py": """garbage_marker_12345 = "flask garbage"
unused_marker_67890 = "unused flask"
""",
        },
        changed_files={
            "app.py": """from flask import Flask
from routes import bp

app = Flask(__name__)
app.register_blueprint(bp, url_prefix="/api")
""",
        },
        must_include=["routes.py"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_051_flask_extension_init",
        initial_files={
            "extensions.py": """from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
""",
            "app.py": """from flask import Flask
""",
            "garbage.py": """garbage_marker_12345 = "extension garbage"
unused_marker_67890 = "unused extension"
""",
        },
        changed_files={
            "app.py": """from flask import Flask
from extensions import init_extensions, db

app = Flask(__name__)
init_extensions(app)
""",
        },
        must_include=["def init_extensions"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]


PYTHON_DJANGO_CASES = [
    DiffTestCase(
        name="python_052_django_model_query",
        initial_files={
            "models.py": """from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
""",
            "views.py": """def index():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "django garbage"
unused_marker_67890 = "unused django"
""",
        },
        changed_files={
            "views.py": """from models import User

def index():
    users = User.objects.filter(name__icontains="john")
    return list(users)
""",
        },
        must_include=["class User"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_053_django_cbv_url",
        initial_files={
            "views.py": """from django.views.generic import ListView
from models import Article

class ArticleListView(ListView):
    model = Article
    template_name = "articles/list.html"
    context_object_name = "articles"
    paginate_by = 10
""",
            "urls.py": """from django.urls import path
""",
            "garbage.py": """garbage_marker_12345 = "cbv garbage"
unused_marker_67890 = "unused cbv"
""",
        },
        changed_files={
            "urls.py": """from django.urls import path
from views import ArticleListView

urlpatterns = [
    path("articles/", ArticleListView.as_view(), name="article-list"),
]
""",
        },
        must_include=["class ArticleListView"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]


PYTHON_FASTAPI_CASES = [
    DiffTestCase(
        name="python_054_fastapi_router_include",
        initial_files={
            "routers/users.py": """from fastapi import APIRouter, Depends
from schemas import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate):
    return {"id": 1, **user.dict()}

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    return {"id": user_id, "name": "John"}
""",
            "main.py": """from fastapi import FastAPI
""",
            "garbage.py": """garbage_marker_12345 = "fastapi garbage"
unused_marker_67890 = "unused fastapi"
""",
        },
        changed_files={
            "main.py": """from fastapi import FastAPI
from routers.users import router as users_router

app = FastAPI()
app.include_router(users_router)
""",
        },
        must_include=["users.py"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_055_fastapi_dependency_injection",
        initial_files={
            "dependencies.py": """from fastapi import Depends, HTTPException
from database import get_db

async def get_current_user(db = Depends(get_db)):
    user = await db.get_user()
    if not user:
        raise HTTPException(status_code=401)
    return user
""",
            "routers/protected.py": """from fastapi import APIRouter
""",
            "garbage.py": """garbage_marker_12345 = "di garbage"
unused_marker_67890 = "unused di"
""",
        },
        changed_files={
            "routers/protected.py": """from fastapi import APIRouter, Depends
from dependencies import get_current_user

router = APIRouter()

@router.get("/profile")
async def get_profile(user = Depends(get_current_user)):
    return {"user": user}
""",
        },
        must_include=["async def get_current_user"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_056_pydantic_validator",
        initial_files={
            "schemas.py": """from pydantic import BaseModel, validator

class UserCreate(BaseModel):
    email: str
    password: str

    @validator("email")
    def email_must_be_valid(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email")
        return v.lower()

    @validator("password")
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError("Password too short")
        return v
""",
            "api.py": """def register():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "validator garbage"
unused_marker_67890 = "unused validator"
""",
        },
        changed_files={
            "api.py": """from schemas import UserCreate

def register(data: dict):
    user = UserCreate(**data)
    return user
""",
        },
        must_include=["@validator"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]


PYTHON_SQLALCHEMY_CASES = [
    DiffTestCase(
        name="python_057_sqlalchemy_model_query",
        initial_files={
            "models.py": """from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    posts = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
""",
            "queries.py": """def get_user():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "sqlalchemy garbage"
unused_marker_67890 = "unused sqlalchemy"
""",
        },
        changed_files={
            "queries.py": """from models import User, Post
from sqlalchemy.orm import Session

def get_user_with_posts(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()
""",
        },
        must_include=["class User"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_058_sqlalchemy_relationship",
        initial_files={
            "models/order.py": """from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
""",
            "models/item.py": """from sqlalchemy import Column, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    price = Column(Float)
    order = relationship("Order", back_populates="items")
""",
            "services/order.py": """def calculate_total():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "relationship garbage"
unused_marker_67890 = "unused relationship"
""",
        },
        changed_files={
            "services/order.py": """from models.order import Order

def calculate_total(order: Order) -> float:
    return sum(item.price for item in order.items)
""",
        },
        must_include=["class Order"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]


PYTHON_CELERY_CASES = [
    DiffTestCase(
        name="python_059_celery_task_delay",
        initial_files={
            "tasks.py": """from celery import shared_task

@shared_task
def send_email(to: str, subject: str, body: str):
    print(f"Sending email to {to}")
    return True

@shared_task
def process_data(data: dict):
    return {"processed": True}
""",
            "views.py": """def submit():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "celery garbage"
unused_marker_67890 = "unused celery"
""",
        },
        changed_files={
            "views.py": """from tasks import send_email

def submit(email: str):
    send_email.delay(email, "Welcome", "Hello!")
    return {"status": "queued"}
""",
        },
        must_include=["@shared_task"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]


PYTHON_PYTEST_CASES = [
    DiffTestCase(
        name="python_060_pytest_fixture_usage",
        initial_files={
            "conftest.py": """import pytest

@pytest.fixture
def db_session():
    from database import Session
    session = Session()
    yield session
    session.close()

@pytest.fixture
def test_user(db_session):
    from models import User
    user = User(name="Test")
    db_session.add(user)
    db_session.commit()
    return user
""",
            "test_service.py": """def test_example():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "pytest garbage"
unused_marker_67890 = "unused pytest"
""",
        },
        changed_files={
            "test_service.py": """def test_create_user(db_session, test_user):
    assert test_user.name == "Test"
""",
        },
        must_include=["@pytest.fixture"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="python_061_pytest_parametrize",
        initial_files={
            "validators.py": """def validate_email(email: str) -> bool:
    return "@" in email and "." in email
""",
            "test_validators.py": """def test_email():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "parametrize garbage"
unused_marker_67890 = "unused parametrize"
""",
        },
        changed_files={
            "test_validators.py": """import pytest
from validators import validate_email

@pytest.mark.parametrize("email,expected", [
    ("test@example.com", True),
    ("invalid", False),
    ("no@dot", False),
])
def test_email(email, expected):
    assert validate_email(email) == expected
""",
        },
        must_include=["def validate_email"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]


PYTHON_LOGGING_CASES = [
    DiffTestCase(
        name="python_062_logging_setup",
        initial_files={
            "logging_config.py": """import logging

def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)
""",
            "app.py": """def main():
    pass
""",
            "garbage.py": """garbage_marker_12345 = "logging garbage"
unused_marker_67890 = "unused logging"
""",
        },
        changed_files={
            "app.py": """from logging_config import setup_logging

logger = setup_logging("DEBUG")

def main():
    logger.info("Application started")
""",
        },
        must_include=["def setup_logging"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]


ALL_PYTHON_CASES = (
    PYTHON_BASIC_CASES
    + PYTHON_ASYNC_CASES
    + PYTHON_TYPE_ANNOTATION_CASES
    + PYTHON_FUNCTION_CALL_CASES
    + PYTHON_TYPE_HINT_CASES
    + PYTHON_IMPORT_CASES
    + PYTHON_EXCEPTION_CASES
    + PYTHON_FLASK_CASES
    + PYTHON_DJANGO_CASES
    + PYTHON_FASTAPI_CASES
    + PYTHON_SQLALCHEMY_CASES
    + PYTHON_CELERY_CASES
    + PYTHON_PYTEST_CASES
    + PYTHON_LOGGING_CASES
)


@pytest.mark.parametrize("case", ALL_PYTHON_CASES, ids=lambda c: c.name)
def test_python_diff_context(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
