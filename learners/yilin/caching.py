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
# system prompt (~5000 tokens) as a content block with
#   "cache_control": {"type": "ephemeral"}
# and prints cache_creation_input_tokens and cache_read_input_tokens. Call it 3
# times. Run 1 creates the cache (creation > 0); runs 2-3 read it (read > 0), as
# long as they're within the 5-minute TTL.

# Run 1 - Cache creation input tokens: 5602, Cache read input tokens: 0
# Run 2 - Cache creation input tokens: 0, Cache read input tokens: 5602
# Run 3 - Cache creation input tokens: 0, Cache read input tokens: 5602

LARGE_SYSTEM_PROMPT = "This is a large system prompt " * 800  # ~5600 tokens. NOTE: Haiku 4.5's cache minimum is ~4096 tokens (higher than older Haiku's 2048); ~2800 tokens did NOT cache.
LARGE_TOOL_DEFINITION = {"name": "example_tool", "description": LARGE_SYSTEM_PROMPT, "input_schema": {"type": "object", "properties": {}}}

def call_with_system_cache(question, run_label, system_prompt=LARGE_SYSTEM_PROMPT):
    response = client.messages.create(
        model=MODEL,
        system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": question}],
        max_tokens=50
    )
    print(f"{run_label} - Cache creation input tokens: {response.usage.cache_creation_input_tokens}, Cache read input tokens: {response.usage.cache_read_input_tokens}")

# call_with_system_cache("What is the capital of France?", "Run 1")
# call_with_system_cache("What is the capital of Germany?", "Run 2")
# call_with_system_cache("What is the capital of Italy?", "Run 3")

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

# Run 1 - Cache creation input tokens: 5605, Cache read input tokens: 0
# Run 2 - Cache creation input tokens: 0, Cache read input tokens: 5605

REFERENCE_DOC = "This is a large reference document " * 800  # ~5600 tokens

def call_with_doc_cache(question, run_label):
    response = client.messages.create(
        model=MODEL,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": REFERENCE_DOC, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": question}
        ]}],
        max_tokens=50
    )
    print(f"{run_label} - Cache creation input tokens: {response.usage.cache_creation_input_tokens}, Cache read input tokens: {response.usage.cache_read_input_tokens}")

# call_with_doc_cache("What is the cache TTL?", "Run 1")
# call_with_doc_cache("What is the largest animal in the world?", "Run 2")

# TODO (b) — placement test: run it once caching ONLY the system prompt, once
#   caching a TOOL definition (wrap a tool in {"cache_control":{"type":"ephemeral"}}).
#   Compare how many tokens each placement caches on a typical agent-loop call.
# System Run - Cache creation input tokens: 4802, Cache read input tokens: 0
# Tool Run - Cache creation input tokens: 5010, Cache read input tokens: 0
def call_with_tool_cache(question, run_label):
    response = client.messages.create(
        model=MODEL,
        messages=[{"role": "user", "content": question}],
        tools=[LARGE_TOOL_DEFINITION],
        max_tokens=50
    )
    print(f"{run_label} - Cache creation input tokens: {response.usage.cache_creation_input_tokens}, Cache read input tokens: {response.usage.cache_read_input_tokens}")

# call_with_system_cache("What is the cache TTL?", "System Run")
# call_with_tool_cache("What is the cache TTL?", "Tool Run")


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

# ANSWER: For 20-step, % goes down. Caching dominates the cost as the number of steps go up.
# Caching breaks even after just 1 read (2 total calls):
# 1.25 + 0.1 (N-1) < N
# 1.15 < 0.9N
# 1.28 < N

# Not cached
# {'total_steps': 5, 'total_input_tokens': 58853, 'total_cache_read_tokens': 0}
# Cached
# {'total_steps': 5, 'total_input_tokens': 6344, 'total_cache_read_tokens': 40334}

def run_agent_loop(messages, use_cache=False, max_steps=5) -> dict:
    step, total_input_tokens, total_cache_read_tokens = 0, 0, 0

    system_block = {"type": "text", "text": LARGE_SYSTEM_PROMPT}
    tool_def = LARGE_TOOL_DEFINITION.copy()
    if use_cache:
        system_block["cache_control"] = {"type": "ephemeral"}
        tool_def["cache_control"] = {"type": "ephemeral"}
        
    while step < max_steps:
        r = client.messages.create(
            model=MODEL, max_tokens=10, 
            system=[system_block],
            tools=[tool_def],
            tool_choice={"type": "none"},
            messages=messages
        )
        print(f"\nStep {step + 1}", r.content)

        total_input_tokens += r.usage.input_tokens
        total_cache_read_tokens += r.usage.cache_read_input_tokens
        step += 1

        messages.append({"role": "assistant", "content": r.content})
        messages.append({"role": "user", "content": "Keep going."})

    return {
        "total_steps": step,
        "total_input_tokens": total_input_tokens,
        "total_cache_read_tokens": total_cache_read_tokens,
    }

# print("\nNot cached")
# print(run_agent_loop([{"role": "user", "content": "Research penguins."}], use_cache=False))

print("\nCached, 5 steps")
cached_5_step = run_agent_loop([{"role": "user", "content": "Research penguins."}], use_cache=True, max_steps=5)
print(cached_5_step)
print("\nCached percentage", f"{(cached_5_step['total_cache_read_tokens'] / (cached_5_step['total_input_tokens'] + cached_5_step['total_cache_read_tokens'])) * 100:.2f}%")  # Cached percentage for 5 steps
# Cached percentage 99.71%

print("\nCached, 20 steps")
cached_20_step = run_agent_loop([{"role": "user", "content": "Research penguins."}], use_cache=True, max_steps=20)
print(cached_20_step)
print("\nCached percentage", f"{(cached_20_step['total_cache_read_tokens'] / (cached_20_step['total_input_tokens'] + cached_20_step['total_cache_read_tokens'])) * 100:.2f}%")  # Cached percentage for 20 steps
# Cached percentage 99.64%

# ─── DELIVERABLE ─────────────────────────────────────────────────────────────
# Your A2 run_agent_loop output IS the deliverable. Make sure you can answer:
#   - What % of tokens were cache reads in the 5-step cached run?
#   - How does that % change for a 20-step run?
#   - At roughly what step count does caching break even (cost < uncached)?

# ANSWERS:
# Not cached: {'total_steps': 5, 'total_input_tokens': 58853, 'total_cache_read_tokens': 0}
# Cached 5 steps: {'total_steps': 5, 'total_input_tokens': 6344, 'total_cache_read_tokens': 40334}
# Cached % (5 steps): 99.71% — nearly all tokens served from cache after step 1.
# Cached 20 steps: % goes to 99.64% — marginally lower because new messages accumulate.
# Break-even: after just 1 read (2 total calls): 1.25 + 0.1(N-1) < N → N > 1.28.