from __future__ import annotations

from .config import CODE_EXTENSIONS, CONFIG_EXTENSIONS, DOC_EXTENSIONS

CONFIG_KEY_COMMON_PREFIXES = frozenset({"default", "max", "min", "smtp", "http", "https", "api", "db", "app", "allowed"})

__all__ = [
    "CODE_EXTENSIONS",
    "CONFIG_EXTENSIONS",
    "CONFIG_KEY_COMMON_PREFIXES",
    "DOC_EXTENSIONS",
    "expand_config_key",
]


def expand_config_key(key: str) -> set[str]:
    expanded: set[str] = {key}
    parts = key.split("_")
    for part in parts:
        if len(part) >= 3:
            expanded.add(part)
    for prefix in CONFIG_KEY_COMMON_PREFIXES:
        if key.startswith(prefix + "_") and len(key) > len(prefix) + 1:
            stripped = key[len(prefix) + 1 :]
            expanded.add(stripped)
            for sub in stripped.split("_"):
                if len(sub) >= 3:
                    expanded.add(sub)
    return expanded
