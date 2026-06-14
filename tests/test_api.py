from __future__ import annotations

from pathlib import Path

import diffctx

import treemapper


def test_public_api_is_exported() -> None:
    for name in ("map_directory", "build_diff_context", "run", "to_yaml", "to_json", "to_text", "to_markdown"):
        assert hasattr(treemapper, name), name


def test_run_is_the_engine_entry() -> None:
    assert treemapper.run is diffctx.run


def test_map_directory_round_trips_to_yaml(sample_project: Path) -> None:
    tree = treemapper.map_directory(str(sample_project))
    assert tree["type"] == "directory"
    rendered = treemapper.to_yaml(tree)
    assert "alpha.py" in rendered


def test_build_diff_context_on_real_repo(git_repo: Path) -> None:
    context = treemapper.build_diff_context(root_dir=git_repo, diff_range="HEAD~1")
    assert isinstance(context, dict)
    rendered = treemapper.to_yaml(context)
    assert "module.py" in rendered
