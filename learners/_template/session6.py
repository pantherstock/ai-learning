"""
Session 6 — Production Basics
Make it real: reliability, cost, and responsiveness.

Each chunk is CONCEPT -> TODO -> CHALLENGE (see session1.py).
Run with: python session6.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import time
import json

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"


# ─── WARM-UP: Watch it die ───────────────────────────────────────────────────
# Reliability is invisible until something fails.
#
# TODO: write fragile_api_call(**kwargs) that raises anthropic.RateLimitError on
# every 3rd call and otherwise returns client.messages.create(**kwargs). Call it
# in a loop and watch your code crash with no recovery. This session is the fix.


# ─── CHUNK 6A: Retry with exponential backoff ────────────────────────────────
# CONCEPT
#   Transient errors (rate limits, timeouts, 5xx) are worth retrying — wait longer
#   each attempt (1s, 2s, 4s) so you don't hammer a struggling service. Permanent
#   errors (bad key, malformed request / 4xx) will never succeed; fail fast on those.
#
# TODO: implement call_with_retry(fn, max_retries=3):
#   - on anthropic.RateLimitError: sleep 2**attempt, retry; re-raise on last attempt
#   - on anthropic.APIStatusError: retry if status is 5xx, raise immediately on 4xx
#   Wire fragile_api_call into it and confirm it now recovers.
#
# CHALLENGE (write the answers in comments):
#   Make fragile_api_call fail with probability p (use random.random() < p). Run 20
#   tasks each at p = 0.10, 0.30, 0.50 with max_retries=3 and record the success
#   rate at each. At which p does 3 retries stop being enough? What does that imply
#   about how much real-world error budget retries actually buy you?


# ─── CHUNK 6B: Streaming & structured output ─────────────────────────────────
# CONCEPT
#   Streaming delivers tokens as they're generated — same TOTAL time, but the user
#   sees output immediately, so it FEELS far faster. Separately, an app needs
#   machine-readable output: ask for a JSON summary, and if the model forgets it,
#   send a correction and let it self-correct.
#
# TODO (a) — streaming: send one prompt two ways and time both with time.time().
#   Non-streaming: a normal create() call (time the full wait).
#   Streaming: with client.messages.stream(...) as stream:  print each text delta
#     via print(text, end="", flush=True); afterwards read stream.get_final_message().
# TODO (b) — structured output: implement get_structured_result(task) -> dict:
#   - system: 'Complete the task, then end with this JSON on its own line:
#       {"result": "...", "steps_taken": N, "confidence": "high|medium|low"}'
#   - parse JSON from the end of the reply: json.loads(text[text.rfind("{"):])
#   - on parse failure: append the bad reply + "Your response is missing the
#     required JSON summary. Please add it now." and make ONE more call.
#
# CHALLENGE (write the answers in comments):
#   1. Print the time-to-FIRST-token for streaming vs the total wait for
#      non-streaming on the prompt "Explain how TCP works in 5 sentences." Which
#      number is the user actually waiting on?
#   2. Run get_structured_result 5 times WITHOUT the JSON instruction in system,
#      then 5 times WITH it. How many of each 5 produced valid JSON? Did the
#      self-correction retry ever fail too?


# ─── CHUNK 6C: Prompt caching ────────────────────────────────────────────────
# CONCEPT
#   Your system prompt and tool definitions are byte-for-byte identical on every
#   call, yet you pay full input price each time. cache_control marks a prefix for
#   caching; cached reads cost ~10% of normal input tokens (writes cost ~1.25x).
#
# TODO: write a large fixed system prompt (~300+ tokens). Make TWO calls that pass
#   it as a content block with "cache_control": {"type": "ephemeral"}, changing only
#   the user question. Print cache_creation_input_tokens and cache_read_input_tokens
#   for each — run 1 creates the cache, run 2 reads it.
#
# CHALLENGE (write the answers in comments):
#   On run 2, what % of input tokens were cache READS? Now shrink the system prompt
#   to ~2 lines and repeat — does caching still help, or has the ~1.25x write cost
#   erased the savings? Estimate the minimum prompt size where caching is worth it.


# ─── DELIVERABLE (no mini project): the numbers ──────────────────────────────
# Log a small before/after table — it IS this session's output:
#   ☐ retry recovery rate at p = 0.10 / 0.30 / 0.50
#   ☐ cache-read % on run 2 (large vs small system prompt)
#   ☐ valid-JSON rate out of 5, without vs with the format instruction
# Done when: all three rows are filled with real numbers from your runs.
