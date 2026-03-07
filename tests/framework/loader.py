from __future__ import annotations

from pathlib import Path

import yaml

from tests.framework.types import YamlTestCase


def _parse_yaml_test(data: dict, source_file: Path | None = None) -> YamlTestCase:
    name = data.get("name", source_file.stem if source_file else "unnamed")
    initial_files = data.get("initial", data.get("initial_files", {}))
    changed_files = data.get("changed", data.get("changed_files", {}))

    assertions = data.get("assertions", {})

    must_include = assertions.get("must_include", data.get("must_include", []))
    must_include_files = assertions.get("must_include_files", data.get("must_include_files", []))
    must_not_include = assertions.get("must_not_include", data.get("must_not_include", []))

    raw_content = assertions.get("must_include_content", data.get("must_include_content", []))
    must_include_content = [s.rstrip("\n") for s in raw_content]

    raw_content_from = assertions.get("must_include_content_from", data.get("must_include_content_from", {}))
    must_include_content_from = {path: [s.rstrip("\n") for s in snippets] for path, snippets in raw_content_from.items()}

    must_not_include_files = assertions.get("must_not_include_files", data.get("must_not_include_files", []))

    options = data.get("options", {})

    return YamlTestCase(
        name=name,
        initial_files=initial_files,
        changed_files=changed_files,
        must_include=must_include,
        must_include_files=must_include_files,
        must_include_content=must_include_content,
        must_not_include=must_not_include,
        must_include_content_from=must_include_content_from,
        must_not_include_files=must_not_include_files,
        max_fragments=options.get("max_fragments", data.get("max_fragments")),
        max_files=options.get("max_files", data.get("max_files")),
        commit_message=options.get("commit_message", data.get("commit_message", "Update files")),
        min_budget=options.get("min_budget", data.get("min_budget")),
        add_garbage_files=options.get("add_garbage", data.get("add_garbage_files", True)),
        skip_garbage_check=options.get("skip_garbage_check", data.get("skip_garbage_check", False)),
        source_file=source_file,
    )


def load_test_cases(yaml_path: Path) -> list[YamlTestCase]:
    with yaml_path.open("r", encoding="utf-8") as f:
        content = yaml.safe_load(f)

    if content is None:
        return []

    if isinstance(content, list):
        return [_parse_yaml_test(item, yaml_path) for item in content]

    if isinstance(content, dict):
        if "tests" in content:
            return [_parse_yaml_test(item, yaml_path) for item in content["tests"]]
        if "name" in content or "initial" in content:
            return [_parse_yaml_test(content, yaml_path)]

    return []


def load_test_cases_from_dir(cases_dir: Path, pattern: str = "**/*.yaml") -> list[YamlTestCase]:
    cases: list[YamlTestCase] = []
    for yaml_file in sorted(cases_dir.glob(pattern)):
        cases.extend(load_test_cases(yaml_file))
    return cases
