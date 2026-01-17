import pytest

from tests.utils import DiffTestCase, DiffTestRunner

FORWARD_DEPENDENCY_CASES = [
    DiffTestCase(
        name="dep_001_forward_function_call",
        initial_files={
            "utils/math.py": """def calculate_tax(amount):
    rate = 0.15
    return amount * rate
""",
            "main.py": """def process():
    pass
""",
        },
        changed_files={
            "main.py": """from utils.math import calculate_tax

def process():
    amount = 100
    result = calculate_tax(amount)
    return result
""",
        },
        must_include=["main.py", "calculate_tax"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="dep_002_forward_method_on_imported_class",
        initial_files={
            "services/user.py": """class UserService:
    def __init__(self):
        self.users = []

    def validate(self):
        return len(self.users) > 0

    def add_user(self, name):
        self.users.append(name)
""",
            "handler.py": """def handle():
    pass
""",
        },
        changed_files={
            "handler.py": """from services.user import UserService

def handle():
    user = UserService()
    user.validate()
    return user
""",
        },
        must_include=["handler.py"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="dep_003_forward_chained_methods",
        initial_files={
            "database/query.py": """class QueryBuilder:
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
            "query.py": """def run_query():
    pass
""",
        },
        changed_files={
            "query.py": """from database.query import QueryBuilder

def run_query():
    db = QueryBuilder("users")
    result = db.query("users").filter(active=True).limit(10)
    return result
""",
        },
        must_include=["query.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_004_forward_aliased_import",
        initial_files={
            "utils/helper.py": """def process(data):
    return [x * 2 for x in data]
""",
            "app.py": """def run():
    pass
""",
        },
        changed_files={
            "app.py": """from utils import helper as h

def run():
    data = [1, 2, 3]
    result = h.process(data)
    return result
""",
        },
        must_include=["app.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_005_forward_nested_inner_function",
        initial_files={
            "outer.py": """def outer():
    def inner():
        return 42

    return 0
""",
        },
        changed_files={
            "outer.py": """def outer():
    def inner():
        return 42

    result = inner()
    return result
""",
        },
        must_include=["outer.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_006_forward_type_annotation",
        initial_files={
            "models/request.py": """class RequestModel:
    def __init__(self, data):
        self.data = data
""",
            "models/response.py": """class ResponseModel:
    def __init__(self, result):
        self.result = result
""",
            "service.py": """def process():
    pass
""",
        },
        changed_files={
            "service.py": """from models.request import RequestModel
from models.response import ResponseModel

def process(request: RequestModel) -> ResponseModel:
    result = request.data * 2
    return ResponseModel(result)
""",
        },
        must_include=["service.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_007_forward_inherits_base_class",
        initial_files={
            "handlers/base.py": """class BaseHandler:
    def handle(self):
        return "base"

    def setup(self):
        pass
""",
            "custom_handler.py": """def placeholder():
    pass
""",
        },
        changed_files={
            "custom_handler.py": """from handlers.base import BaseHandler

class CustomHandler(BaseHandler):
    def handle(self):
        super().handle()
        return "custom"
""",
        },
        must_include=["custom_handler.py", "base.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_008_forward_implements_protocol",
        initial_files={
            "interfaces/repository.py": """from typing import Protocol

class Repository(Protocol):
    def find(self, id: int):
        ...

    def save(self, entity):
        ...
""",
            "impl.py": """def placeholder():
    pass
""",
        },
        changed_files={
            "impl.py": """from interfaces.repository import Repository

class MyRepo(Repository):
    def find(self, id: int):
        return {"id": id}

    def save(self, entity):
        pass
""",
        },
        must_include=["impl.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_009_forward_uses_constant",
        initial_files={
            "constants.py": """MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
""",
            "validator.py": """def validate():
    pass
""",
        },
        changed_files={
            "validator.py": """from constants import MIN_PASSWORD_LENGTH

def validate(password):
    if len(password) < MIN_PASSWORD_LENGTH:
        return False
    return True
""",
        },
        must_include=["validator.py"],
        must_not_include=["garbage_marker_12345"],
        min_budget=500,
    ),
    DiffTestCase(
        name="dep_010_forward_uses_enum",
        initial_files={
            "enums/order.py": """from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
""",
            "order.py": """def create_order():
    pass
""",
        },
        changed_files={
            "order.py": """from enums.order import OrderStatus

class Order:
    def __init__(self):
        self.status = OrderStatus.PENDING

    def complete(self):
        self.status = OrderStatus.COMPLETED
""",
        },
        must_include=["order.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_011_forward_reexported_import",
        initial_files={
            "mylib/core.py": """def process():
    return "processed"
""",
            "mylib/__init__.py": """from .core import process
""",
            "app.py": """def run():
    pass
""",
        },
        changed_files={
            "app.py": """from mylib import process

def run():
    result = process()
    return result
""",
        },
        must_include=["app.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_012_forward_relative_import",
        initial_files={
            "pkg/__init__.py": "",
            "pkg/utils.py": """def helper():
    return "help"
""",
            "pkg/subpkg/__init__.py": "",
            "pkg/subpkg/module.py": """def action():
    pass
""",
        },
        changed_files={
            "pkg/subpkg/module.py": """from ..utils import helper

def action():
    result = helper()
    return result
""",
        },
        must_include=["module.py"],
        must_not_include=["garbage_marker_12345"],
    ),
]


BACKWARD_DEPENDENCY_CASES = [
    DiffTestCase(
        name="dep_101_backward_function_signature_changed",
        initial_files={
            "utils.py": """def format_date(date):
    return date.strftime("%Y-%m-%d")
""",
            "reports/generator.py": """from utils import format_date

def generate_report(today):
    formatted = format_date(today)
    return f"Report for {formatted}"
""",
            "api/views.py": """from utils import format_date

def get_created_date(created_at):
    return format_date(created_at)
""",
        },
        changed_files={
            "utils.py": """def format_date(date, timezone=None):
    if timezone:
        date = date.astimezone(timezone)
    return date.strftime("%Y-%m-%d")
""",
        },
        must_include=["utils.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_102_backward_function_body_changed",
        initial_files={
            "calculator.py": """def calculate_total(items):
    return sum(i.price for i in items)
""",
            "checkout.py": """from calculator import calculate_total

class CartItem:
    def __init__(self, price, quantity):
        self.price = price
        self.quantity = quantity

def process_checkout(cart_items):
    total = calculate_total(cart_items)
    return {"total": total}
""",
            "invoice.py": """from calculator import calculate_total

def create_invoice(line_items):
    amount = calculate_total(line_items)
    return {"amount": amount}
""",
        },
        changed_files={
            "calculator.py": """def calculate_total(items):
    return sum(i.price * i.quantity for i in items)
""",
        },
        must_include=["calculator.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_103_backward_method_signature_changed",
        initial_files={
            "user.py": """class User:
    def __init__(self, first, last):
        self.first = first
        self.last = last

    def get_full_name(self):
        return f"{self.first} {self.last}"
""",
            "templates/profile.py": """from user import User

def render_profile(user):
    name = user.get_full_name()
    return f"<h1>{name}</h1>"
""",
            "emails/welcome.py": """from user import User

def send_welcome(recipient):
    name = recipient.get_full_name()
    return f"Welcome, {name}!"
""",
        },
        changed_files={
            "user.py": """class User:
    def __init__(self, first, last, title=None):
        self.first = first
        self.last = last
        self.title = title

    def get_full_name(self, include_title=False):
        if include_title and self.title:
            return f"{self.title} {self.first} {self.last}"
        return f"{self.first} {self.last}"
""",
        },
        must_include=["user.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_104_backward_base_class_method_changed",
        initial_files={
            "base.py": """class BaseProcessor:
    def process(self, data):
        return data
""",
            "processors/json.py": """from base import BaseProcessor

class JsonProcessor(BaseProcessor):
    def process(self, data):
        import json
        return json.loads(data)
""",
            "processors/xml.py": """from base import BaseProcessor

class XmlProcessor(BaseProcessor):
    def process(self, data):
        return f"<xml>{data}</xml>"
""",
        },
        changed_files={
            "base.py": """class BaseProcessor:
    def process(self, data, options=None):
        if options:
            data = self.preprocess(data, options)
        return data

    def preprocess(self, data, options):
        return data
""",
        },
        must_include=["base.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_105_backward_protocol_changed",
        initial_files={
            "interfaces.py": """from typing import Protocol

class Repository(Protocol):
    def find(self, id: int):
        ...
""",
            "repos/user_repo.py": """from interfaces import Repository

class UserRepository:
    def find(self, id: int):
        return {"id": id, "name": "User"}
""",
            "repos/order_repo.py": """from interfaces import Repository

class OrderRepository:
    def find(self, id: int):
        return {"id": id, "total": 100}
""",
        },
        changed_files={
            "interfaces.py": """from typing import Protocol

class Repository(Protocol):
    def find(self, id: int):
        ...

    def find_by_criteria(self, criteria: dict) -> list:
        ...
""",
        },
        must_include=["interfaces.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_106_backward_global_constant_changed",
        initial_files={
            "config.py": """MAX_RETRIES = 3
TIMEOUT = 30
""",
            "client.py": """from config import MAX_RETRIES

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
            "worker.py": """from config import MAX_RETRIES

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
        },
        changed_files={
            "config.py": """MAX_RETRIES = 5
TIMEOUT = 30
""",
        },
        must_include=["config.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_107_backward_class_attribute_changed",
        initial_files={
            "models.py": """class Config:
    timeout = 30
    max_connections = 10
""",
            "client.py": """from models import Config

def make_request():
    timeout = Config.timeout
    return f"Request with timeout {timeout}"
""",
            "settings.py": """from models import Config

default_timeout = Config.timeout
""",
        },
        changed_files={
            "models.py": """class Config:
    timeout = 60
    max_connections = 10
""",
        },
        must_include=["models.py"],
        must_not_include=["garbage_marker_12345"],
    ),
]


REVERSE_DEPENDENCY_CASES = [
    DiffTestCase(
        name="dep_201_reverse_multiple_callers_function",
        initial_files={
            "core/calculator.py": """def calculate(x: float) -> float:
    return x * 2
""",
            "services/billing.py": """from core.calculator import calculate

def compute_bill(amount: float) -> float:
    base = calculate(amount)
    return base + 10
""",
            "services/pricing.py": """from core.calculator import calculate

def get_price(value: float) -> float:
    return calculate(value) * 1.1
""",
            "api/endpoints.py": """from core.calculator import calculate

def handle_request(data: dict) -> dict:
    result = calculate(data["value"])
    return {"result": result}
""",
            "utils/helpers.py": """def format_output(value: float) -> str:
    return f"Result: {value:.2f}"
""",
        },
        changed_files={
            "core/calculator.py": """def calculate(x: float, precision: int = 2) -> float:
    result = x * 2
    return round(result, precision)
""",
        },
        must_include=["calculator.py", "def calculate"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_202_reverse_multiple_callers_method",
        initial_files={
            "models/user.py": """class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    def get_display_name(self) -> str:
        return self.name
""",
            "views/profile.py": """from models.user import User

def render_profile(user: User) -> str:
    name = user.get_display_name()
    return f"<h1>{name}</h1>"
""",
            "views/header.py": """from models.user import User

def render_header(user: User) -> str:
    display = user.get_display_name()
    return f"<span>{display}</span>"
""",
            "emails/welcome.py": """from models.user import User

def send_welcome_email(user: User) -> None:
    name = user.get_display_name()
    print(f"Welcome, {name}!")
""",
        },
        changed_files={
            "models/user.py": """class User:
    def __init__(self, name: str, email: str, title: str = ""):
        self.name = name
        self.email = email
        self.title = title

    def get_display_name(self, include_title: bool = False) -> str:
        if include_title and self.title:
            return f"{self.title} {self.name}"
        return self.name
""",
        },
        must_include=["user.py", "def get_display_name"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_203_reverse_dependency_injection",
        initial_files={
            "services/database.py": """class DatabaseService:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connected = False

    def connect(self) -> bool:
        self.connected = True
        return True

    def query(self, sql: str) -> list:
        return []
""",
            "repositories/user_repo.py": """from services.database import DatabaseService

class UserRepository:
    def __init__(self, db_service: DatabaseService):
        self.db = db_service

    def find_by_id(self, user_id: int) -> dict:
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")
""",
            "repositories/order_repo.py": """from services.database import DatabaseService

class OrderRepository:
    def __init__(self, db_service: DatabaseService):
        self.db = db_service

    def get_orders(self, user_id: int) -> list:
        return self.db.query(f"SELECT * FROM orders WHERE user_id = {user_id}")
""",
            "handlers/api_handler.py": """from services.database import DatabaseService

class ApiHandler:
    def __init__(self, db_service: DatabaseService):
        self.db = db_service

    def handle(self, request: dict) -> dict:
        self.db.connect()
        return {"status": "ok"}
""",
        },
        changed_files={
            "services/database.py": """class DatabaseService:
    def __init__(self, connection_string: str, pool_size: int = 5):
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.connected = False
        self.pool = []

    def connect(self) -> bool:
        self.pool = [None] * self.pool_size
        self.connected = True
        return True

    def query(self, sql: str) -> list:
        if not self.connected:
            self.connect()
        return []

    def close(self) -> None:
        self.pool.clear()
        self.connected = False
""",
        },
        must_include=["database.py", "class DatabaseService"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_204_reverse_protocol_definition_change",
        initial_files={
            "interfaces/repository.py": """from typing import Protocol, TypeVar

T = TypeVar('T')

class Repository(Protocol[T]):
    def find(self, id: int) -> T:
        ...

    def save(self, entity: T) -> None:
        ...
""",
            "repos/user_repository.py": """from interfaces.repository import Repository

class User:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

class UserRepository:
    def __init__(self):
        self.users = {}

    def find(self, id: int) -> User:
        return self.users.get(id)

    def save(self, entity: User) -> None:
        self.users[entity.id] = entity
""",
            "repos/product_repository.py": """from interfaces.repository import Repository

class Product:
    def __init__(self, id: int, name: str, price: float):
        self.id = id
        self.name = name
        self.price = price

class ProductRepository:
    def __init__(self):
        self.products = {}

    def find(self, id: int) -> Product:
        return self.products.get(id)

    def save(self, entity: Product) -> None:
        self.products[entity.id] = entity
""",
        },
        changed_files={
            "interfaces/repository.py": """from typing import Protocol, TypeVar, Optional

T = TypeVar('T')

class Repository(Protocol[T]):
    def find(self, id: int) -> Optional[T]:
        ...

    def save(self, entity: T) -> None:
        ...

    def delete(self, id: int) -> bool:
        ...

    def find_all(self) -> list[T]:
        ...
""",
        },
        must_include=["repository.py", "class Repository"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_205_reverse_abstract_base_class_change",
        initial_files={
            "base/handler.py": """from abc import ABC, abstractmethod

class BaseHandler(ABC):
    @abstractmethod
    def handle(self, request: dict) -> dict:
        pass

    @abstractmethod
    def validate(self, request: dict) -> bool:
        pass
""",
            "handlers/user_handler.py": """from base.handler import BaseHandler

class UserHandler(BaseHandler):
    def handle(self, request: dict) -> dict:
        return {"user": request.get("user_id")}

    def validate(self, request: dict) -> bool:
        return "user_id" in request
""",
            "handlers/order_handler.py": """from base.handler import BaseHandler

class OrderHandler(BaseHandler):
    def handle(self, request: dict) -> dict:
        return {"order": request.get("order_id")}

    def validate(self, request: dict) -> bool:
        return "order_id" in request
""",
        },
        changed_files={
            "base/handler.py": """from abc import ABC, abstractmethod
from typing import Optional

class BaseHandler(ABC):
    @abstractmethod
    def handle(self, request: dict) -> dict:
        pass

    @abstractmethod
    def validate(self, request: dict) -> bool:
        pass

    @abstractmethod
    def authorize(self, request: dict) -> bool:
        pass

    def pre_process(self, request: dict) -> Optional[dict]:
        return request

    def post_process(self, response: dict) -> dict:
        return response
""",
        },
        must_include=["handler.py", "class BaseHandler"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_206_reverse_event_dispatcher_change",
        initial_files={
            "events/dispatcher.py": """class EventDispatcher:
    def __init__(self):
        self.handlers = {}

    def register(self, event_type: str, handler):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)

    def emit(self, event_type: str, data: dict) -> None:
        for handler in self.handlers.get(event_type, []):
            handler(data)
""",
            "handlers/user_created_handler.py": """from events.dispatcher import EventDispatcher

def on_user_created(data: dict) -> None:
    user_id = data.get("user_id")
    print(f"User {user_id} created, sending welcome email")

def setup_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.register("user.created", on_user_created)
""",
            "handlers/audit_handler.py": """from events.dispatcher import EventDispatcher

def on_any_event(data: dict) -> None:
    print(f"Audit log: {data}")

def setup_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.register("user.created", on_any_event)
    dispatcher.register("order.placed", on_any_event)
""",
        },
        changed_files={
            "events/dispatcher.py": """import asyncio
from typing import Callable, Awaitable

class EventDispatcher:
    def __init__(self):
        self.handlers = {}
        self.async_handlers = {}

    def register(self, event_type: str, handler: Callable) -> None:
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)

    def register_async(self, event_type: str, handler: Callable[..., Awaitable]) -> None:
        if event_type not in self.async_handlers:
            self.async_handlers[event_type] = []
        self.async_handlers[event_type].append(handler)

    def emit(self, event_type: str, data: dict, metadata: dict = None) -> None:
        payload = {"data": data, "metadata": metadata or {}}
        for handler in self.handlers.get(event_type, []):
            handler(payload)

    async def emit_async(self, event_type: str, data: dict, metadata: dict = None) -> None:
        payload = {"data": data, "metadata": metadata or {}}
        tasks = []
        for handler in self.async_handlers.get(event_type, []):
            tasks.append(handler(payload))
        if tasks:
            await asyncio.gather(*tasks)
""",
        },
        must_include=["dispatcher.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_207_reverse_observable_pattern_change",
        initial_files={
            "core/observable.py": """from typing import Callable

class Observable:
    def __init__(self):
        self._observers = []

    def subscribe(self, observer: Callable) -> None:
        self._observers.append(observer)

    def notify(self, value) -> None:
        for observer in self._observers:
            observer(value)
""",
            "ui/display.py": """from core.observable import Observable

class DisplayComponent:
    def __init__(self, data_source: Observable):
        data_source.subscribe(self.on_update)

    def on_update(self, value) -> None:
        print(f"Display updated: {value}")
""",
            "logging/logger.py": """from core.observable import Observable

class LogObserver:
    def __init__(self, observable: Observable):
        observable.subscribe(self.log_change)

    def log_change(self, value) -> None:
        print(f"[LOG] Value changed to: {value}")
""",
        },
        changed_files={
            "core/observable.py": """from typing import Callable, Optional

class Observable:
    def __init__(self):
        self._observers = []
        self._last_value = None

    def subscribe(self, observer: Callable, immediate: bool = False) -> Callable:
        self._observers.append(observer)
        if immediate and self._last_value is not None:
            observer(self._last_value)
        return lambda: self._observers.remove(observer)

    def notify(self, value, force: bool = False) -> None:
        if not force and value == self._last_value:
            return
        self._last_value = value
        for observer in self._observers:
            observer(value)

    def get_value(self) -> Optional:
        return self._last_value
""",
        },
        must_include=["observable.py"],
        must_not_include=["garbage_marker_12345"],
        min_budget=800,
    ),
    DiffTestCase(
        name="dep_208_reverse_django_signal_change",
        initial_files={
            "models/user.py": """from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'users'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
""",
            "signals/user_signals.py": """from django.db.models.signals import post_save
from django.dispatch import receiver
from models.user import User

@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if created:
        print(f"Sending welcome email to {instance.email}")

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        print(f"Creating profile for {instance.name}")
""",
        },
        changed_files={
            "models/user.py": """from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        app_label = 'users'

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)
        post_save.send(
            sender=self.__class__,
            instance=self,
            created=self._state.adding,
            update_fields=kwargs.get('update_fields'),
        )
""",
        },
        must_include=["user.py", "class User"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_209_reverse_custom_signal_definition_change",
        initial_files={
            "signals/custom.py": """from django.dispatch import Signal

order_placed = Signal()
order_shipped = Signal()
order_delivered = Signal()
""",
            "handlers/order_handlers.py": """from django.dispatch import receiver
from signals.custom import order_placed, order_shipped

@receiver(order_placed)
def handle_order_placed(sender, order_id, customer_id, **kwargs):
    print(f"Order {order_id} placed by customer {customer_id}")

@receiver(order_shipped)
def handle_order_shipped(sender, order_id, tracking_number, **kwargs):
    print(f"Order {order_id} shipped with tracking {tracking_number}")
""",
            "handlers/notification_handlers.py": """from django.dispatch import receiver
from signals.custom import order_placed, order_delivered

@receiver(order_placed)
def notify_customer_order_placed(sender, order_id, customer_id, **kwargs):
    print(f"Notifying customer {customer_id} about order {order_id}")

@receiver(order_delivered)
def notify_customer_order_delivered(sender, order_id, **kwargs):
    print(f"Order {order_id} has been delivered")
""",
        },
        changed_files={
            "signals/custom.py": """from django.dispatch import Signal

order_placed = Signal()
order_shipped = Signal()
order_delivered = Signal()
order_cancelled = Signal()

payment_received = Signal()
payment_failed = Signal()
""",
        },
        must_include=["custom.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_210_reverse_flask_signal_change",
        initial_files={
            "app/signals.py": """from blinker import signal

user_registered = signal('user-registered')
user_logged_in = signal('user-logged-in')
user_logged_out = signal('user-logged-out')
""",
            "handlers/email_handler.py": """from app.signals import user_registered

@user_registered.connect
def send_welcome_email(sender, user, **kwargs):
    print(f"Sending welcome email to {user.email}")
""",
            "handlers/metrics_handler.py": """from app.signals import user_registered, user_logged_in

@user_registered.connect
def track_registration(sender, user, **kwargs):
    print(f"Tracking registration for {user.id}")

@user_logged_in.connect
def track_login(sender, user, **kwargs):
    print(f"Tracking login for {user.id}")
""",
        },
        changed_files={
            "app/signals.py": """from blinker import signal

user_registered = signal('user-registered')
user_logged_in = signal('user-logged-in')
user_logged_out = signal('user-logged-out')
user_profile_updated = signal('user-profile-updated')
user_password_changed = signal('user-password-changed')

def emit_user_registered(sender, user, source='web'):
    user_registered.send(sender, user=user, source=source)

def emit_user_logged_in(sender, user, ip_address=None):
    user_logged_in.send(sender, user=user, ip_address=ip_address)
""",
        },
        must_include=["signals.py"],
        must_not_include=["garbage_marker_12345"],
    ),
]


TEST_RELATION_CASES = [
    DiffTestCase(
        name="dep_301_test_function_changed_find_tests",
        initial_files={
            "calculator.py": """def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
""",
            "tests/test_calculator.py": """from calculator import add, subtract

def test_add():
    assert add(1, 2) == 3
    assert add(-1, 1) == 0

def test_subtract():
    assert subtract(5, 3) == 2
""",
        },
        changed_files={
            "calculator.py": """def add(a, b):
    return float(a) + float(b)

def subtract(a, b):
    return a - b
""",
        },
        must_include=["calculator.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_302_test_class_changed_find_test_class",
        initial_files={
            "user_service.py": """class UserService:
    def __init__(self):
        self.users = []

    def add_user(self, name):
        self.users.append(name)
""",
            "tests/test_user_service.py": """from user_service import UserService

class TestUserService:
    def test_add_user(self):
        service = UserService()
        service.add_user("Alice")
        assert "Alice" in service.users
""",
        },
        changed_files={
            "user_service.py": """class UserService:
    def __init__(self):
        self.users = []

    def add_user(self, name):
        self.users.append(name)

    def deactivate(self, user_id):
        pass
""",
        },
        must_include=["user_service.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_303_test_module_changed_find_test_module",
        initial_files={
            "utils/formatting.py": """def format_currency(amount):
    return f"${amount:.2f}"
""",
            "tests/utils/test_formatting.py": """from utils.formatting import format_currency

def test_format_currency():
    assert format_currency(10) == "$10.00"
""",
        },
        changed_files={
            "utils/formatting.py": """def format_currency(amount, symbol="$"):
    return f"{symbol}{amount:.2f}"
""",
        },
        must_include=["formatting.py", "test_formatting.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_304_test_integration_covers_endpoint",
        initial_files={
            "api/users.py": """def list_users():
    return [{"id": 1, "name": "Alice"}]
""",
            "tests/integration/test_api.py": """from api.users import list_users

def test_list_users_endpoint():
    users = list_users()
    assert len(users) == 1
    assert users[0]["name"] == "Alice"
""",
        },
        changed_files={
            "api/users.py": """def list_users(page=1, limit=10):
    users = [{"id": 1, "name": "Alice"}]
    return users[(page-1)*limit:page*limit]
""",
        },
        must_include=["users.py", "test_api.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_305_test_changed_find_fixtures",
        initial_files={
            "tests/conftest.py": """import pytest

@pytest.fixture
def db_session():
    return {"connected": True}

@pytest.fixture
def sample_products():
    return [
        {"id": 1, "name": "Widget"},
        {"id": 2, "name": "Gadget"},
    ]
""",
            "tests/test_orders.py": """def test_create_order():
    assert True
""",
        },
        changed_files={
            "tests/test_orders.py": """def test_create_order(db_session):
    assert db_session["connected"]

def test_bulk_order(db_session, sample_products):
    assert len(sample_products) == 2
""",
        },
        must_include=["test_orders.py", "conftest.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_306_test_fixture_changed_find_using_tests",
        initial_files={
            "tests/conftest.py": """import pytest

@pytest.fixture
def mock_api():
    return {"status": "ok"}
""",
            "tests/test_client.py": """def test_fetch(mock_api):
    assert mock_api["status"] == "ok"
""",
            "tests/test_sync.py": """def test_sync(mock_api):
    assert mock_api["status"] == "ok"
""",
        },
        changed_files={
            "tests/conftest.py": """import pytest

@pytest.fixture
def mock_api():
    return {"status": "ok", "version": "2.0"}
""",
        },
        must_include=["conftest.py"],
        must_not_include=["garbage_marker_12345"],
    ),
]


TEST_PATTERN_CASES = [
    DiffTestCase(
        name="dep_401_test_parametrize_includes_function",
        initial_files={
            "src/calculator.py": """def add(a: int, b: int) -> int:
    return a + b

def subtract(a: int, b: int) -> int:
    return a - b

def multiply(a: int, b: int) -> int:
    return a * b

def divide(a: int, b: int) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
""",
            "tests/test_calculator.py": """import pytest
from src.calculator import add

def test_add_basic():
    assert add(1, 2) == 3
""",
        },
        changed_files={
            "tests/test_calculator.py": """import pytest
from src.calculator import add, subtract, multiply

@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
    (-5, -3, -8),
])
def test_add_parametrized(a, b, expected):
    assert add(a, b) == expected

@pytest.mark.parametrize("a,b,expected", [
    (5, 3, 2),
    (0, 0, 0),
    (-1, -1, 0),
])
def test_subtract_parametrized(a, b, expected):
    assert subtract(a, b) == expected

def test_multiply_basic():
    assert multiply(2, 3) == 6
""",
        },
        must_include=["test_calculator.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_402_test_conftest_fixture_change",
        initial_files={
            "src/database.py": """class Database:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connected = False

    def connect(self):
        self.connected = True

    def disconnect(self):
        self.connected = False

    def query(self, sql: str) -> list:
        if not self.connected:
            raise RuntimeError("Not connected")
        return []
""",
            "tests/conftest.py": """import pytest
from src.database import Database

@pytest.fixture
def db():
    database = Database("test://localhost")
    database.connect()
    yield database
    database.disconnect()
""",
            "tests/test_queries.py": """def test_query_returns_list(db):
    result = db.query("SELECT * FROM users")
    assert isinstance(result, list)

def test_db_is_connected(db):
    assert db.connected is True
""",
        },
        changed_files={
            "tests/conftest.py": """import pytest
from src.database import Database

@pytest.fixture
def db():
    database = Database("test://localhost")
    database.connect()
    yield database
    database.disconnect()

@pytest.fixture
def db_with_data(db):
    db.query("INSERT INTO users VALUES (1, 'test')")
    return db

@pytest.fixture
def transaction_db(db):
    db.query("BEGIN TRANSACTION")
    yield db
    db.query("ROLLBACK")
""",
        },
        must_include=["conftest.py", "@pytest.fixture"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_403_test_mock_side_effect",
        initial_files={
            "src/api_client.py": """import requests

class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def fetch_data(self, endpoint: str) -> dict:
        response = requests.get(f"{self.base_url}/{endpoint}")
        response.raise_for_status()
        return response.json()

    def post_data(self, endpoint: str, data: dict) -> dict:
        response = requests.post(f"{self.base_url}/{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
""",
            "src/data_processor.py": """from src.api_client import ApiClient

class DataProcessor:
    def __init__(self, client: ApiClient):
        self.client = client

    def process_user_data(self, user_id: int) -> dict:
        data = self.client.fetch_data(f"users/{user_id}")
        return {"processed": True, "user": data}

    def process_with_retry(self, endpoint: str, retries: int = 3) -> dict:
        for attempt in range(retries):
            try:
                return self.client.fetch_data(endpoint)
            except Exception as e:
                if attempt == retries - 1:
                    raise
        return {}
""",
            "tests/test_data_processor.py": """from unittest.mock import Mock
from src.data_processor import DataProcessor

def test_process_user_data():
    mock_client = Mock()
    mock_client.fetch_data.return_value = {"id": 1, "name": "Test"}
    processor = DataProcessor(mock_client)
    result = processor.process_user_data(1)
    assert result["processed"] is True
""",
        },
        changed_files={
            "tests/test_data_processor.py": """from unittest.mock import Mock
import pytest
from src.data_processor import DataProcessor

def test_process_user_data():
    mock_client = Mock()
    mock_client.fetch_data.return_value = {"id": 1, "name": "Test"}
    processor = DataProcessor(mock_client)
    result = processor.process_user_data(1)
    assert result["processed"] is True

def test_retry_on_failure():
    mock_client = Mock()
    mock_client.fetch_data.side_effect = [
        ConnectionError("First failure"),
        ConnectionError("Second failure"),
        {"id": 1, "data": "success"},
    ]
    processor = DataProcessor(mock_client)
    result = processor.process_with_retry("users/1", retries=3)
    assert result["data"] == "success"
    assert mock_client.fetch_data.call_count == 3

def test_retry_exhausted_raises():
    mock_client = Mock()
    mock_client.fetch_data.side_effect = [
        ConnectionError("Failure 1"),
        ConnectionError("Failure 2"),
        ConnectionError("Failure 3"),
    ]
    processor = DataProcessor(mock_client)
    with pytest.raises(ConnectionError):
        processor.process_with_retry("users/1", retries=3)
""",
        },
        must_include=["test_data_processor.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_404_test_pytest_raises_includes_exception",
        initial_files={
            "src/exceptions.py": """class ValidationError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class NotFoundError(Exception):
    def __init__(self, resource: str, identifier: str):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} with id {identifier} not found")
""",
            "src/user_repository.py": """from src.exceptions import NotFoundError, ValidationError

class UserRepository:
    def __init__(self):
        self.users = {}

    def get(self, user_id: int):
        if user_id not in self.users:
            raise NotFoundError("User", str(user_id))
        return self.users[user_id]

    def create(self, data: dict):
        if "email" not in data:
            raise ValidationError("email", "is required")
        user_id = len(self.users) + 1
        self.users[user_id] = {**data, "id": user_id}
        return self.users[user_id]
""",
            "tests/test_user_repository.py": """from src.user_repository import UserRepository

def test_create_user():
    repo = UserRepository()
    user = repo.create({"name": "Test", "email": "test@example.com"})
    assert user["name"] == "Test"
""",
        },
        changed_files={
            "src/exceptions.py": """class ValidationError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class NotFoundError(Exception):
    def __init__(self, resource: str, identifier: str):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} with id {identifier} not found")

class PermissionDeniedError(Exception):
    def __init__(self, action: str, resource: str):
        self.action = action
        self.resource = resource
        super().__init__(f"Permission denied: cannot {action} {resource}")
""",
            "src/user_repository.py": """from src.exceptions import NotFoundError, ValidationError

class UserRepository:
    def __init__(self):
        self.users = {}

    def get(self, user_id: int):
        if user_id not in self.users:
            raise NotFoundError("User", str(user_id))
        return self.users[user_id]

    def create(self, data: dict):
        if "email" not in data:
            raise ValidationError("email", "is required")
        if "name" not in data:
            raise ValidationError("name", "is required")
        user_id = len(self.users) + 1
        self.users[user_id] = {**data, "id": user_id}
        return self.users[user_id]
""",
            "tests/test_user_repository.py": """import pytest
from src.user_repository import UserRepository
from src.exceptions import NotFoundError, ValidationError

def test_create_user():
    repo = UserRepository()
    user = repo.create({"name": "Test", "email": "test@example.com"})
    assert user["name"] == "Test"

def test_get_nonexistent_raises_not_found():
    repo = UserRepository()
    with pytest.raises(NotFoundError) as exc_info:
        repo.get(999)
    assert exc_info.value.resource == "User"
    assert exc_info.value.identifier == "999"

def test_create_without_email_raises_validation_error():
    repo = UserRepository()
    with pytest.raises(ValidationError) as exc_info:
        repo.create({"name": "Test"})
    assert exc_info.value.field == "email"
    assert "required" in exc_info.value.message

def test_create_without_name_raises_validation_error():
    repo = UserRepository()
    with pytest.raises(ValidationError) as exc_info:
        repo.create({"email": "test@example.com"})
    assert exc_info.value.field == "name"
""",
        },
        must_include=["exceptions.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_405_test_snapshot_assertion",
        initial_files={
            "src/report_generator.py": """from datetime import datetime

class ReportGenerator:
    def __init__(self, title: str):
        self.title = title

    def generate_summary(self, data: list[dict]) -> dict:
        total = sum(item.get("value", 0) for item in data)
        count = len(data)
        avg = total / count if count > 0 else 0
        return {
            "title": self.title,
            "total": total,
            "count": count,
            "average": round(avg, 2),
            "items": data,
        }

    def generate_html(self, data: list[dict]) -> str:
        summary = self.generate_summary(data)
        html = f"<html><head><title>{summary['title']}</title></head>"
        html += f"<body><h1>{summary['title']}</h1>"
        html += f"<p>Total: {summary['total']}</p>"
        html += f"<p>Count: {summary['count']}</p>"
        html += f"<p>Average: {summary['average']}</p>"
        html += "<ul>"
        for item in summary["items"]:
            html += f"<li>{item.get('name', 'Unknown')}: {item.get('value', 0)}</li>"
        html += "</ul></body></html>"
        return html
""",
            "tests/test_report_generator.py": """from src.report_generator import ReportGenerator

def test_generate_summary_basic():
    generator = ReportGenerator("Test Report")
    data = [{"name": "A", "value": 10}]
    result = generator.generate_summary(data)
    assert result["total"] == 10
""",
        },
        changed_files={
            "tests/test_report_generator.py": """from src.report_generator import ReportGenerator

def test_generate_summary_basic():
    generator = ReportGenerator("Test Report")
    data = [{"name": "A", "value": 10}]
    result = generator.generate_summary(data)
    assert result["total"] == 10

def test_generate_summary_snapshot():
    generator = ReportGenerator("Sales Report")
    data = [
        {"name": "Product A", "value": 100},
        {"name": "Product B", "value": 200},
        {"name": "Product C", "value": 150},
    ]
    result = generator.generate_summary(data)

    expected = {
        "title": "Sales Report",
        "total": 450,
        "count": 3,
        "average": 150.0,
        "items": data,
    }
    assert result == expected

def test_generate_html_snapshot():
    generator = ReportGenerator("Monthly Summary")
    data = [
        {"name": "Revenue", "value": 5000},
        {"name": "Expenses", "value": 3000},
    ]
    result = generator.generate_html(data)

    assert "<title>Monthly Summary</title>" in result
    assert "<h1>Monthly Summary</h1>" in result
    assert "<p>Total: 8000</p>" in result
    assert "<p>Count: 2</p>" in result
    assert "<p>Average: 4000.0</p>" in result
    assert "<li>Revenue: 5000</li>" in result
    assert "<li>Expenses: 3000</li>" in result
""",
        },
        must_include=["test_report_generator.py"],
        must_not_include=["garbage_marker_12345"],
    ),
    DiffTestCase(
        name="dep_406_test_api_response_snapshot",
        initial_files={
            "src/api_handlers.py": """from dataclasses import dataclass
from typing import Optional
import json

@dataclass
class ApiResponse:
    status: str
    data: Optional[dict] = None
    error: Optional[str] = None
    meta: Optional[dict] = None

    def to_json(self) -> str:
        result = {"status": self.status}
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            result["error"] = self.error
        if self.meta is not None:
            result["meta"] = self.meta
        return json.dumps(result, indent=2)

class UserApiHandler:
    def __init__(self):
        self.users = {
            1: {"id": 1, "name": "Admin", "role": "admin"},
            2: {"id": 2, "name": "User", "role": "user"},
        }

    def get_user(self, user_id: int) -> ApiResponse:
        if user_id not in self.users:
            return ApiResponse(
                status="error",
                error=f"User {user_id} not found",
                meta={"request_id": "req_123"}
            )
        return ApiResponse(
            status="success",
            data=self.users[user_id],
            meta={"request_id": "req_123", "cached": False}
        )

    def list_users(self, page: int = 1, limit: int = 10) -> ApiResponse:
        users = list(self.users.values())
        return ApiResponse(
            status="success",
            data={"users": users, "total": len(users)},
            meta={"page": page, "limit": limit}
        )
""",
            "tests/test_api_handlers.py": """from src.api_handlers import UserApiHandler

def test_get_user_exists():
    handler = UserApiHandler()
    response = handler.get_user(1)
    assert response.status == "success"
""",
        },
        changed_files={
            "tests/test_api_handlers.py": """import json
from src.api_handlers import UserApiHandler, ApiResponse

def test_get_user_exists():
    handler = UserApiHandler()
    response = handler.get_user(1)
    assert response.status == "success"

def test_get_user_success_snapshot():
    handler = UserApiHandler()
    response = handler.get_user(1)
    result = json.loads(response.to_json())

    assert result["status"] == "success"
    assert result["data"]["id"] == 1
    assert result["data"]["name"] == "Admin"
    assert result["data"]["role"] == "admin"
    assert "meta" in result
    assert result["meta"]["cached"] is False

def test_get_user_not_found_snapshot():
    handler = UserApiHandler()
    response = handler.get_user(999)
    result = json.loads(response.to_json())

    assert result["status"] == "error"
    assert "999" in result["error"]
    assert "not found" in result["error"]
    assert "data" not in result

def test_list_users_snapshot():
    handler = UserApiHandler()
    response = handler.list_users(page=1, limit=10)
    result = json.loads(response.to_json())

    assert result["status"] == "success"
    assert result["data"]["total"] == 2
    assert len(result["data"]["users"]) == 2
    assert result["meta"]["page"] == 1
    assert result["meta"]["limit"] == 10
""",
        },
        must_include=["test_api_handlers.py"],
        must_not_include=["garbage_marker_12345"],
    ),
]


ALL_DEPENDENCY_CASES = (
    FORWARD_DEPENDENCY_CASES + BACKWARD_DEPENDENCY_CASES + REVERSE_DEPENDENCY_CASES + TEST_RELATION_CASES + TEST_PATTERN_CASES
)


@pytest.fixture
def diff_test_runner(tmp_path):
    return DiffTestRunner(tmp_path)


@pytest.mark.parametrize("case", ALL_DEPENDENCY_CASES, ids=lambda c: c.name)
def test_dependency_cases(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
