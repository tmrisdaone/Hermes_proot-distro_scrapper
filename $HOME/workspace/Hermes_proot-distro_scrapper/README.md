# Hermes_proot-distro_scrapper

A Python utility that combines DuckDuckGo search results with Groq LLM completions to provide concise answers.

## Usage

```bash
python3 scripts/ddg_groq_search.py "<query>"
```

## Requirements

- Python 3.8+
- `ddgs` and `groq` pip packages

## Configuration

Set `GROQ_API_KEY` environment variable with your Groq API key. If not set, the script will use a placeholder `[REDACTED]`.

## License

MIT