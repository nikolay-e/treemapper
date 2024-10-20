from treemapper.treemapper import read_ignore_file, should_ignore, load_pathspec
import os
import sys

# Add the src directory to the Python path
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '..',
            'src')))


def test_read_ignore_file(tmp_path):
    ignore_file = tmp_path / ".treemapperignore"
    ignore_file.write_text("*.txt\ndir1\n*.class\n")
    ignore_patterns = read_ignore_file(ignore_file)
    assert "*.txt" in ignore_patterns
    assert "dir1" in ignore_patterns
    assert "*.class" in ignore_patterns


def test_should_ignore():
    combined_patterns = ["*.txt", "dir1", "file[1-3].py", "log/**", ".git/"]
    combined_spec = load_pathspec(combined_patterns)
    assert should_ignore("file.txt/", combined_spec)
    assert should_ignore("dir1/", combined_spec)
    assert should_ignore("file2.py", combined_spec)
    assert should_ignore(
        os.path.join(
            "log",
            "subdir",
            "file.log"),
        combined_spec)
    assert should_ignore(".git/", combined_spec)
    assert not should_ignore("file4.py", combined_spec)
    assert not should_ignore("dir2/", combined_spec)
    assert not should_ignore("directory/", combined_spec)


def test_read_ignore_file_with_comments(tmp_path):
    ignore_file = tmp_path / ".treemapperignore"
    ignore_file.write_text(
        "*.txt\n# This is a comment\ndir1\n\n# Another comment\n*.log\n*.class")
    ignore_patterns = read_ignore_file(ignore_file)
    assert "*.txt" in ignore_patterns
    assert "dir1" in ignore_patterns
    assert "*.log" in ignore_patterns
    assert "*.class" in ignore_patterns
    assert "# This is a comment" not in ignore_patterns
    assert "# Another comment" not in ignore_patterns
    assert "" not in ignore_patterns


def test_should_ignore_edge_cases():
    combined_patterns = ["dir1/*", "*.py", "dir2/*.txt"]
    combined_spec = load_pathspec(combined_patterns)
    assert should_ignore("dir1/file.txt", combined_spec)
    assert should_ignore("dir2/file.txt", combined_spec)
    # Expect this file to be ignored due to the "*.py" pattern.
    assert should_ignore("dir2/file.py", combined_spec)
    # Add more relevant test cases as necessary.
