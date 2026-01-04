from __future__ import annotations

import keyword
from collections.abc import Iterable
from typing import ClassVar

PY_KEYWORDS: frozenset[str] = frozenset(keyword.kwlist)

_CODE_STOPWORDS: frozenset[str] = frozenset(
    {
        "todo",
        "fixme",
        "note",
        "hack",
        "xxx",
        "test",
        "tests",
        "spec",
        "mock",
        "stub",
        "tmp",
        "temp",
        "foo",
        "bar",
        "baz",
        "qux",
        "data",
        "value",
        "values",
        "result",
        "results",
        "item",
        "items",
        "element",
        "elements",
        "entry",
        "entries",
        "record",
        "records",
        "obj",
        "objs",
        "object",
        "objects",
        "name",
        "names",
        "key",
        "keys",
        "id",
        "ids",
        "index",
        "idx",
        "num",
        "count",
        "size",
        "length",
        "len",
        "type",
        "types",
        "kind",
        "kinds",
        "str",
        "int",
        "bool",
        "float",
        "list",
        "dict",
        "set",
        "tuple",
        "string",
        "number",
        "boolean",
        "array",
        "map",
        "arg",
        "args",
        "kwargs",
        "param",
        "params",
        "opt",
        "opts",
        "option",
        "options",
        "config",
        "conf",
        "cfg",
        "settings",
        "env",
        "var",
        "vars",
        "val",
        "vals",
        "ref",
        "refs",
        "ptr",
        "path",
        "paths",
        "file",
        "files",
        "dir",
        "dirs",
        "folder",
        "line",
        "lines",
        "col",
        "column",
        "row",
        "src",
        "dst",
        "source",
        "dest",
        "target",
        "origin",
        "node",
        "nodes",
        "tree",
        "root",
        "parent",
        "child",
        "children",
        "left",
        "right",
        "prev",
        "next",
        "head",
        "tail",
        "first",
        "last",
        "util",
        "utils",
        "helper",
        "helpers",
        "common",
        "handler",
        "handlers",
        "manager",
        "managers",
        "factory",
        "builder",
        "wrapper",
        "base",
        "abstract",
        "logger",
        "log",
        "debug",
        "info",
        "warn",
        "error",
        "trace",
        "ret",
        "res",
        "out",
        "output",
        "input",
        "stdin",
        "stdout",
        "err",
        "exc",
        "exception",
        "msg",
        "message",
        "text",
        "content",
        "body",
        "self",
        "cls",
        "super",
        "new",
        "del",
        "get",
        "set",
        "has",
        "is",
        "can",
        "do",
        "true",
        "false",
        "none",
        "null",
        "nil",
        "undefined",
        "run",
        "start",
        "stop",
        "main",
        "exec",
        "execute",
        "read",
        "write",
        "open",
        "close",
        "flush",
        "add",
        "remove",
        "delete",
        "update",
        "create",
        "insert",
        "load",
        "save",
        "parse",
        "format",
        "render",
        "build",
        "encode",
        "decode",
        "serialize",
        "deserialize",
        "init",
        "setup",
        "teardown",
        "cleanup",
    }
)

_DOCS_STOPWORDS: frozenset[str] = frozenset(
    {
        "the",
        "a",
        "an",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "as",
        "and",
        "or",
        "but",
        "if",
        "then",
        "else",
        "when",
        "while",
        "it",
        "its",
        "this",
        "that",
        "these",
        "those",
        "which",
        "who",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "use",
        "used",
        "using",
        "make",
        "made",
        "see",
        "also",
        "example",
        "examples",
        "note",
        "notes",
        "warning",
        "tip",
        "section",
        "chapter",
        "page",
        "figure",
        "table",
        "above",
        "below",
        "following",
        "previous",
        "next",
    }
)

_LEGAL_STOPWORDS: frozenset[str] = _DOCS_STOPWORDS | frozenset(
    {
        "article",
        "articles",
        "section",
        "sections",
        "paragraph",
        "paragraphs",
        "clause",
        "clauses",
        "pursuant",
        "hereby",
        "thereof",
        "herein",
        "whereas",
        "shall",
        "must",
        "may",
        "subject",
    }
)

_DATA_STOPWORDS: frozenset[str] = frozenset(
    {
        "id",
        "ids",
        "key",
        "keys",
        "value",
        "values",
        "name",
        "names",
        "type",
        "types",
        "data",
        "null",
        "none",
        "true",
        "false",
        "row",
        "rows",
        "column",
        "columns",
        "field",
        "fields",
        "index",
        "count",
        "total",
        "sum",
        "avg",
        "min",
        "max",
    }
)

CODE_STOPWORDS: frozenset[str] = _CODE_STOPWORDS


class TokenProfile:
    CODE = "code"
    DOCS = "docs"
    LEGAL = "legal"
    DATA = "data"
    GENERIC = "generic"

    _PROFILES: ClassVar[dict[str, tuple[frozenset[str], int]]] = {
        CODE: (_CODE_STOPWORDS | PY_KEYWORDS, 3),
        DOCS: (_DOCS_STOPWORDS, 3),
        LEGAL: (_LEGAL_STOPWORDS, 4),
        DATA: (_DATA_STOPWORDS, 2),
        GENERIC: (_CODE_STOPWORDS, 3),
    }

    @classmethod
    def get_stopwords(cls, profile: str) -> frozenset[str]:
        return cls._PROFILES.get(profile, cls._PROFILES[cls.GENERIC])[0]

    @classmethod
    def get_min_len(cls, profile: str) -> int:
        return cls._PROFILES.get(profile, cls._PROFILES[cls.GENERIC])[1]

    @classmethod
    def from_path(cls, path_str: str) -> str:
        from pathlib import Path

        p = Path(path_str)
        suffix = p.suffix.lower()
        name_lower = p.name.lower()

        code_exts = {
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".go",
            ".rs",
            ".java",
            ".rb",
            ".php",
            ".c",
            ".cpp",
            ".h",
            ".cs",
            ".kt",
            ".swift",
        }
        if suffix in code_exts:
            return cls.CODE

        doc_exts = {".md", ".markdown", ".rst", ".txt", ".adoc", ".tex"}
        if suffix in doc_exts:
            return cls.DOCS

        data_exts = {".csv", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".xml", ".ini", ".env"}
        if suffix in data_exts:
            return cls.DATA

        legal_names = {"license", "licence", "legal", "terms", "agreement", "contract", "policy", "privacy", "tos", "eula"}
        stem = p.stem.lower()
        if stem in legal_names or any(lw in name_lower for lw in ("license", "legal", "terms")):
            return cls.LEGAL

        return cls.GENERIC


def is_reasonable_ident(ident: str, *, min_len: int = 3, profile: str = "code") -> bool:
    if not ident or len(ident) < min_len:
        return False
    low = ident.lower()
    stopwords = TokenProfile.get_stopwords(profile)
    if low in stopwords:
        return False
    if low.isdigit():
        return False
    return True


def filter_idents(idents: Iterable[str], *, min_len: int = 3, profile: str = "code") -> list[str]:
    return [s for s in idents if is_reasonable_ident(s, min_len=min_len, profile=profile)]
