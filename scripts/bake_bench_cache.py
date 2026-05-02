#!/usr/bin/env python3
"""Bake bench repo cache into a Docker layer.

Clones all repos referenced by the three test-set datasets as bare mirrors
and fetches every required commit. Designed to run inside a Docker build
stage so that /cache/contextbench_repos becomes a baked-in image layer.

Datasets baked:
  - Contextbench/ContextBench   (default config, train split)
  - princeton-nlp/SWE-bench_Verified  (test split)
  - AmazonScience/SWE-PolyBench_500   (test split)

Idempotent: skips clones that already exist, skips commits already local.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

CLONE_TIMEOUT_SECS = 1800
FETCH_TIMEOUT_SECS = 600
CLONE_PARALLELISM = int(os.environ.get("BAKE_PARALLELISM", "4"))

DATASETS: list[tuple[str, str | None, str]] = [
    ("Contextbench/ContextBench", "default", "train"),
    ("Contextbench/ContextBench", "contextbench_verified", "train"),
    ("princeton-nlp/SWE-bench_Verified", None, "test"),
    ("AmazonScience/SWE-PolyBench_500", None, "test"),
]


def safe_name(repo: str) -> str:
    return repo.replace("/", "__")


def run(cmd: list[str], timeout: int) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        return r.returncode, (r.stderr or "")[:500]
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout}s"


def clone_one(repo: str, url: str, target: Path) -> tuple[str, bool, str]:
    cache_dir = target / safe_name(repo)
    if cache_dir.exists():
        return repo, True, "exists"
    print(f"  CLONE {repo} <- {url}", flush=True)
    rc, err = run(["git", "clone", "--quiet", "--bare", url, str(cache_dir)], CLONE_TIMEOUT_SECS)
    if rc != 0:
        return repo, False, err
    run(["git", "-C", str(cache_dir), "config", "gc.auto", "0"], 30)
    return repo, True, "cloned"


def fetch_one(repo: str, commit: str, target: Path) -> tuple[str, str, bool, str]:
    cache_dir = target / safe_name(repo)
    if not cache_dir.exists():
        return repo, commit, False, "no cache dir"
    rc, _ = run(["git", "-C", str(cache_dir), "cat-file", "-t", commit], 30)
    if rc == 0:
        return repo, commit, True, "have"
    print(f"  FETCH {repo}@{commit[:12]}", flush=True)
    rc, err = run(["git", "-C", str(cache_dir), "fetch", "--quiet", "origin", commit], FETCH_TIMEOUT_SECS)
    return repo, commit, rc == 0, err if rc != 0 else "fetched"


def collect_repos_commits(
    hf_path: str,
    config: str | None,
    split: str,
    limit: int,
) -> tuple[dict[str, str], set[tuple[str, str]]]:
    from datasets import load_dataset

    kwargs: dict = {"split": split}
    if config:
        kwargs["name"] = config
    print(f"  Loading {hf_path} (config={config or 'default'}, split={split}) ...", flush=True)
    ds = load_dataset(hf_path, **kwargs)
    instances = list(ds)
    if limit:
        instances = instances[:limit]
    repos: dict[str, str] = {}
    commits: set[tuple[str, str]] = set()
    for raw in instances:
        inst = dict(raw)
        repo = inst.get("repo") or inst.get("repo_name") or ""
        if not repo:
            continue
        commit = inst.get("base_commit") or inst.get("commit") or ""
        if not commit:
            continue
        if repo not in repos:
            url = inst.get("repo_url") or f"https://github.com/{repo}.git"
            repos[repo] = url
        commits.add((repo, commit))
    print(f"  → {len(repos)} unique repos, {len(commits)} unique commits", flush=True)
    return repos, commits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", type=Path, help="Target cache dir (e.g. /cache/contextbench_repos)")
    ap.add_argument("--limit", type=int, default=0, help="Cap instances per dataset (0 = all)")
    args = ap.parse_args()

    args.target.mkdir(parents=True, exist_ok=True)

    all_repos: dict[str, str] = {}
    all_commits: set[tuple[str, str]] = set()

    for hf_path, config, split in DATASETS:
        repos, commits = collect_repos_commits(hf_path, config, split, args.limit)
        all_repos.update(repos)
        all_commits.update(commits)

    print(
        f"\nTotal: {len(all_repos)} unique repos, {len(all_commits)} unique commits",
        flush=True,
    )
    print(f"Cloning with parallelism={CLONE_PARALLELISM}", flush=True)

    failed_clones: list[tuple[str, str]] = []
    with ThreadPoolExecutor(max_workers=CLONE_PARALLELISM) as pool:
        futs = {pool.submit(clone_one, r, u, args.target): r for r, u in all_repos.items()}
        for fut in as_completed(futs):
            repo, ok, msg = fut.result()
            if not ok:
                failed_clones.append((repo, msg))
                print(f"  CLONE FAIL {repo}: {msg}", flush=True)

    print(f"\nClones: {len(all_repos) - len(failed_clones)}/{len(all_repos)} successful", flush=True)

    failed_fetches: list[tuple[str, str, str]] = []
    with ThreadPoolExecutor(max_workers=CLONE_PARALLELISM * 2) as pool:
        futs = {pool.submit(fetch_one, r, c, args.target): (r, c) for r, c in all_commits}
        ok_count = 0
        for fut in as_completed(futs):
            repo, commit, ok, msg = fut.result()
            if ok:
                ok_count += 1
            else:
                failed_fetches.append((repo, commit, msg))

    print(f"\nCommits: {ok_count}/{len(all_commits)} present", flush=True)
    if failed_fetches:
        print(f"  Failed fetches: {len(failed_fetches)}", flush=True)
        for r, c, m in failed_fetches[:10]:
            print(f"    {r}@{c[:12]}: {m}", flush=True)

    print("\nCache size:", flush=True)
    subprocess.run(["du", "-sh", str(args.target)], check=False)

    return 0


if __name__ == "__main__":
    sys.exit(main())
