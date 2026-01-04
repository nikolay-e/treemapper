from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

import pathspec

from ..ignore import get_ignore_specs, should_ignore
from ..tokens import count_tokens
from .fragments import enclosing_fragment, fragment_file
from .git import (
    GitError,
    get_changed_files,
    get_diff_text,
    is_git_repo,
    parse_diff,
    show_file_at_revision,
    split_diff_range,
)
from .graph import build_graph
from .ppr import personalized_pagerank
from .render import build_partial_tree
from .select import lazy_greedy_select
from .types import Fragment, FragmentId, extract_identifiers
from .utility import concepts_from_diff_text

__all__ = ["GitError", "build_diff_context"]

_RARE_THRESHOLD = 3
_MAX_EXPANSION_FILES = 20
_OVERHEAD_PER_FRAGMENT = 18


def _read_file_content(
    file_path: Path,
    root_dir: Path,
    preferred_revs: list[str],
) -> str | None:
    try:
        rel = file_path.relative_to(root_dir)
    except ValueError:
        rel = Path(file_path.name)

    # Try git revisions first for consistency with diff range
    for rev in preferred_revs:
        try:
            return show_file_at_revision(root_dir, rev, rel)
        except GitError:
            continue

    # Fallback to filesystem for working tree diffs
    if file_path.exists() and file_path.is_file():
        try:
            return file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            pass

    return None


_DEFAULT_BUDGET_TOKENS = 50_000
_MAX_FRAGMENTS = 200


def build_diff_context(
    root_dir: Path,
    diff_range: str,
    budget_tokens: int | None = None,
    alpha: float = 0.60,
    tau: float = 0.08,
    no_content: bool = False,
    ignore_file: Path | None = None,
    no_default_ignores: bool = False,
    full: bool = False,
) -> dict[str, Any]:
    if not is_git_repo(root_dir):
        raise GitError(f"'{root_dir}' is not a git repository")

    if not (0.0 < alpha < 1.0):
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    if tau < 0.0:
        raise ValueError(f"tau must be >= 0, got {tau}")

    hunks = parse_diff(root_dir, diff_range)
    if not hunks:
        return _empty_tree(root_dir)

    combined_spec = get_ignore_specs(root_dir, ignore_file, no_default_ignores, None)

    diff_text = get_diff_text(root_dir, diff_range)
    concepts = concepts_from_diff_text(diff_text)

    changed_files = get_changed_files(root_dir, diff_range)
    changed_files = _filter_ignored(changed_files, root_dir, combined_spec)

    base_rev, head_rev = split_diff_range(diff_range)
    preferred_revs: list[str] = []
    if head_rev:
        preferred_revs.append(head_rev)
    if base_rev and base_rev != head_rev:
        preferred_revs.append(base_rev)

    all_fragments: list[Fragment] = []
    seen_frag_ids: set[FragmentId] = set()

    for file_path in changed_files:
        content = _read_file_content(file_path, root_dir, preferred_revs)
        if content is None:
            continue
        frags = fragment_file(file_path, content)
        for frag in frags:
            if frag.id not in seen_frag_ids:
                all_fragments.append(frag)
                seen_frag_ids.add(frag.id)

    expanded_files = _expand_universe_by_rare_identifiers(root_dir, concepts, changed_files, combined_spec)
    for file_path in expanded_files:
        content = _read_file_content(file_path, root_dir, preferred_revs)
        if content is None:
            continue
        frags = fragment_file(file_path, content)
        for frag in frags:
            if frag.id not in seen_frag_ids:
                all_fragments.append(frag)
                seen_frag_ids.add(frag.id)

    for frag in all_fragments:
        token_result = count_tokens(frag.content)
        frag.token_count = token_result.count + _OVERHEAD_PER_FRAGMENT

    frags_by_path: dict[Path, list[Fragment]] = defaultdict(list)
    for frag in all_fragments:
        frags_by_path[frag.path].append(frag)

    core_ids: set[FragmentId] = set()
    for h in hunks:
        frags = frags_by_path.get(h.path, [])
        if not frags:
            continue
        h_start = h.new_start
        h_end = h.end_line

        # Find fragments that fully cover the hunk
        covering = [f for f in frags if f.start_line <= h_start and h_end <= f.end_line]

        if covering:
            # Select minimal covering fragment (smallest by line count)
            best = min(covering, key=lambda f: f.line_count)
            core_ids.add(best.id)
        else:
            # Check for fragments that OVERLAP with the hunk (partial coverage)
            overlapping = [f for f in frags if f.start_line <= h_end and f.end_line >= h_start]
            if overlapping:
                # Add all overlapping fragments as core
                for f in overlapping:
                    core_ids.add(f.id)
            elif (enc := enclosing_fragment(frags, h_start)) is not None:
                # Fallback: use enclosing fragment
                core_ids.add(enc.id)
            else:
                # For hunks in gaps between fragments, find nearest adjacent fragments
                before = [f for f in frags if f.end_line < h_start]
                after = [f for f in frags if f.start_line > h_end]
                if before:
                    nearest_before = max(before, key=lambda f: f.end_line)
                    core_ids.add(nearest_before.id)
                if after:
                    nearest_after = min(after, key=lambda f: f.start_line)
                    core_ids.add(nearest_after.id)

    if full:
        changed_paths = set(changed_files)
        selected = [f for f in all_fragments if f.path in changed_paths]
        selected.sort(key=lambda f: (f.path, f.start_line))

        try:
            used = sum(f.token_count for f in selected)
            logging.info(
                "diffctx: full mode selected=%d from changed files used=%d tokens",
                len(selected),
                used,
            )
        except Exception:
            pass
    else:
        graph = build_graph(all_fragments)

        rel_scores = personalized_pagerank(graph, core_ids, alpha=alpha)

        effective_budget = budget_tokens if budget_tokens is not None else _DEFAULT_BUDGET_TOKENS

        result = lazy_greedy_select(
            fragments=all_fragments,
            core_ids=core_ids,
            rel=rel_scores,
            concepts=concepts,
            budget_tokens=effective_budget,
            tau=tau,
        )

        selected = result.selected

        try:
            used = sum(f.token_count for f in selected)
            budget_str = str(budget_tokens) if budget_tokens is not None else "unlimited"
            logging.info(
                "diffctx: selected=%d core=%d used=%d/%s reason=%s utility=%.4f alpha=%.3f tau=%.3f",
                len(selected),
                len(core_ids),
                used,
                budget_str,
                result.reason,
                result.utility,
                alpha,
                tau,
            )
        except Exception:
            pass

    if no_content:
        for frag in selected:
            frag.content = ""

    return build_partial_tree(root_dir, selected)


_MAX_FILE_SIZE = 100_000  # 100KB


def _expand_universe_by_rare_identifiers(
    root_dir: Path,
    concepts: frozenset[str],
    already_included: list[Path],
    combined_spec: pathspec.PathSpec,
) -> list[Path]:
    if not concepts:
        return []

    included_set = set(already_included)
    inverted_index: dict[str, list[Path]] = defaultdict(list)

    exts = {".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".java", ".kt", ".go", ".rb", ".php", ".cs"}
    cfg_exts = {".yaml", ".yml", ".json", ".toml", ".ini", ".env"}
    allowed = exts | cfg_exts

    files: list[Path] = []
    for file_path in root_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in allowed:
            continue
        if file_path in included_set:
            continue
        try:
            rel_path = file_path.relative_to(root_dir).as_posix()
            if should_ignore(rel_path, combined_spec):
                continue
            if file_path.stat().st_size > _MAX_FILE_SIZE:
                continue
        except (ValueError, OSError):
            continue
        files.append(file_path)

    for file_path in sorted(files)[:2000]:
        try:
            content = file_path.read_text(encoding="utf-8")
            file_idents = extract_identifiers(content)
            for ident in file_idents:
                if ident in concepts:
                    inverted_index[ident].append(file_path)
        except (OSError, UnicodeDecodeError):
            continue

    rare_concepts = [c for c in concepts if 0 < len(inverted_index.get(c, [])) <= _RARE_THRESHOLD]

    expansion_files: set[Path] = set()
    for concept in rare_concepts:
        for file_path in inverted_index.get(concept, []):
            if file_path not in included_set:
                expansion_files.add(file_path)
                if len(expansion_files) >= _MAX_EXPANSION_FILES:
                    return list(expansion_files)

    return list(expansion_files)


def _filter_ignored(
    files: list[Path],
    root_dir: Path,
    combined_spec: pathspec.PathSpec,
) -> list[Path]:
    result: list[Path] = []
    for file_path in files:
        try:
            rel_path = file_path.relative_to(root_dir).as_posix()
            if not should_ignore(rel_path, combined_spec):
                result.append(file_path)
        except ValueError:
            result.append(file_path)
    return result


def _empty_tree(root_dir: Path) -> dict[str, Any]:
    return {
        "name": root_dir.name,
        "type": "diff_context",
        "fragment_count": 0,
        "fragments": [],
    }
