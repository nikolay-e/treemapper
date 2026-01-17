from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class JsFragmentInfo:
    defines: frozenset[str]
    references: frozenset[str]
    calls: frozenset[str]
    type_refs: frozenset[str]
    imports: frozenset[str]
    exports: frozenset[str]


_EMPTY_INFO = JsFragmentInfo(frozenset(), frozenset(), frozenset(), frozenset(), frozenset(), frozenset())

_NAMED_IMPORT_RE = re.compile(r"import\s*\{([^}]+)\}\s*from\s*['\"]([^'\"]+)['\"]", re.MULTILINE)
_DEFAULT_IMPORT_RE = re.compile(r"import\s+(\w+)\s+from\s*['\"]([^'\"]+)['\"]", re.MULTILINE)
_NAMESPACE_IMPORT_RE = re.compile(r"import\s*\*\s*as\s+(\w+)\s+from\s*['\"]([^'\"]+)['\"]", re.MULTILINE)
_SIDE_EFFECT_IMPORT_RE = re.compile(r"import\s*['\"]([^'\"]+)['\"]", re.MULTILINE)
_DYNAMIC_IMPORT_RE = re.compile(r"import\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", re.MULTILINE)
_TYPE_IMPORT_RE = re.compile(r"import\s+type\s+\{([^}]+)\}\s*from\s*['\"]([^'\"]+)['\"]", re.MULTILINE)
_REQUIRE_RE = re.compile(
    r"(?:const|let|var)\s+(?:\{([^}]+)\}|(\w+))\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
    re.MULTILINE,
)

_NAMED_EXPORT_RE = re.compile(r"export\s+(?:const|let|var|function\*?|class|async\s+function)\s+(\w+)", re.MULTILINE)
_DEFAULT_EXPORT_RE = re.compile(r"export\s+default\s+(?:(?:class|function\*?|async\s+function)\s+)?(\w+)?", re.MULTILINE)
_EXPORT_LIST_RE = re.compile(r"export\s*\{([^}]+)\}", re.MULTILINE)
_REEXPORT_RE = re.compile(r"export\s*\{([^}]*)\}\s*from\s*['\"]([^'\"]+)['\"]", re.MULTILINE)
_EXPORT_ALL_RE = re.compile(r"export\s*\*\s*from\s*['\"]([^'\"]+)['\"]", re.MULTILINE)

_FUNCTION_DECL_RE = re.compile(r"function\s+(\w+)\s*\(", re.MULTILINE)
_ASYNC_FUNCTION_RE = re.compile(r"async\s+function\s+(\w+)\s*\(", re.MULTILINE)
_ARROW_FUNCTION_RE = re.compile(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>", re.MULTILINE)
_CLASS_RE = re.compile(
    r"class\s+(\w+)(?:\s+extends\s+([\w.]+))?(?:\s+implements\s+([\w,\s]+))?\s*\{",
    re.MULTILINE,
)

_CALL_EXPR_RE = re.compile(r"\b(\w+)\s*\(", re.MULTILINE)
_MEMBER_CALL_RE = re.compile(r"\.(\w+)\s*\(", re.MULTILINE)
_NEW_EXPR_RE = re.compile(r"new\s+(\w+)\s*\(", re.MULTILINE)
_OPTIONAL_CHAIN_RE = re.compile(r"\?\.\s*(\w+)", re.MULTILINE)

_TYPE_ANNOTATION_RE = re.compile(r":\s*([A-Z]\w+)(?:<[^>]+>)?", re.MULTILINE)
_GENERIC_TYPE_RE = re.compile(r"<\s*([A-Z]\w+)(?:\s*,\s*([A-Z]\w+))*\s*>", re.MULTILINE)
_EXTENDS_TYPE_RE = re.compile(r"extends\s+([A-Z]\w+)", re.MULTILINE)
_IMPLEMENTS_TYPE_RE = re.compile(r"implements\s+([\w,\s]+)", re.MULTILINE)
_TYPE_ALIAS_RE = re.compile(r"type\s+(\w+)(?:<[^>]+>)?\s*=", re.MULTILINE)
_INTERFACE_RE = re.compile(r"interface\s+(\w+)(?:<[^>]+>)?(?:\s+extends\s+([\w,\s]+))?\s*\{", re.MULTILINE)
_RETURN_TYPE_RE = re.compile(r"\)\s*:\s*([A-Z]\w+)(?:<[^>]+>)?", re.MULTILINE)

_UTILITY_TYPES = frozenset(
    [
        "Partial",
        "Required",
        "Readonly",
        "Record",
        "Pick",
        "Omit",
        "Exclude",
        "Extract",
        "NonNullable",
        "Parameters",
        "ConstructorParameters",
        "ReturnType",
        "InstanceType",
        "ThisParameterType",
        "OmitThisParameter",
        "ThisType",
        "Uppercase",
        "Lowercase",
        "Capitalize",
        "Uncapitalize",
        "Awaited",
        "Promise",
        "Array",
        "Map",
        "Set",
        "WeakMap",
        "WeakSet",
    ]
)

_IDENT_RE = re.compile(r"\b([A-Za-z_$][A-Za-z0-9_$]*)\b")

_JS_KEYWORDS = frozenset(
    [
        "async",
        "await",
        "break",
        "case",
        "catch",
        "class",
        "const",
        "continue",
        "debugger",
        "default",
        "delete",
        "do",
        "else",
        "enum",
        "export",
        "extends",
        "false",
        "finally",
        "for",
        "from",
        "function",
        "if",
        "implements",
        "import",
        "in",
        "instanceof",
        "interface",
        "let",
        "new",
        "null",
        "of",
        "package",
        "private",
        "protected",
        "public",
        "return",
        "static",
        "super",
        "switch",
        "this",
        "throw",
        "true",
        "try",
        "type",
        "typeof",
        "undefined",
        "var",
        "void",
        "while",
        "with",
        "yield",
        "as",
        "is",
        "keyof",
        "readonly",
        "infer",
        "never",
        "unknown",
        "any",
        "string",
        "number",
        "boolean",
        "object",
        "symbol",
        "bigint",
        "module",
        "namespace",
        "declare",
        "abstract",
        "satisfies",
    ]
)

_BUILTIN_GLOBALS = frozenset(
    [
        "console",
        "window",
        "document",
        "global",
        "process",
        "require",
        "module",
        "exports",
        "Buffer",
        "setTimeout",
        "setInterval",
        "clearTimeout",
        "clearInterval",
        "setImmediate",
        "clearImmediate",
        "JSON",
        "Math",
        "Date",
        "RegExp",
        "Error",
        "TypeError",
        "RangeError",
        "SyntaxError",
        "Object",
        "Array",
        "String",
        "Number",
        "Boolean",
        "Symbol",
        "BigInt",
        "Function",
        "Promise",
        "Proxy",
        "Reflect",
        "Map",
        "Set",
        "WeakMap",
        "WeakSet",
        "ArrayBuffer",
        "DataView",
        "Int8Array",
        "Uint8Array",
        "Float32Array",
        "Float64Array",
        "Intl",
        "fetch",
        "URL",
        "URLSearchParams",
        "Headers",
        "Request",
        "Response",
        "FormData",
        "Blob",
        "File",
        "FileReader",
        "WebSocket",
        "Worker",
        "SharedWorker",
        "MessageChannel",
        "MessagePort",
        "performance",
        "navigator",
        "location",
        "history",
        "localStorage",
        "sessionStorage",
        "indexedDB",
        "crypto",
        "TextEncoder",
        "TextDecoder",
        "atob",
        "btoa",
        "queueMicrotask",
        "structuredClone",
        "AbortController",
        "AbortSignal",
        "Event",
        "EventTarget",
        "CustomEvent",
        "Node",
        "Element",
        "HTMLElement",
        "DocumentFragment",
        "NodeList",
        "HTMLCollection",
        "MutationObserver",
        "IntersectionObserver",
        "ResizeObserver",
        "requestAnimationFrame",
        "cancelAnimationFrame",
        "getComputedStyle",
        "matchMedia",
        "addEventListener",
        "removeEventListener",
        "dispatchEvent",
        "alert",
        "confirm",
        "prompt",
        "open",
        "close",
        "print",
        "scroll",
        "scrollTo",
        "scrollBy",
        "focus",
        "blur",
        "getSelection",
    ]
)


def _extract_imports(code: str) -> tuple[frozenset[str], frozenset[str]]:
    import_sources: set[str] = set()
    imported_names: set[str] = set()

    for match in _NAMED_IMPORT_RE.finditer(code):
        names_str = match.group(1)
        source = match.group(2)
        import_sources.add(source)
        for name in names_str.split(","):
            name = name.strip()
            if " as " in name:
                name = name.split(" as ")[0].strip()
            if name and not name.startswith("type "):
                imported_names.add(name)

    for match in _DEFAULT_IMPORT_RE.finditer(code):
        imported_names.add(match.group(1))
        import_sources.add(match.group(2))

    for match in _NAMESPACE_IMPORT_RE.finditer(code):
        imported_names.add(match.group(1))
        import_sources.add(match.group(2))

    for match in _SIDE_EFFECT_IMPORT_RE.finditer(code):
        import_sources.add(match.group(1))

    for match in _DYNAMIC_IMPORT_RE.finditer(code):
        import_sources.add(match.group(1))

    for match in _TYPE_IMPORT_RE.finditer(code):
        names_str = match.group(1)
        source = match.group(2)
        import_sources.add(source)
        for name in names_str.split(","):
            name = name.strip()
            if " as " in name:
                name = name.split(" as ")[0].strip()
            if name:
                imported_names.add(name)

    for match in _REQUIRE_RE.finditer(code):
        destructured = match.group(1)
        default_name = match.group(2)
        source = match.group(3)
        import_sources.add(source)
        if destructured:
            for name in destructured.split(","):
                name = name.strip()
                if ":" in name:
                    name = name.split(":")[0].strip()
                if name:
                    imported_names.add(name)
        if default_name:
            imported_names.add(default_name)

    return frozenset(import_sources), frozenset(imported_names)


def _extract_exports(code: str) -> frozenset[str]:
    exports: set[str] = set()

    for match in _NAMED_EXPORT_RE.finditer(code):
        exports.add(match.group(1))

    for match in _DEFAULT_EXPORT_RE.finditer(code):
        name = match.group(1)
        if name:
            exports.add(name)
        exports.add("default")

    for match in _EXPORT_LIST_RE.finditer(code):
        names_str = match.group(1)
        for name in names_str.split(","):
            name = name.strip()
            if " as " in name:
                parts = name.split(" as ")
                exports.add(parts[0].strip())
                exports.add(parts[1].strip())
            elif name:
                exports.add(name)

    for match in _REEXPORT_RE.finditer(code):
        names_str = match.group(1)
        for name in names_str.split(","):
            name = name.strip()
            if " as " in name:
                exports.add(name.split(" as ")[1].strip())
            elif name:
                exports.add(name)

    return frozenset(exports)


def _extract_defines(code: str) -> frozenset[str]:
    defines: set[str] = set()

    for match in _FUNCTION_DECL_RE.finditer(code):
        defines.add(match.group(1))

    for match in _ASYNC_FUNCTION_RE.finditer(code):
        defines.add(match.group(1))

    for match in _ARROW_FUNCTION_RE.finditer(code):
        defines.add(match.group(1))

    for match in _CLASS_RE.finditer(code):
        defines.add(match.group(1))

    for match in _TYPE_ALIAS_RE.finditer(code):
        defines.add(match.group(1))

    for match in _INTERFACE_RE.finditer(code):
        defines.add(match.group(1))

    return frozenset(defines)


def _extract_calls(code: str) -> frozenset[str]:
    calls: set[str] = set()

    for match in _CALL_EXPR_RE.finditer(code):
        name = match.group(1)
        if name not in _JS_KEYWORDS and name not in _BUILTIN_GLOBALS:
            calls.add(name)

    for match in _MEMBER_CALL_RE.finditer(code):
        calls.add(match.group(1))

    for match in _NEW_EXPR_RE.finditer(code):
        name = match.group(1)
        if name not in _BUILTIN_GLOBALS:
            calls.add(name)

    for match in _OPTIONAL_CHAIN_RE.finditer(code):
        calls.add(match.group(1))

    return frozenset(calls)


def _extract_type_refs(code: str) -> frozenset[str]:
    type_refs: set[str] = set()

    for match in _TYPE_ANNOTATION_RE.finditer(code):
        type_name = match.group(1)
        if type_name not in _UTILITY_TYPES and type_name not in _BUILTIN_GLOBALS:
            type_refs.add(type_name)

    for match in _GENERIC_TYPE_RE.finditer(code):
        for group in match.groups():
            if group and group not in _UTILITY_TYPES:
                type_refs.add(group)

    for match in _EXTENDS_TYPE_RE.finditer(code):
        type_name = match.group(1)
        if type_name not in _BUILTIN_GLOBALS:
            type_refs.add(type_name)

    for match in _IMPLEMENTS_TYPE_RE.finditer(code):
        types_str = match.group(1)
        for type_name in types_str.split(","):
            type_name = type_name.strip()
            if type_name and type_name not in _BUILTIN_GLOBALS:
                type_refs.add(type_name)

    for match in _RETURN_TYPE_RE.finditer(code):
        type_name = match.group(1)
        if type_name not in _UTILITY_TYPES and type_name not in _BUILTIN_GLOBALS:
            type_refs.add(type_name)

    return frozenset(type_refs)


def _extract_references(code: str, defines: frozenset[str]) -> frozenset[str]:
    refs: set[str] = set()

    for match in _IDENT_RE.finditer(code):
        ident = match.group(1)
        if ident not in _JS_KEYWORDS and ident not in _BUILTIN_GLOBALS and ident not in defines and len(ident) >= 2:
            refs.add(ident)

    return frozenset(refs)


def analyze_javascript_fragment(code: str) -> JsFragmentInfo:
    if not code.strip():
        return _EMPTY_INFO

    import_sources, imported_names = _extract_imports(code)
    exports = _extract_exports(code)
    defines = _extract_defines(code)
    calls = _extract_calls(code)
    type_refs = _extract_type_refs(code)
    references = _extract_references(code, defines | imported_names)

    return JsFragmentInfo(
        defines=defines | exports,
        references=references,
        calls=calls,
        type_refs=type_refs,
        imports=import_sources,
        exports=exports,
    )
