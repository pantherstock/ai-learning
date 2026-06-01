"""
Section C — Subagents vs Skills
When does something belong in a tool, a skill module, or a subagent?
Learn to make that call, and refactor your code accordingly.

Prerequisites: complete Sessions 2 and 4 first.
Run with: python skills.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import os
import time

client = anthropic.Anthropic()


# ─── WARM-UP: Cost and latency comparison ────────────────────────────────────
# Solve the same task two ways and measure tokens + wall-clock time for each.
#
# TODO: write as_tool_call(query) (plain Python, e.g. a word count — 0 tokens,
# <1ms) and as_subagent_call(query) (delegate the same task to a Claude call —
# tokens + ~1–2s latency). Time both on the same input.
# OBSERVATION: for a task solvable by code alone, when is paying the subagent
# cost worth it?


# ─── SECTION C1: The decision framework ──────────────────────────────────────
# Use this mental model when deciding how to implement a capability:
#
#   Tool (Python function):
#     - Deterministic, no reasoning needed; fast (<1ms); zero token cost
#     - Examples: file I/O, math, date parsing, API calls with fixed schemas
#   Skill module (Python class wrapping tools):
#     - Reusable across agents; bundles related tools + error handling; zero LLM cost
#     - Examples: SearchSkill, MemorySkill, FileSkill
#   Subagent (Claude instance):
#     - Needs reasoning/language understanding; own tools; own context window;
#       token cost + latency per call
#     - Examples: code reviewer, research assistant, summarizer
#   Independent agent (top-level loop):
#     - Long-running autonomous task; manages its own context, compression, logging
#     - Examples: Session 3's research agent, the capstone
#
# TODO: classify each capability as tool / skill / subagent / agent, with one
# sentence of why for each:
#   - Parse a date string into a datetime object
#   - Decide whether a question is about billing or technical support
#   - Fetch a URL and return the HTML
#   - Write a three-paragraph summary of 5 search results
#   - Validate that a JSON object matches a schema
#   - Generate a code review for a Python function
#   - Retry an API call with exponential backoff
#   - Translate a user message to Spanish


# ─── SECTION C2: Skill modules ───────────────────────────────────────────────
# A skill is a Python class that bundles related tools and their schemas behind
# one consistent interface, regardless of what's underneath.
#
# TODO: build three skill classes:
#   - SearchSkill: a tool_definition property + run(query) (Brave search with a
#     fake-result fallback when BRAVE_SEARCH_API_KEY is unset)
#   - FileSkill: a tool_definitions property + read(path) (handle FileNotFoundError)
#     + write(path, content) + run(name, args) dispatcher
#   - MemorySkill: wraps an in-memory list of facts — a tool_definition for a
#     "remember_fact" tool, remember(fact) -> confirmation, recall_all() -> all
#     facts as a string (or "(empty)")
# Instantiate them and smoke-test each.


# ─── SECTION C3: Subagent specialization ─────────────────────────────────────
# Give each subagent different tools and a different system prompt. A researcher
# (search + memory) and a writer (file I/O only) each work better staying in lane.
#
# TODO: build ResearcherAgent (uses SearchSkill + MemorySkill, system "You are a
# research assistant...") and WriterAgent (uses FileSkill, system "You are a
# technical writer..."), each with its own agent loop.
# TODO: run a two-phase pipeline:
#   1. researcher.run("Find 3 key facts about FastAPI") -> facts
#   2. writer.run("Write a short intro to fastapi.md", context=facts)
# Log the number of messages in each loop. Why does keeping them separate keep
# each one's context smaller?
# OBSERVATION:


# ─── MINI PROJECT: Refactor the Session 3 research agent ─────────────────────
# Session 3's research agent has all its tools and logic inline. Refactor it to
# use SearchSkill, FileSkill, and MemorySkill. The agent should research a topic,
# remember key facts, and write a summary file. Is the new code easier to test,
# read, and modify? Push to GitHub when done.
#
# TODO: wire SearchSkill + FileSkill + MemorySkill into one agent loop.
