import pytest

from tests.utils import DiffTestCase, DiffTestRunner

RUBY_BASICS_CASES = [
    DiffTestCase(
        name="ruby_001_method_definition",
        initial_files={
            "processor.rb": """class Processor
  def process(data)
    data.upcase
  end
end
""",
            "app.rb": """# Initial file
puts 'Hello'
""",
            "garbage.rb": """garbage_marker_12345 = "never used"
unused_marker_67890 = "not used"
""",
        },
        changed_files={
            "app.rb": """require_relative 'processor'

processor = Processor.new
result = processor.process("hello")
puts result
""",
        },
        must_include=["app.rb", "process"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="ruby_002_block_yield",
        initial_files={
            "retry_helper.rb": """module RetryHelper
  def with_retry(max_attempts: 3)
    attempts = 0
    begin
      attempts += 1
      yield
    rescue StandardError => e
      retry if attempts < max_attempts
      raise e
    end
  end
end
""",
            "service.rb": """# Initial
class Service
end
""",
            "garbage.rb": """garbage_helper_unused_67890 = "never invoked"
unused_marker_12345 = "not used"
""",
        },
        changed_files={
            "service.rb": """require_relative 'retry_helper'

class Service
  include RetryHelper

  def fetch_data
    with_retry(max_attempts: 5) do
      raise "Error" if rand < 0.5
    end
  end
end
""",
        },
        must_include=["service.rb", "with_retry"],
        must_not_include=["garbage_helper_unused_67890", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="ruby_003_module_mixin",
        initial_files={
            "logging.rb": """module Logging
  def log(message)
    puts "[LOG] #{message}"
  end

  def log_error(message)
    puts "[ERROR] #{message}"
  end
end
""",
            "worker.rb": """# Initial
class Worker
end
""",
            "garbage.rb": """garbage_log_unused_99999 = "never used"
unused_marker_12345 = "not used"
""",
        },
        changed_files={
            "worker.rb": """require_relative 'logging'

class Worker
  include Logging

  def perform
    log("Starting work")
    log("Work completed")
  end
end
""",
        },
        must_include=["worker.rb", "log"],
        must_not_include=["garbage_log_unused_99999", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="ruby_004_extend",
        initial_files={
            "class_methods.rb": """module ClassMethods
  def find(id)
    new(id: id)
  end

  def all
    []
  end
end
""",
            "model.rb": """# Initial
class Model
end
""",
            "garbage.rb": """garbage_class_method_unused_12345 = "never called"
unused_marker_67890 = "not used"
""",
        },
        changed_files={
            "model.rb": """require_relative 'class_methods'

class Model
  extend ClassMethods

  attr_reader :id

  def initialize(id:)
    @id = id
  end
end

model = Model.find(1)
""",
        },
        must_include=["model.rb", "find"],
        must_not_include=["garbage_class_method_unused_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="ruby_005_prepend",
        initial_files={
            "wrapper.rb": """module Wrapper
  def process(data)
    puts "Before processing"
    result = super
    puts "After processing"
    result
  end
end
""",
            "handler.rb": """# Initial
class Handler
  def process(data)
    data.upcase
  end
end
""",
            "garbage.rb": """garbage_wrapper_unused_67890 = "never called"
unused_marker_12345 = "not used"
""",
        },
        changed_files={
            "handler.rb": """require_relative 'wrapper'

class Handler
  prepend Wrapper

  def process(data)
    data.upcase
  end
end
""",
        },
        must_include=["handler.rb", "prepend"],
        must_not_include=["garbage_wrapper_unused_67890", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="ruby_006_attr_accessor",
        initial_files={
            "user.rb": """class User
  attr_accessor :name, :email

  def initialize(name:, email:)
    @name = name
    @email = email
  end
end
""",
            "app.rb": """# Initial
puts 'Hello'
""",
            "garbage.rb": """garbage_user_unused_99999 = "never accessed"
unused_marker_12345 = "not used"
""",
        },
        changed_files={
            "app.rb": """require_relative 'user'

user = User.new(name: 'John', email: 'john@example.com')
puts user.name
user.email = 'new@example.com'
""",
        },
        must_include=["app.rb", "name"],
        must_not_include=["garbage_user_unused_99999", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="ruby_007_class_method",
        initial_files={
            "user.rb": """class User
  def self.find(id)
    new(id: id, name: "User")
  end

  def self.all
    []
  end

  attr_reader :id, :name

  def initialize(id:, name:)
    @id = id
    @name = name
  end
end
""",
            "controller.rb": """# Initial
class Controller
end
""",
            "garbage.rb": """garbage_class_find_unused_12345 = "never called"
unused_marker_67890 = "not used"
""",
        },
        changed_files={
            "controller.rb": """require_relative 'user'

class Controller
  def show(id)
    @user = User.find(id)
  end

  def index
    @users = User.all
  end
end
""",
        },
        must_include=["controller.rb", "find"],
        must_not_include=["garbage_class_find_unused_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="ruby_008_private_method",
        initial_files={
            "service.rb": """class Service
  def process(data)
    validated = validate(data)
    transform(validated)
  end

  private

  def validate(data)
    raise "Invalid" if data.nil?
    data
  end

  def transform(data)
    data.to_s.upcase
  end
end
""",
            "app.rb": """# Initial
puts 'Hello'
""",
            "garbage.rb": """garbage_private_unused_67890 = "never called"
unused_marker_12345 = "not used"
""",
        },
        changed_files={
            "app.rb": """require_relative 'service'

service = Service.new
result = service.process("hello")
puts result
""",
        },
        must_include=["app.rb", "process"],
        must_not_include=["garbage_private_unused_67890", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="ruby_009_method_missing",
        initial_files={
            "dynamic_struct.rb": """class DynamicStruct
  def initialize(hash = {})
    @data = hash
  end

  def method_missing(name, *args)
    if name.to_s.end_with?('=')
      @data[name.to_s.chop.to_sym] = args.first
    else
      @data[name]
    end
  end
end
""",
            "app.rb": """# Initial
puts 'Hello'
""",
            "garbage.rb": """garbage_dynamic_unused_99999 = "never called"
unused_marker_12345 = "not used"
""",
        },
        changed_files={
            "app.rb": """require_relative 'dynamic_struct'

obj = DynamicStruct.new(name: 'John')
puts obj.name
obj.email = 'john@example.com'
""",
        },
        must_include=["app.rb", "name"],
        must_not_include=["garbage_dynamic_unused_99999", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="ruby_010_proc_lambda",
        initial_files={
            "validators.rb": """module Validators
  POSITIVE = ->(x) { x > 0 }
  NON_EMPTY = ->(s) { !s.nil? && !s.empty? }
  EMAIL_FORMAT = ->(e) { e =~ /\\A[^@\\s]+@[^@\\s]+\\z/ }
end
""",
            "form.rb": """# Initial
class Form
end
""",
            "garbage.rb": """GARBAGE_VALIDATOR_UNUSED = "never_used_12345"
unused_marker_67890 = "not used"
""",
        },
        changed_files={
            "form.rb": """require_relative 'validators'

class Form
  def validate(data)
    return false unless Validators::POSITIVE.call(data[:age])
    return false unless Validators::NON_EMPTY.call(data[:name])
    return false unless Validators::EMAIL_FORMAT.call(data[:email])
    true
  end
end
""",
        },
        must_include=["form.rb", "POSITIVE"],
        must_not_include=["GARBAGE_VALIDATOR_UNUSED", "unused_marker_67890"],
    ),
]

RUBY_ADVANCED_CASES = [
    DiffTestCase(
        name="ruby_011_symbol_to_proc",
        initial_files={
            "user.rb": """class User
  attr_reader :name, :email, :age

  def initialize(name:, email:, age:)
    @name = name
    @email = email
    @age = age
  end
end
""",
            "report.rb": """# Initial
class Report
end
""",
            "garbage.rb": """garbage_user_method_unused_67890 = "never called"
unused_marker_12345 = "not used"
""",
        },
        changed_files={
            "report.rb": """require_relative 'user'

class Report
  def initialize(users)
    @users = users
  end

  def names
    @users.map(&:name)
  end

  def emails
    @users.map(&:email)
  end
end
""",
        },
        must_include=["report.rb", "name"],
        must_not_include=["garbage_user_method_unused_67890", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="ruby_012_struct",
        initial_files={
            "types.rb": """Point = Struct.new(:x, :y) do
  def distance_from_origin
    Math.sqrt(x**2 + y**2)
  end
end

Rectangle = Struct.new(:width, :height) do
  def area
    width * height
  end
end
""",
            "geometry.rb": """# Initial
module Geometry
end
""",
            "garbage.rb": """GarbageStruct = "unused_99999"
unused_marker_12345 = "not used"
""",
        },
        changed_files={
            "geometry.rb": """require_relative 'types'

module Geometry
  def self.create_point(x, y)
    Point.new(x, y)
  end

  def self.create_rectangle(w, h)
    Rectangle.new(w, h)
  end
end

p = Geometry.create_point(3, 4)
puts p.distance_from_origin
""",
        },
        must_include=["geometry.rb", "Point"],
        must_not_include=["GarbageStruct", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="ruby_013_refinement",
        initial_files={
            "string_ext.rb": """module StringExtensions
  refine String do
    def shout
      upcase + "!"
    end

    def whisper
      downcase + "..."
    end
  end
end
""",
            "messenger.rb": """# Initial
class Messenger
end
""",
            "garbage.rb": """garbage_refine_unused_12345 = "never used"
unused_marker_67890 = "not used"
""",
        },
        changed_files={
            "messenger.rb": """require_relative 'string_ext'

class Messenger
  using StringExtensions

  def loud_message(text)
    text.shout
  end

  def quiet_message(text)
    text.whisper
  end
end
""",
        },
        must_include=["messenger.rb", "shout"],
        must_not_include=["garbage_refine_unused_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="ruby_014_metaprogramming",
        initial_files={
            "dsl.rb": """module DSL
  def self.define_accessors(*names)
    names.each do |name|
      define_method(name) do
        instance_variable_get("@" + name.to_s)
      end

      define_method(name.to_s + "=") do |value|
        instance_variable_set("@" + name.to_s, value)
      end
    end
  end
end
""",
            "config.rb": """# Initial
class Config
end
""",
            "garbage.rb": """garbage_meta_unused_67890 = "never called"
unused_marker_12345 = "not used"
""",
        },
        changed_files={
            "config.rb": """require_relative 'dsl'

class Config
  extend DSL

  define_accessors :host, :port, :debug

  def initialize(host: 'localhost', port: 3000, debug: false)
    @host = host
    @port = port
    @debug = debug
  end
end

config = Config.new
puts config.host
""",
        },
        must_include=["config.rb", "define_accessors"],
        must_not_include=["garbage_meta_unused_67890", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="ruby_015_rails_controller",
        initial_files={
            "user.rb": """class User
  attr_accessor :id, :name, :email

  def self.find(id)
    new(id: id, name: "User")
  end

  def initialize(id: nil, name: nil, email: nil)
    @id = id
    @name = name
    @email = email
  end

  def save
    true
  end
end
""",
            "users_controller.rb": """# Initial
class UsersController
end
""",
            "garbage.rb": """garbage_find_unused_99999 = "never called"
unused_marker_12345 = "not used"
""",
        },
        changed_files={
            "users_controller.rb": """require_relative 'user'

class UsersController
  def create
    @user = User.new(user_params)
    @user.save
  end

  def show
    @user = User.find(params[:id])
  end

  private

  def user_params
    { name: 'John', email: 'john@example.com' }
  end

  def params
    { id: 1 }
  end
end
""",
        },
        must_include=["users_controller.rb", "find"],
        must_not_include=["garbage_find_unused_99999", "unused_marker_12345"],
    ),
]

PHP_BASICS_CASES = [
    DiffTestCase(
        name="php_001_class_instantiation",
        initial_files={
            "User.php": """<?php
class User {
    private string $name;
    private string $email;

    public function __construct(string $name, string $email) {
        $this->name = $name;
        $this->email = $email;
    }

    public function getName(): string {
        return $this->name;
    }
}
""",
            "app.php": """<?php
echo "Hello";
""",
            "garbage.php": """<?php
$garbageUnused99999 = "never called";
$unused_marker_12345 = "not used";
""",
        },
        changed_files={
            "app.php": """<?php
require_once 'User.php';

$user = new User('John', 'john@example.com');
echo $user->getName();
""",
        },
        must_include=["app.php", "getName"],
        must_not_include=["garbageUnused99999", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="php_002_namespace_use",
        initial_files={
            "PaymentService.php": """<?php
namespace App\\Services;

class PaymentService {
    public function process(float $amount): bool {
        return $amount > 0;
    }
}
""",
            "Controller.php": """<?php
class Controller {}
""",
            "garbage.php": """<?php
$garbagePayment12345 = false;
$unused_marker_67890 = "not used";
""",
        },
        changed_files={
            "Controller.php": """<?php
use App\\Services\\PaymentService;

class Controller {
    private PaymentService $paymentService;

    public function __construct() {
        $this->paymentService = new PaymentService();
    }

    public function checkout(float $amount): bool {
        return $this->paymentService->process($amount);
    }
}
""",
        },
        must_include=["Controller.php", "process"],
        must_not_include=["garbagePayment12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="php_003_trait",
        initial_files={
            "LoggingTrait.php": """<?php
trait LoggingTrait {
    public function log(string $message): void {
        echo "[LOG] " . $message . "\\n";
    }

    public function logError(string $message): void {
        echo "[ERROR] " . $message . "\\n";
    }
}
""",
            "Service.php": """<?php
class Service {}
""",
            "garbage.php": """<?php
$garbageLogUnused67890 = "never called";
$unused_marker_12345 = "not used";
""",
        },
        changed_files={
            "Service.php": """<?php
require_once 'LoggingTrait.php';

class Service {
    use LoggingTrait;

    public function process(): void {
        $this->log("Processing started");
        $this->log("Processing completed");
    }
}
""",
        },
        must_include=["Service.php", "log"],
        must_not_include=["garbageLogUnused67890", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="php_004_interface",
        initial_files={
            "RequestHandler.php": """<?php
interface RequestHandler {
    public function handle(array $request): array;
    public function validate(array $request): bool;
}
""",
            "Handler.php": """<?php
class Handler {}
""",
            "garbage.php": """<?php
interface GarbageHandler99999 {
    public function unused(): void;
}
$unused_marker_12345 = "not used";
""",
        },
        changed_files={
            "Handler.php": """<?php
require_once 'RequestHandler.php';

class Handler implements RequestHandler {
    public function handle(array $request): array {
        if (!$this->validate($request)) {
            return ['error' => 'Invalid request'];
        }
        return ['success' => true];
    }

    public function validate(array $request): bool {
        return isset($request['action']);
    }
}
""",
        },
        must_include=["Handler.php", "handle"],
        must_not_include=["GarbageHandler99999", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="php_005_abstract_class",
        initial_files={
            "BaseController.php": """<?php
abstract class BaseController {
    abstract protected function getModel(): string;

    public function index(): array {
        return ['model' => $this->getModel()];
    }

    protected function respond(array $data): void {
        echo json_encode($data);
    }
}
""",
            "UserController.php": """<?php
class UserController {}
""",
            "garbage.php": """<?php
$garbageBaseUnused12345 = "never called";
$unused_marker_67890 = "not used";
""",
        },
        changed_files={
            "UserController.php": """<?php
require_once 'BaseController.php';

class UserController extends BaseController {
    protected function getModel(): string {
        return 'User';
    }

    public function show(int $id): void {
        $this->respond(['id' => $id, 'model' => $this->getModel()]);
    }
}
""",
        },
        must_include=["UserController.php", "getModel"],
        must_not_include=["garbageBaseUnused12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="php_006_static_method",
        initial_files={
            "User.php": """<?php
class User {
    private static array $users = [];
    public int $id;
    public string $name;

    public function __construct(int $id, string $name) {
        $this->id = $id;
        $this->name = $name;
    }

    public static function find(int $id): ?self {
        return self::$users[$id] ?? null;
    }

    public static function create(string $name): self {
        $id = count(self::$users) + 1;
        $user = new self($id, $name);
        self::$users[$id] = $user;
        return $user;
    }
}
""",
            "app.php": """<?php
echo "Hello";
""",
            "garbage.php": """<?php
$garbageStatic67890 = "never called";
$unused_marker_12345 = "not used";
""",
        },
        changed_files={
            "app.php": """<?php
require_once 'User.php';

$user = User::create('John');
$found = User::find($user->id);
echo $found->name;
""",
        },
        must_include=["app.php", "create"],
        must_not_include=["garbageStatic67890", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="php_007_magic_method",
        initial_files={
            "DynamicObject.php": """<?php
class DynamicObject {
    private array $data = [];

    public function __get(string $name): mixed {
        return $this->data[$name] ?? null;
    }

    public function __set(string $name, mixed $value): void {
        $this->data[$name] = $value;
    }

    public function __isset(string $name): bool {
        return isset($this->data[$name]);
    }
}
""",
            "app.php": """<?php
echo "Hello";
""",
            "garbage.php": """<?php
$garbageMagic99999 = "never called";
$unused_marker_12345 = "not used";
""",
        },
        changed_files={
            "app.php": """<?php
require_once 'DynamicObject.php';

$obj = new DynamicObject();
$obj->name = 'John';
$obj->email = 'john@example.com';

echo $obj->name;
if (isset($obj->email)) {
    echo $obj->email;
}
""",
        },
        must_include=["app.php", "__get"],
        must_not_include=["garbageMagic99999", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="php_008_type_declaration",
        initial_files={
            "Response.php": """<?php
class Response {
    private int $status;
    private array $data;

    public function __construct(int $status, array $data) {
        $this->status = $status;
        $this->data = $data;
    }

    public function getStatus(): int {
        return $this->status;
    }

    public function getData(): array {
        return $this->data;
    }
}
""",
            "Processor.php": """<?php
class Processor {}
""",
            "garbage.php": """<?php
$garbageResponse12345 = -1;
$unused_marker_67890 = "not used";
""",
        },
        changed_files={
            "Processor.php": """<?php
require_once 'Response.php';

class Processor {
    public function process(array $data): Response {
        $result = array_map(fn($x) => $x * 2, $data);
        return new Response(200, $result);
    }
}
""",
        },
        must_include=["Processor.php", "Response"],
        must_not_include=["garbageResponse12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="php_009_nullable_type",
        initial_files={
            "User.php": """<?php
class User {
    public int $id;
    public string $name;

    public function __construct(int $id, string $name) {
        $this->id = $id;
        $this->name = $name;
    }
}
""",
            "Repository.php": """<?php
class Repository {}
""",
            "garbage.php": """<?php
$garbageNullable67890 = null;
$unused_marker_12345 = "not used";
""",
        },
        changed_files={
            "Repository.php": """<?php
require_once 'User.php';

class Repository {
    private array $users = [];

    public function find(int $id): ?User {
        return $this->users[$id] ?? null;
    }

    public function save(User $user): void {
        $this->users[$user->id] = $user;
    }
}
""",
        },
        must_include=["Repository.php", "find"],
        must_not_include=["garbageNullable67890", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="php_010_union_type",
        initial_files={
            "Data.php": """<?php
class Data {
    public mixed $value;

    public function __construct(mixed $value) {
        $this->value = $value;
    }
}
""",
            "Parser.php": """<?php
class Parser {}
""",
            "garbage.php": """<?php
$garbageUnion99999 = "never used";
$unused_marker_12345 = "not used";
""",
        },
        changed_files={
            "Parser.php": """<?php
require_once 'Data.php';

class Parser {
    public function parse(string|array $input): Data {
        if (is_string($input)) {
            return new Data(json_decode($input, true));
        }
        return new Data($input);
    }
}
""",
        },
        must_include=["Parser.php", "Data"],
        must_not_include=["garbageUnion99999", "unused_marker_12345"],
    ),
]

PHP_ADVANCED_CASES = [
    DiffTestCase(
        name="php_011_attribute",
        initial_files={
            "Route.php": """<?php
#[Attribute]
class Route {
    public function __construct(
        public string $path,
        public string $method = 'GET'
    ) {}
}
""",
            "Controller.php": """<?php
class Controller {}
""",
            "garbage.php": """<?php
$garbageRoute12345 = "never called";
$unused_marker_67890 = "not used";
""",
        },
        changed_files={
            "Controller.php": """<?php
require_once 'Route.php';

class Controller {
    #[Route('/api/users', 'GET')]
    public function index(): array {
        return ['users' => []];
    }

    #[Route('/api/users', 'POST')]
    public function store(): array {
        return ['created' => true];
    }
}
""",
        },
        must_include=["Controller.php", "Route"],
        must_not_include=["garbageRoute12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="php_012_constructor_promotion",
        initial_files={
            "Config.php": """<?php
class Config {
    public function __construct(
        private string $host,
        private int $port,
        private bool $debug = false
    ) {}

    public function getHost(): string {
        return $this->host;
    }

    public function getPort(): int {
        return $this->port;
    }

    public function isDebug(): bool {
        return $this->debug;
    }
}
""",
            "app.php": """<?php
echo "Hello";
""",
            "garbage.php": """<?php
$garbageConfig67890 = "never called";
$unused_marker_12345 = "not used";
""",
        },
        changed_files={
            "app.php": """<?php
require_once 'Config.php';

$config = new Config('localhost', 8080, true);
echo $config->getHost() . ':' . $config->getPort();
""",
        },
        must_include=["app.php", "getHost"],
        must_not_include=["garbageConfig67890", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="php_013_anonymous_class",
        initial_files={
            "Handler.php": """<?php
interface Handler {
    public function handle(mixed $data): mixed;
}
""",
            "app.php": """<?php
echo "Hello";
""",
            "garbage.php": """<?php
interface GarbageAnon99999 {
    public function unused(): void;
}
$unused_marker_12345 = "not used";
""",
        },
        changed_files={
            "app.php": """<?php
require_once 'Handler.php';

$handler = new class implements Handler {
    public function handle(mixed $data): mixed {
        return strtoupper($data);
    }
};

echo $handler->handle('hello');
""",
        },
        must_include=["app.php", "Handler"],
        must_not_include=["GarbageAnon99999", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="php_014_closure",
        initial_files={
            "Multiplier.php": """<?php
class Multiplier {
    public function __construct(private int $factor) {}

    public function getFactor(): int {
        return $this->factor;
    }
}
""",
            "app.php": """<?php
echo "Hello";
""",
            "garbage.php": """<?php
$garbageClosure12345 = -1;
$unused_marker_67890 = "not used";
""",
        },
        changed_files={
            "app.php": """<?php
require_once 'Multiplier.php';

$multiplier = new Multiplier(10);
$factor = $multiplier->getFactor();

$callback = function(int $x) use ($factor): int {
    return $x * $factor;
};

$numbers = [1, 2, 3, 4, 5];
$result = array_map($callback, $numbers);
print_r($result);
""",
        },
        must_include=["app.php", "getFactor"],
        must_not_include=["garbageClosure12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="php_015_laravel_controller",
        initial_files={
            "StoreUserRequest.php": """<?php
namespace App\\Http\\Requests;

class StoreUserRequest {
    public function validated(): array {
        return [
            'name' => 'John',
            'email' => 'john@example.com'
        ];
    }
}
""",
            "UserController.php": """<?php
class UserController {}
""",
            "garbage.php": """<?php
$garbageRequest67890 = [];
$unused_marker_12345 = "not used";
""",
        },
        changed_files={
            "UserController.php": """<?php
use App\\Http\\Requests\\StoreUserRequest;

class UserController {
    public function store(StoreUserRequest $request): array {
        $data = $request->validated();
        return ['user' => $data, 'created' => true];
    }
}
""",
        },
        must_include=["UserController.php", "validated"],
        must_not_include=["garbageRequest67890", "unused_marker_12345"],
    ),
]

ALL_RUBY_CASES = RUBY_BASICS_CASES + RUBY_ADVANCED_CASES
ALL_PHP_CASES = PHP_BASICS_CASES + PHP_ADVANCED_CASES
ALL_SCRIPTING_CASES = ALL_RUBY_CASES + ALL_PHP_CASES


@pytest.fixture
def diff_test_runner(tmp_path):
    return DiffTestRunner(tmp_path)


@pytest.mark.parametrize("case", ALL_SCRIPTING_CASES, ids=lambda c: c.name)
def test_scripting_cases(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
