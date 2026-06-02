"""
Session 7 — Capstone
Design and ship something real.

This file is a stub — you build it from scratch based on your own design.
Before writing any code, complete DESIGN.md (see Chunk 7A).
Run with: python session7.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import json
import time

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"


# ─── WARM-UP: Design before you code ─────────────────────────────────────────
# Before opening your editor, answer these five questions with ACTUAL answers
# (not "TBD"). If you can't answer all five in 10 minutes, the design isn't ready.
#
#   1. Which architecture pattern from Session 4 (ReAct, plan-execute, multi-agent)?
#   2. What external tools does it need? Are any stateful?
#   3. Where does memory live — in-context, rolling summary, or vector store?
#   4. What are the three most likely failure modes?
#   5. What gets logged, and what would you look at first in a failed run?


# ─── CHUNK 7A: Written design ────────────────────────────────────────────────
# Save your answers to DESIGN.md before writing code. Short is fine — it just has
# to be DECIDED. Cover: pattern choice (and why, over the others); tools (and which
# are stateful); memory strategy + the token threshold where compression fires;
# the max_steps and token-budget limits; what events you log.
# Then write the hardest tradeoff explicitly: what you chose and what you gave up.
#
# Done when: DESIGN.md exists and answers all five warm-up questions concretely.


# ─── CHUNK 7B: Build it ──────────────────────────────────────────────────────
# Implement your design against this required checklist:
#   ☐ At least one REAL external tool (not faked)
#   ☐ Context compression at a defined token threshold
#   ☐ max_steps AND token budget enforced
#   ☐ Structured JSON log file (one event per line)
#   ☐ Retry with exponential backoff on API calls
#
# Reuse what you already built:
#   - log(f, event_type, **data)          (Session 3)
#   - maybe_compress(messages, threshold)  (Session 3)
#   - call_with_retry(fn, max_retries=3)  (Session 6)
#
# TODO: define your tools; implement execute_tool; implement the agent loop with
#   compression + limits + logging wired in. Write down any decision you make
#   mid-build that wasn't in DESIGN.md — those surprises are a real output here.
#
# Done when: the agent completes its target task end-to-end and every checklist box
#   above is satisfied by code that actually runs.


# ─── CHUNK 7C: Document it ───────────────────────────────────────────────────
# Write ARCHITECTURE.md and README.md.
#   ARCHITECTURE.md: pattern + why; where memory lives and when compression fires;
#     the failure modes you designed for; one thing you'd rebuild differently.
#   README.md: one-paragraph what-it-does; setup (pip install, env vars); how to run.
#
# Done when: a reader could run your agent from the README alone, AND you can say in
#   30 seconds where a new fact-checking sub-agent would plug into your architecture.


# ─── CHUNK 7D: Ship it ───────────────────────────────────────────────────────
#   git add .
#   git commit -m "capstone: v1.0"
#   git tag v1.0
#   git push origin main --tags
#
# Then write a 4-sentence retrospective (here or in RETRO.md):
#   1. What clicked   2. What surprised you   3. What you'd do differently
#   4. One thing you want to learn next
#
# Finally, list every component you added since Session 1 — history management,
# tool loop, max_steps, token budget, compression, logging, retry, RAG, an
# architecture pattern, docs. That list is what separates a chatbot from an agent.
#
# Done when: v1.0 is tagged and pushed, and the retrospective is written.
# RETROSPECTIVE:
