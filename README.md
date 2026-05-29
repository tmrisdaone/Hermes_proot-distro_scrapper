# DuckDuckGo + Groq Search (proot-browser-search)

This repository contains a **reliable web search tool** designed for Android/Termux environments where the native `ddgs` library crashes due to Rust-NDK limitations.

## Overview

The `hermes_web_search.py` script enables reliable DuckDuckGo searches **inside an Ubuntu proot-distro environment**, bypassing Rust-NDK panics entirely. Returns clean JSON for easy parsing by Hermes Agent or any tool.

### Features

- **Proot-isolated**: Runs inside Ubuntu proot-distro to avoid Android Rust-NDK crashes
- **Two interfaces**: Standalone Python script + shell wrapper
- **Smart caching**: JSON cache at `~/.hermes/.ddg_cache.json` with configurable TTL (default 5 min)
- **Optional Groq summarization**: Pass `--summarize` for AI-powered result summary
- **JSON output**: Easy to pipe into other tools, Hermes, or scripts

## Installation

### Prerequisites
- `proot-distro` installed with Ubuntu
- Python 3 + `pip install ddgs` inside the proot Ubuntu

### Quick Start

```bash
# Search with 3 results
python3 hermes_web_search.py "your query" --max 3

# Search with Groq summarization
python3 hermes_web_search.py "your query" --max 5 --summarize

# Or use the shell wrapper
./web_search.sh "your query" 3
```

### Sample output

```json
{
  "query": "what is deepseek",
  "timestamp": "2026-05-29 21:49:29",
  "cached": false,
  "web": [
    {
      "title": "DeepSeek - Wikipedia",
      "href": "https://en.wikipedia.org/wiki/DeepSeek",
      "body": "Based in Hangzhou, Zhejiang, ..."
    }
  ],
  "error": null
}
```

## Configuration (env vars)

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | — | Required for `--summarize` |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | Groq model for summarization |
| `DDG_CACHE_TTL` | `300` | Cache TTL in seconds |
| `DDG_MAX_RESULTS` | `5` | Default result count |

## Hermes Agent Integration

The script is designed to be called from Hermes Agent via `terminal` tool:

```bash
python3 /path/to/hermes_web_search.py "query" --max 5
```

It's also registered as the `proot-browser-search` skill in Hermes, so you can invoke it with: `hermes script run proot-search -- "query"`

## Comparison with ddg_groq_search.py

The old `ddg_groq_search.py` used the deprecated `ddgs.results()` API which is no longer available in newer `ddgs` library versions. The new `hermes_web_search.py` uses `DDGS().text()` which is the current API.
