# Plan: Token Counting Feature

Add `--tokens` flag to show token count for LLM context planning.

## Design

- **tiktoken** as optional dependency with fallback to `chars / 4`
- **o200k_base** encoding (GPT-4o default)
- Output to stderr only when TTY (don't break pipes)

## Implementation

### UPDATE: `pyproject.toml`

```toml
[project.optional-dependencies]
tokens = ["tiktoken>=0.7,<1.0"]
```

### NEW: `src/treemapper/tokens.py`

```python
import sys
from dataclasses import dataclass
from functools import lru_cache

@dataclass
class TokenCountResult:
    count: int
    is_exact: bool
    encoding: str

@lru_cache(maxsize=4)
def _get_encoder(encoding: str):
    try:
        import tiktoken
        return tiktoken.get_encoding(encoding)
    except (ImportError, Exception):
        return None

def count_tokens(text: str, encoding: str = "o200k_base") -> TokenCountResult:
    encoder = _get_encoder(encoding)
    if encoder:
        return TokenCountResult(len(encoder.encode(text)), True, encoding)
    return TokenCountResult(len(text) // 4, False, "approximation")

def print_token_summary(text: str, encoding: str = "o200k_base") -> None:
    if not sys.stderr.isatty():
        return
    result = count_tokens(text, encoding)
    prefix = "" if result.is_exact else "~"
    print(f"{prefix}{result.count:,} tokens ({result.encoding})", file=sys.stderr)
```

### UPDATE: `cli.py`

```python
# ParsedArgs
show_tokens: bool
token_encoding: str

# Arguments
parser.add_argument("--tokens", action="store_true")
parser.add_argument("--token-encoding", choices=["o200k_base", "cl100k_base"], default="o200k_base")
```

### UPDATE: `treemapper.py`

```python
if args.show_tokens:
    print_token_summary(output_content, args.token_encoding)
```

## Usage

```bash
treemapper . --tokens                    # 12,847 tokens (o200k_base)
treemapper . --tokens --copy             # tokens + clipboard

pip install treemapper[tokens]           # exact counts with tiktoken
```
