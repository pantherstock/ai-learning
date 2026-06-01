# AI Agents from Scratch

A hands-on plan for building real AI agents with the Anthropic API and Python. You learn by building and breaking things — no passive reading.

7 core sessions (`index.html`) + 4 advanced topics (`advanced.html`). Each session is 2–4 hours and ships a real artifact.

---

## Setup (5 minutes)

**You need:** Python 3.10+ and an [Anthropic API key](https://console.anthropic.com) (free tier covers Sessions 1–2; ~$1–3 for the whole plan). A free [Brave Search key](https://brave.com/search/api/) is needed from Session 3 on.

```bash
# 1. Create your own learning folder
cp -r learners/_template learners/your-name
cd learners/your-name

# 2. Add your keys
cp .env.example .env        # then edit .env and paste your keys in

# 3. Install dependencies
pip install anthropic requests sentence-transformers
```

That's it. Your keys **load automatically** when you run a session — no `export`, no setup per session. Just:

```bash
python session1.py
```

> Advanced Section D also needs `pip install fastmcp`.

---

## The learning loop

1. Open `index.html` in your browser, enter your name on first load (ties progress to your folder).
2. Read the session, then open the matching file — e.g. `session1.py`.
3. Fill in every `# TODO:` and run it: `python session1.py`.
4. Click **Verify with Claude**, paste the prompt into Claude Code — Claude reads your code and confirms what's done.
5. Click **Mark session complete** and move on.

---

## What you'll build

### Part 1 · Fundamentals (`index.html`)

| Session | Topic | Build |
|---------|-------|-------|
| 1 · First Contact | API shape, tokens, statelessness | Chatbot class with token logging |
| 2 · Give the Model Hands | Tool use, the agent loop | File agent with real read/write tools |
| 3 · Context is Your Budget | Token limits, compression, logging | Research agent with Brave Search |
| 4 · Architecture Patterns | ReAct, plan-execute, multi-agent | Three-pattern comparison with logs |
| 5 · Memory & Retrieval | Embeddings, cosine similarity, RAG | RAG tool wired into the research agent |
| 6 · Production Basics | Retry, streaming, caching, validation | Before/after measurements |
| 7 · Capstone | Design and ship something real | Your agent, documented and tagged v1.0 |

### Part 2 · Advanced Topics (`advanced.html`)

Do Part 1 first — these build on all 7 fundamentals.

| Section | Topic | Build |
|---------|-------|-------|
| A · Prompt Caching | Document caching, TTL, cost math | Session 3 agent with cache profiling |
| B · Advanced Patterns | Reflection, parallel fan-out, routing, human-in-the-loop | Four pattern implementations |
| C · Subagents vs Skills | Decision framework, skill modules | Refactored research agent |
| D · Plugins & MCP | MCP protocol, tool servers, resources | RAG knowledge base as an MCP server |

---

## File layout

```
ai-learning/
├── index.html              Part 1: Fundamentals
├── advanced.html           Part 2: Advanced topics
├── README.md
└── learners/
    └── _template/          Copy this to start
        ├── env.py          Auto-loads your .env (don't edit)
        ├── .env.example    Copy to .env and add your keys
        ├── session1.py … session7.py   (Part 1)
        ├── caching.py      (Section A)
        ├── patterns.py     (Section B)
        ├── skills.py       (Section C)
        └── mcp.py          (Section D)
```

Your `.env` and personal `learners/your-name/` folder are git-ignored — your keys and progress stay local.

---

## If you get stuck

- Read the full error message first — most Python errors name the exact problem.
- Print intermediate values: `print(r.content)`, `print(r.usage)`.
- Paste your code and the error into Claude Code: `What's wrong with this?`
