from __future__ import annotations

import logging
import sys
from functools import partial
from pathlib import Path

import anyio
from mcp.server.fastmcp import FastMCP

from treemapper.diffctx import GitError, build_diff_context

from .formatting import format_diff_context_as_markdown
from .security import validate_repo_path

logger = logging.getLogger(__name__)

mcp = FastMCP("treemapper")

_TOOL_DESCRIPTION = (
    "Get the most relevant code fragments for understanding a git diff. "
    "Returns ranked function/class definitions, type references, and "
    "cross-file dependencies needed to understand a change WITHOUT "
    "dumping entire files.\n\n"
    "Use this tool when:\n"
    "- Reviewing a pull request or commit\n"
    "- Explaining what a change does\n"
    "- Analyzing the impact of a refactor\n"
    "- Investigating why tests broke after a commit\n\n"
    "Returns Markdown-formatted context with file paths, line ranges, "
    "and source code, ranked by relevance. Stays within the specified "
    "token budget using submodular optimization.\n\n"
    "Supports 50+ languages including Python, JavaScript, TypeScript, "
    "Go, Rust, Java, C/C++, Ruby, PHP, and more."
)


@mcp.tool(description=_TOOL_DESCRIPTION)
async def get_diff_context(
    repo_path: str,
    diff_range: str = "HEAD~1..HEAD",
    budget_tokens: int = 8000,
    clipboard: bool = False,
) -> str:
    validated_path = validate_repo_path(repo_path)
    try:
        result = await anyio.to_thread.run_sync(
            partial(
                build_diff_context,
                root_dir=validated_path,
                diff_range=diff_range,
                budget_tokens=budget_tokens,
            )
        )
    except GitError as e:
        msg = str(e)
        if "unknown revision" in msg or "bad revision" in msg:
            raise ValueError(
                f"Invalid diff range '{diff_range}'. "
                "Try 'HEAD~1..HEAD' for the last commit, "
                "'main..feature' for a branch comparison, "
                "or check that both refs exist with 'git log --oneline'."
            ) from e
        raise ValueError(f"Git error: {e}") from e

    content = format_diff_context_as_markdown(result)

    if clipboard:
        from treemapper.clipboard import copy_to_clipboard

        await anyio.to_thread.run_sync(lambda: copy_to_clipboard(content))
        frag_count = result.get("fragment_count", 0)
        return f"Copied diff context ({frag_count} fragments) to clipboard"

    return content


_TREE_MAP_DESCRIPTION = (
    "Get a structured map of a codebase — directory tree with file contents "
    "in YAML or Markdown format, optimized for LLM comprehension. "
    "Respects .gitignore and smart defaults to skip binaries/build artifacts.\n\n"
    "Use this tool when:\n"
    "- You need to understand the structure of a project\n"
    "- You want to read multiple files at once\n"
    "- You need full file contents for a subdirectory\n"
    "- You want to copy code context for analysis\n\n"
    "Pass a subdirectory path to scope the output (e.g. 'src/components'). "
    "Use no_content=true for structure-only view. "
    "Use max_depth to limit directory depth."
)


@mcp.tool(description=_TREE_MAP_DESCRIPTION)
async def get_tree_map(
    repo_path: str,
    subdirectory: str = "",
    output_format: str = "yaml",
    no_content: bool = False,
    max_depth: int | None = None,
    max_file_bytes: int = 100_000,
    clipboard: bool = False,
) -> str:
    from treemapper.ignore import get_ignore_specs, get_whitelist_spec
    from treemapper.tokens import count_tokens
    from treemapper.tree import TreeBuildContext, build_tree
    from treemapper.writer import tree_to_string

    validated_path = validate_repo_path(repo_path)
    target = validated_path / subdirectory if subdirectory else validated_path
    if not target.is_dir():
        raise ValueError(f"Not a directory: {target}")

    def _build() -> str:
        ctx = TreeBuildContext(
            base_dir=target,
            combined_spec=get_ignore_specs(target, None, False, None),
            output_file=None,
            max_depth=max_depth,
            no_content=no_content,
            max_file_bytes=max_file_bytes,
            whitelist_spec=get_whitelist_spec(None, target),
        )
        tree = {"name": target.name or str(target), "type": "directory", "children": build_tree(target, ctx)}
        return tree_to_string(tree, output_format)

    content: str = await anyio.to_thread.run_sync(_build)
    token_info = count_tokens(content)

    if clipboard:
        from treemapper.clipboard import copy_to_clipboard

        await anyio.to_thread.run_sync(lambda: copy_to_clipboard(content))
        return f"Copied to clipboard ({token_info.count:,} tokens, {token_info.encoding})"

    return f"<!-- {token_info.count:,} tokens ({token_info.encoding}) -->\n{content}"


_FILE_CONTEXT_DESCRIPTION = (
    "Read specific files from a repository, formatted for LLM consumption. "
    "Accepts glob patterns (e.g. 'src/**/*.py', 'benchmarks/*.py').\n\n"
    "Use this tool when:\n"
    "- You need contents of specific files by pattern\n"
    "- You want to read a known set of files efficiently\n"
    "- You need to compare files across directories\n\n"
    "Returns file contents with paths and line numbers in Markdown format."
)


@mcp.tool(description=_FILE_CONTEXT_DESCRIPTION)
async def get_file_context(
    repo_path: str,
    patterns: list[str],
    max_files: int = 50,
    max_file_bytes: int = 100_000,
    clipboard: bool = False,
) -> str:
    validated_path = validate_repo_path(repo_path)

    def _read() -> tuple[str, int, int]:
        import glob as globmod

        matched: list[Path] = []
        for pattern in patterns:
            full_pattern = str(validated_path / pattern)
            for match in sorted(globmod.glob(full_pattern, recursive=True)):
                p = Path(match)
                if p.is_file() and len(matched) < max_files:
                    matched.append(p)

        if not matched:
            return f"No files matched patterns: {patterns}", 0, 0

        parts = [f"# {len(matched)} files matched\n"]
        total_lines = 0
        for p in matched:
            rel = p.relative_to(validated_path)
            try:
                size = p.stat().st_size
                if size > max_file_bytes:
                    parts.append(f"## {rel}\n*Skipped: {size:,} bytes exceeds limit*\n")
                    continue
                content = p.read_text(encoding="utf-8", errors="replace")
                total_lines += content.count("\n") + 1
                suffix = p.suffix.lstrip(".")
                parts.append(f"## {rel}\n```{suffix}\n{content}\n```\n")
            except OSError as e:
                parts.append(f"## {rel}\n*Error: {e}*\n")

        return "\n".join(parts), len(matched), total_lines

    raw_result: tuple[str, int, int] = await anyio.to_thread.run_sync(_read)
    content, n_files, n_lines = raw_result

    if clipboard and n_files > 0:
        from treemapper.clipboard import copy_to_clipboard

        await anyio.to_thread.run_sync(lambda: copy_to_clipboard(content))
        return f"Copied {n_files} files ({n_lines:,} lines) to clipboard"

    return content


def run_server() -> None:
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.WARNING,
        format="%(name)s: %(message)s",
    )
    mcp.run(transport="stdio")
