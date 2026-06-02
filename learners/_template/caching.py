"""
Section A — Prompt Caching Deep Dive
Build on Session 6 (6C). Understand where caching applies, how to measure it, and
how to maximize ROI.

Each section is CONCEPT -> TODO -> CHALLENGE (see session1.py).
Prerequisites: complete Session 6 first.
Run with: python caching.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import time

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"


# ─── WARM-UP: Establish your baseline ────────────────────────────────────────
# TODO: write call_with_cache(user_message, run_label) that sends a large FIXED
# system prompt (~500 tokens) as a content block with
#   "cache_control": {"type": "ephemeral"}
# and prints cache_creation_input_tokens and cache_read_input_tokens. Call it 3
# times. Run 1 creates the cache (creation > 0); runs 2-3 read it (read > 0), as
# long as they're within the 5-minute TTL.


# ─── SECTION A1: What & where to cache ───────────────────────────────────────
# CONCEPT
#   System prompts aren't the only cacheable thing — large documents and tool
#   definitions are too. cache_control is a WATERMARK: everything BEFORE it in
#   token order gets cached, everything after does not. Where you place it decides
#   how much you save. (Write cost ~1.25x a normal input token; read cost ~0.1x.)
#
# TODO (a) — cache a document: make 2 calls that include a large REFERENCE_DOC in
#   the user message with cache_control on the document block, changing only the
#   question between calls:
#       messages=[{"role":"user","content":[
#           {"type":"text","text":REFERENCE_DOC,
#            "cache_control":{"type":"ephemeral"}},
#           {"type":"text","text":"What is the cache TTL?"}]}]
#   Measure cached vs regular tokens on each call.
# TODO (b) — placement test: run it once caching ONLY the system prompt, once
#   caching a TOOL definition (wrap a tool in {"cache_control":{"type":"ephemeral"}}).
#   Compare how many tokens each placement caches on a typical agent-loop call.
#
# CHALLENGE (write the answers in comments):
#   1. On call 2 of TODO (a), what % of input tokens were cache reads?
#   2. Given write cost ~1.25x and read cost ~0.1x, a cache pays off once you read
#      it enough times. Roughly how many reads does ONE write need to break even?
#   3. In a loop where the system prompt is ~200 tokens and tools are ~300 tokens,
#      which single placement caches the most per call?


# ─── SECTION A2: Agent-loop caching ──────────────────────────────────────────
# CONCEPT
#   In a multi-step loop, the system prompt + tool definitions are identical every
#   iteration. Without caching you re-pay for them on every call; with caching,
#   after step 1 you only pay for the NEW messages. The payoff compounds with steps.
#
# TODO: implement run_agent_loop(messages, use_cache=False, max_steps=5) -> returns
#   (total_input_tokens, total_cache_read_tokens). Run it twice on the SAME task,
#   once with use_cache=False and once True, and compare the totals.
#
# CHALLENGE (write the answers in comments):
#   After a 5-step loop with caching on, what % of total input tokens were served
#   from cache? Now reason it out for a 20-step loop: does that % go up, down, or
#   hold? At what step count does caching clearly dominate the cost?


# ─── MINI PROJECT: Cache-profiled research agent ─────────────────────────────
# Push to GitHub when the checklist passes.
#
#   ☐ Take your Session 3 research agent; add cache_control at the right breakpoint
#     (after the stable system prompt + tools, before the growing messages).
#   ☐ Run it COLD once, then re-run within 5 minutes (warm).
#   ☐ Log per step: regular_tokens, cache_creation_tokens, cache_read_tokens, e.g.:
#         Step 1: regular=2341  created=847  read=0
#         Step 2: regular=312   created=0    read=847
#   ☐ Compute the cache-hit rate and the estimated cost reduction (read ~= 0.1x input).
#
# Done when: the warm run shows cache reads on step 2+, and you can state the
#   overall cost reduction and the minimum step count where caching breaks even.
#
# TODO: implement the cache-profiled research agent.
