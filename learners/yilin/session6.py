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
import httpx  # anthropic depends on it; used here to build a realistic 429
import random

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"


# ─── WARM-UP: Watch it die ───────────────────────────────────────────────────
# Reliability is invisible until something fails.
#
# TODO: write fragile_api_call(**kwargs) that raises anthropic.RateLimitError on
# every 3rd call and otherwise returns client.messages.create(**kwargs). Call it
# in a loop and watch your code crash with no recovery. This session is the fix.
def fragile_api_call(turn, p, **kwargs):
    if random.random() < p:
        response = httpx.Response(429, request=httpx.Request("POST", "https://api.anthropic.com"))
        raise anthropic.RateLimitError("simulated rate limit", response=response, body=None)
    return client.messages.create(**kwargs)

# turn = 0

# while True:
#     r = fragile_api_call(turn=turn, p=0.3, model=MODEL, max_tokens=100, messages=[{"role": "user", "content": "Hello"}])
#     print(f"Turn {turn}: {r}")
#     turn += 1


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

# ANSWER:
# Success rate at p=0.10: 100.00%
# Success rate at p=0.30: 100.00%
# Success rate at p=0.50: 90.00%

def call_with_retry(fn, max_retries=3):
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except anthropic.RateLimitError:
            print(f"Rate limit hit on attempt {attempt} — retrying after backoff")
            if attempt == max_retries:
                raise
            time.sleep(2 ** attempt)  # 1s, 2s, 4s — back off so you don't pile on
        except anthropic.APIStatusError as e:
            if 500 <= e.status_code < 600 and attempt < max_retries:
                time.sleep(2 ** attempt)
                print(f"Server error {e.status_code} on attempt {attempt} — retrying after backoff")
                continue
            print(f"API status error {e.status_code} on attempt {attempt} — not retrying")
            raise  # 4xx is permanent — fail fast

turn = 0

# while True:
#     r = call_with_retry(lambda: fragile_api_call(turn=turn, model=MODEL, max_tokens=100, messages=[{"role": "user", "content": "Hello"}]))
#     print(f"Turn {turn}: {r}")
#     turn += 1

# probabilities = [0.10, 0.30, 0.50]
# for p in probabilities:
#     successes = 0
#     trials = 20
#     for _ in range(trials):
#         try:
#             call_with_retry(lambda: fragile_api_call(turn=0, p=p, model=MODEL, max_tokens=100, messages=[{"role": "user", "content": "Hello"}]))
#             successes += 1
#         except anthropic.RateLimitError:
#             pass  # This means the call failed even after retries
#     success_rate = successes / trials
#     print(f"Success rate at p={p:.2f}: {success_rate:.2%}")


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

# ANSWER:
# Non-streaming - Time to full response: 2.58 seconds
# Streaming - Time to first token: 0.68 seconds | Time to full response: 2.14 seconds
# WITHOUT system prompt: 0/5 valid JSON results, self-correction retry failed 5/5
# WITH system prompt: 5/5 valid JSON results (self-correction not needed)

# messages = [{"role": "user", "content": "Explain how TCP works in 5 sentences."}]

# print("Non-streaming")
# start_time = time.time()
# response = client.messages.create(model=MODEL, messages=messages, max_tokens=200)
# end_time = time.time()
# print(f"Time to full response: {end_time - start_time:.2f} seconds")

# print("\nStreaming")
# start_time = time.time()
# first_token_time = None
# with client.messages.stream(model=MODEL, messages=messages, max_tokens=200) as stream:
#     for text in stream.text_stream:
#         if first_token_time is None:
#             first_token_time = time.time()
#             print(f"Time to first token: {first_token_time - start_time:.2f} seconds")
#         print(text, end="", flush=True)
#     print(stream.get_final_message())
# end_time = time.time()
# print(f"\nTime to full response: {end_time - start_time:.2f} seconds")

def get_structured_result(task, include_instruction=True):
    if include_instruction:
        system_prompt = (
            "Complete the task, then end with this JSON on its own line:\n"
            '{"result": "...", "steps_taken": N, "confidence": "high|medium|low"}'
        )
    else:
        system_prompt = ""
    messages = [{"role": "user", "content": task}]
    
    response = client.messages.create(model=MODEL, system=system_prompt, messages=messages, max_tokens=1024)
    text = response.content[0].text
    
    try:
        json_part = text[text.rfind("{"):]
        result = json.loads(json_part)
        return result
    except json.JSONDecodeError:
        correction_message = (
            text + "\nYour response is missing the required JSON summary. Please add it now."
        )
        correction_response = client.messages.create(model=MODEL, system=system_prompt, messages=[{"role": "user", "content": correction_message}], max_tokens=1024)
        
        correction_text = correction_response.content[0].text
        try:
            json_part = correction_text[correction_text.rfind("{"):]
            result = json.loads(json_part)
            return result
        except json.JSONDecodeError:
            print("Self-correction failed to produce valid JSON.")
            return None
        
# for i in range(5):
#     result_without_instruction = get_structured_result("Summarize the plot of 'The Great Gatsby'.", include_instruction=False)
#     print(f"Result without instruction {i+1}: {result_without_instruction}")

# for i in range(5):
#     result_with_instruction = get_structured_result("Summarize the plot of 'The Great Gatsby'.", include_instruction=True)
#     print(f"Result with instruction {i+1}: {result_with_instruction}")


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
#
# Large system prompt:
# Run 1 - Cache creation input tokens: 5602, Cache read input tokens: 0
# Run 2 - Cache creation input tokens: 0, Cache read input tokens: 5602
# Run 2 - Percentage of input tokens that were cache reads: 99.77%
# 
# Caching only kicks in above certain token counts (Haiku 4.5's is ~4096 tokens) — below that, the write cost can outweigh the read savings, so you see 0 cache reads and 0% cache read percentage.
# Small system prompt:
# Run 1 - Cache creation input tokens: 0, Cache read input tokens: 0
# Run 2 - Cache creation input tokens: 0, Cache read input tokens: 0
# Run 2 - Percentage of input tokens that were cache reads: 0.00%

LARGE_SYSTEM_PROMPT = "This is a large system prompt! " * 800  # ~5600 tokens. NOTE: Haiku 4.5's cache minimum is ~4096 tokens (higher than older Haiku's 2048); ~2800 tokens did NOT cache.
SMALL_SYSTEM_PROMPT = "This is a small system prompt?" * 2  # ~10 tokens

# cache_control goes ON a system content block (system must be a list), NOT as a
# top-level kwarg — and the cached prefix must exceed the model's minimum length.
response1 = client.messages.create(
    model=MODEL,
    system=[{"type": "text", "text": SMALL_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
    messages=[{"role": "user", "content": "What is the capital of France?"}],
    max_tokens=50
)
print(f"Run 1 - Cache creation input tokens: {response1.usage.cache_creation_input_tokens}, Cache read input tokens: {response1.usage.cache_read_input_tokens}")

response2 = client.messages.create(
    model=MODEL,
    system=[{"type": "text", "text": SMALL_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
    messages=[{"role": "user", "content": "What is the capital of Germany?"}],
    max_tokens=50
)
print(f"Run 2 - Cache creation input tokens: {response2.usage.cache_creation_input_tokens}, Cache read input tokens: {response2.usage.cache_read_input_tokens}")
print(f"Run 2 - Percentage of input tokens that were cache reads: {(response2.usage.cache_read_input_tokens / (response2.usage.input_tokens + response2.usage.cache_read_input_tokens)) * 100:.2f}%")

# ─── DELIVERABLE (no mini project): the numbers ──────────────────────────────
# Log a small before/after table — it IS this session's output:
#   ☐ retry recovery rate at p = 0.10 / 0.30 / 0.50
# 100% / 100% / 90%
#   ☐ cache-read % on run 2 (large vs small system prompt)
# Large system prompt - Cache read percentage: 99.77%
# Small system prompt - Cache read percentage: 0.00%
#   ☐ valid-JSON rate out of 5, without vs with the format instruction
# WITHOUT system prompt: 0/5 valid JSON results, self-correction retry failed 5/5
# WITH system prompt: 5/5 valid JSON results (self-correction not needed)
# Done when: all three rows are filled with real numbers from your runs.
