"""
Session 4 — Architecture Patterns
There are several ways to structure an agent. Each one wins in different situations.

Requires: BRAVE_SEARCH_API_KEY in your .env (auto-loaded, for the comparison task).
Run with: python session4.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import os
import json

client = anthropic.Anthropic()

# Reuse search + write_file from session 3 (copy or import if you prefer)
BRAVE_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")

def search(query: str) -> str:
    if not BRAVE_KEY:
        return f"[fake search result for: {query}]"
    import requests
    r = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={"X-Subscription-Token": BRAVE_KEY},
        params={"q": query, "count": 3}
    )
    results = r.json().get("web", {}).get("results", [])
    return "\n".join(f"- {x['title']}: {x['description']}" for x in results)

def write_file(path: str, content: str) -> str:
    with open(path, "w") as f:
        f.write(content)
    return f"Written to {path}"

agent_tools = [
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

def execute_tool(name, args):
    if name == "search": return search(args["query"])
    if name == "write_file": return write_file(args["path"], args["content"])
    return f"Unknown tool: {name}"


# ─── WARM-UP: Turn on Thought lines ──────────────────────────────────────────
# Add one sentence to your system prompt to enable ReAct:

react_system = """You are a research assistant.
Before every tool call, write a line starting with 'Thought:' explaining what you're about to do and why."""

# Run any task from Session 3 with this system prompt. Read the Thought lines.
# (This is the ReAct pattern — you just turned it on with one sentence.)


# ─── CHUNK 4A: ReAct — thinking before acting ────────────────────────────────
# Build a proper ReAct agent. Enforce the Thought: format. Compare with and without.

def run_react_agent(task: str, max_steps=10) -> dict:
    messages = [{"role": "user", "content": task}]
    steps = 0
    total_tokens = 0

    # TODO: implement the ReAct agent loop using react_system
    # Log each tool choice and the Thought: line that preceded it
    # Return {"steps": steps, "tokens": total_tokens, "quality": ""}

    return {"steps": steps, "tokens": total_tokens, "quality": ""}


# ─── CHUNK 4B: Plan-and-execute — and break it ───────────────────────────────
# Two API calls instead of one loop: first produce a plan, then execute it.

def run_plan_execute_agent(task: str, max_steps=10) -> dict:
    # Phase 1: plan only (no tools available)
    plan_r = client.messages.create(
        model="claude-haiku-4-5-20251001", max_tokens=400,
        system="Create a numbered step-by-step plan. Do not execute. Be specific.",
        messages=[{"role": "user", "content": task}]
    )
    plan = plan_r.content[0].text
    print(f"\nPlan:\n{plan}\n")

    # Phase 2: execute with tools, plan as context
    exec_system = f"Execute this plan step by step:\n\n{plan}"
    messages = [{"role": "user", "content": task}]
    steps = 0
    total_tokens = plan_r.usage.input_tokens + plan_r.usage.output_tokens

    # TODO: run the agent loop with exec_system as the system prompt
    # Watch for: does it adapt when step N's result differs from what the plan assumed?

    return {"steps": steps, "tokens": total_tokens, "quality": ""}


# ─── CHUNK 4C: Multi-agent — orchestrator and sub-agent ──────────────────────
# The orchestrator's only tool is call_subagent(task).
# Each agent has its own independent context window — this is the key insight.

def call_subagent(task: str) -> str:
    """Run the agent loop on a subtask and return the final answer."""
    sub_messages = [{"role": "user", "content": task}]
    step = 0

    # TODO: implement the sub-agent loop (max 8 steps)
    # Log len(sub_messages) at each step so you can compare context size
    # Return the final text or "Sub-agent reached step limit."
    return "Sub-agent not implemented yet."

orchestrator_tools = [{
    "name": "call_subagent",
    "description": "Delegate a specific, self-contained research subtask to a sub-agent.",
    "input_schema": {
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "The complete, self-contained task for the sub-agent."}
        },
        "required": ["task"]
    }
}]

def run_multi_agent(task: str, max_steps=8) -> dict:
    messages = [{"role": "user", "content": task}]
    steps = 0
    total_tokens = 0

    # TODO: implement the orchestrator loop
    # When stop_reason == "tool_use" and tool name == "call_subagent":
    #   result = call_subagent(block.input["task"])
    # Track orchestrator context size vs sub-agent context size

    return {"steps": steps, "tokens": total_tokens, "quality": ""}


# ─── CHUNK 4D: Compare all three patterns ────────────────────────────────────
# Run the exact same task through all three patterns.
# Log steps, tokens, and your quality judgement.

COMPARISON_TASK = (
    "Find 3 recent Python libraries for building REST APIs, "
    "compare their GitHub star counts, and write a brief recommendation to api-libraries.md."
)

results = {
    "react":            {"steps": 0, "tokens": 0, "quality": ""},
    "plan_and_execute": {"steps": 0, "tokens": 0, "quality": ""},
    "multi_agent":      {"steps": 0, "tokens": 0, "quality": ""}
}

if __name__ == "__main__":
    print("─── Session 4: Architecture Pattern Comparison ───")
    print(f"Task: {COMPARISON_TASK}\n")

    # TODO: run each pattern and fill in results
    # results["react"] = run_react_agent(COMPARISON_TASK)
    # results["plan_and_execute"] = run_plan_execute_agent(COMPARISON_TASK)
    # results["multi_agent"] = run_multi_agent(COMPARISON_TASK)

    print("\n─── Comparison Results ───")
    for pattern, data in results.items():
        print(f"{pattern:20s}: {data['steps']} steps, {data['tokens']:,} tokens — {data['quality']}")

    # After running 3 times per pattern, note which has the most consistent step count.
    # The logs from this comparison are your deliverable for this session.
