# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Language detection utility that processes `data1.csv` and outputs language-labeled results to `result2.csv`. Supports detecting Chinese (Simplified/Traditional/Cantonese), English, French, Japanese, Korean, and other languages.

**⚠️ IMPORTANT: This project uses Python 3.12 ONLY. Do NOT use Python 3.13.**

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
- **Poetry compatibility issue**: Poetry may fail with "Unable to find installation candidates" if `requires-python` doesn't match the environment. Solution: set `requires-python = ">=3.12"`

## Publishing lingua-slim to PyPI

### Prerequisites

- Python 3.12 only (MUST)
- `maturin` installed (`pipx install maturin`)
- PyPI token in `~/.pypirc`

### Publishing Steps

1. **Pin Python version**:
   ```bash
   uv python pin 3.12
   ```

2. **Update version** in `lingua-rs/Cargo.toml`:
   ```toml
   [package]
   name = "lingua"
   version = "2.4.0"  # Update this
   ```

3. **Update classifiers** in `lingua-rs/pyproject.toml` (only list 3.12):
   ```toml
   classifiers = [
       ...
       "Programming Language :: Python :: 3.12",  # Only 3.12, remove 3.13/3.14
       ...
   ]
   ```

4. **Commit lingua-rs changes** (separate git repo):
   ```bash
   cd lingua-rs
   git add Cargo.toml Cargo.lock pyproject.toml
   git commit -m "feat: bump version to x.x.x"
   ```

5. **Build wheel**:
   ```bash
   cd lingua-rs
   maturin build --interpreter /usr/bin/python3.12 --release
   ```

6. **Upload to PyPI**:
   ```bash
   twine upload --skip-existing target/wheels/lingua_slim-*.whl
   ```

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
- **Poetry compatibility**: Poetry fails with "Unable to find installation candidates" when `requires-python` doesn't match environment - set `requires-python = ">=3.12"`
- **uv advantage**: `uv pip install` handles binary wheels better than Poetry
- **Python 3.12 ONLY**: Coze plugin uses Python 3.12, so PyPI must host cp312 wheels

### PyPI Status

- Package: `lingua-slim`
- Latest version: 2.4.0
- Available wheels: `lingua_slim-2.4.0-cp312-cp312-manylinux_2_34_x86_64.whl` (Python 3.12)
