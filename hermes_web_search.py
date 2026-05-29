#!/usr/bin/env python3
"""Hermes web_search tool — DuckDuckGo via proot-distro + optional Groq summarization."""
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Optional

# ─── Config ───────────────────────────────────────────────
CACHE_FILE = Path.home() / ".hermes" / ".ddg_cache.json"
CACHE_TTL = int(os.getenv("DDG_CACHE_TTL", "300"))
DEFAULT_MAX = int(os.getenv("DDG_MAX_RESULTS", "5"))

# ─── Cache helpers ─────────────────────────────────────────
def _load_cache() -> dict:
    if CACHE_FILE.is_file():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            return {}
    return {}

def _save_cache(cache: dict):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        CACHE_FILE.write_text(json.dumps(cache, indent=2))
    except Exception:
        pass

# ─── Search via proot ──────────────────────────────────────
def search_duckduckgo(query: str, max_results: int = DEFAULT_MAX) -> dict:
    """Run DuckDuckGo search inside proot-distro ubuntu."""
    safe_query = json.dumps(query)
    script = (
        "from ddgs import DDGS\n"
        "import json\n"
        f"results = list(DDGS().text({safe_query}, max_results={max_results}))\n"
        "print(json.dumps(results))\n"
    )
    try:
        result = subprocess.run(
            ["proot-distro", "login", "ubuntu", "--", "python3", "-c", script],
            capture_output=True, text=True, timeout=20
        )
    except subprocess.TimeoutExpired:
        return {"error": "Search timed out after 20s", "results": []}  # type: ignore
    
    if result.returncode != 0:
        stderr = result.stderr.strip()
        return {"error": f"Search failed (exit {result.returncode}): {stderr}", "results": []}  # type: ignore
    
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if line.startswith("["):
            try:
                data = json.loads(line)
                if isinstance(data, list):
                    return {"error": None, "results": data}  # type: ignore
            except json.JSONDecodeError:
                continue
    
    return {"error": "Could not parse search results", "results": []}  # type: ignore

# ─── Groq summarizer (optional) ───────────────────────────
def summarize_with_groq(text: str, max_tokens: int = 512) -> Optional[str]:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return None
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a search result summarizer. Give a concise (2-3 sentence) summary of the key information."},
            {"role": "user", "content": f"Summarize these search results:\n\n{text}"}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3
    }).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Groq error: {e}]"

# ─── Main ──────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print(json.dumps({
            "usage": "hermes_web_search.py <query> [--max N] [--summarize]",
            "description": "Search DuckDuckGo via proot-distro. Returns JSON.",
            "env_vars": "GROQ_API_KEY, GROQ_MODEL, DDG_CACHE_TTL, DDG_MAX_RESULTS"
        }, indent=2))
        sys.exit(0)

    query = sys.argv[1]
    max_results = DEFAULT_MAX

    if "--max" in sys.argv:
        idx = sys.argv.index("--max")
        if idx + 1 < len(sys.argv):
            try:
                max_results = int(sys.argv[idx + 1])
            except ValueError:
                pass

    # Check cache
    cache = _load_cache()
    cache_key = f"{query}::{max_results}"
    now = time.time()
    from_cache = False

    if cache_key in cache:
        ts, cached_data = cache[cache_key]
        if now - ts < CACHE_TTL:
            result = cached_data
            from_cache = True
        else:
            del cache[cache_key]
            result = search_duckduckgo(query, max_results)
    else:
        result = search_duckduckgo(query, max_results)

    if not from_cache and isinstance(result.get("results"), list) and len(result.get("results", [])):
        cache[cache_key] = (now, result)
        _save_cache(cache)

    # Format output
    output: dict[str, Any] = {
        "query": query,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "cached": from_cache,
        "web": result.get("results", []),
        "error": result.get("error")
    }

    # If there are results, optionally summarize them
    results_raw = result.get("results", [])
    if isinstance(results_raw, list) and results_raw and "--summarize" in sys.argv:
        texts = [r.get("body", "") for r in results_raw if isinstance(r, dict) and r.get("body")]
        if texts:
            combined = "\n\n".join(texts)
            summary = summarize_with_groq(combined[:3000])
            if summary:
                output["summary"] = summary

    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()