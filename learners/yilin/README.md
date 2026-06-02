# Your Learning Folder

Your personal workspace for *AI Agents from Scratch*.

## Setup

```bash
# 1. Add your keys
cp .env.example .env        # then edit .env and paste your keys in

# 2. Install dependencies
pip install anthropic requests sentence-transformers
```

Your keys **load automatically** — `env.py` reads `.env` every time you run a session. No `export`, nothing to remember. Just:

```bash
python session1.py
```

You need an [Anthropic key](https://console.anthropic.com) from the start, and a free [Brave Search key](https://brave.com/search/api/) from Session 4 on (optional — search falls back to a fake result when the key is unset). Add both to `.env` whenever you have them.

## Working through sessions

1. Open `index.html` in your browser and enter your name on first load — that ties browser progress to this folder.
2. Open a session file and fill in every `# TODO:` top to bottom.
3. Run it: `python session1.py`.
4. Click **Verify with Claude**, paste the prompt into Claude Code. Claude reads your file and confirms what's done.
5. Click **Mark session complete**.

## Files

`env.py` auto-loads your keys — you never need to edit it.

### Part 1 — Fundamentals (`index.html`)
| File | Contents |
|------|----------|
| `session1.py` | API fundamentals, Chatbot class |
| `session2.py` | Tool use, agent loop |
| `session3.py` | Context limits, compression, logging |
| `session4.py` | ReAct, plan-execute, multi-agent |
| `session5.py` | Embeddings, cosine similarity, RAG |
| `session6.py` | Retry, streaming, caching, validation |
| `session7.py` | Capstone design + build |

### Part 2 — Advanced Topics (`advanced.html`)
Section D also needs `pip install fastmcp`.

| File | Contents |
|------|----------|
| `caching.py` | Document caching, cache placement, agent loop caching |
| `patterns.py` | Reflection loops, parallel fan-out, routing, human-in-the-loop |
| `skills.py` | Skill modules, subagent specialization, decision framework |
| `mcp.py` | MCP server with tools, resources, and prompts |
