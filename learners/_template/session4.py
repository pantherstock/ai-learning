"""
Session 4 — Architecture Patterns
There are several ways to structure an agent. Each one wins in different situations.

Requires: BRAVE_SEARCH_API_KEY in your .env (auto-loaded, for the comparison task).
Run with: python session4.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import os
import json

client = anthropic.Anthropic()

BRAVE_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")

# TODO: reuse search + write_file (and execute_tool + their schemas) from
# Session 3. Copy them here, or import them. The patterns below all share them.


# ─── WARM-UP: Turn on Thought lines ──────────────────────────────────────────
# ReAct is one sentence in the system prompt.
#
# TODO: run any Session 3 task with this system prompt and read the Thought lines:
#   "You are a research assistant. Before every tool call, write a line starting
#    with 'Thought:' explaining what you're about to do and why."


# ─── CHUNK 4A: ReAct — thinking before acting ────────────────────────────────
# Build a proper ReAct agent. Enforce the Thought: format. Compare with and without.
#
# TODO: implement run_react_agent(task, max_steps=10) -> dict using the ReAct
# system prompt above. Log each tool choice and the Thought: line that preceded
# it. Return {"steps": steps, "tokens": total_tokens, "quality": ""}.


# ─── CHUNK 4B: Plan-and-execute — and break it ───────────────────────────────
# Two phases instead of one loop: first produce a plan, then execute it.
#
# TODO: implement run_plan_execute_agent(task, max_steps=10) -> dict:
#   Phase 1 — one call with NO tools and system "Create a numbered step-by-step
#     plan. Do not execute. Be specific." Capture the plan text.
#   Phase 2 — run the agent loop with system f"Execute this plan step by step:\n\n{plan}".
#   Watch for: does it adapt when step N's result differs from what the plan assumed?
#   Return {"steps", "tokens", "quality"} (seed tokens with the planning call's usage).


# ─── CHUNK 4C: Multi-agent — orchestrator and sub-agent ──────────────────────
# The orchestrator's only tool is call_subagent(task). Each agent has its own
# independent context window — this is the key insight.
#
# TODO: implement call_subagent(task) -> str — a self-contained agent loop
# (max 8 steps) that logs len(sub_messages) each step and returns the final answer.
# TODO: define the call_subagent tool schema and implement run_multi_agent(task,
# max_steps=8) -> dict. When the orchestrator calls call_subagent, run the
# sub-agent and feed its answer back. Track orchestrator vs sub-agent context size.


# ─── CHUNK 4D: Compare all three patterns ────────────────────────────────────
# Run the exact same task through all three patterns. Log steps, tokens, and your
# quality judgement — there is no universal best pattern.
#
# TODO: run each pattern on one shared task, e.g.:
#   "Find 3 recent Python libraries for building REST APIs, compare their GitHub
#    star counts, and write a brief recommendation to api-libraries.md."
# Collect results for "react", "plan_and_execute", "multi_agent" and print a
# steps / tokens / quality table. Run 3 times per pattern and note which has the
# most consistent step count. The logged comparison is this session's deliverable.
