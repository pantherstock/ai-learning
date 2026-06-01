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
# Wrap your API call in a function that fails every 3rd call.
# Run your agent — it crashes on the first failure with no recovery.
# This session is the fix.

call_count = 0

def fragile_api_call(**kwargs):
    global call_count
    call_count += 1
    if call_count % 3 == 1:  # fail on calls 1, 4, 7, ...
        raise anthropic.RateLimitError("simulated rate limit", response=None, body={})
    return client.messages.create(**kwargs)

# Try it:
print("Warm-up — fragile call (will raise on first attempt):")
try:
    r = fragile_api_call(
        model="claude-haiku-4-5-20251001",
        max_tokens=50,
        messages=[{"role": "user", "content": "Say hello"}]
    )
    print("Got response:", r.content[0].text)
except anthropic.RateLimitError as e:
    print(f"Crashed as expected: {e}")
call_count = 0  # reset for the rest of the session
print()


# ─── CHUNK 6A: Retry with exponential backoff ─────────────────────────────────
# Transient errors (rate limits, 5xx) are worth retrying.
# Permanent errors (bad key, malformed request) are not.

def call_with_retry(fn, max_retries=3):
    for attempt in range(max_retries):
        try:
            return fn()
        except anthropic.RateLimitError:
            if attempt == max_retries - 1: raise
            wait = 2 ** attempt   # 1s, 2s, 4s
            print(f"  Rate limited. Retrying in {wait}s (attempt {attempt + 1}/{max_retries})...")
            time.sleep(wait)
        except anthropic.APIStatusError as e:
            # TODO: retry on 5xx (server error), raise immediately on 4xx (client error)
            raise

print("6A — retry with backoff:")
# Reset the fragile counter and wire it into call_with_retry
call_count = 0
try:
    response = call_with_retry(
        lambda: fragile_api_call(
            model="claude-haiku-4-5-20251001",
            max_tokens=50,
            messages=[{"role": "user", "content": "What's 2+2?"}]
        )
    )
    print("Succeeded:", response.content[0].text)
except Exception as e:
    print(f"Failed after retries: {e}")

# TODO: test at simulated failure rates of 10%, 30%, 50%
# Change fragile_api_call so `call_count % N == 1` controls failure rate
# At what rate does the agent still succeed most of the time with 3 retries?
print()


# ─── CHUNK 6B: Streaming ──────────────────────────────────────────────────────
# Tokens arrive as they're generated. Total time is similar — perceived responsiveness is not.

print("6B — streaming vs. non-streaming:")

prompt = "Write a two-sentence explanation of how neural networks learn."

# Non-streaming (baseline):
t_start = time.time()
r = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=200,
    messages=[{"role": "user", "content": prompt}]
)
t_regular = time.time() - t_start
print(f"Regular (waited {t_regular:.2f}s):")
print(r.content[0].text)

# Streaming:
print(f"\nStreaming (tokens arrive as generated):")
t_start = time.time()

# TODO: use client.messages.stream() context manager
# Print each text chunk as it arrives with print(text, end="", flush=True)
# After the stream, print total time and input tokens from stream.get_final_message()

print()

# Bonus: in the stream, can you print "🔧 Calling tool..." the moment you see a tool_use
# block start — before the full block arrives? What would you need to detect?
# OBSERVATION:
print()


# ─── CHUNK 6C: Prompt caching ─────────────────────────────────────────────────
# Your system prompt is byte-for-byte identical every call. You're paying full price.
# cache_control marks it for caching at ~10% the normal input token cost.

SYSTEM_PROMPT = """You are an expert Python developer. You write clean, idiomatic Python code.
When answering questions, always include:
1. A brief explanation of the approach
2. Working code with clear variable names
3. One edge case to watch out for
Always respond in this structured format."""

print("6C — prompt caching:")

# First call — cache is created (cache_creation_input_tokens > 0):
r1 = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=300,
    system=[{
        "type": "text",
        "text": SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"}
    }],
    messages=[{"role": "user", "content": "How do I reverse a list in Python?"}]
)
print(f"Run 1 — created: {r1.usage.cache_creation_input_tokens}, read: {r1.usage.cache_read_input_tokens}")

# Second call — cache is read (cache_read_input_tokens > 0):
r2 = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=300,
    system=[{
        "type": "text",
        "text": SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"}
    }],
    messages=[{"role": "user", "content": "How do I sort a dict by value in Python?"}]
)
print(f"Run 2 — created: {r2.usage.cache_creation_input_tokens}, read: {r2.usage.cache_read_input_tokens}")

# TODO: calculate what % of total input tokens were cache hits on run 2
# Cached tokens cost ~10x less than regular input tokens.
# What's the minimum system prompt length where caching starts to matter?
# OBSERVATION:
print()


# ─── CHUNK 6D: Structured output and self-correction ─────────────────────────
# Ask the model to always end with a JSON summary. If it doesn't, send a correction.

REQUIRED_SCHEMA = '{"result": "...", "steps_taken": N, "confidence": "high|medium|low"}'

def get_structured_result(task: str) -> dict:
    system = f"Complete the task, then end your response with this JSON on its own line: {REQUIRED_SCHEMA}"
    messages = [{"role": "user", "content": task}]

    r = client.messages.create(
        model="claude-haiku-4-5-20251001", max_tokens=600,
        system=system, messages=messages
    )
    text = r.content[0].text

    try:
        json_start = text.rfind("{")
        return json.loads(text[json_start:])
    except (json.JSONDecodeError, ValueError):
        # TODO: ask for correction
        # append the bad response to messages
        # append {"role": "user", "content": "Your response is missing the required JSON summary. Please add it now."}
        # make a second call and parse the result
        print("  [self-correcting...]")
        pass

print("6D — structured output (5 trials):")
task = "List 3 benefits of using type hints in Python."
correct_count = 0

for i in range(5):
    result = get_structured_result(task)
    if result and "result" in result:
        correct_count += 1
        print(f"  Trial {i+1}: ✓ confidence={result.get('confidence', '?')}")
    else:
        print(f"  Trial {i+1}: ✗ malformed")

print(f"\nFormat compliance: {correct_count}/5 ({correct_count*20}%)")
print("\nNo mini project this session — your measurements are the deliverable.")
print("Log: retry recovery %, cache hit %, malformed output rate before/after format instructions.")
