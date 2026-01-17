import pytest

from tests.utils import DiffTestCase, DiffTestRunner

BASIC_CASES = [
    DiffTestCase(
        name="go_001_import_package_source",
        initial_files={
            "pkg/utils/helpers.go": """package utils

func FormatString(s string) string {
    return "[" + s + "]"
}
""",
            "main.go": """package main

import "mymodule/pkg/utils"

func main() {
    result := utils.FormatString("hello")
    println(result)
}
""",
            "unrelated/garbage.go": """package unrelated

func GarbageHelperUnused_12345() string {
    return "garbage_marker_12345"
}

func AnotherUnused_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "pkg/utils/helpers.go": """package utils

func FormatString(s string) string {
    return "[[" + s + "]]"
}

func TrimString(s string) string {
    return s
}
""",
        },
        must_include=["FormatString", "TrimString"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Update FormatString and add TrimString",
    ),
    DiffTestCase(
        name="go_002_receiver_type_definition",
        initial_files={
            "repo.go": """package main

type Repo struct {
    db *Database
}

func (r *Repo) Find(id int) *Entity {
    return r.db.Query(id)
}
""",
            "types.go": """package main

type Database struct {
    conn string
}

func (d *Database) Query(id int) *Entity {
    return &Entity{ID: id}
}

type Entity struct {
    ID int
}
""",
            "unrelated/garbage.go": """package unrelated

func GarbageUnused_12345() {
    println("garbage_marker_12345")
}

func AnotherUnused_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "repo.go": """package main

type Repo struct {
    db *Database
}

func (r *Repo) Find(id int) *Entity {
    return r.db.Query(id)
}

func (r *Repo) FindAll() []*Entity {
    return r.db.QueryAll()
}
""",
        },
        must_include=["FindAll", "Repo"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add FindAll method",
    ),
]


INTERFACE_CASES = [
    DiffTestCase(
        name="go_003_interface_implementations",
        initial_files={
            "interfaces.go": """package main

type Storage interface {
    Save(data []byte) error
    Load(key string) ([]byte, error)
}
""",
            "file_storage.go": """package main

import "os"

type FileStorage struct {
    path string
}

func (f *FileStorage) Save(data []byte) error {
    return os.WriteFile(f.path, data, 0644)
}

func (f *FileStorage) Load(key string) ([]byte, error) {
    return os.ReadFile(f.path + "/" + key)
}
""",
            "memory_storage.go": """package main

type MemoryStorage struct {
    data map[string][]byte
}

func (m *MemoryStorage) Save(data []byte) error {
    m.data["default"] = data
    return nil
}

func (m *MemoryStorage) Load(key string) ([]byte, error) {
    return m.data[key], nil
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedFileMethod_12345() {
    println("garbage_marker_12345")
}

func UnusedMemoryMethod_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "interfaces.go": """package main

type Storage interface {
    Save(data []byte) error
    Load(key string) ([]byte, error)
    Delete(key string) error
}
""",
        },
        must_include=["Storage", "Delete"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Delete to Storage interface",
    ),
    DiffTestCase(
        name="go_028_interface_composition",
        initial_files={
            "interfaces.go": """package main

type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

type Closer interface {
    Close() error
}
""",
            "file.go": """package main

type File struct {
    path string
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedFileFunc_12345() {
    println("garbage_marker_12345")
}

func AnotherUnusedFunc_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "interfaces.go": """package main

type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

type Closer interface {
    Close() error
}

type ReadWriter interface {
    Reader
    Writer
}

type ReadWriteCloser interface {
    Reader
    Writer
    Closer
}
""",
            "file.go": """package main

type File struct {
    path string
}

func (f *File) Read(p []byte) (int, error)  { return 0, nil }
func (f *File) Write(p []byte) (int, error) { return 0, nil }
func (f *File) Close() error                { return nil }

func Process(rwc ReadWriteCloser) {
    defer rwc.Close()
    buf := make([]byte, 1024)
    rwc.Read(buf)
    rwc.Write(buf)
}
""",
        },
        must_include=["ReadWriter", "ReadWriteCloser", "Process"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add composed interfaces",
    ),
]


DIRECTIVE_CASES = [
    DiffTestCase(
        name="go_004_embed_directive",
        initial_files={
            "templates/index.html": """<!DOCTYPE html>
<html><body>Hello</body></html>
""",
            "server.go": """package main

import (
    "embed"
    "net/http"
)

//go:embed templates/*
var content embed.FS

func handler(w http.ResponseWriter, r *http.Request) {
    data, _ := content.ReadFile("templates/index.html")
    w.Write(data)
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedServerFunc_12345() {
    println("garbage_marker_12345")
}

func AnotherUnused_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "templates/index.html": """<!DOCTYPE html>
<html><body>Hello World!</body></html>
""",
        },
        must_include=["index.html", "Hello World"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Update template",
    ),
    DiffTestCase(
        name="go_005_go_generate_directive",
        initial_files={
            "generate.go": """package main

//go:generate mockgen -source=interfaces.go -destination=mocks.go
""",
            "interfaces.go": """package main

type UserService interface {
    GetUser(id int) (*User, error)
}

type User struct {
    ID   int
    Name string
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedGenerate_12345() {
    println("garbage_marker_12345")
}

func UnusedInterface_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "interfaces.go": """package main

type UserService interface {
    GetUser(id int) (*User, error)
    CreateUser(name string) (*User, error)
}

type User struct {
    ID   int
    Name string
}
""",
        },
        must_include=["UserService", "CreateUser"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add CreateUser to interface",
    ),
]


MODULE_CASES = [
    DiffTestCase(
        name="go_006_go_mod_require",
        initial_files={
            "go.mod": """module myproject

go 1.21

require (
    github.com/gin-gonic/gin v1.9.0
)
""",
            "server.go": """package main

import "github.com/gin-gonic/gin"

func main() {
    r := gin.Default()
    r.GET("/", func(c *gin.Context) {
        c.JSON(200, gin.H{"status": "ok"})
    })
    r.Run()
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedServerFunc_12345() {
    println("garbage_marker_12345")
}

func AnotherUnused_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "go.mod": """module myproject

go 1.21

require (
    github.com/gin-gonic/gin v1.9.0
    github.com/redis/go-redis/v9 v9.0.0
)
""",
        },
        must_include=["go.mod", "redis"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add redis dependency",
    ),
    DiffTestCase(
        name="go_007_go_mod_replace",
        initial_files={
            "go.mod": """module myproject

go 1.21

require mymodule/pkg v0.0.0

replace mymodule/pkg => ./pkg
""",
            "pkg/lib.go": """package pkg

func Helper() string {
    return "helper"
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedPkgFunc_12345() {
    println("garbage_marker_12345")
}

func AnotherUnused_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "pkg/lib.go": """package pkg

func Helper() string {
    return "improved helper"
}

func NewHelper() string {
    return "new helper"
}
""",
        },
        must_include=["Helper", "NewHelper"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Update local module",
    ),
]


FUNCTION_CASES = [
    DiffTestCase(
        name="go_008_init_function",
        initial_files={
            "config.go": """package main

var Config map[string]string

func init() {
    Config = make(map[string]string)
    Config["env"] = "development"
}
""",
            "main.go": """package main

func main() {
    println(Config["env"])
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedMainFunc_12345() {
    println("garbage_marker_12345")
}

func AnotherUnused_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "config.go": """package main

import "os"

var Config map[string]string

func init() {
    Config = make(map[string]string)
    Config["env"] = os.Getenv("APP_ENV")
    if Config["env"] == "" {
        Config["env"] = "development"
    }
}
""",
        },
        must_include=["Config", "init", "APP_ENV"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Read env from environment",
    ),
    DiffTestCase(
        name="go_009_defer_cleanup",
        initial_files={
            "cleanup.go": """package main

func cleanup() {
    println("Cleanup resources")
}
""",
            "handler.go": """package main

func process() {
    defer cleanup()
    println("Processing")
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedCleanup_12345() {
    println("garbage_marker_12345")
}

func UnusedHandler_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "cleanup.go": """package main

import "log"

func cleanup() {
    log.Println("Cleanup resources")
    flushLogs()
}

func flushLogs() {
    log.Println("Flushing logs")
}
""",
        },
        must_include=["cleanup", "flushLogs"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Enhanced cleanup with logging",
    ),
    DiffTestCase(
        name="go_017_variadic_function",
        initial_files={
            "logger.go": """package main

import "fmt"

func Log(format string, args ...interface{}) {
    fmt.Printf(format, args...)
}
""",
            "app.go": """package main

func Run() {
    println("running")
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedApp_12345() {
    println("garbage_marker_12345")
}

func AnotherUnused_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "app.go": """package main

func Run() {
    Log("Starting app: %s, version: %d", "myapp", 1)
    Log("Config loaded")
}
""",
        },
        must_include=["Log", "Starting app"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Use variadic Log function",
    ),
    DiffTestCase(
        name="go_018_function_type",
        initial_files={
            "types.go": """package main

type Handler func(req Request) Response
type Middleware func(Handler) Handler

type Request struct {
    Path string
}

type Response struct {
    Status int
}
""",
            "router.go": """package main

func NewRouter() *Router {
    return &Router{}
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedTypes_12345() {
    println("garbage_marker_12345")
}

func UnusedRouter_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "router.go": """package main

type Router struct {
    middleware []Middleware
}

func NewRouter() *Router {
    return &Router{}
}

func (r *Router) Use(m Middleware) {
    r.middleware = append(r.middleware, m)
}

func (r *Router) Handle(h Handler) Handler {
    for i := len(r.middleware) - 1; i >= 0; i-- {
        h = r.middleware[i](h)
    }
    return h
}
""",
        },
        must_include=["Router", "Use", "Handle", "Middleware"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add middleware support",
    ),
    DiffTestCase(
        name="go_019_closure",
        initial_files={
            "counter.go": """package main

type Counter struct {
    value int
}
""",
            "factory.go": """package main

func placeholder() {}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedCounter_12345() {
    println("garbage_marker_12345")
}

func UnusedFactory_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "factory.go": """package main

func NewCounter() func() int {
    count := 0
    return func() int {
        count++
        return count
    }
}

func NewAdder(base int) func(int) int {
    return func(n int) int {
        return base + n
    }
}
""",
        },
        must_include=["NewCounter", "NewAdder"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add closure factories",
    ),
    DiffTestCase(
        name="go_020_method_value",
        initial_files={
            "notifier.go": """package main

type Notifier struct {
    prefix string
}

func (n *Notifier) Notify(msg string) {
    println(n.prefix + ": " + msg)
}

func (n *Notifier) Alert(msg string) {
    println("ALERT: " + n.prefix + ": " + msg)
}
""",
            "dispatcher.go": """package main

func Dispatch() {}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedNotifier_12345() {
    println("garbage_marker_12345")
}

func UnusedDispatcher_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "dispatcher.go": """package main

type Callback func(string)

func Dispatch(callbacks []Callback, msg string) {
    for _, cb := range callbacks {
        cb(msg)
    }
}

func SetupNotifications() {
    n := &Notifier{prefix: "App"}
    callbacks := []Callback{
        n.Notify,
        n.Alert,
    }
    Dispatch(callbacks, "Hello")
}
""",
        },
        must_include=["Dispatch", "SetupNotifications", "Callback"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Use method values as callbacks",
    ),
]


CONCURRENCY_CASES = [
    DiffTestCase(
        name="go_010_goroutine_function",
        initial_files={
            "worker.go": """package main

func worker(id int, jobs <-chan int) {
    for j := range jobs {
        println("Worker", id, "processing job", j)
    }
}
""",
            "main.go": """package main

func main() {
    jobs := make(chan int, 100)
    go worker(1, jobs)
    go worker(2, jobs)
    for j := 0; j < 10; j++ {
        jobs <- j
    }
    close(jobs)
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedWorker_12345() {
    println("garbage_marker_12345")
}

func UnusedMain_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "worker.go": """package main

import "time"

func worker(id int, jobs <-chan int, results chan<- int) {
    for j := range jobs {
        time.Sleep(time.Millisecond * 100)
        results <- j * 2
    }
}
""",
        },
        must_include=["worker", "results"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add results channel to worker",
    ),
    DiffTestCase(
        name="go_011_channel_receive",
        initial_files={
            "producer.go": """package main

func produce(ch chan<- int) {
    for i := 0; i < 10; i++ {
        ch <- i
    }
    close(ch)
}
""",
            "consumer.go": """package main

func consume(ch <-chan int) {
    for v := range ch {
        println(v)
    }
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedProducer_12345() {
    println("garbage_marker_12345")
}

func UnusedConsumer_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "producer.go": """package main

import "time"

func produce(ch chan<- int) {
    for i := 0; i < 10; i++ {
        time.Sleep(time.Millisecond * 50)
        ch <- i * 2
    }
    close(ch)
}
""",
        },
        must_include=["produce", "chan<- int"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Double values in producer",
    ),
    DiffTestCase(
        name="go_012_select_case",
        initial_files={
            "multiplexer.go": """package main

func multiplex(ch1, ch2 <-chan int, out chan<- int) {
    for {
        select {
        case v := <-ch1:
            out <- v
        case v := <-ch2:
            out <- v
        }
    }
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedMux_12345() {
    println("garbage_marker_12345")
}

func AnotherUnused_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "multiplexer.go": """package main

import "time"

func multiplex(ch1, ch2 <-chan int, out chan<- int, done <-chan struct{}) {
    for {
        select {
        case v := <-ch1:
            out <- v
        case v := <-ch2:
            out <- v
        case <-done:
            return
        case <-time.After(time.Second * 5):
            return
        }
    }
}
""",
        },
        must_include=["multiplex", "select", "done"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add done channel and timeout",
    ),
    DiffTestCase(
        name="go_013_context_with_cancel",
        initial_files={
            "service.go": """package main

import "context"

func longOperation(ctx context.Context) error {
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
        return nil
    }
}
""",
            "handler.go": """package main

import "context"

func handle() {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()
    longOperation(ctx)
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedService_12345() {
    println("garbage_marker_12345")
}

func UnusedHandler_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "service.go": """package main

import (
    "context"
    "time"
)

func longOperation(ctx context.Context) error {
    ticker := time.NewTicker(time.Second)
    defer ticker.Stop()

    for {
        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-ticker.C:
            if err := doWork(); err != nil {
                return err
            }
        }
    }
}

func doWork() error {
    return nil
}
""",
        },
        must_include=["longOperation", "doWork", "ticker"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add ticker-based work loop",
    ),
]


ERROR_CASES = [
    DiffTestCase(
        name="go_014_errors_is",
        initial_files={
            "errors.go": """package main

import "errors"

var ErrNotFound = errors.New("not found")
var ErrUnauthorized = errors.New("unauthorized")
""",
            "handler.go": """package main

import "errors"

func handleError(err error) string {
    if errors.Is(err, ErrNotFound) {
        return "404"
    }
    if errors.Is(err, ErrUnauthorized) {
        return "401"
    }
    return "500"
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedErrors_12345() {
    println("garbage_marker_12345")
}

func UnusedHandler_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "errors.go": """package main

import "errors"

var ErrNotFound = errors.New("not found")
var ErrUnauthorized = errors.New("unauthorized")
var ErrForbidden = errors.New("forbidden")
var ErrConflict = errors.New("conflict")
""",
        },
        must_include=["ErrForbidden", "ErrConflict"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add more error types",
    ),
    DiffTestCase(
        name="go_016_error_wrapping",
        initial_files={
            "errors.go": """package main

import "errors"

var ErrNotFound = errors.New("not found")
var ErrPermission = errors.New("permission denied")
""",
            "service.go": """package main

func GetUser(id int) (*User, error) {
    return nil, nil
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedErrors_12345() {
    println("garbage_marker_12345")
}

func UnusedService_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "service.go": """package main

import "fmt"

func GetUser(id int) (*User, error) {
    user, err := repo.Find(id)
    if err != nil {
        return nil, fmt.Errorf("GetUser(%d): %w", id, err)
    }
    return user, nil
}

func GetUserOrDefault(id int) *User {
    user, err := GetUser(id)
    if errors.Is(err, ErrNotFound) {
        return &User{Name: "Guest"}
    }
    return user
}
""",
        },
        must_include=["GetUser", "GetUserOrDefault", "Errorf"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add error wrapping",
    ),
    DiffTestCase(
        name="go_033_error_interface",
        initial_files={
            "errors.go": """package main

import "errors"

var ErrNotFound = errors.New("not found")
""",
            "service.go": """package main

func Find(id int) (interface{}, error) {
    return nil, ErrNotFound
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedErrors_12345() {
    println("garbage_marker_12345")
}

func UnusedService_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "errors.go": """package main

import "fmt"

type AppError struct {
    Code    int
    Message string
    Err     error
}

func (e *AppError) Error() string {
    if e.Err != nil {
        return fmt.Sprintf("[%d] %s: %v", e.Code, e.Message, e.Err)
    }
    return fmt.Sprintf("[%d] %s", e.Code, e.Message)
}

func (e *AppError) Unwrap() error {
    return e.Err
}

func NewNotFoundError(resource string) *AppError {
    return &AppError{Code: 404, Message: resource + " not found"}
}

func NewValidationError(msg string, err error) *AppError {
    return &AppError{Code: 400, Message: msg, Err: err}
}
""",
        },
        must_include=["AppError", "Error()", "Unwrap"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add custom error type",
    ),
]


DEPENDENCY_INJECTION_CASES = [
    DiffTestCase(
        name="go_015_wire_build",
        initial_files={
            "wire.go": """//go:build wireinject
// +build wireinject

package main

import "github.com/google/wire"

func InitializeApp() *App {
    wire.Build(NewApp, NewDB, NewConfig)
    return nil
}
""",
            "providers.go": """package main

type App struct {
    db *DB
}

type DB struct {
    config *Config
}

type Config struct {
    DSN string
}

func NewApp(db *DB) *App {
    return &App{db: db}
}

func NewDB(config *Config) *DB {
    return &DB{config: config}
}

func NewConfig() *Config {
    return &Config{DSN: "postgres://localhost/db"}
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedWire_12345() {
    println("garbage_marker_12345")
}

func UnusedProvider_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "providers.go": """package main

type App struct {
    db     *DB
    cache  *Cache
}

type DB struct {
    config *Config
}

type Config struct {
    DSN      string
    CacheURL string
}

type Cache struct {
    url string
}

func NewApp(db *DB, cache *Cache) *App {
    return &App{db: db, cache: cache}
}

func NewDB(config *Config) *DB {
    return &DB{config: config}
}

func NewConfig() *Config {
    return &Config{
        DSN:      "postgres://localhost/db",
        CacheURL: "redis://localhost:6379",
    }
}

func NewCache(config *Config) *Cache {
    return &Cache{url: config.CacheURL}
}
""",
        },
        must_include=["Cache", "NewCache", "CacheURL"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Cache provider",
    ),
]


TYPE_SYSTEM_CASES = [
    DiffTestCase(
        name="go_021_type_assertion",
        initial_files={
            "types.go": """package main

type Reader interface {
    Read() string
}

type Writer interface {
    Write(s string)
}

type FileHandler struct {
    path string
}

func (f *FileHandler) Read() string {
    return "content"
}

func (f *FileHandler) Write(s string) {}
""",
            "processor.go": """package main

func Process(r Reader) {}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedTypes_12345() {
    println("garbage_marker_12345")
}

func UnusedProcessor_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "processor.go": """package main

func Process(r Reader) {
    content := r.Read()

    if w, ok := r.(Writer); ok {
        w.Write("processed: " + content)
    }

    if fh, ok := r.(*FileHandler); ok {
        println("File path:", fh.path)
    }
}
""",
        },
        must_include=["Process", "Writer", "FileHandler"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add type assertion",
    ),
    DiffTestCase(
        name="go_022_type_switch",
        initial_files={
            "shapes.go": """package main

type Shape interface {
    Area() float64
}

type Circle struct {
    Radius float64
}

func (c Circle) Area() float64 {
    return 3.14 * c.Radius * c.Radius
}

type Rectangle struct {
    Width, Height float64
}

func (r Rectangle) Area() float64 {
    return r.Width * r.Height
}

type Triangle struct {
    Base, Height float64
}

func (t Triangle) Area() float64 {
    return 0.5 * t.Base * t.Height
}
""",
            "describe.go": """package main

func Describe(s Shape) string {
    return "shape"
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedShapes_12345() {
    println("garbage_marker_12345")
}

func UnusedDescribe_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "describe.go": """package main

import "fmt"

func Describe(s Shape) string {
    switch v := s.(type) {
    case Circle:
        return fmt.Sprintf("Circle with radius %.2f", v.Radius)
    case Rectangle:
        return fmt.Sprintf("Rectangle %.2fx%.2f", v.Width, v.Height)
    case Triangle:
        return fmt.Sprintf("Triangle base=%.2f height=%.2f", v.Base, v.Height)
    default:
        return "Unknown shape"
    }
}
""",
        },
        must_include=["Describe", "Circle", "Rectangle", "Triangle"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add type switch",
    ),
    DiffTestCase(
        name="go_027_custom_type",
        initial_files={
            "types.go": """package main

type UserID int64
type Status string

const (
    StatusPending Status = "pending"
    StatusActive  Status = "active"
    StatusClosed  Status = "closed"
)

func (s Status) IsActive() bool {
    return s == StatusActive
}
""",
            "service.go": """package main

func GetUserStatus(id int) string {
    return "unknown"
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedTypes_12345() {
    println("garbage_marker_12345")
}

func UnusedService_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "service.go": """package main

func GetUserStatus(id UserID) Status {
    return StatusActive
}

func ProcessActive(id UserID) {
    status := GetUserStatus(id)
    if status.IsActive() {
        println("User is active")
    }
}
""",
        },
        must_include=["GetUserStatus", "UserID", "Status"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Use custom types",
    ),
]


PANIC_RECOVERY_CASES = [
    DiffTestCase(
        name="go_023_recover",
        initial_files={
            "handler.go": """package main

func HandleRequest() {
    println("handling request")
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedHandler_12345() {
    println("garbage_marker_12345")
}

func AnotherUnused_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "handler.go": """package main

import "log"

func HandleRequest() {
    defer func() {
        if r := recover(); r != nil {
            log.Printf("Recovered from panic: %v", r)
        }
    }()

    processRequest()
}

func processRequest() {
    panic("something went wrong")
}
""",
        },
        must_include=["HandleRequest", "recover", "processRequest"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add panic recovery",
    ),
]


BUILD_TAG_CASES = [
    DiffTestCase(
        name="go_024_build_tags",
        initial_files={
            "platform.go": """package main

func GetPlatform() string {
    return "unknown"
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedPlatform_12345() {
    println("garbage_marker_12345")
}

func AnotherUnused_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "platform_linux.go": """//go:build linux

package main

func GetPlatform() string {
    return "linux"
}

func LinuxSpecific() {
    println("Linux only")
}
""",
            "platform_darwin.go": """//go:build darwin

package main

func GetPlatform() string {
    return "darwin"
}

func DarwinSpecific() {
    println("macOS only")
}
""",
        },
        must_include=["GetPlatform"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add platform-specific files",
    ),
]


STRUCT_PATTERN_CASES = [
    DiffTestCase(
        name="go_025_struct_embedding",
        initial_files={
            "base.go": """package main

type Base struct {
    ID        int
    CreatedAt string
}

func (b *Base) GetID() int {
    return b.ID
}

type Timestamps struct {
    CreatedAt string
    UpdatedAt string
}
""",
            "user.go": """package main

type User struct {
    Name string
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedBase_12345() {
    println("garbage_marker_12345")
}

func UnusedUser_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "user.go": """package main

type User struct {
    Base
    Timestamps
    Name  string
    Email string
}

func NewUser(name, email string) *User {
    return &User{
        Base:  Base{ID: 1},
        Name:  name,
        Email: email,
    }
}

func (u *User) Display() string {
    return u.Name + " (ID: " + string(u.GetID()) + ")"
}
""",
        },
        must_include=["User", "Base", "Timestamps", "NewUser"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Embed Base and Timestamps in User",
    ),
    DiffTestCase(
        name="go_026_struct_tags",
        initial_files={
            "models.go": """package main

type User struct {
    ID   int
    Name string
}
""",
            "api.go": """package main

import "encoding/json"

func SerializeUser(u *User) ([]byte, error) {
    return json.Marshal(u)
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedModels_12345() {
    println("garbage_marker_12345")
}

func UnusedApi_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "models.go": """package main

type User struct {
    ID        int    `json:"id" db:"user_id"`
    Name      string `json:"name" db:"full_name" validate:"required"`
    Email     string `json:"email,omitempty" validate:"email"`
    CreatedAt string `json:"created_at" db:"created_at"`
}
""",
        },
        must_include=["User", "json:", "db:"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add struct tags",
    ),
]


GENERICS_CASES = [
    DiffTestCase(
        name="go_029_generic_type",
        initial_files={
            "container.go": """package main

type IntSlice []int

func (s IntSlice) First() int {
    if len(s) == 0 {
        return 0
    }
    return s[0]
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedContainer_12345() {
    println("garbage_marker_12345")
}

func AnotherUnused_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "container.go": """package main

type Slice[T any] []T

func (s Slice[T]) First() (T, bool) {
    var zero T
    if len(s) == 0 {
        return zero, false
    }
    return s[0], true
}

func (s Slice[T]) Map(fn func(T) T) Slice[T] {
    result := make(Slice[T], len(s))
    for i, v := range s {
        result[i] = fn(v)
    }
    return result
}

type Ordered interface {
    ~int | ~int64 | ~float64 | ~string
}

func Max[T Ordered](a, b T) T {
    if a > b {
        return a
    }
    return b
}
""",
        },
        must_include=["Slice[T]", "Ordered", "Max[T"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add generic types",
    ),
]


CONSTRUCTOR_PATTERN_CASES = [
    DiffTestCase(
        name="go_030_constructor_pattern",
        initial_files={
            "config.go": """package main

type Config struct {
    Host    string
    Port    int
    Timeout int
}
""",
            "server.go": """package main

type Server struct {
    config Config
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedConfig_12345() {
    println("garbage_marker_12345")
}

func UnusedServer_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "server.go": """package main

import "fmt"

type Server struct {
    config *Config
    logger Logger
}

func NewServer(config *Config, logger Logger) (*Server, error) {
    if config == nil {
        return nil, fmt.Errorf("config is required")
    }
    if config.Port <= 0 {
        config.Port = 8080
    }
    return &Server{
        config: config,
        logger: logger,
    }, nil
}

func (s *Server) Start() error {
    s.logger.Info("Starting server on port", s.config.Port)
    return nil
}
""",
        },
        must_include=["NewServer", "Server", "Config"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add constructor",
    ),
    DiffTestCase(
        name="go_031_option_pattern",
        initial_files={
            "client.go": """package main

type Client struct {
    baseURL string
    timeout int
}

func NewClient(baseURL string) *Client {
    return &Client{baseURL: baseURL}
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedClient_12345() {
    println("garbage_marker_12345")
}

func AnotherUnused_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "client.go": """package main

import "time"

type Client struct {
    baseURL   string
    timeout   time.Duration
    retries   int
    userAgent string
}

type Option func(*Client)

func WithTimeout(d time.Duration) Option {
    return func(c *Client) {
        c.timeout = d
    }
}

func WithRetries(n int) Option {
    return func(c *Client) {
        c.retries = n
    }
}

func WithUserAgent(ua string) Option {
    return func(c *Client) {
        c.userAgent = ua
    }
}

func NewClient(baseURL string, opts ...Option) *Client {
    c := &Client{
        baseURL: baseURL,
        timeout: 30 * time.Second,
        retries: 3,
    }
    for _, opt := range opts {
        opt(c)
    }
    return c
}
""",
        },
        must_include=["Client", "Option", "WithTimeout", "WithRetries"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add functional options",
    ),
]


STD_INTERFACE_CASES = [
    DiffTestCase(
        name="go_032_stringer_interface",
        initial_files={
            "status.go": """package main

type Status int

const (
    StatusUnknown Status = iota
    StatusPending
    StatusRunning
    StatusCompleted
    StatusFailed
)
""",
            "job.go": """package main

import "fmt"

type Job struct {
    ID     int
    Status Status
}

func (j *Job) Print() {
    fmt.Printf("Job %d: %d\n", j.ID, j.Status)
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedStatus_12345() {
    println("garbage_marker_12345")
}

func UnusedJob_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "status.go": """package main

type Status int

const (
    StatusUnknown Status = iota
    StatusPending
    StatusRunning
    StatusCompleted
    StatusFailed
)

func (s Status) String() string {
    switch s {
    case StatusPending:
        return "pending"
    case StatusRunning:
        return "running"
    case StatusCompleted:
        return "completed"
    case StatusFailed:
        return "failed"
    default:
        return "unknown"
    }
}
""",
            "job.go": """package main

import "fmt"

type Job struct {
    ID     int
    Status Status
}

func (j *Job) Print() {
    fmt.Printf("Job %d: %s\n", j.ID, j.Status)
}
""",
        },
        must_include=["Status", "String()"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Stringer implementation",
    ),
    DiffTestCase(
        name="go_034_json_marshaler",
        initial_files={
            "types.go": """package main

import "time"

type Event struct {
    Name      string
    Timestamp time.Time
}
""",
            "api.go": """package main

import "encoding/json"

func SerializeEvent(e *Event) ([]byte, error) {
    return json.Marshal(e)
}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedTypes_12345() {
    println("garbage_marker_12345")
}

func UnusedApi_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "types.go": """package main

import (
    "encoding/json"
    "time"
)

type Event struct {
    Name      string
    Timestamp time.Time
}

func (e Event) MarshalJSON() ([]byte, error) {
    type Alias Event
    return json.Marshal(&struct {
        Alias
        Timestamp string `json:"timestamp"`
    }{
        Alias:     Alias(e),
        Timestamp: e.Timestamp.Format(time.RFC3339),
    })
}

func (e *Event) UnmarshalJSON(data []byte) error {
    type Alias Event
    aux := &struct {
        *Alias
        Timestamp string `json:"timestamp"`
    }{
        Alias: (*Alias)(e),
    }
    if err := json.Unmarshal(data, &aux); err != nil {
        return err
    }
    t, err := time.Parse(time.RFC3339, aux.Timestamp)
    if err != nil {
        return err
    }
    e.Timestamp = t
    return nil
}
""",
        },
        must_include=["MarshalJSON", "UnmarshalJSON", "Event"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add custom JSON marshaling",
    ),
]


HTTP_CASES = [
    DiffTestCase(
        name="go_035_http_handler",
        initial_files={
            "handlers.go": """package main

type UserHandler struct{}
""",
            "router.go": """package main

import "net/http"

func SetupRoutes(mux *http.ServeMux) {}
""",
            "unrelated/garbage.go": """package unrelated

func UnusedHandlers_12345() {
    println("garbage_marker_12345")
}

func UnusedRouter_67890() {
    println("unused_marker_67890")
}
""",
        },
        changed_files={
            "handlers.go": """package main

import (
    "encoding/json"
    "net/http"
)

type UserHandler struct {
    service *UserService
}

func NewUserHandler(svc *UserService) *UserHandler {
    return &UserHandler{service: svc}
}

func (h *UserHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    switch r.Method {
    case http.MethodGet:
        h.handleGet(w, r)
    case http.MethodPost:
        h.handlePost(w, r)
    default:
        http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
    }
}

func (h *UserHandler) handleGet(w http.ResponseWriter, r *http.Request) {
    users := h.service.GetAll()
    json.NewEncoder(w).Encode(users)
}

func (h *UserHandler) handlePost(w http.ResponseWriter, r *http.Request) {
    var user User
    if err := json.NewDecoder(r.Body).Decode(&user); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    h.service.Create(&user)
    w.WriteHeader(http.StatusCreated)
}
""",
            "router.go": """package main

import "net/http"

func SetupRoutes(mux *http.ServeMux, userHandler *UserHandler) {
    mux.Handle("/users", userHandler)
    mux.Handle("/users/", userHandler)
}
""",
        },
        must_include=["UserHandler", "ServeHTTP", "handleGet", "handlePost"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add HTTP handlers",
    ),
]


ALL_GO_CASES = (
    BASIC_CASES
    + INTERFACE_CASES
    + DIRECTIVE_CASES
    + MODULE_CASES
    + FUNCTION_CASES
    + CONCURRENCY_CASES
    + ERROR_CASES
    + DEPENDENCY_INJECTION_CASES
    + TYPE_SYSTEM_CASES
    + PANIC_RECOVERY_CASES
    + BUILD_TAG_CASES
    + STRUCT_PATTERN_CASES
    + GENERICS_CASES
    + CONSTRUCTOR_PATTERN_CASES
    + STD_INTERFACE_CASES
    + HTTP_CASES
)


@pytest.fixture
def diff_test_runner(tmp_path):
    return DiffTestRunner(tmp_path)


@pytest.mark.parametrize("case", ALL_GO_CASES, ids=lambda c: c.name)
def test_go_cases(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
