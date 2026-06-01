"""
Session 6 — Production Basics
Make it real: reliability, cost, and responsiveness.

Run with: python session6.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import time
import json

client = anthropic.Anthropic()


# ─── WARM-UP: Watch it die ────────────────────────────────────────────────────
# Reliability is invisible until something fails.
#
# TODO: write fragile_api_call(**kwargs) that raises anthropic.RateLimitError on
# every 3rd call and otherwise returns client.messages.create(**kwargs). Call it
# once and watch your code crash with no recovery. This session is the fix.


# ─── CHUNK 6A: Retry with exponential backoff ─────────────────────────────────
# Transient errors (rate limits, 5xx) are worth retrying.
# Permanent errors (bad key, malformed request) are not.
#
# TODO: implement call_with_retry(fn, max_retries=3):
#   - on anthropic.RateLimitError: sleep 2**attempt (1s, 2s, 4s) and retry,
#     re-raising on the last attempt
#   - on anthropic.APIStatusError: retry on 5xx, raise immediately on 4xx
# Wire fragile_api_call into it and confirm it now recovers.
# TODO: test at simulated failure rates of 10%, 30%, 50%. At what rate does the
# agent still succeed most of the time with 3 retries?


# ─── CHUNK 6B: Streaming ──────────────────────────────────────────────────────
# Tokens arrive as they're generated. Total time is similar — perceived
# responsiveness is not.
#
# TODO: send the same prompt two ways and compare. First non-streaming (time the
# full wait). Then with client.messages.stream() as a context manager: print each
# text chunk with print(text, end="", flush=True) as it arrives, then read total
# time and input tokens from stream.get_final_message().
# OBSERVE: could you print "🔧 Calling tool..." the moment a tool_use block starts,
# before the full block arrives? What would you need to detect?


# ─── CHUNK 6C: Prompt caching ─────────────────────────────────────────────────
# Your system prompt is byte-for-byte identical every call. You're paying full
# price. cache_control marks it for caching at ~10% the normal input token cost.
#
# TODO: write a large, fixed system prompt (~5+ lines). Make two calls that pass
# it as a content block with "cache_control": {"type": "ephemeral"}, changing only
# the user question. Print cache_creation_input_tokens and cache_read_input_tokens
# for each: run 1 creates the cache, run 2 reads it.
# TODO: calculate what % of input tokens were cache hits on run 2, and find the
# minimum system-prompt length where caching starts to matter.
# OBSERVATION:


# ─── CHUNK 6D: Structured output and self-correction ─────────────────────────
# Ask the model to always end with a JSON summary. If it doesn't, send a correction.
#
# TODO: implement get_structured_result(task) -> dict:
#   - system: 'Complete the task, then end your response with this JSON on its own
#     line: {"result": "...", "steps_taken": N, "confidence": "high|medium|low"}'
#   - parse the JSON from the end of the reply (text[text.rfind("{"):])
#   - on a parse failure: append the bad reply + a correction message
#     ("Your response is missing the required JSON summary. Please add it now.")
#     and make a second call
# TODO: run 5 trials and report format compliance (correct/5).
#
# No mini project this session — your measurements are the deliverable.
# Log: retry recovery %, cache hit %, malformed-output rate before/after the
# format instructions.
