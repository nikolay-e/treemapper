import pytest

from tests.utils import DiffTestCase, DiffTestRunner

PHP_BASIC_CASES = [
    DiffTestCase(
        name="php_301_class_instantiation",
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
        },
        changed_files={
            "app.php": """<?php
require_once 'User.php';

$user = new User('John', 'john@example.com');
echo $user->getName();
""",
        },
        must_include=["new User", "getName"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add class instantiation",
    ),
    DiffTestCase(
        name="php_302_namespace_use",
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
        must_include=["PaymentService", "process"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add namespace use",
    ),
    DiffTestCase(
        name="php_303_trait",
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
        },
        changed_files={
            "Service.php": """<?php
require_once 'LoggingTrait.php';

class Service {
    use LoggingTrait;

    public function process(): void {
        $this->log("Processing started");
        // Do work
        $this->log("Processing completed");
    }
}
""",
        },
        must_include=["use LoggingTrait", "$this->log"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add trait",
    ),
    DiffTestCase(
        name="php_304_interface",
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
        must_include=["implements RequestHandler", "handle", "validate"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add interface implementation",
    ),
    DiffTestCase(
        name="php_305_abstract_class",
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
        must_include=["extends BaseController", "getModel", "respond"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add abstract class implementation",
    ),
    DiffTestCase(
        name="php_306_static_method",
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
        },
        changed_files={
            "app.php": """<?php
require_once 'User.php';

$user = User::create('John');
$found = User::find($user->id);
echo $found->name;
""",
        },
        must_include=["User::create", "User::find"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add static method usage",
    ),
    DiffTestCase(
        name="php_307_magic_method",
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
        must_include=["new DynamicObject", "$obj->name"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add magic method usage",
    ),
    DiffTestCase(
        name="php_308_type_declaration",
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
        must_include=["new Response", "process"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add type declaration",
    ),
    DiffTestCase(
        name="php_309_nullable_type",
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
        must_include=["?User", "save(User"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add nullable type",
    ),
    DiffTestCase(
        name="php_310_union_type",
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
        must_include=["new Data", "string|array"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add union type",
    ),
]


PHP_ADVANCED_CASES = [
    DiffTestCase(
        name="php_311_attribute",
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
        must_include=["#[Route"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add attribute",
    ),
    DiffTestCase(
        name="php_312_constructor_promotion",
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
        },
        changed_files={
            "app.php": """<?php
require_once 'Config.php';

$config = new Config('localhost', 8080, true);
echo $config->getHost() . ':' . $config->getPort();
""",
        },
        must_include=["new Config", "getHost", "getPort"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add constructor promotion usage",
    ),
    DiffTestCase(
        name="php_313_anonymous_class",
        initial_files={
            "Handler.php": """<?php
interface Handler {
    public function handle(mixed $data): mixed;
}
""",
            "app.php": """<?php
echo "Hello";
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
        must_include=["implements Handler", "handle"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add anonymous class",
    ),
    DiffTestCase(
        name="php_314_closure",
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
        must_include=["new Multiplier", "getFactor"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add closure",
    ),
    DiffTestCase(
        name="php_315_laravel_controller",
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
        must_include=["StoreUserRequest", "validated"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Laravel controller",
    ),
    DiffTestCase(
        name="php_316_laravel_model",
        initial_files={
            "Model.php": """<?php
abstract class Model {
    protected array $fillable = [];
    protected array $attributes = [];

    public function fill(array $data): self {
        foreach ($data as $key => $value) {
            if (in_array($key, $this->fillable)) {
                $this->attributes[$key] = $value;
            }
        }
        return $this;
    }
}
""",
            "User.php": """<?php
class User {}
""",
        },
        changed_files={
            "User.php": """<?php
require_once 'Model.php';

class User extends Model {
    protected array $fillable = ['name', 'email', 'password'];

    public static function create(array $data): self {
        $user = new self();
        return $user->fill($data);
    }
}
""",
        },
        must_include=["extends Model", "fill"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Laravel model",
    ),
    DiffTestCase(
        name="php_317_laravel_relationship",
        initial_files={
            "Post.php": """<?php
class Post {
    public int $id;
    public int $user_id;
    public string $title;

    public function __construct(int $id, int $user_id, string $title) {
        $this->id = $id;
        $this->user_id = $user_id;
        $this->title = $title;
    }
}
""",
            "User.php": """<?php
class User {}
""",
        },
        changed_files={
            "User.php": """<?php
require_once 'Post.php';

class User {
    public int $id;
    public string $name;
    private array $posts = [];

    public function __construct(int $id, string $name) {
        $this->id = $id;
        $this->name = $name;
    }

    public function posts(): array {
        return $this->posts;
    }

    public function addPost(Post $post): void {
        $this->posts[] = $post;
    }
}
""",
        },
        must_include=["addPost(Post", "posts()"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Laravel relationship",
    ),
    DiffTestCase(
        name="php_318_laravel_migration",
        initial_files={
            "Blueprint.php": """<?php
class Blueprint {
    private array $columns = [];

    public function id(): self {
        $this->columns[] = ['name' => 'id', 'type' => 'bigint'];
        return $this;
    }

    public function string(string $name, int $length = 255): self {
        $this->columns[] = ['name' => $name, 'type' => 'string', 'length' => $length];
        return $this;
    }

    public function unique(): self {
        return $this;
    }

    public function timestamps(): self {
        $this->columns[] = ['name' => 'created_at', 'type' => 'timestamp'];
        $this->columns[] = ['name' => 'updated_at', 'type' => 'timestamp'];
        return $this;
    }
}
""",
            "CreateUsersTable.php": """<?php
class CreateUsersTable {}
""",
        },
        changed_files={
            "CreateUsersTable.php": """<?php
require_once 'Blueprint.php';

class CreateUsersTable {
    public function up(): void {
        $table = new Blueprint();
        $table->id();
        $table->string('name');
        $table->string('email')->unique();
        $table->string('password');
        $table->timestamps();
    }
}
""",
        },
        must_include=["new Blueprint", "id()", "string(", "timestamps"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Laravel migration",
    ),
    DiffTestCase(
        name="php_319_dependency_injection",
        initial_files={
            "UserRepository.php": """<?php
class UserRepository {
    public function find(int $id): array {
        return ['id' => $id, 'name' => 'User'];
    }

    public function save(array $data): bool {
        return true;
    }
}
""",
            "UserService.php": """<?php
class UserService {}
""",
        },
        changed_files={
            "UserService.php": """<?php
require_once 'UserRepository.php';

class UserService {
    public function __construct(private UserRepository $repo) {}

    public function getUser(int $id): array {
        return $this->repo->find($id);
    }

    public function createUser(array $data): bool {
        return $this->repo->save($data);
    }
}
""",
        },
        must_include=["UserRepository $repo", "find", "save"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add dependency injection",
    ),
    DiffTestCase(
        name="php_320_phpunit",
        initial_files={
            "User.php": """<?php
class User {
    public function __construct(
        public string $name,
        public string $email
    ) {}

    public function isValidEmail(): bool {
        return filter_var($this->email, FILTER_VALIDATE_EMAIL) !== false;
    }
}
""",
            "UserTest.php": """<?php
class UserTest {}
""",
        },
        changed_files={
            "UserTest.php": """<?php
require_once 'User.php';

class UserTest {
    public function testUserCreation(): void {
        $user = new User('John', 'john@example.com');

        assert($user->name === 'John');
        assert($user->email === 'john@example.com');
    }

    public function testEmailValidation(): void {
        $validUser = new User('John', 'john@example.com');
        $invalidUser = new User('Jane', 'invalid-email');

        assert($validUser->isValidEmail() === true);
        assert($invalidUser->isValidEmail() === false);
    }
}
""",
        },
        must_include=["new User", "isValidEmail"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add PHPUnit test",
    ),
]


ALL_PHP_CASES = PHP_BASIC_CASES + PHP_ADVANCED_CASES


@pytest.mark.parametrize("case", ALL_PHP_CASES, ids=lambda c: c.name)
def test_php_diff_context(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
