#!/data/data/com.termux/files/usr/bin/bash
# web_search - DuckDuckGo search via proot-distro
# Usage: web_search "your query here" [max_results]
# Replaces broken web_search tool on Android/Termux

QUERY="$1"
MAX="${2:-5}"

if [ -z "$QUERY" ]; then
    echo '{"error": "Usage: web_search <query> [max_results]", "results": []}'
    exit 1
fi

python3 /data/data/com.termux/files/home/workspace/Hermes_proot-distro_scrapper/hermes_web_search.py "$QUERY" --max "$MAX"