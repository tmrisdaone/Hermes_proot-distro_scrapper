# Hermes_proot-distro_scrapper

A Python utility that combines DuckDuckGo search results with optional Groq LLM
summarization. Runs the search backend inside `proot-distro` Ubuntu so the
`ddgs` library (which is hard to install in bare Termux) works on Android.

## Usage

```bash
# Basic search (no API key needed)
./web_search.sh "your query here"

# With LLM summarization (requires GROQ_API_KEY in your env)
export GROQ_API_KEY=sk-...
./web_search.sh "your query here" 5
```

`web_search.sh` wraps `hermes_web_search.py` with `~/.hermes/proot` paths
already configured for this device.

## Requirements

- Python 3.10+ (uses PEP 604 `int | None` syntax)
- `proot-distro` with Ubuntu installed (`proot-distro install ubuntu`)
- Inside the proot Ubuntu, the `ddgs` package:
  ```bash
  proot-distro login ubuntu -- apt install python3-pip
  proot-distro login ubuntu -- pip3 install ddgs
  ```

## Configuration

`GROQ_API_KEY` is read from your environment and **passed to the proot
container as an environment variable** (not interpolated into a `python -c`
argument, so it does not appear in `ps aux`). When the key is missing, the
`--summarize` flag is a no-op and `summary_error: "GROQ_API_KEY not set"`
is returned in the JSON output.

## API

```python
from hermes_web_search import search

result = search("my query", max_results=5)
# {
#   "query": "my query",
#   "timestamp": "2026-06-19 12:34:56",
#   "cached": false,
#   "web": [
#     {"title": ..., "url": ..., "snippet": ..., "content": "<full page via Jina>"}
#   ]
# }
```

`content` is the full page text fetched via [Jina AI Reader](https://r.jina.ai/),
capped at 8000 characters. Cached on disk for 5 minutes.

## License

MIT
