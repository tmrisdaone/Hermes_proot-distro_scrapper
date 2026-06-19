#!/data/data/com.termux/files/usr/bin/bash
# web_search - DuckDuckGo search via proot-distro
# Usage: web_search "your query here" [max_results]
#
# The script lives next to hermes_web_search.py; if you copy just this
# wrapper somewhere else, edit SCRIPT_DIR below or set HERMES_SEARCH_PY
# in your environment.

set -e

QUERY="$1"
MAX="${2:-5}"

if [ -z "$QUERY" ]; then
    echo '{"error": "Usage: web_search <query> [max_results]", "results": []}'
    exit 1
fi

# Locate hermes_web_search.py: prefer $HERMES_SEARCH_PY, else sibling of this script.
if [ -n "${HERMES_SEARCH_PY:-}" ] && [ -f "$HERMES_SEARCH_PY" ]; then
    SCRIPT="$HERMES_SEARCH_PY"
elif [ -f "$(dirname "$0")/hermes_web_search.py" ]; then
    SCRIPT="$(dirname "$0")/hermes_web_search.py"
else
    echo '{"error": "hermes_web_search.py not found. Set HERMES_SEARCH_PY."}' >&2
    exit 1
fi

exec python3 "$SCRIPT" "$QUERY" --max "$MAX"
