"""
Session 6 — Production Basics · REFERENCE ANSWERS

One worked solution per chunk. Read AFTER you've tried session6.py yourself.

Run with: python session6.py
"""

import env  # auto-loads .env — no manual `export` needed
import sys
import time
import json
import random
import anthropic
import httpx  # anthropic depends on it; used here to build a realistic 429

sys.stdout.reconfigure(encoding="utf-8")

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"


# ─── WARM-UP: a flaky call to test against ───────────────────────────────────
_calls = 0


def _rate_limited():
    resp = httpx.Response(429, request=httpx.Request("POST", "https://api.anthropic.com"))
    return anthropic.RateLimitError("simulated rate limit", response=resp, body=None)


def fragile_api_call(fail_prob=None, **kwargs):
    global _calls
    _calls += 1
    fails = (random.random() < fail_prob) if fail_prob is not None else (_calls % 3 == 0)
    if fails:
        raise _rate_limited()
    return client.messages.create(**kwargs)


# ─── CHUNK 6A: retry with exponential backoff ────────────────────────────────
def call_with_retry(fn, max_retries=3):
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except anthropic.RateLimitError:
            if attempt == max_retries:
                raise
            time.sleep(2 ** attempt)  # 1s, 2s, 4s — back off so you don't pile on
        except anthropic.APIStatusError as e:
            if 500 <= e.status_code < 600 and attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            raise  # 4xx is permanent — fail fast

# CHALLENGE ANSWER:
#   Success rate stays ~100% at p=0.10 and is still high at p=0.30, but at p=0.50
#   three retries stop being enough — a task needs ALL attempts to fail, and
#   0.5^4 = ~6% of tasks still do, so you drop below ~95%. Retries buy you a lot of
#   error budget cheaply, but they can't rescue a service that fails half the time.


# ─── CHUNK 6B: streaming & structured output ─────────────────────────────────
def streaming_demo(prompt="Explain how TCP works in 5 sentences."):
    t0 = time.time()
    client.messages.create(model=MODEL, max_tokens=400,
                           messages=[{"role": "user", "content": prompt}])
    print(f"\nnon-streaming total wait: {time.time() - t0:.2f}s")

    t0 = time.time()
    first = None
    with client.messages.stream(model=MODEL, max_tokens=400,
                                messages=[{"role": "user", "content": prompt}]) as stream:
        for text in stream.text_stream:
            if first is None:
                first = time.time() - t0
            print(text, end="", flush=True)
        stream.get_final_message()
    print(f"\nstreaming time-to-FIRST-token: {first:.2f}s")


def parse_json(text):
    # Tolerant: decode the first {...} object and ignore any prose around it.
    start = text.find("{")
    if start == -1:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
        return obj
    except json.JSONDecodeError:
        return None


def get_structured_result(task, with_instruction=True):
    system = ('Complete the task, then end with this JSON on its own line: '
              '{"result": "...", "steps_taken": N, "confidence": "high|medium|low"}'
              ) if with_instruction else "Complete the task."
    messages = [{"role": "user", "content": task}]
    r = client.messages.create(model=MODEL, max_tokens=500, system=system, messages=messages)
    text = r.content[0].text
    result = parse_json(text)
    if result is not None:
        return result

    # Self-correct: show the model its own bad reply and ask for the JSON.
    messages += [{"role": "assistant", "content": text},
                 {"role": "user", "content": 'Your response is missing the required JSON summary. '
                  'Add it now as {"result": "...", "steps_taken": N, "confidence": "high|medium|low"}.'}]
    r = client.messages.create(model=MODEL, max_tokens=500, system=system, messages=messages)
    result = parse_json(r.content[0].text)
    return result if result is not None else {"error": "no valid JSON after self-correction"}

# CHALLENGE ANSWER:
#   1. Streaming's time-to-first-token is a fraction of a second; non-streaming's
#      total wait is the whole generation. Same total time, but the user only feels
#      the first number — that is why streaming feels "faster".
#   2. WITHOUT the instruction almost none of 5 are valid JSON; WITH it, ~5/5. When a
#      stray one still misses, the self-correction retry almost always fixes it.


# ─── CHUNK 6C: prompt caching ────────────────────────────────────────────────
# Caching only kicks in above a per-model MINIMUM prefix (~1024 tokens for most
# models, ~2048 for Haiku). This is comfortably over that so the cache actually fires.
BIG_SYSTEM = ("You are a meticulous research assistant who always cites sources. "
              * 250).strip()


def caching_demo(system_text=BIG_SYSTEM):
    # NOTE: this is the exact documented caching pattern. If both runs print 0/0, your
    # key or gateway isn't surfacing cache usage (some proxied keys don't) — the code
    # is still correct; try a direct console.anthropic.com key to see the numbers.
    system = [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}]
    for q in ["What is 2+2?", "What is 3+3?"]:  # run 1 writes the cache, run 2 reads it
        r = client.messages.create(model=MODEL, max_tokens=50, system=system,
                                   messages=[{"role": "user", "content": q}])
        u = r.usage
        print(f"q={q!r}  created={u.cache_creation_input_tokens}  read={u.cache_read_input_tokens}")

# CHALLENGE ANSWER:
#   On run 2 nearly all input tokens are cache READS (~90%), at ~10% of the price. A
#   ~2-line system prompt has too few tokens to matter — the ~1.25x write surcharge on
#   run 1 erases the savings. Caching pays off once the cached prefix is large and
#   reused: roughly 1k+ tokens reused several times.


if __name__ == "__main__":
    # 6A: prove recovery
    r = call_with_retry(lambda: fragile_api_call(
        model=MODEL, max_tokens=50, messages=[{"role": "user", "content": "Say hi"}]))
    print("6A recovered:", r.content[0].text)

    streaming_demo()
    print("\n6B with instruction:", get_structured_result("Name 3 primary colors."))
    print("6B without instruction:",
          get_structured_result("Name 3 primary colors.", with_instruction=False))
    print("\n6C:")
    caching_demo()
