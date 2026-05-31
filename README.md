# 🌐 Hermes Proot-Distro Web Search

A high-reliability web search engine specifically engineered for **Android/Termux** environments. 

## ⚠️ Why this exists?
Native Python libraries like `duckduckgo_search` (`ddgs`) often crash on Android due to **Rust-NDK panics** (specifically issues with the `jiter` library and memory allocation). 

This tool solves this by executing the search logic inside a **proot-distro Ubuntu** container, where the native binaries are stable, while providing a clean JSON interface for the Hermes Agent on the Termux host.

## 🚀 Features

- **🛡️ Rust-Panic Proof**: Runs inside Ubuntu proot-distro to ensure 100% stability on ARM64 Android.
- **⚡ High Performance**: Uses `DDGS().text()` for rapid, lightweight search retrieval.
- **🛠️ Built-in Page Reader (Jina AI)**: Every result includes full article content fetched via [Jina AI Reader](https://r.jina.ai/) — so you get the actual article text, not just snippets. No API key required.
- **💾 Smart Caching**: Implements a local JSON cache at `~/.hermes/.ddg_cache.json` with a configurable TTL (default 5m) to avoid rate limits and speed up repeated queries.
- **🤖 AI Summarization**: Integrated with Groq LLMs to condense multiple search results into a single, concise answer via the `--summarize` flag.
- **🛠️ Dual Interface**:
  - **Python Script**: For programmatic use and Hermes Agent integration.
  - **Shell Wrapper**: For quick CLI usage in Termux.

## 📦 Installation

### 1. Setup Proot Ubuntu
```bash
pkg install proot-distro
proot-distro install ubuntu
proot-distro login ubuntu -- bash -c "apt update && apt install python3 python3-pip -y && pip install ddgs"
```

### 2. Deploy Tool
Clone this repo to your Termux home:
```bash
git clone https://github.com/tmrisdaone/Hermes_proot-distro_scrapper.git ~/workspace/Hermes_proot-distro_scrapper
chmod +x ~/workspace/Hermes_proot-distro_scrapper/*.py
chmod +x ~/workspace/Hermes_proot-distro_scrapper/*.sh
```

## 🛠️ Usage

### Option A: Direct Python (Recommended for Agents)
```bash
python3 hermes_web_search.py "What is the latest Llama model?" --max 5 --summarize
```

### Option B: Shell Wrapper (Recommended for Humans)
```bash
./web_search.sh "Latest AI news" 3
```

### Command Line Arguments
| Flag | Description | Default |
|------|-------------|----------|
| `query` | The search string | Required |
| `--max N` | Number of results to fetch | `5` |
| `--summarize` | Uses Groq to summarize the body of the results | Disabled |

## ⚙️ Configuration (Environment Variables)

These can be added to your `~/.bashrc` or `~/.hermes/.env`:

| Variable | Description | Default |
|-----------|-------------|----------|
| `GROQ_API_KEY` | API key for Groq summarization | `None` |
| `GROQ_MODEL` | The LLM used for summarization | `llama-3.1-8b-instant` |
| `DDG_CACHE_TTL` | Cache expiration in seconds | `300` |
| `DDG_MAX_RESULTS`| Default number of results per search | `5` |

## 🤖 Hermes Agent Integration

To use this as a custom script in your `config.yaml`:

```yaml
scripts:
  proot-search:
    path: /data/data/com.termux/files/home/workspace/Hermes_proot-distro_scrapper/hermes_web_search.py
    description: "Reliable DDG search via proot-distro"
    args: ["query"]
```

**Invoke via:** `hermes script run proot-search -- "query here"`

## 📊 Output Format
The tool returns a structured JSON object:
```json
{
 "query": "...",
 "timestamp": "...",
 "cached": true/false,
 "web": [
  {
   "title": "...",
   "url": "...",
   "snippet": "...",
   "content": "..."   // Full article text fetched via Jina AI Reader
  }
 ],
 "summary": "...", // Only if --summarize is used
 "error": null
}
```
