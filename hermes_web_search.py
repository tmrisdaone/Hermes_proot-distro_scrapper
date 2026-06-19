#!/usr/bin/env python3
"""Hermes web_search tool — DuckDuckGo via proot-distro + page reader via Jina AI."""
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

CACHE_PATH = Path.home() / ".hermes" / ".ddg_cache.json"
CACHE_TTL = 300  # seconds
PROOT = "proot-distro"
UBUNTU_CMD = ["login", "ubuntu", "--", "bash", "-c"]


def _run_proot(python_code: str, env: dict | None = None) -> tuple[str, int]:
    """Run python_code inside proot-distro ubuntu. Returns (output, exit_code).

    Security note: `python_code` is passed as a single argv item. Any string
    interpolation into it (e.g. secrets, file paths) becomes visible in
    `ps aux`. Use `env` to pass sensitive values via env vars instead.
    """
    cmd = [PROOT] + UBUNTU_CMD + [f'python3 -c {repr(python_code)}']
    full_env = {**os.environ, **(env or {})}
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45,
                                env=full_env)
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", 124
    except Exception as e:
        return str(e), 1


def _cache_get(key: str):
    if not CACHE_PATH.exists():
        return None
    try:
        data = json.loads(CACHE_PATH.read_text())
        entry = data.get(key)
        if entry and time.time() - entry.get("ts", 0) < CACHE_TTL:
            return entry["val"]
    except Exception:
        pass
    return None


def _cache_set(key: str, val):
    try:
        data = {}
        if CACHE_PATH.exists():
            data = json.loads(CACHE_PATH.read_text())
        data[key] = {"ts": time.time(), "val": val}
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


def _search_ddg(query: str, max_results: int = 5) -> list[dict]:
    code = (
        "from ddgs import DDGS; "
        f"results = DDGS().text({repr(query)}, max_results={max_results}); "
        "import json; print(json.dumps(results))"
    )
    stdout, rc = _run_proot(code)
    if rc != 0:
        return []
    try:
        raw = json.loads(stdout)
        # Normalize
        out = []
        for r in raw:
            out.append({
                "title": r.get("title", ""),
                "href": r.get("href", r.get("url", "")),
                "body": r.get("body", r.get("snippet", ""))[:300],
            })
        return out
    except Exception:
        return []


def _read_page(url: str) -> str:
    """Fetch full page text via Jina AI Reader (free, no auth)."""
    cache_key = f"page:{url}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    jina_url = f"https://r.jina.ai/{url}"
    try:
        req = urllib.request.Request(jina_url, headers={"Accept": "text/plain", "User-Agent": "Hermes/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            # Truncate to reasonable size
            text = text[:8000]
            _cache_set(cache_key, text)
            return text
    except Exception as e:
        return f"[Error reading page: {e}]"


def search(query: str, max_results: int = 5) -> dict:
    """Search DuckDuckGo and auto-fetch full page content via Jina AI."""
    cache_key = f"search:{query.lower()}:{max_results}"
    cached = _cache_get(cache_key)
    if cached is not None:
        results = cached
    else:
        results = _search_ddg(query, max_results)
        _cache_set(cache_key, results)

    out = {
        "query": query,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cached": cached is not None,
        "web": [],
    }

    for r in results:
        entry = {"title": r["title"], "url": r["href"], "snippet": r["body"]}
        entry["content"] = _read_page(r["href"])
        out["web"].append(entry)

    return out


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Hermes web search tool (proot-distro + Jina AI)")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--max", type=int, default=5, help="Max results")
    parser.add_argument("--summarize", action="store_true", help="Summarize with Groq (requires GROQ_API_KEY)")
    args = parser.parse_args()

    result = search(args.query, args.max)

    if args.summarize:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if api_key:
            # Build a quick summary prompt from results
            snippets = "\n".join(
                f"- {w['title']}: {w.get('content', w['snippet'])[:300]}"
                for w in result["web"]
            )
            prompt = f"Summarize these search results for: {args.query}\n\n{snippets}"
            summary = _groq_summarize(api_key, prompt)
            result["summary"] = summary
        else:
            result["summary_error"] = "GROQ_API_KEY not set"

    print(json.dumps(result, indent=2, ensure_ascii=False))


def _groq_summarize(api_key: str, prompt: str) -> str:
    # Pass the API key via env var, NOT as a literal interpolated into
    # the python source — that would expose the key in `ps aux` on the
    # proot login. The receiving script reads GROQ_API_KEY from os.environ.
    code = (
        "import urllib.request, json, os\n"
        "key = os.environ['GROQ_API_KEY']\n"
        "body = json.dumps({\n"
        '    "model": "llama-3.3-70b-versatile",\n'
        '    "messages": [{"role": "user", "content": ' + repr(prompt) + '}],\n'
        '    "max_tokens": 500\n'
        "}).encode()\n"
        "req = urllib.request.Request('https://api.groq.com/openai/v1/chat/completions',\n"
        "    data=body,\n"
        "    headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},\n"
        "    method='POST')\n"
        "try:\n"
        "    with urllib.request.urlopen(req, timeout=20) as r:\n"
        "        d = json.loads(r.read())\n"
        "        print(d['choices'][0]['message']['content'])\n"
        "except Exception as e:\n"
        "    print(f'[Groq error: {e}]')\n"
    )
    stdout, rc = _run_proot(code, env={"GROQ_API_KEY": api_key})
    return stdout.strip() if rc == 0 else f"[Groq failed: rc={rc}]"


if __name__ == "__main__":
    main()
