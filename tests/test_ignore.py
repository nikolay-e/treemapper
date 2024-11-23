import pytest

from .utils import load_yaml, get_all_files_in_tree


def test_custom_ignore(temp_project, run_mapper):
    """Test custom ignore patterns."""
    # Create custom ignore file
    ignore_file = temp_project / "custom.ignore"
    ignore_file.write_text("""
# Ignore all Python files
*.py
# Ignore docs directory
docs/
# Ignore specific file
.gitignore
""")

    assert run_mapper([".", "-i", str(ignore_file)])

    result = load_yaml(temp_project / "directory_tree.yaml")
    all_files = get_all_files_in_tree(result)

    # Check that custom ignores are applied
    assert not any(f.endswith(".py") for f in all_files)
    assert "docs" not in all_files
    assert ".gitignore" not in all_files


def test_gitignore_patterns(temp_project, run_mapper):
    """Test .gitignore pattern handling."""
    # Create nested .gitignore files
    (temp_project / ".gitignore").write_text("*.pyc\n__pycache__")
    (temp_project / "src" / ".gitignore").write_text("local_only.py")

    # Create test files
    (temp_project / "test.pyc").touch()
    (temp_project / "__pycache__").mkdir()
    (temp_project / "src" / "local_only.py").touch()
    (temp_project / "src" / "allowed.py").touch()

    assert run_mapper(["."])

    result = load_yaml(temp_project / "directory_tree.yaml")
    all_files = get_all_files_in_tree(result)

    assert "test.pyc" not in all_files
    assert "__pycache__" not in all_files
    assert "local_only.py" not in all_files
    assert "allowed.py" in all_files


def test_symlinks_and_special_files(temp_project, run_mapper):
    """Test ignore patterns with symlinks and special files."""
    try:
        # Create some special files/dirs
        (temp_project / ".hidden_dir").mkdir()
        (temp_project / ".hidden_file").touch()

        # Add ignore patterns
        (temp_project / ".treemapperignore").write_text(".*\n!.gitignore")

        assert run_mapper(["."])
        result = load_yaml(temp_project / "directory_tree.yaml")
        all_files = get_all_files_in_tree(result)

        # Check ignore patterns
        assert ".hidden_dir" not in all_files
        assert ".hidden_file" not in all_files
        assert ".gitignore" in all_files  # Should be included due to negation
    except OSError as e:
        pytest.skip(f"Failed to create special files: {e}")


def test_empty_and_invalid_ignores(temp_project, run_mapper):
    """Test handling of empty and invalid ignore files."""
    # Create empty ignore files
    (temp_project / ".gitignore").write_text("")
    (temp_project / ".treemapperignore").write_text("\n\n# Just comments\n\n")
    (temp_project / "empty.ignore").write_text("")

    # Create invalid ignore file
    (temp_project / "invalid.ignore").write_text("[\ninvalid\npattern\n")

    # Test various scenarios
    assert run_mapper(["."])  # Should handle empty files
    assert run_mapper([".", "-i", str(temp_project / "empty.ignore")])  # Empty custom ignore
    assert run_mapper([".", "-i", str(temp_project / "invalid.ignore")])  # Invalid patterns
    assert run_mapper([".", "-i", "nonexistent.ignore"])  # Non-existent file

    # All runs should succeed without errors and produce valid YAML
    result = load_yaml(temp_project / "directory_tree.yaml")
    assert result is not None
