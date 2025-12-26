# Plan: Clipboard Copy Feature

Add `--copy/-c` and `--copy-only` flags to copy output to system clipboard.

## Design

- **No external dependencies** — use native OS tools (pbcopy, xclip, wl-copy)
- **Error handling** — warning to stderr, exit 0 (non-critical)
- **Feedback** — `Copied to clipboard (12.5 KB)` to stderr

## Flag Behavior

| Flags | stdout | file | clipboard |
|-------|--------|------|-----------|
| (none) | ✓ | - | - |
| `-o file` | - | ✓ | - |
| `-c` / `--copy` | ✓ | - | ✓ |
| `--copy -o file` | - | ✓ | ✓ |
| `--copy-only` | - | - | ✓ |

## Detection Logic

```
macOS: pbcopy
Windows: clip.exe
Linux (Wayland): wl-copy
Linux (X11): xclip -selection clipboard
```

## Implementation

### NEW: `src/treemapper/clipboard.py`

```python
import os
import platform
import shutil
import subprocess

class ClipboardError(Exception):
    pass

def detect_clipboard_command() -> list[str] | None:
    system = platform.system()
    if system == "Darwin":
        return ["pbcopy"]
    if system == "Windows":
        return ["clip"]
    if system in ("Linux", "FreeBSD"):
        if os.environ.get("WAYLAND_DISPLAY") and shutil.which("wl-copy"):
            return ["wl-copy"]
        if os.environ.get("DISPLAY") and shutil.which("xclip"):
            return ["xclip", "-selection", "clipboard"]
    return None

def copy_to_clipboard(text: str) -> None:
    cmd = detect_clipboard_command()
    if cmd is None:
        raise ClipboardError("No clipboard tool found")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    _, stderr = proc.communicate(input=text.encode("utf-8"), timeout=5)
    if proc.returncode != 0:
        raise ClipboardError(stderr.decode())

def clipboard_available() -> bool:
    return detect_clipboard_command() is not None
```

### UPDATE: `cli.py`

```python
# ParsedArgs
copy: bool
copy_only: bool

# Arguments
parser.add_argument("-c", "--copy", action="store_true")
parser.add_argument("--copy-only", action="store_true")
```

### UPDATE: `treemapper.py`

```python
if args.copy:
    try:
        copy_to_clipboard(output_content)
        print(f"Copied to clipboard ({len(output_content) / 1024:.1f} KB)", file=sys.stderr)
    except ClipboardError as e:
        logging.warning(f"Clipboard: {e}")

if args.copy_only and args.output_file is None:
    return
```

## Testing

Skip clipboard tests in CI (no display):

```python
@pytest.mark.skipif(os.environ.get("CI") or not os.environ.get("DISPLAY"))
def test_clipboard_roundtrip():
    pass
```
