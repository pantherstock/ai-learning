"""
Session 4 — Architecture Patterns
There are several ways to structure an agent. Each one wins in different situations.

Each chunk is CONCEPT -> TODO -> CHALLENGE (see session1.py).
Run with: python session4.py

The big idea: all three patterns reuse ONE loop. Build it once (below), then each
pattern is just a different system prompt + toolset. Stuck? See ../_answers/session4.py.
"""

import env  # auto-loads .env — no manual `export` needed
import os
import anthropic
import requests

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"
BRAVE_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")

# TODO: reuse search + write_file + execute_tool (and their schemas) from Session 2.
# Wire search(query) to the real Brave Search, with a fake fallback so it still runs
# with no key / no network — the structural lessons show up either way:
#   - if not BRAVE_KEY: return f"[fake search result for '{query}']"
#   - GET https://api.search.brave.com/res/v1/web/search
#       headers={"X-Subscription-Token": BRAVE_KEY}, params={"q": query, "count": 3}
#   - results = r.json().get("web", {}).get("results", [])
#   - return "\n".join(f"- {x['title']}: {x['description']}" for x in results)
#
# TODO: factor the Session 2 agent loop into ONE reusable function — this is the
#   whole point of the session, so every pattern shares it:
#     def agent_loop(messages, system, tools, max_steps=10) -> dict:
#         # loop: create() -> append assistant -> run tool_use blocks -> repeat
#         # until stop_reason != "tool_use" or max_steps; tally r.usage tokens.
#         # return {"steps": ..., "tokens": ..., "answer": ...}
#   ReAct, plan-execute, and the multi-agent sub-agent are all just calls to this.


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
# TODO: run_react_agent(task) — just call agent_loop with the warm-up system prompt
#   ("...write a line starting with 'Thought:' before every tool call..."). Print each
#   Thought: line as it streams. Add your own "quality" judgement to the result dict.
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
# TODO: run_plan_execute_agent(task) — two phases:
#   Phase 1 — one call, NO tools, system "Create a numbered step-by-step plan. Do
#     not execute it. Be specific." Capture the plan text.
#   Phase 2 — agent_loop with system f"Execute this plan step by step:\n\n{plan}".
#   Add the planning call's usage to the loop's token count.
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
# TODO: call_subagent(task) -> str — agent_loop on a FRESH messages list (its own
#   context), returning the answer; print len(sub_messages) so you can see it stays
#   short. Add call_subagent to execute_tool. Then run_multi_agent(task) is just
#   agent_loop with the orchestrator system prompt and ONLY the call_subagent tool.
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
