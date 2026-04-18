# QA Methodology

## CI

- treemapper CI: Linux/macOS/Windows × Python 3.10-3.14
  (15 test matrices + 3 lint/arch jobs)
- Windows jobs slowest — typically 3-5min after Linux/macOS
- All jobs must pass; no flaky CI tolerance

## SonarCloud

- Credentials in 1Password under "Sonarcloud" items
- API: Bearer auth, not Basic auth
- Organization param required for project search
- Credentials expire — regenerate at sonarcloud.io/account

## Test Suite

- Run `python -m pytest --tb=no -q` for quick status
- xfail(strict=True): XPASS = FAIL — remove stale xfails
- xfail(strict=False): XPASS = OK, check stability (5 runs)
- Determinism: `set` → `list` must use `sorted()`
  to avoid flaky tests under pytest-xdist
- test_graph.py separate from test_yaml_diff.py — check both
