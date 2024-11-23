import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_project():
    """Create a temporary project structure for testing."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create a test project structure
    (temp_dir / "src").mkdir()
    (temp_dir / "src" / "main.py").write_text("def main():\n    print('hello')\n")
    (temp_dir / "src" / "test.py").write_text("def test():\n    pass\n")
    (temp_dir / "docs").mkdir()
    (temp_dir / "docs" / "readme.md").write_text("# Documentation\n")
    (temp_dir / "output").mkdir()
    (temp_dir / ".git").mkdir()
    (temp_dir / ".gitignore").write_text("*.pyc\n__pycache__\n")
    (temp_dir / ".treemapperignore").write_text("output/\n")

    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def run_mapper(monkeypatch, temp_project):
    """Helper to run treemapper with given args."""

    def _run(args):
        with monkeypatch.context() as m:
            m.chdir(temp_project)
            m.setattr("sys.argv", ["treemapper"] + args)
            try:
                from treemapper.treemapper import main
                main()
                return True
            except SystemExit as e:
                if e.code != 0:
                    return False
                return True

    return _run
