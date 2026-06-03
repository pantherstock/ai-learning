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

# NOTE: Haiku 4.5's cache minimum is ~4096 tokens (higher than older models).
# Prompts shorter than that will NOT be cached — you'll see 0 cache tokens.
# Use ~5000+ tokens for your LARGE_SYSTEM_PROMPT and LARGE_TOOL_DEFINITION
# to reliably hit the threshold. "This is a large system prompt " * 800 works.


# ─── WARM-UP: Establish your baseline ────────────────────────────────────────
# TODO: define LARGE_SYSTEM_PROMPT (~5000 tokens) and write
#   call_with_system_cache(user_message, run_label) that sends it as a content
#   block with "cache_control": {"type": "ephemeral"} and prints
#   cache_creation_input_tokens and cache_read_input_tokens. Call it 3 times.
#   Run 1 creates the cache (creation > 0); runs 2-3 read it (read > 0), as
#   long as they're within the 5-minute TTL.


# ─── SECTION A1: What & where to cache ───────────────────────────────────────
# CONCEPT
#   System prompts aren't the only cacheable thing — large documents and tool
#   definitions are too. cache_control is a WATERMARK: everything BEFORE it in
#   token order gets cached, everything after does not. Where you place it decides
#   how much you save. (Write cost ~1.25x a normal input token; read cost ~0.1x.)
#
# TODO (a) — cache a document: define REFERENCE_DOC (~5000 tokens) and make 2
#   calls that include it in the user message with cache_control on the document
#   block, changing only the question between calls:
#       messages=[{"role":"user","content":[
#           {"type":"text","text":REFERENCE_DOC,
#            "cache_control":{"type":"ephemeral"}},
#           {"type":"text","text":"What is the cache TTL?"}]}]
#   Measure cached vs regular tokens on each call.
# TODO (b) — placement test: define LARGE_TOOL_DEFINITION (~5000 tokens in its
#   description field) and run once caching ONLY the system prompt, once caching
#   the tool definition (add "cache_control":{"type":"ephemeral"} to the tool
#   dict). Compare how many tokens each placement caches.
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
# TODO: implement run_agent_loop(messages, use_cache=False, max_steps=5) that
#   includes LARGE_SYSTEM_PROMPT and LARGE_TOOL_DEFINITION on every call (use
#   tool_choice={"type":"none"} so the model doesn't actually try to call them).
#   Returns {"total_steps", "total_input_tokens", "total_cache_read_tokens"}.
#   Run it twice on the SAME task, once with use_cache=False and once True,
#   and compare the totals.
#
# CHALLENGE (write the answers in comments):
#   After a 5-step loop with caching on, what % of total input tokens were served
#   from cache? Now reason it out for a 20-step loop: does that % go up, down, or
#   hold? At what step count does caching clearly dominate the cost?


# ─── DELIVERABLE ─────────────────────────────────────────────────────────────
# Your A2 run_agent_loop output IS the deliverable. Make sure you can answer:
#   - What % of tokens were cache reads in the 5-step cached run?
#   - How does that % change for a 20-step run?
#   - At roughly what step count does caching break even (cost < uncached)?
