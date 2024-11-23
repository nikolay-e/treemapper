# tests/test_basic.py
import yaml


def normalize_content(content):
    """Normalize content by stripping whitespace and line endings."""
    if content is None:
        return None
    return content.strip()


def normalize_tree(tree):
    """Normalize tree for comparison by sorting children and normalizing content."""
    if isinstance(tree, dict):
        result = tree.copy()
        if 'content' in result:
            result['content'] = normalize_content(result['content'])
        if 'children' in result:
            result['children'] = sorted(
                [normalize_tree(child) for child in result['children']],
                key=lambda x: x['name']
            )
        return result
    return tree


def test_basic_mapping(temp_project, run_mapper):
    """Test basic directory mapping with default settings."""
    assert run_mapper(["."])

    # Check file exists
    output_file = temp_project / "directory_tree.yaml"
    assert output_file.exists()

    # Verify structure
    result = yaml.safe_load(output_file.read_text())
    assert result["type"] == "directory"
    assert result["name"] == temp_project.name

    # Get all files
    def get_files(node):
        files = {node["name"]}
        if "children" in node:
            for child in node["children"]:
                files.update(get_files(child))
        return files

    all_files = get_files(result)

    # Check included files
    assert "src" in all_files
    assert "main.py" in all_files
    assert "test.py" in all_files
    assert "docs" in all_files

    # Check excluded files
    assert ".git" not in all_files
    assert "output" not in all_files
    assert "directory_tree.yaml" not in all_files


def test_directory_content(temp_project, run_mapper):
    """Test directory structure and content preservation."""
    assert run_mapper(["."])

    result = yaml.safe_load((temp_project / "directory_tree.yaml").read_text())

    # Find src directory
    src_dir = next(c for c in result["children"] if c["name"] == "src")
    assert src_dir["type"] == "directory"

    # Verify src directory contents
    main_py = next(c for c in src_dir["children"] if c["name"] == "main.py")
    assert main_py["type"] == "file"
    assert "def main()" in normalize_content(main_py["content"])
    assert "print('hello')" in normalize_content(main_py["content"])


def test_custom_output(temp_project, run_mapper):
    """Test custom output file locations and names."""
    # Test in root directory
    assert run_mapper([".", "-o", "custom.yaml"])
    assert (temp_project / "custom.yaml").exists()

    # Test in subdirectory
    subdir = temp_project / "subdir"
    subdir.mkdir()
    assert run_mapper([".", "-o", str(subdir / "output.yaml")])
    assert (subdir / "output.yaml").exists()

    # Compare normalized content
    result1 = normalize_tree(yaml.safe_load((temp_project / "custom.yaml").read_text()))
    result2 = normalize_tree(yaml.safe_load((subdir / "output.yaml").read_text()))

    # Remove output files from comparison
    def remove_output_files(tree):
        if 'children' in tree:
            tree['children'] = [
                c for c in tree['children']
                if c['name'] not in ['custom.yaml', 'output.yaml']
            ]
        return tree

    assert remove_output_files(result1) == remove_output_files(result2)


def test_file_content_encoding(temp_project, run_mapper):
    """Test handling of different file encodings and content."""
    # Create files with different content types
    (temp_project / "ascii.txt").write_text("Hello World")
    (temp_project / "multiline.txt").write_text("line1\nline2\nline3")
    (temp_project / "empty.txt").write_text("")

    assert run_mapper(["."])
    result = yaml.safe_load((temp_project / "directory_tree.yaml").read_text())

    # Find and verify each file
    files = {f["name"]: normalize_content(f["content"])
             for f in result["children"] if f["type"] == "file"}

    assert files["ascii.txt"] == "Hello World"
    assert files["multiline.txt"] == "line1\nline2\nline3"
    assert files["empty.txt"] == ""


def test_nested_structures(temp_project, run_mapper):
    """Test handling of deeply nested directory structures."""
    # Create nested structure
    current = temp_project
    for i in range(5):  # Create 5 levels deep
        current = current / f"level{i}"
        current.mkdir()
        (current / f"file{i}.txt").write_text(f"Content {i}")

    assert run_mapper(["."])
    result = yaml.safe_load((temp_project / "directory_tree.yaml").read_text())

    # Verify all levels are present
    current_level = result
    for i in range(5):
        # Find next level
        level_dir = next(
            c for c in current_level["children"]
            if c["name"] == f"level{i}" and c["type"] == "directory"
        )
        # Find file at this level
        level_file = next(
            c for c in level_dir["children"]
            if c["name"] == f"file{i}.txt" and c["type"] == "file"
        )
        assert normalize_content(level_file["content"]) == f"Content {i}"
        current_level = level_dir


def test_absolute_relative_paths(temp_project, run_mapper):
    """Test handling of absolute and relative paths."""
    # Test with absolute path
    assert run_mapper([str(temp_project.absolute())])

    # Test with relative path components
    assert run_mapper(["./src", "-o", "src.yaml"])
    assert run_mapper([".", "-o", "root.yaml"])

    # Compare results
    src_result = normalize_tree(yaml.safe_load((temp_project / "src.yaml").read_text()))
    root_result = normalize_tree(yaml.safe_load((temp_project / "root.yaml").read_text()))

    # Verify src is a subset of root
    src_dir = next(c for c in root_result["children"] if c["name"] == "src")
    assert src_dir["type"] == "directory"
    assert normalize_tree(src_result)["children"] == src_dir["children"]


def test_output_handling(temp_project, run_mapper):
    """Test various output file scenarios."""
    # Test overwriting existing file
    output_file = temp_project / "output.yaml"
    output_file.write_text("original content")
    assert run_mapper([".", "-o", str(output_file)])
    assert "original content" not in output_file.read_text()
    assert yaml.safe_load(output_file.read_text()) is not None

    # Test output to new directory
    new_dir = temp_project / "new_dir"
    new_dir.mkdir()
    assert run_mapper([".", "-o", str(new_dir / "tree.yaml")])
    assert (new_dir / "tree.yaml").exists()
    assert yaml.safe_load((new_dir / "tree.yaml").read_text()) is not None
