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
# Run the same agent-style call 3 times in a row with a large system prompt.
# Print cache_creation_input_tokens and cache_read_input_tokens for each run.
# On run 1: cache_creation > 0. On runs 2–3: cache_read > 0 (if within 5 min).

LARGE_SYSTEM = """You are a senior Python engineer and code reviewer.

When reviewing code, you follow these principles:
- Check for correctness first: does it do what it claims?
- Check for edge cases: null inputs, empty lists, division by zero, etc.
- Check for idiomatic Python: use of list comprehensions, context managers, type hints.
- Check for performance: unnecessary loops, redundant API calls, unbounded data structures.
- Check for security: hardcoded secrets, unsanitized inputs, open file handles.

You respond with structured feedback in this format:
1. Summary (1 sentence)
2. Issues found (numbered list, or "None found")
3. Suggestions (numbered list, or "None")
""" * 3  # repeat to make it large enough to benefit from caching (~500 tokens)

def call_with_cache(user_message, run_label=""):
    t = time.time()
    r = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=[{
            "type": "text",
            "text": LARGE_SYSTEM,
            "cache_control": {"type": "ephemeral"}
        }],
        messages=[{"role": "user", "content": user_message}]
    )
    elapsed = time.time() - t
    created = r.usage.cache_creation_input_tokens
    read    = r.usage.cache_read_input_tokens
    regular = r.usage.input_tokens
    print(f"{run_label}: regular={regular} created={created} read={read} ({elapsed:.2f}s)")
    return r

print("Warm-up — cache warm-up across 3 calls:")
call_with_cache("Review this: x = 1/0", "Run 1 (cold)")
time.sleep(1)
call_with_cache("Review this: open('f.txt')", "Run 2 (warm)")
time.sleep(1)
call_with_cache("Review this: password = 'abc123'", "Run 3 (warm)")
print()


# ─── SECTION A1: Caching large documents ─────────────────────────────────────
# System prompts aren't the only thing worth caching. Large context documents
# (documentation, codebases, knowledge bases) can be cached too.
# The rule: content BEFORE cache_control gets cached. Content AFTER does not.

REFERENCE_DOC = """
# Anthropic API Reference (excerpt)

## Messages API
POST /v1/messages

Parameters:
- model (required): claude-haiku-4-5-20251001, claude-sonnet-4-6, etc.
- max_tokens (required): integer, 1–200000
- messages (required): list of {role, content} objects
- system (optional): string or list of content blocks
- tools (optional): list of tool definitions
- temperature (optional): 0.0–1.0 (default 1.0)

## Tool use
Tools are defined as JSON Schema objects. The model returns stop_reason="tool_use"
when it decides to call a tool. Your code must execute the tool and return a
tool_result message before the model can continue.

## Token counting
- input_tokens: tokens in the prompt (regular + cached)
- output_tokens: tokens in the response
- cache_creation_input_tokens: tokens written to cache this call
- cache_read_input_tokens: tokens read from cache this call

Cache reads cost ~10x less than regular input tokens.
Cache writes cost ~1.25x regular input tokens.
Cache TTL is 5 minutes (ephemeral) or longer (for supported models).
""" * 5  # make it big

print("A1 — document caching:")
# TODO: make 2 calls that include REFERENCE_DOC in the context, with cache_control
# on the document. On call 2, change only the user question.
# Measure: how many tokens are cached vs regular?
# Key: put cache_control AFTER the document, not in the system prompt.
# Use a messages list like:
#   messages=[
#     {"role": "user", "content": [
#       {"type": "text", "text": REFERENCE_DOC, "cache_control": {"type": "ephemeral"}},
#       {"type": "text", "text": "What is the cache TTL?"}
#     ]}
#   ]
print()


# ─── SECTION A2: Cache placement matters ─────────────────────────────────────
# cache_control is a watermark: everything before it (in token order) gets cached.
# Test what happens when you move it to different positions.

TOOLS = [
    {
        "name": "search",
        "description": "Search the web for real-time information.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"]
        }
    }
]

print("A2 — cache placement experiment:")
# TODO: experiment 1 — cache_control on the system prompt only
#   Measure how many tokens are cached vs regular on call 2
#
# TODO: experiment 2 — cache_control on a tool definition
#   Wrap the search tool in {"cache_control": {"type": "ephemeral"}} at the end
#   Measure: do tool definitions get cached separately from the system prompt?
#
# NOTE: Tool definitions are passed as a list to the `tools` param, not in messages.
# The API caches tools that have cache_control in their definition.
#
# Print the before/after token counts for both experiments.
# OBSERVATION: which placement gives better cache utilization for an agent loop?
print()


# ─── SECTION A3: Agent loop caching ──────────────────────────────────────────
# In a multi-step agent loop, the system prompt + tool definitions are identical
# on every iteration. Without caching, you pay for them in full on every call.
# With caching, after the first call you only pay for the new messages.

print("A3 — agent loop with and without caching:")

def run_agent_loop(messages, use_cache=False, max_steps=5):
    """Run a simple agent loop and return total tokens spent."""
    total_input = 0
    total_cached = 0

    system = [{"type": "text", "text": LARGE_SYSTEM}]
    if use_cache:
        system[0]["cache_control"] = {"type": "ephemeral"}

    for step in range(max_steps):
        r = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            system=system,
            messages=messages,
            tools=TOOLS
        )
        total_input += r.usage.input_tokens
        total_cached += r.usage.cache_read_input_tokens

        # For this demo, just add a fake response and continue
        messages.append({"role": "assistant", "content": r.content})
        if r.stop_reason == "end_turn":
            break
        # Add fake tool result to continue the loop
        for block in r.content:
            if block.type == "tool_use":
                messages.append({"role": "user", "content": [{
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"[fake result for {block.name}]"
                }]})
                break

    return total_input, total_cached

base_messages = [{"role": "user", "content": "Search for Python best practices and write a summary to notes.txt"}]

# TODO: run the loop twice (once without cache, once with cache)
# Compare total_input and total_cached
# Calculate: what % of tokens were served from cache with caching enabled?
print()


# ─── MINI PROJECT: Cache-optimize the Session 3 research agent ───────────────
# Take session3.py and add cache_control at the right breakpoints.
# Run it once cold, then re-run within 5 minutes.
# Log: regular tokens, cache_creation tokens, cache_read tokens per step.
# Calculate: total cost reduction from caching (cache read ~= 10% of input price).

# Import your research agent from session3 and wrap it here, OR
# copy the agent loop and add cache profiling.

# Expected output:
#   Step 1: regular=2341  created=847  read=0
#   Step 2: regular=312   created=0    read=847
#   Step 3: regular=198   created=0    read=847
#   Cache hit rate: 73%   Estimated cost reduction: ~63%

if __name__ == "__main__":
    print("\n─── Mini Project: Cache Profiler ───")
    # TODO: implement the cache-profiled research agent
    pass
