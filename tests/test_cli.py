# tests/test_cli.py
import pytest

from .conftest import run_treemapper_subprocess


@pytest.mark.parametrize("flag", ["-h", "--help"])
def test_cli_help(temp_project, flag):
    result = run_treemapper_subprocess([flag], cwd=temp_project)
    assert result.returncode == 0
    assert "usage: treemapper" in result.stdout.lower()
    assert "--help" in result.stdout
    assert "--output-file" in result.stdout
    assert "--verbosity" in result.stdout


@pytest.mark.parametrize("invalid_value", ["5", "-1"])
def test_cli_invalid_verbosity(temp_project, invalid_value):
    result = run_treemapper_subprocess(["-v", invalid_value], cwd=temp_project)
    assert result.returncode != 0
    assert (
        f"invalid choice: '{invalid_value}'" in result.stderr or f"invalid choice: {invalid_value}" in result.stderr
    ), f"stderr: {result.stderr}"


def test_cli_version_display(temp_project):
    result = run_treemapper_subprocess(["--version"], cwd=temp_project)
    assert result.returncode == 0
    assert "treemapper" in result.stdout.lower()


def test_main_module_execution(temp_project):
    output_file = temp_project / "output.yaml"
    result = run_treemapper_subprocess([str(temp_project), "-o", str(output_file)])
    assert result.returncode == 0
    assert output_file.exists()
