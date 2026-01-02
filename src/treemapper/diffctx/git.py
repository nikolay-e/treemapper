from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .types import DiffHunk

_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
_RANGE_RE = re.compile(r"^\s*(\S+?)(\.\.\.?)(\S+?)\s*$")  # NOSONAR(S5852)


class GitError(Exception):
    pass


def run_git(repo_root: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise GitError(f"git {' '.join(args)} failed: {e.stderr.strip()}") from e
    except FileNotFoundError as e:
        raise GitError("git is not installed or not in PATH") from e


def is_git_repo(path: Path) -> bool:
    try:
        run_git(path, ["rev-parse", "--git-dir"])
        return True
    except GitError:
        return False


def get_diff_text(repo_root: Path, diff_range: str) -> str:
    return run_git(repo_root, ["diff", diff_range])


def parse_diff(repo_root: Path, diff_range: str) -> list[DiffHunk]:
    output = run_git(repo_root, ["diff", "--unified=0", diff_range])
    hunks: list[DiffHunk] = []
    old_path: Path | None = None
    new_path: Path | None = None

    for line in output.splitlines():
        if line.startswith("--- a/"):
            rel_path = line.removeprefix("--- a/").strip()
            old_path = repo_root / rel_path
            continue

        if line.startswith("--- /dev/null"):
            old_path = None
            continue

        if line.startswith("+++ b/"):
            rel_path = line.removeprefix("+++ b/").strip()
            new_path = repo_root / rel_path
            continue

        if line.startswith("+++ /dev/null"):
            new_path = None
            continue

        match = _HUNK_RE.match(line)
        if match:
            # For deletions, use old_path; for additions/modifications, use new_path
            current_path = new_path if new_path else old_path
            if not current_path:
                continue

            old_start = int(match.group(1))
            old_len_str = match.group(2)
            old_len = int(old_len_str) if old_len_str else 1
            new_start = int(match.group(3))
            new_len_str = match.group(4)
            new_len = int(new_len_str) if new_len_str else 1

            hunks.append(
                DiffHunk(
                    path=current_path,
                    new_start=new_start,
                    new_len=new_len,
                    old_start=old_start,
                    old_len=old_len,
                )
            )

    return hunks


def get_changed_files(repo_root: Path, diff_range: str) -> list[Path]:
    output = run_git(repo_root, ["diff", "--name-only", diff_range])
    files: list[Path] = []
    for line in output.splitlines():
        line = line.strip()
        if line:
            files.append(repo_root / line)
    return files


def split_diff_range(diff_range: str) -> tuple[str | None, str | None]:
    m = _RANGE_RE.match(diff_range)
    if not m:
        return (None, None)
    base = m.group(1).strip()
    head = m.group(3).strip()
    return (base or None, head or None)


def show_file_at_revision(repo_root: Path, rev: str, rel_path: Path) -> str:
    spec = f"{rev}:{rel_path.as_posix()}"
    return run_git(repo_root, ["show", spec])
