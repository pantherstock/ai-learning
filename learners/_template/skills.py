"""
Section C — Subagents vs Skills
When does something belong in a tool, a skill module, or a subagent? Learn to make
that call, and refactor your code accordingly.

Each section is CONCEPT -> TODO -> CHALLENGE (see session1.py).
Prerequisites: complete Sessions 2 and 4 first.
Run with: python skills.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import os
import time

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"


# ─── WARM-UP: Cost and latency comparison ────────────────────────────────────
# TODO: solve ONE task two ways and time both with time.time():
#   as_tool_call(text)     -> plain Python word count (0 tokens, <1ms)
#   as_subagent_call(text) -> ask Claude to count the words (tokens + ~1-2s)
# Use the EXACT input: "the quick brown fox jumps over the lazy dog". The numbers
# make the tradeoff obvious: only pay for a subagent when you need real reasoning.


# ─── SECTION C1: The decision framework ──────────────────────────────────────
# CONCEPT — four levels of capability:
#   Tool (Python fn):     deterministic, no reasoning, <1ms, 0 tokens.
#                         e.g. file I/O, math, date parsing, fixed-schema API calls.
#   Skill module (class): reusable bundle of related tools + schemas + error
#                         handling; 0 LLM cost. e.g. SearchSkill, MemorySkill.
#   Subagent (Claude):    needs language understanding; own context; tokens + latency.
#                         e.g. code reviewer, summarizer.
#   Independent agent:    long-running autonomous loop managing its own context.
#                         e.g. the Session 3 research agent, the capstone.
#
# TODO: classify each capability below as tool / skill / subagent / agent, with one
#   sentence of why:
#     - Parse a date string into a datetime object
#     - Decide whether a question is about billing or technical support
#     - Fetch a URL and return the HTML
#     - Write a three-paragraph summary of 5 search results
#     - Validate that a JSON object matches a schema
#     - Generate a code review for a Python function
#     - Retry an API call with exponential backoff
#     - Translate a user message to Spanish
#
# CHALLENGE (write the answers in comments):
#   Which two from that list are genuinely AMBIGUOUS (both tool and subagent could
#   work)? Write the exact condition that tips you one way — that condition is your
#   personal decision rule.


# ─── SECTION C2: Skill modules & specialization ──────────────────────────────
# CONCEPT
#   A skill is a class bundling related tools, schemas, and error handling behind
#   one interface. Specialized subagents that hold ONLY the skills they need keep
#   their context small and their behavior predictable.
#
# TODO (a) — build three skills:
#   SearchSkill: tool_definition property + run(query) (Brave search, fake-result
#                fallback when BRAVE_SEARCH_API_KEY is unset)
#   FileSkill:   tool_definitions property + read(path) (handle FileNotFoundError)
#                + write(path, content) + run(name, args) dispatcher
#   MemorySkill: wraps a list of facts — tool_definition for "remember_fact",
#                remember(fact) -> confirmation, recall_all() -> facts or "(empty)"
#   Smoke-test each one.
# TODO (b) — specialize: build ResearcherAgent (SearchSkill + MemorySkill) and
#   WriterAgent (FileSkill only), each with its own loop and system prompt. Run a
#   two-phase pipeline with these EXACT calls:
#     facts = researcher.run("Find 3 key facts about FastAPI")
#     writer.run("Write a short intro to fastapi.md", context=facts)
#   Log len(messages) for each loop.
#
# CHALLENGE (write the answers in comments):
#   How many messages does the researcher accumulate vs the writer? Estimate how
#   much LARGER one combined agent's context would be doing both phases. Did
#   splitting them help or hurt the final fastapi.md?
#   Then: swap SearchSkill's run(query) to return a different hardcoded fake result
#   WITHOUT changing any line in ResearcherAgent. Does it still work? That swap
#   test is the whole point of the skill interface.
