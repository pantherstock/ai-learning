"""
Section B — Advanced Agentic Patterns
Four patterns that go beyond the basics in Session 4: reflection, parallel fan-out, routing, human-in-the-loop.

Prerequisites: complete Session 4 first.
Run with: python patterns.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import threading
import os

client = anthropic.Anthropic()
BRAVE_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")

# TODO: bring forward search(query) from Session 3/4 (with the BRAVE_KEY fallback)
# — the patterns below reuse it.


# ─── WARM-UP: Reflection in 3 lines ──────────────────────────────────────────
# Add a self-critique pass to any prior agent's output. The model reads its own
# response and identifies what could be improved.
#
# TODO: make one call to get a first_answer (e.g. "Explain what an API is in one
# sentence."), then a second call showing first_answer and asking
# "Critique this explanation in one sentence. What's imprecise or misleading?"
# Print both.


# ─── SECTION B1: Reflection loop ─────────────────────────────────────────────
# Systematic draft → critique → revise cycle. Stop when the model rates its own
# output as "good" or after N iterations — whichever comes first.
#
# TODO: implement reflection_loop(task, max_iterations=3) -> str:
#   - draft an answer
#   - each iteration: ask the model to rate it good/needs-work ("If needs-work,
#     explain what's wrong in one sentence. If good, say DONE."). If "DONE", break;
#     otherwise ask it to rewrite the draft addressing the critique.
#   - print whether each iteration continued or stopped; return the final draft.


# ─── SECTION B2: Parallel fan-out ────────────────────────────────────────────
# Fork work to multiple independent subagents running in parallel. Each has its
# own context window. Merge their results afterwards. Use threading.Thread —
# simpler than asyncio here.
#
# TODO: implement run_subagent(subtask, results, key) (a simple agent loop, max 5
# steps, storing the answer in results[key]). Decompose a task like
# "Compare Django vs FastAPI vs Flask for building a REST API" into independent
# subtasks, run them in parallel threads, join them, then make one synthesis call
# that merges the results into a comparison.


# ─── SECTION B3: Router pattern ──────────────────────────────────────────────
# A fast, cheap classifier reads the user request and decides which specialist
# agent handles it. The router itself does no domain work.
#
# TODO: implement classify_intent(user_message) -> one of research/code/summarize/
# other (a max_tokens=10 call). Implement research_agent / code_agent /
# summarize_agent (stubs are fine to start) and route(user_message) that
# dispatches on the intent, falling back to a plain call for "other".
# Test it on a research, a code, a summarize, and an off-topic input.


# ─── SECTION B4: Human-in-the-loop ───────────────────────────────────────────
# The agent pauses at key decision points and asks for human confirmation before
# an irreversible or risky action. Implement it as a tool: ask_human(question) ->
# the human's typed response.
#
# TODO: implement ask_human(question) (print the question, return input()).
# Define ask_human + write_file tool schemas and an agent loop that uses them on:
#   "Write a summary of machine learning to ml_summary.txt, but ask the human how
#    detailed it should be before writing."
# When the agent calls ask_human, invoke it and feed the answer back as a
# tool_result. Does it actually ask before writing? Try rephrasing the system
# prompt to make it more or less likely to ask.
# OBSERVATION:
