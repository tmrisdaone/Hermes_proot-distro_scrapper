#!/usr/bin/env python3
"""DuckDuckGo + Groq search script with modular sub‑agent architecture.

The script is designed to be executed via ``python3 scripts/ddg_groq_search.py "<query>"``.

It is split into a small set of reusable functions that can be invoked independently
or orchestrated by an external agent.  Each function carries its own type hints
and basic error handling.  Results are cached using a simple JSON file under
``~/.hermes/.ddg_cache.json`` to reduce network calls when the same query is
issued frequently.

Sub‑agent usage is supported via command‑line flags:

* ``--search`` – run only the DuckDuckGo search part.
* ``--summarize`` – only run the summariser on the cached search results.
* ``--all`` – full orchestration (default).

The script is intentionally lightweight – no external binaries are required –
and it works inside the Ubuntu proot‑distro that the user already runs.
"""

# Standard library imports
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple

# Third‑party imports
try:  # pragma: no cover
    import ddgs
except Exception as exc:  # pragma: no cover
    print(f"[ERROR] failed to import ddgs: {exc}", file=sys.stderr)
    ddgs = None  # type: ignore

try:  # pragma: no cover
    import groq
except Exception as exc:  # pragma: no cover
    print(f"[ERROR] failed to import groq: {exc}", file=sys.stderr)
    groq = None  # type: ignore

# ---------------------------------------------------------------------------
# Configuration & helpers
# ---------------------------------------------------------------------------
# dotenv fallback – the user may keep a ``~/.hermes/.env`` file with the API key.
_dotenv = Path.home() / ".hermes" / ".env"
if _dotenv.is_file():
    try:  # pragma: no cover
        for line in _dotenv.read_text().splitlines():
            if line.strip() and not line.startswith("#"):
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())
    except Exception:  # pragma: no cover
        pass

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "[REDACTED]")
DEFAULT_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
CACHE_TTL: int = int(os.getenv("DDG_CACHE_TTL", "300"))  # 5 min
CACHE_FILE: Path = Path.home() / ".hermes" / ".ddg_cache.json"

# ======================================================================================
# 1. DuckDuckGo search
# ======================================================================================
def search_duckduckgo(query: str, timeout: int = 7) -> List[Dict[str, str]]:
    """Return DuckDuckGo results for *query* using :mod:`ddgs`.

    Parameters
    ----------
    query:
        Search query string.
    timeout:
        Seconds to wait for the network call.
    """
    if not ddgs:  # pragma: no cover
        raise RuntimeError("ddgs library not available")
    return ddgs.results(query, timeout=timeout)

# ======================================================================================
# 2. Caching wrapper
# ======================================================================================
def _load_cache() -> Dict[str, Tuple[float, List[Dict[str, str]]]]:
    if CACHE_FILE.is_file():
        try:  # pragma: no cover
            return json.load(CACHE_FILE)
        except Exception:
            return {}
    return {}

_CACHE: Dict[str, Tuple[float, List[Dict[str, str]]]] = _load_cache()


def _persist_cache() -> None:  # pragma: no cover
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        CACHE_FILE.write_text(json.dumps(_CACHE, indent=2))
    except Exception:
        pass

# Run on exit to guarantee persistence
import atexit
atexit.register(_persist_cache)


def cached_search(query: str, timeout: int = 7) -> List[Dict[str, str]]:
    """Return cached results if fresh else run a fresh DuckDuckGo search.
    """
    entry = _CACHE.get(query)
    if entry:
        ts, data = entry
        if time.time() - ts < CACHE_TTL:
            return data
        _CACHE.pop(query)
    results = search_duckduckgo(query, timeout=timeout)
    _CACHE[query] = (time.time(), results)
    return results

# ======================================================================================
# 3. Summariser using Groq
# ======================================================================================
class Summariser:  # pragma: no cover by static analysis
    def __init__(self, api_key: str = GROQ_API_KEY, model: str = DEFAULT_MODEL):
        if not groq:
            raise RuntimeError("groq library not available")
        self.client = groq.Groq(api_key)
        self.model = model

    def summarize(self, text: str, temperature: float = 0.3, max_tokens: int = 512) -> str:
        """Return a short summary of *text* using the Groq model."""
        prompt = (
            "Summarise the following content in a concise paragraph, preserving key facts:\n\n"
            f"{text}"
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            raise RuntimeError(f"Groq summarisation failed: {exc}")

# ======================================================================================
# 4. Formatting helpers
# ======================================================================================
def format_output(query: str, summary: str, sources: List[str], model: str) -> dict:
    """Return a serialisable dictionary ready for printing or JSON export."""
    return {
        "query": query,
        "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "model": model,
        "summary": summary,
        "sources": sources,
    }

# ======================================================================================
# 5. CLI entry point
# ======================================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DuckDuckGo + Groq search script")
    parser.add_argument("query", help="Search query string")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Groq model to use")
    parser.add_argument("--no-cache", action="store_true", help="Disable cache lookup")
    parser.add_argument("--out", help="Write raw JSON to file")
    parser.add_argument("--part", choices=["search", "summarise", "all"], default="all", help="Run single part only")

    args = parser.parse_args()

    # 1. Search
    if args.no_cache:
        search_results = search_duckduckgo(args.query)
    else:
        search_results = cached_search(args.query)

    if args.part in ("search", "all"):
        print("\n**** DuckDuckGo Results ****")
        for r in search_results:
            print(f"- {r.get('title', 'no title')} ({r.get('src', '')})")

    if args.part in ("summarise", "all"):
        # gather text for summarisation
        concat_text = "\n".join(r.get("text", "") for r in search_results if r.get("text"))
        summariser = Summariser(api_key=GROQ_API_KEY, model=args.model)
        summary = summariser.summarize(concat_text)
        sources = [r.get("src", "[no src]") for r in search_results]
        out = format_output(args.query, summary, sources, args.model)
        if args.out:
            Path(args.out).write_text(json.dumps(out, indent=2))
        else:
            print("\n===== Summary =====")
            print(summary)
            print("\n===== Sources =====")
            for src in sources:
                print("-", src)
    sys.exit(0)
