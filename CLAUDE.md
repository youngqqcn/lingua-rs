# CLAUDE.md

## Project Overview

Language detection utility that processes `data1.csv` and outputs language-labeled results to `result2.csv`. Supports detecting Chinese (Simplified/Traditional/Cantonese), English, French, Japanese, Korean, and other languages.

**⚠️ IMPORTANT: This project uses Python 3.12 for development. lingua-slim package supports Python 3.10-3.14.**

## Project Structure

```
cs_language_detect/
├── .venv/                  # Virtual environment (managed by uv)
├── lingua-rs/              # Rust/Python package (lingua-slim)
│   ├── Cargo.toml          # Rust project config
│   ├── pyproject.toml     # Python package config
│   ├── src/               # Rust source code
│   ├── language-models/    # Language model data (en, fr, id, ms, pt, es)
│   └── target/wheels/     # Built wheels output here
├── language_detect_v2.py   # Main detection library (Unicode + OpenCC + lingua-slim)
├── main.py                # Entry point
├── data1.csv              # Input data
├── result2.csv            # Output results
└── pyproject.toml         # Project dependencies
```

## Commands

```bash
# Install dependencies (REQUIRED: use uv)
uv sync

# Run the language detection
uv run python main.py

# Add a new dependency
uv add <package-name>
```

## 禁止使用直接安装依赖

- **DO NOT**: Use `pip install` or `uv pip install` directly to install dependencies
- **DO**: Use `uv add` to install dependencies

## Architecture

### language_detect_v2.py

Unified language detector combining multiple detection strategies:

1. **Chinese variants** (OpenCC-based):
   - `Chinese(Simplified)` / `Chinese(Traditional)` / `Cantonese`
   - Uses OpenCC conversion comparison for accurate detection

2. **Unicode-based detection**:
   - Japanese, Korean, Thai, Russian, Arabic, Hindi, Tamil, Greek, Hebrew, Vietnamese

3. **lingua-slim** (Rust-based):
   - English, French, Malay, Spanish, Portuguese, Indonesian

### lingua-rs Subdirectory

The `lingua-rs/` directory is a **separate Rust project** that publishes `lingua-slim` to PyPI.

- Package name on PyPI: `lingua-slim`
- Python import name: `lingua` (NOT `lingua_slim`)
- Built with `maturin` (Rust + Python bindings)
- Only publishes binary wheels (`.whl`), no source distribution

## Important Notes

- **Package installation**: Always use `uv add`, NOT `pip install` directly
- **Chinese variant detection**: Uses OpenCC conversion comparison (reliable), not Unicode ranges
- **lingua-slim import**: Use `from lingua import LanguageDetector`, NOT `from lingua_slim`
- **Poetry compatibility issue**: Poetry may fail with "Unable to find installation candidates" if `requires-python` doesn't match the environment. Solution: Build wheels for ALL Python versions (3.10-3.14) so Poetry can find a matching binary wheel

## Publishing lingua-slim to PyPI (Multi-Version Wheels)

### Prerequisites

- Python 3.12 only (MUST) for building
- `maturin` installed (`pipx install maturin`)
- PyPI token in `~/.pypirc`
- `uv` for managing Python versions

### Publishing Steps

**Option A: Use the publish script (recommended)**
```bash
cd lingua-rs
./publish.sh 2.6.0
```

**Option B: Manual steps**

1. **Update version** in `lingua-rs/Cargo.toml`:
   ```toml
   [package]
   name = "lingua"
   version = "2.6.0"  # Update this
   ```

2. **Update version** in `lingua-rs/pyproject.toml`:
   ```toml
   [project]
   version = "2.6.0"  # Update this
   ```

3. **Commit, build, upload**:
   ```bash
   cd lingua-rs
   git add Cargo.toml Cargo.lock pyproject.toml
   git commit -m "feat: bump version to x.x.x"

   # Build all wheels
   for py in 3.10 3.11 3.12 3.13 3.14; do
       maturin build --interpreter $(uv python list --only-installed | grep "cpython-${py}" | head -1 | awk '{print $2}') --release --out target/wheels
   done

   # Upload
   twine upload target/wheels/lingua_slim-x.x.x-*.whl
   ```

4. **Verify on PyPI**:
   ```bash
   curl -s https://pypi.org/pypi/lingua-slim/<version>/json | python3 -c "import sys,json; d=json.load(sys.stdin); print('Available wheels:'); [print(' ', w['filename']) for w in d['urls']]"
   ```

5. **Update parent repo CLAUDE.md** with new PyPI status

### ⚠️ Important: Separate Git Repository

**`lingua-rs/` is a separate git repository** - you MUST commit changes there separately:

```bash
cd lingua-rs
git add <changed files>
git commit -m "your message"
```

Do NOT confuse with the main project commits in the parent directory.

### Key Lessons

- **Binary-only package**: `lingua-slim` publishes only `.whl` files, no `sdist`
- **Poetry compatibility root cause**: Poetry validates ALL Python versions allowed by `requires-python` against available wheels. If any version lacks a wheel, Poetry rejects the entire package
- **Solution: multi-version wheels**: Build wheels for all Python versions (3.10, 3.11, 3.12, 3.13, 3.14) so Poetry can find a matching binary wheel regardless of environment
- **uv advantage**: `uv pip install` handles binary wheels better than Poetry - it can pick the best matching wheel
- **twine upload**: Use `twine upload` instead of curl - it properly handles version management
- **--skip-existing**: Only skips if exact filename exists; for new versions, use `twine upload` without this flag
- **curl upload issue**: curl returns 404 even when upload succeeds (file already exists on PyPI), making it unreliable for verification

### PyPI Status

- Package: `lingua-slim`
- Latest version: 2.7.0
- Requires: Python >=3.10
- Available wheels:
  - `lingua_slim-2.7.0-cp310-cp310-manylinux_2_34_x86_64.whl` (Python 3.10)
  - `lingua_slim-2.7.0-cp311-cp311-manylinux_2_34_x86_64.whl` (Python 3.11)
  - `lingua_slim-2.7.0-cp312-cp312-manylinux_2_34_x86_64.whl` (Python 3.12)
  - `lingua_slim-2.7.0-cp313-cp313-manylinux_2_34_x86_64.whl` (Python 3.13)
  - `lingua_slim-2.7.0-cp314-cp314-manylinux_2_34_x86_64.whl` (Python 3.14)
