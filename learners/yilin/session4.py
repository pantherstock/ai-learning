"""
Session 4 — Architecture Patterns
There are several ways to structure an agent. Each one wins in different situations.

Each chunk is CONCEPT -> TODO -> CHALLENGE (see session1.py).
Requires: BRAVE_SEARCH_API_KEY in your .env (auto-loaded, for the comparison task).
Run with: python session4.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import os
import json

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"
BRAVE_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")

# TODO: reuse search + write_file (+ execute_tool and their schemas) from Session 3.
# Copy them here or import them. All three patterns below share the same tools.


# ─── WARM-UP: Turn on Thought lines ──────────────────────────────────────────
# ReAct is literally one sentence in the system prompt. Run any Session 3 task with:
#   "You are a research assistant. Before every tool call, write a line starting
#    with 'Thought:' explaining what you're about to do and why."
# Read the Thought lines as they stream. You just turned on the ReAct pattern.


# ─── CHUNK 4A: ReAct — thinking before acting ────────────────────────────────
# CONCEPT
#   Reason + Act: the model states a Thought: before each action. This tends to
#   improve decisions AND gives you a trace to debug. But stated reasoning and the
#   tool actually chosen don't always agree — that gap is worth seeing.
#
# TODO: implement run_react_agent(task, max_steps=10) -> dict using the warm-up
#   system prompt. Log each step's Thought: line and the tool it then called.
#   Return {"steps": steps, "tokens": total_tokens, "quality": "<your judgement>"}.
#
# CHALLENGE (write the answers in comments):
#   Run this EXACT task: "Find the current population of Tokyo, then convert it to
#   millions rounded to one decimal." Find one step where the Thought: correctly
#   describes the need but the tool call (or its arguments) is wrong. Quote both
#   lines. What was the mismatch?


# ─── CHUNK 4B: Plan-and-execute — and break it ───────────────────────────────
# CONCEPT
#   Two phases instead of one loop: first produce a plan, then execute it. Great
#   for well-defined tasks; fragile when reality diverges from the plan mid-run.
#
# TODO: implement run_plan_execute_agent(task, max_steps=10) -> dict:
#   Phase 1 — one call, NO tools, system "Create a numbered step-by-step plan. Do
#     not execute it. Be specific." Capture the plan text.
#   Phase 2 — run the tool loop with system f"Execute this plan step by step:\n\n{plan}".
#   Return {"steps","tokens","quality"}; seed tokens with the planning call's usage.
#
# CHALLENGE (write the answers in comments):
#   Run this EXACT task, designed so step 3 depends on step 2's result:
#     "Find the most popular Python web framework. Then look up its latest version.
#      Then state whether that version is less than a year old."
#   When execution reaches a step whose assumption the plan got wrong, does the
#   executor adapt, skip ahead, or proceed blindly to a wrong answer? Note the exact
#   step where it diverges and what it did.


# ─── CHUNK 4C: Multi-agent — orchestrator and sub-agent ──────────────────────
# CONCEPT
#   The orchestrator's ONLY tool is call_subagent(task). The sub-agent is your
#   Session 2 loop. Key insight: each agent has its OWN context window, so the
#   sub-agent's context stays short and focused — a feature, not a limitation.
#
# TODO: implement call_subagent(task) -> str — a self-contained loop (max 8 steps)
#   that prints len(sub_messages) each step and returns the final answer.
#   Define the call_subagent schema and implement run_multi_agent(task, max_steps=8)
#   -> dict, feeding each sub-agent answer back to the orchestrator.
#
# CHALLENGE (write the answers in comments):
#   Run this EXACT task: "Research three programming languages — Rust, Go, and
#   Python — and recommend one for a new CLI tool." Print len(messages) for the
#   orchestrator and len(sub_messages) for each sub-agent call. Why does each
#   sub-agent stay shorter than a single agent doing all three would?


# ─── COMPARE: one task, all three patterns (this session's deliverable) ──────
# CONCEPT
#   There is no universal best pattern. You build intuition by running ONE task
#   through all three and comparing cost, consistency, and quality.
#
# TODO: run react / plan_execute / multi_agent on this EXACT shared task:
#     "Find 3 recent Python libraries for building REST APIs, compare their GitHub
#      star counts, and write a brief recommendation to api-libraries.md."
#   Print a table of steps / tokens / your-quality-rating for each pattern.
#
# CHALLENGE (the deliverable — keep the table + notes):
#   Run each pattern 3 times on the task. Which pattern has the most CONSISTENT
#   step count across its 3 runs? Which produced the best single result? If those
#   are different patterns, what does that say about reliability vs. quality?
#
# Done when: you have a 3x3 (pattern x metric) table and a one-paragraph note on
#   which pattern you'd pick for this task and why.
