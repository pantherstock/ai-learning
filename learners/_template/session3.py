"""
Session 3 — Context is Your Budget
Hit the limits, then build instincts to manage them.

Requires: BRAVE_SEARCH_API_KEY in your .env (auto-loaded).
Run with: python session3.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import requests
import json
import time
import os

client = anthropic.Anthropic()

BRAVE_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")


# ─── WARM-UP: Watch the tokens climb ─────────────────────────────────────────
# Take your agent from Session 2. Add this line at the start of each loop
# iteration, before the API call:
#   print(f"Step {step}: {sum(len(str(m)) for m in messages)//4} approx tokens in messages")
# Run a 15-step task and watch the number grow every single step.
# Everything in this session is a direct response to that problem.
# (Do this in your session2.py first — then come back here.)


# ─── CHUNK 3A: Wire a real search tool ───────────────────────────────────────
# Replace fake search with the real Brave Search API.
#
# TODO: implement search(query) -> str:
#   - if not BRAVE_KEY: return "Error: BRAVE_SEARCH_API_KEY not set"
#   - GET https://api.search.brave.com/res/v1/web/search
#     headers={"X-Subscription-Token": BRAVE_KEY}, params={"q": query, "count": 3}
#   - parse results = r.json().get("web", {}).get("results", [])
#   - return "\n".join(f"- {x['title']}: {x['description']}" for x in results)
# Also define the matching search tool schema. Test it on a real query.


# ─── CHUNK 3B: Rolling compression ───────────────────────────────────────────
# When message history gets too large, summarize the oldest turns and drop them.
# Trade precision for space.
#
# TODO: implement maybe_compress(messages, threshold=4000):
#   - approx_tokens = sum(len(str(m)) for m in messages) // 4
#   - if below threshold: return messages unchanged
#   - else summarize messages[:-4] via an API call into 2–3 sentences, wrap it as
#     [{"role": "user", "content": f"[Earlier context]: {summary}"}], and return
#     that + messages[-4:]
#   - print f"Compressed {len(to_compress)} messages → 1 summary"


# ─── CHUNK 3C: The cost of forgetting ────────────────────────────────────────
# This is the tradeoff made concrete.
#
# TODO: design and run the experiment yourself:
#   1. Run a 20-step task with compression enabled
#   2. In step 5, note a specific fact the agent encountered (number, name, URL)
#   3. Let compression run
#   4. In step 18, ask the agent directly about that fact
# Does it recall correctly, admit it doesn't know, or confabulate?
# OBSERVATION:


# ─── CHUNK 3D: Structured logging ────────────────────────────────────────────
# When a loop fails on step 7, logs are the only way to understand why.
#
# TODO: write log(f, event_type, **data) that appends one JSON line per event:
#   f.write(json.dumps({"ts": time.time(), "type": event_type, **data}) + "\n")
# Integrate it into the agent loop — log every tool_call (step, tool, args,
# result[:200], tokens_in) and every compression event (before/after msg counts).


# ─── MINI PROJECT: Research agent with compression and logging ────────────────
# Combine: Brave search, write_file, rolling compression at 4000 tokens,
# max_steps=15, token_budget=50_000, and a JSON log file. Push to GitHub.
#
# TODO: define search + write_file tools and execute_tool(name, args).
# TODO: run the agent on a task like "Research the history of reinforcement
# learning and write a 300-word summary to research.md":
#   - call maybe_compress(messages) before each API call
#   - stop at MAX_STEPS=15 or TOKEN_BUDGET=50_000
#   - log every tool call and compression event to agent.log
# Then read agent.log to trace the full run.
