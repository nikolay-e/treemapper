from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .stopwords import TokenProfile

_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


@dataclass(frozen=True)
class FragmentId:
    path: Path
    start_line: int
    end_line: int

    def __str__(self) -> str:
        return f"{self.path}:{self.start_line}-{self.end_line}"

    def __hash__(self) -> int:
        return hash((str(self.path), self.start_line, self.end_line))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FragmentId):
            return NotImplemented
        return str(self.path) == str(other.path) and self.start_line == other.start_line and self.end_line == other.end_line

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, FragmentId):
            return NotImplemented
        return (str(self.path), self.start_line, self.end_line) < (str(other.path), other.start_line, other.end_line)


@dataclass
class Fragment:
    id: FragmentId
    kind: str
    content: str
    identifiers: frozenset[str] = field(default_factory=frozenset)
    token_count: int = 0

    @property
    def path(self) -> Path:
        return self.id.path

    @property
    def start_line(self) -> int:
        return self.id.start_line

    @property
    def end_line(self) -> int:
        return self.id.end_line

    @property
    def line_count(self) -> int:
        return self.end_line - self.start_line + 1


@dataclass(frozen=True)
class DiffHunk:
    path: Path
    new_start: int
    new_len: int
    old_start: int = 0
    old_len: int = 0

    @property
    def end_line(self) -> int:
        if self.new_len == 0:
            return self.new_start
        return self.new_start + self.new_len - 1

    @property
    def is_deletion(self) -> bool:
        return self.new_len == 0 and self.old_len > 0

    @property
    def is_addition(self) -> bool:
        return self.old_len == 0 and self.new_len > 0


def extract_identifiers(text: str, profile: str = "code") -> frozenset[str]:
    raw = _IDENT_RE.findall(text)
    stopwords = TokenProfile.get_stopwords(profile)
    min_len = TokenProfile.get_min_len(profile)
    return frozenset({ident for ident in raw if len(ident) >= min_len and ident.lower() not in stopwords})


def extract_identifier_list(text: str, profile: str = "code") -> list[str]:
    raw = _IDENT_RE.findall(text)
    stopwords = TokenProfile.get_stopwords(profile)
    min_len = TokenProfile.get_min_len(profile)
    return [ident for ident in raw if len(ident) >= min_len and ident.lower() not in stopwords]
