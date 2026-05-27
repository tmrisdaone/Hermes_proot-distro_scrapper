# DuckDuckGo + Groq Search (proot-browser-search)

This repository contains a high-reliability web search tool designed for Android/Termux environments.

## Overview

The `ddg_groq_search.py` script enables reliable DuckDuckGo searches within an Ubuntu `proot-distro` environment. This approach bypasses common Rust-NDK limitation panics encountered when running the native `ddgs` library directly on Android.

### Key Features
- **Proot-isolated Execution**: Runs inside Ubuntu to ensure dependency stability.
- **Groq Integration**: Uses Groq LLMs to summarize search results into a concise paragraph.
- **Smart Caching**: Implements a local JSON cache (`~/.hermes/.ddg_cache.json`) with a configurable TTL to reduce redundant API calls.
- **Modular Design**: Supports running the search and summarization steps independently.

## Installation & Usage

### Prerequisites
- `proot-distro` installed and configured with Ubuntu.
- A Groq API Key.

### Quick Start
1. Place the script in your environment.
2. Execute via:
   ```bash
   python3 ddg_groq_search.py "Your search query here"
   ```

### Configuration
The script reads the following environment variables from `~/.hermes/.env` or your system shell:
- `GROQ_API_KEY`: Your API key for Groq.
- `GROQ_MODEL`: The model to use for summarization (default: `llama-3.1-8b-instant`).
- `DDG_CACHE_TTL`: Cache expiration time in seconds (default: `300`).

## Hermes Skill Integration
This tool is implemented as the `proot-browser-search` skill in Hermes Agent, allowing the agent to perform autonomous, verified web research on mobile hardware.
