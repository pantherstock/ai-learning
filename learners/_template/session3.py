"""
Session 3 — Context is Your Budget
Hit the limits, then build instincts to manage them.

Requires: BRAVE_SEARCH_API_KEY in your .env (auto-loaded).
Run with: python session3.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import requests
import json
import time
import os

client = anthropic.Anthropic()

BRAVE_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")


# ─── WARM-UP: Watch the tokens climb ─────────────────────────────────────────
# Take your agent from Session 2. Add this line at the start of each loop
# iteration before the API call:
#   print(f"Step {step}: {sum(len(str(m)) for m in messages)//4} approx tokens in messages")
#
# Run a 15-step task and watch the number grow every single step.
# Everything in this session is a direct response to that problem.

# (Do this in your session2.py first — then come back here.)


# ─── CHUNK 3A: Wire a real search tool ───────────────────────────────────────
# Replace fake search with real Brave Search API.

def search(query: str) -> str:
    if not BRAVE_KEY:
        return "Error: BRAVE_SEARCH_API_KEY not set"

    # TODO: make the Brave Search request:
    #   GET https://api.search.brave.com/res/v1/web/search
    #   Headers: {"X-Subscription-Token": BRAVE_KEY}
    #   Params: {"q": query, "count": 3}
    #
    # Parse results = r.json().get("web", {}).get("results", [])
    # Return "\n".join(f"- {x['title']}: {x['description']}" for x in results)
    pass

search_tool = {
    "name": "search",
    "description": "Search the web for real-time information not available in your training data.",
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "The search query"}},
        "required": ["query"]
    }
}

# Test your search function:
print("3A — search test:")
print(search("Python 3.13 new features"))
print()


# ─── CHUNK 3B: Rolling compression ───────────────────────────────────────────
# When message history gets too large, summarize the oldest turns and drop them.
# Trade precision for space.

def maybe_compress(messages, threshold=4000):
    approx_tokens = sum(len(str(m)) for m in messages) // 4
    if approx_tokens < threshold:
        return messages

    to_compress = messages[:-4]   # summarize everything except the last 2 turns
    len_before = len(messages)

    # TODO: call the API to summarize to_compress into 2-3 sentences:
    #   messages=[{"role": "user", "content":
    #       f"Summarize this conversation history in 2-3 sentences, keeping key facts:\n\n{to_compress}"}]
    # Wrap the summary in: [{"role": "user", "content": f"[Earlier context]: {summary}"}]
    # Print f"Compressed {len(to_compress)} messages → 1 summary"
    # Return compressed + messages[-4:]
    pass


# ─── CHUNK 3C: The cost of forgetting ────────────────────────────────────────
# This is the tradeoff made concrete.
# Task:
#   1. Run a 20-step task with compression enabled
#   2. In step 5, note a specific fact the agent encountered (number, name, URL)
#   3. Let compression run
#   4. In step 18, ask the agent directly about that fact
# Does it recall correctly, admit it doesn't know, or confabulate?
#
# (There's no code scaffold here — design the experiment yourself.)
# Write your observation as a comment below after running it:

# OBSERVATION:


# ─── CHUNK 3D: Structured logging ────────────────────────────────────────────
# When a loop fails on step 7, logs are the only way to understand why.

def log(f, event_type, **data):
    f.write(json.dumps({"ts": time.time(), "type": event_type, **data}) + "\n")

# Usage pattern — integrate this into the agent loop:
#
#   with open("agent.log", "w") as log_file:
#       # after each tool call:
#       log(log_file, "tool_call",
#           step=step, tool=block.name,
#           args=block.input, result=result[:200],
#           tokens_in=r.usage.input_tokens)
#
#       # when compression fires:
#       log(log_file, "compression",
#           before_msgs=len_before, after_msgs=len_after)

# TODO: integrate log() calls into the research agent below


# ─── MINI PROJECT: Research agent with compression and logging ────────────────
# Combine: Brave search, write_file, rolling compression at 4000 tokens,
# max_steps=15, token_budget=50_000, and a JSON log file.
# Push to GitHub when done.

write_file_tool = {
    "name": "write_file",
    "description": "Write content to a file.",
    "input_schema": {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "content": {"type": "string"}
        },
        "required": ["filename", "content"]
    }
}

def execute_tool(name, args):
    if name == "search":
        return search(args["query"])
    if name == "write_file":
        with open(args["filename"], "w") as f:
            f.write(args["content"])
        return f"Written to {args['filename']}"
    return f"Unknown tool: {name}"

MAX_STEPS = 15
TOKEN_BUDGET = 50_000

if __name__ == "__main__":
    print("─── Mini Project: Research Agent ───")
    task = "Research the history of reinforcement learning and write a 300-word summary to research.md"
    messages = [{"role": "user", "content": task}]
    step = 0
    total_tokens = 0

    with open("agent.log", "w") as log_file:
        while step < MAX_STEPS and total_tokens < TOKEN_BUDGET:
            # TODO: call maybe_compress on messages before the API call
            # TODO: call the API with [search_tool, write_file_tool]
            # TODO: log each tool call with log()
            # TODO: handle stop_reason == "end_turn"
            # TODO: handle tool_use blocks
            # TODO: log compression events when maybe_compress compresses
            pass

    print("\nRun complete. Check agent.log for the full trace.")
