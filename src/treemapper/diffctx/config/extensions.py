from __future__ import annotations

PYTHON_EXTENSIONS = frozenset({".py", ".pyi", ".pyw"})

JAVASCRIPT_EXTENSIONS = frozenset({".js", ".jsx", ".mjs", ".cjs"})

TYPESCRIPT_EXTENSIONS = frozenset({".ts", ".tsx", ".mts", ".cts"})

JS_TS_EXTENSIONS = JAVASCRIPT_EXTENSIONS | TYPESCRIPT_EXTENSIONS

GO_EXTENSIONS = frozenset({".go"})

RUST_EXTENSIONS = frozenset({".rs"})

JAVA_EXTENSIONS = frozenset({".java"})

KOTLIN_EXTENSIONS = frozenset({".kt", ".kts"})

SCALA_EXTENSIONS = frozenset({".scala"})

JVM_EXTENSIONS = JAVA_EXTENSIONS | KOTLIN_EXTENSIONS | SCALA_EXTENSIONS

C_EXTENSIONS = frozenset({".c", ".h"})

CPP_EXTENSIONS = frozenset({".cpp", ".hpp", ".cc", ".hh", ".cxx", ".hxx"})

C_FAMILY_EXTENSIONS = C_EXTENSIONS | CPP_EXTENSIONS | frozenset({".m", ".mm"})

CSHARP_EXTENSIONS = frozenset({".cs"})

FSHARP_EXTENSIONS = frozenset({".fs", ".fsx"})

DOTNET_EXTENSIONS = CSHARP_EXTENSIONS | FSHARP_EXTENSIONS

RUBY_EXTENSIONS = frozenset({".rb", ".rake", ".gemspec"})

PHP_EXTENSIONS = frozenset({".php"})

SHELL_EXTENSIONS = frozenset({".sh", ".bash", ".zsh", ".ps1"})

SWIFT_EXTENSIONS = frozenset({".swift"})

OTHER_CODE_EXTENSIONS = frozenset(
    {
        ".lua",
        ".r",
        ".jl",
        ".ex",
        ".exs",
        ".erl",
        ".hs",
        ".clj",
        ".lisp",
        ".ml",
        ".nim",
        ".v",
        ".zig",
        ".d",
        ".ada",
        ".pas",
        ".f90",
        ".f95",
        ".cob",
        ".asm",
        ".s",
        ".vhd",
        ".sv",
    }
)

CODE_EXTENSIONS = (
    PYTHON_EXTENSIONS
    | JS_TS_EXTENSIONS
    | GO_EXTENSIONS
    | RUST_EXTENSIONS
    | JVM_EXTENSIONS
    | C_FAMILY_EXTENSIONS
    | DOTNET_EXTENSIONS
    | RUBY_EXTENSIONS
    | PHP_EXTENSIONS
    | SHELL_EXTENSIONS
    | SWIFT_EXTENSIONS
    | OTHER_CODE_EXTENSIONS
)

CONFIG_EXTENSIONS = frozenset(
    {
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
        ".xml",
        ".properties",
    }
)

DOC_EXTENSIONS = frozenset(
    {
        ".md",
        ".rst",
        ".txt",
        ".adoc",
    }
)

EXTENSION_TO_LANGUAGE: dict[str, str] = {}

for ext in PYTHON_EXTENSIONS:
    EXTENSION_TO_LANGUAGE[ext] = "python"

for ext in JAVASCRIPT_EXTENSIONS:
    EXTENSION_TO_LANGUAGE[ext] = "javascript"

for ext in TYPESCRIPT_EXTENSIONS:
    EXTENSION_TO_LANGUAGE[ext] = "typescript"

for ext in GO_EXTENSIONS:
    EXTENSION_TO_LANGUAGE[ext] = "go"

for ext in RUST_EXTENSIONS:
    EXTENSION_TO_LANGUAGE[ext] = "rust"

for ext in JAVA_EXTENSIONS:
    EXTENSION_TO_LANGUAGE[ext] = "java"

for ext in KOTLIN_EXTENSIONS:
    EXTENSION_TO_LANGUAGE[ext] = "kotlin"

for ext in SCALA_EXTENSIONS:
    EXTENSION_TO_LANGUAGE[ext] = "scala"
