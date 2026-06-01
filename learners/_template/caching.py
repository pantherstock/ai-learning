"""
Section A — Prompt Caching Deep Dive
Build on Session 6 Chunk 6C. Understand where caching applies, how to measure it, and how to maximize ROI.

Prerequisites: complete Session 6 first.
Run with: python caching.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import time

client = anthropic.Anthropic()


# ─── WARM-UP: Establish your baseline ────────────────────────────────────────
# Run the same agent-style call 3 times in a row with a large system prompt
# (~500 tokens). Print cache_creation_input_tokens and cache_read_input_tokens
# for each run. On run 1: cache_creation > 0. On runs 2–3: cache_read > 0 (if
# within the 5-minute TTL).
#
# TODO: write call_with_cache(user_message, run_label) that passes a large fixed
# system prompt as a content block with "cache_control": {"type": "ephemeral"},
# and prints regular/created/read token counts. Call it 3 times.


# ─── SECTION A1: Caching large documents ─────────────────────────────────────
# System prompts aren't the only thing worth caching. Large context documents
# (documentation, codebases, knowledge bases) can be cached too.
# The rule: content BEFORE cache_control gets cached. Content AFTER does not.
#
# TODO: make 2 calls that include a large reference document in the context, with
# cache_control on the document. On call 2, change only the user question. Put
# cache_control AFTER the document, in the messages — not in the system prompt:
#   messages=[{"role": "user", "content": [
#     {"type": "text", "text": REFERENCE_DOC, "cache_control": {"type": "ephemeral"}},
#     {"type": "text", "text": "What is the cache TTL?"}
#   ]}]
# Measure how many tokens are cached vs regular.


# ─── SECTION A2: Cache placement matters ─────────────────────────────────────
# cache_control is a watermark: everything before it (in token order) gets cached.
# Test what happens when you move it to different positions.
#
# TODO: experiment 1 — cache_control on the system prompt only. Measure cached vs
# regular tokens on call 2.
# TODO: experiment 2 — cache_control on a tool definition (wrap a tool in
# {"cache_control": {"type": "ephemeral"}}). Tools are passed to the `tools` param,
# not in messages; the API caches tools whose definition carries cache_control.
# Do tool definitions cache separately from the system prompt?
# OBSERVATION: which placement gives better cache utilization for an agent loop?


# ─── SECTION A3: Agent loop caching ──────────────────────────────────────────
# In a multi-step agent loop, the system prompt + tool definitions are identical
# on every iteration. Without caching you pay for them in full on every call.
# With caching, after the first call you only pay for the new messages.
#
# TODO: implement run_agent_loop(messages, use_cache=False, max_steps=5) that
# returns (total_input, total_cached). Run it twice on the same task — once with
# use_cache=False, once True — and compare. What % of tokens were served from
# cache with caching enabled?


# ─── MINI PROJECT: Cache-optimize the Session 3 research agent ───────────────
# Take session3.py and add cache_control at the right breakpoints. Run it once
# cold, then re-run within 5 minutes. Log regular / cache_creation / cache_read
# tokens per step. Calculate total cost reduction (a cache read costs ~10% of a
# regular input token). Push to GitHub when done.
#
# Expected shape of the output:
#   Step 1: regular=2341  created=847  read=0
#   Step 2: regular=312   created=0    read=847
#   Cache hit rate: 73%   Estimated cost reduction: ~63%
#
# TODO: implement the cache-profiled research agent.
