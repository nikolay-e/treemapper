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
    if len(key) < 6:
        return set()
    return {key}
