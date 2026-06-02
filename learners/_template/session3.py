"""
Session 3 — Context is Your Budget
Hit the limits, then build instincts to manage them.

Each chunk is CONCEPT -> TODO -> CHALLENGE (see session1.py).
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
MODEL = "claude-haiku-4-5-20251001"
BRAVE_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")


# ─── WARM-UP: Watch the tokens climb ─────────────────────────────────────────
# In your Session 2 loop, add this line at the top of each iteration, before the
# API call, then run a 15-step task:
#   print(f"Step {step}: ~{sum(len(str(m)) for m in messages)//4} tokens in messages")
# The number grows EVERY step, even when nothing new happens. That growing number
# is your context window filling up — the problem this whole session answers.


# ─── CHUNK 3A: Wire a real search tool ───────────────────────────────────────
# CONCEPT
#   Until now search was faked. Brave Search (free tier, no card) gives the agent
#   real, current knowledge. The TEXT of a tool's description measurably changes
#   how eagerly the model reaches for it — descriptions are prompt engineering.
#
# TODO: implement search(query) -> str:
#   - if not BRAVE_KEY: return "Error: BRAVE_SEARCH_API_KEY not set"
#   - GET https://api.search.brave.com/res/v1/web/search
#       headers={"X-Subscription-Token": BRAVE_KEY}, params={"q": query, "count": 3}
#   - results = r.json().get("web", {}).get("results", [])
#   - return "\n".join(f"- {x['title']}: {x['description']}" for x in results)
#   Define the matching search schema and test it on the EXACT query:
#       "What is the latest stable version of Python?"
#
# CHALLENGE (write the answers in comments):
#   Run the SAME task — "What's the newest iPhone and when was it released?" —
#   twice, changing only the tool's description string:
#       (a) "Search the web"
#       (b) "Search the web for real-time information not available in your
#            training data."
#   Does the model call search more often with (b)? What does that tell you about
#   how much the description matters versus the tool's name?


# ─── CHUNK 3B: Compression & the cost of forgetting ──────────────────────────
# CONCEPT
#   When history gets too big, summarize the oldest turns and drop them — trading
#   precision for space. The cost is real: a fact the agent saw early may later be
#   recalled correctly, admitted-unknown, or confabulated. There is no fix, only a
#   tradeoff you choose deliberately.
#
# TODO (a): implement maybe_compress(messages, threshold=4000):
#   - approx = sum(len(str(m)) for m in messages) // 4
#   - if approx < threshold: return messages unchanged
#   - else: summarize messages[:-4] in ONE API call into 2-3 sentences, then return
#       [{"role":"user","content": f"[Earlier context]: {summary}"}] + messages[-4:]
#   - print f"Compressed {len(messages)-4} messages -> 1 summary "
#           f"(~{approx} tokens before)"
#
# TODO (b) — the forgetting experiment (deterministic, so anyone can reproduce it):
#   1. Make the FIRST user message exactly:
#        "Remember this reference number for later: RX-4417. Now help me research
#         the history of the internet."
#   2. Run an 18-step research loop with maybe_compress(messages, threshold=1500)
#      called before every API call (low threshold so compression definitely fires).
#   3. As the LAST user message, ask exactly:
#        "What was the reference number I gave you at the very start?"
#
# CHALLENGE (write the answers in comments):
#   1. Print the approx token count right before and right after each compression.
#      What's the rough compression ratio (after / before)?
#   2. In step (b)(3), does the agent return RX-4417, admit it doesn't know, or
#      invent a different number? Paste what it said.


# ─── CHUNK 3C: Structured logging ────────────────────────────────────────────
# CONCEPT
#   When a 10-step loop fails on step 7, a log is the only way to reconstruct why.
#   One JSON object per line ("JSON Lines") is greppable and trivial to parse later.
#
# TODO: write log(f, event_type, **data) that appends one line:
#       f.write(json.dumps({"ts": time.time(), "type": event_type, **data}) + "\n")
#   Open agent.log once and pass the handle in. Log on every tool call
#   (step, tool, args, result[:200], tokens_in) and every compression event
#   (msgs_before, msgs_after).
#
# CHALLENGE (write the answers in comments):
#   After one run, open agent.log. Using ONLY the log (not the console), can you say
#   which tool ran at each step, what it returned, and where compression fired? If
#   something is missing, add a field for it and note what it was.


# ─── MINI PROJECT: Research agent with compression and logging ───────────────
# Everything combined. Push to GitHub when the checklist passes.
#
#   ☐ Tools: real search (3A) + write_file; plus execute_tool(name, args).
#   ☐ maybe_compress(messages, threshold=4000) called before EVERY API call.
#   ☐ Loop stops at MAX_STEPS = 15 OR TOKEN_BUDGET = 50_000 (whichever first).
#   ☐ Every tool call and every compression event written to agent.log (3C).
#   ☐ Run the EXACT task:
#         "Research the history of reinforcement learning and write a 300-word
#          summary to research.md."
#
# Done when: research.md exists with a ~300-word summary, agent.log has one JSON
#   line per event, and you can point to the step where compression first fired.
#
# TODO: assemble the agent and run it.
