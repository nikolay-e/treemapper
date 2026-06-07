from __future__ import annotations

import contextlib
import io
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from treemapper.cli import main


@dataclass
class CliResult:
    stdout: str
    stderr: str
    exit_code: int


def run_cli(argv: list[str]) -> CliResult:
    out, err = io.StringIO(), io.StringIO()
    exit_code = 0
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            main(argv)
        except SystemExit as exc:
            code = exc.code
            exit_code = code if isinstance(code, int) else (0 if code is None else 1)
    return CliResult(stdout=out.getvalue(), stderr=err.getvalue(), exit_code=exit_code)


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    (tmp_path / "alpha.py").write_text("def alpha():\n    return 1\n", encoding="utf-8")
    (tmp_path / "readme.txt").write_text("hello tree\n", encoding="utf-8")
    nested = tmp_path / "pkg"
    nested.mkdir()
    (nested / "beta.py").write_text("def beta():\n    return 2\n", encoding="utf-8")
    return tmp_path


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    target = tmp_path / "module.py"
    target.write_text("def compute(x):\n    return x + 1\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "initial")
    target.write_text("def compute(x):\n    return x + 2\n\n\ndef extra(y):\n    return y * 2\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "change compute and add extra")
    return tmp_path
