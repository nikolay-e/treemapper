from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

from treemapper.version import __version__

from .conftest import CliResult, run_cli


def test_version_is_treemapper_branded() -> None:
    result = run_cli(["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == f"treemapper {__version__}"


def test_help_renders_and_is_treemapper_branded() -> None:
    result = run_cli(["--help"])
    assert result.exit_code == 0
    assert "--diff" in result.stdout
    assert "usage: treemapper" in result.stdout.lower()
    assert "usage: diffctx" not in result.stdout.lower()


def test_yaml_tree_includes_files_and_content(sample_project: Path) -> None:
    result = run_cli([str(sample_project)])
    assert result.exit_code == 0
    tree = yaml.safe_load(result.stdout)
    assert tree["type"] == "directory"
    names = {child["name"] for child in tree["children"]}
    assert "alpha.py" in names
    assert "pkg" in names
    assert "def alpha()" in result.stdout


def test_json_format(sample_project: Path) -> None:
    result = run_cli([str(sample_project), "-f", "json"])
    assert result.exit_code == 0
    tree = json.loads(result.stdout)
    assert tree["type"] == "directory"


def test_no_content_omits_file_bodies(sample_project: Path) -> None:
    result = run_cli([str(sample_project), "--no-content"])
    assert result.exit_code == 0
    assert "def alpha()" not in result.stdout
    assert "alpha.py" in result.stdout


def test_save_writes_file(sample_project: Path, monkeypatch) -> None:
    monkeypatch.chdir(sample_project)
    result = run_cli([str(sample_project), "-f", "md", "--save"])
    assert result.exit_code == 0
    assert (sample_project / "tree.md").is_file()


def test_diff_mode_selects_changed_context(git_repo: Path, monkeypatch) -> None:
    monkeypatch.chdir(git_repo)
    result = run_cli([str(git_repo), "--diff", "HEAD~1"])
    assert result.exit_code == 0
    assert "module.py" in result.stdout
    assert "extra" in result.stdout


def test_console_script_entry_point(sample_project: Path) -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "treemapper", str(sample_project), "--no-content"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "alpha.py" in proc.stdout


def test_result_dataclass_shape() -> None:
    result = run_cli(["--version"])
    assert isinstance(result, CliResult)
