# CLAUDE.md


Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## Project Overview

Language detection utility that processes `data1.csv` and outputs language-labeled results to `result2.csv`. Supports detecting Chinese (Simplified/Traditional/Cantonese), EnglHow to buy tickets on Fantopia?ish, French, Japanese, Korean, and other languages.

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
./publish.sh 2.8.0
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

   # Build sdist first
   maturin build --release --features python --out target/wheels --sdist

   # Build all wheels
   for py in 3.10 3.11 3.12 3.13 3.14; do
       maturin build --interpreter $(uv python list --only-installed | grep "cpython-${py}" | head -1 | awk '{print $2}') --release --features python --out target/wheels
   done

   # Upload wheels + sdist
   pipx run twine upload target/wheels/lingua_slim-x.x.x-*.whl target/wheels/lingua_slim-x.x.x.tar.gz
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

- **Binary wheels + sdist**: Always publish both wheels AND source distribution (sdist) for cross-platform compatibility
- **Poetry compatibility root cause**: Poetry filters out wheels that don't match the target environment (CPU arch, glibc version). Without sdist, there's no fallback
- **Solution: wheels + sdist**: Publish wheels for common platforms (3.10-3.14) AND sdist for environments where no wheel matches
- **uv advantage**: `uv pip install` handles binary wheels better than Poetry - it can pick the best matching wheel
- **twine upload**: Use `twine upload` instead of curl - it properly handles version management

### PyPI Status

- Package: `lingua-slim`
- Latest version: 2.8.0
- Requires: Python >=3.10
- Available packages:
  - 5 wheels: cp310, cp311, cp312, cp313, cp314
  - **Source distribution (sdist)** ← for cross-platform compatibility
  - `lingua_slim-2.8.0.tar.gz`
