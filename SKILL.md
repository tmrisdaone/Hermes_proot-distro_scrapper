---
name: proot-browser-search
description: |
  Executes DuckDuckGo queries inside an Ubuntu proot environment and returns a Groq‑summarised result.
  The skill uses the existing `scripts/ddg_groq_search.py` script residing in the Hermes repo.
  It is intended for reliable web searches on Android/Termux where the native PyPI ddgs library may panic due to Rust‑NDK limits.

tags:
  - web
  - search
  - proot
  - reputable-sources
---

steps:
  - name: Perform proot search
    type: terminal
    args:
      command: |
        proot-distro login ubuntu -- bash -c \
          "python3 /data/data/com.termux/files/home/hermes-agent/scripts/ddg_groq_search.py \"${query}\""
      output: true

  # ${query} is substituted from slash command invoke
