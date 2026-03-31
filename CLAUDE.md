# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Language detection utility that processes `data1.csv` and outputs language-labeled results to `result2.csv`. Supports detecting Chinese (Simplified/Traditional distinction), English, Japanese, Korean, and other languages.

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

- **main.py** - Entry point with:
  - `detect_language(text)` - Main detection function using lingua-py
  - `is_traditional_chinese(text)` - Chinese variant detection (currently uses Unicode ranges, which is unreliable)
  - `TRADITIONAL_CHINESE_RANGES` - Unicode ranges for Traditional Chinese characters
  - `LANG_NAME_MAP` - Maps lingua Language enum to display names

- **Input**: `data1.csv` with columns: `user_id`, `content`
- **Output**: `result2.csv` with columns: `user_id`, `content`, `language`

## Important Notes

- **Package installation**: Always use `uv add` or `uv pip install`, NOT `pip install` directly
- **Chinese variant detection issue**: The current `is_traditional_chinese()` uses Unicode range matching which is unreliable - many Traditional Chinese characters fall outside the predefined ranges (e.g., 愛, 國, 學). A better approach is to use OpenCC conversion comparison:
  1. Convert text: Simplified → Traditional
  2. If result differs significantly → original was Traditional
  3. If mostly unchanged → original was Simplified
- OpenCC (`opencc-python-reimplemented`) is already installed in the project
