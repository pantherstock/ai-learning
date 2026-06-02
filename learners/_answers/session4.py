"""
Session 4 — Architecture Patterns · REFERENCE ANSWERS

One worked solution per chunk. Read these AFTER you've tried session4.py yourself.
The whole point of this file: all three patterns reuse ONE loop (agent_loop). They
differ only in the system prompt and which tools they get — not in the machinery.

Uses the real Brave Search when BRAVE_SEARCH_API_KEY is set, and falls back to a
FAKE one-line search otherwise — so the run stays reproducible with no key / no
network. The structural lessons (Thought-vs-action, plan divergence, context
isolation) show up regardless of whether the search returns real data.

Run with: python session4.py
"""

import env  # auto-loads .env — no manual `export` needed
import os
import sys
import anthropic
import requests

sys.stdout.reconfigure(encoding="utf-8")  # the model sometimes prints emoji (stars); Windows cp1252 console would crash on them

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"
BRAVE_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")


# ─── Shared tools (the same ones from Session 2) ─────────────────────────────
def search(query):
    # Real Brave Search when a key is set; otherwise a fake one-liner so the
    # structural lessons still run with no key and no network.
    if not BRAVE_KEY:
        return f"[fake search result for '{query}']"
    r = requests.get("https://api.search.brave.com/res/v1/web/search",
                     headers={"X-Subscription-Token": BRAVE_KEY},
                     params={"q": query, "count": 3})
    results = r.json().get("web", {}).get("results", [])
    return "\n".join(f"- {x['title']}: {x['description']}" for x in results)


def write_file(filename, content):
    with open(filename, "w", encoding="utf-8") as f:  # utf-8: model output may contain emoji
        f.write(content)
    return f"wrote {filename}"


def execute_tool(name, args):
    if name == "search":
        return search(**args)
    if name == "write_file":
        return write_file(**args)
    if name == "call_subagent":
        return call_subagent(**args)  # defined in 4C
    return f"Error: unknown tool '{name}'"


TOOLS = [
    {"name": "search", "description": "Search the web for recent information",
     "input_schema": {"type": "object",
                      "properties": {"query": {"type": "string"}},
                      "required": ["query"]}},
    {"name": "write_file", "description": "Write text to a file",
     "input_schema": {"type": "object",
                      "properties": {"filename": {"type": "string"},
                                     "content": {"type": "string"}},
                      "required": ["filename", "content"]}},
]


# ─── The ONE loop every pattern reuses ───────────────────────────────────────
# This is just the Session 2 agent loop, returning the numbers we want to compare.
def agent_loop(messages, system, tools=TOOLS, max_steps=10):
    steps, tokens, answer = 0, 0, ""
    while steps < max_steps:
        r = client.messages.create(model=MODEL, max_tokens=1024,
                                   system=system, messages=messages, tools=tools)
        tokens += r.usage.input_tokens + r.usage.output_tokens
        steps += 1
        messages.append({"role": "assistant", "content": r.content})

        for block in r.content:
            if block.type == "text" and "Thought:" in block.text:
                print("  " + block.text.strip().splitlines()[0])  # show the Thought line

        if r.stop_reason != "tool_use":
            answer = next((b.text for b in r.content if b.type == "text"), "")
            break

        for block in r.content:
            if block.type == "tool_use":
                print(f"  -> {block.name}({block.input})")
                messages.append({"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": block.id,
                    "content": execute_tool(block.name, block.input)}]})
    return {"steps": steps, "tokens": tokens, "answer": answer}


# ─── CHUNK 4A: ReAct — thinking before acting ────────────────────────────────
REACT_SYSTEM = ("You are a research assistant. Before every tool call, write a line "
                "starting with 'Thought:' explaining what you're about to do and why.")


def run_react_agent(task, max_steps=10):
    result = agent_loop([{"role": "user", "content": task}], REACT_SYSTEM, max_steps=max_steps)
    result["quality"] = "visible reasoning, easy to debug"
    return result

# CHALLENGE ANSWER:
#   Task: "Find the current population of Tokyo, then convert it to millions..."
#   The Thought line often says "I'll search for Tokyo's population" — then the model
#   answers the conversion straight from its own training knowledge WITHOUT a second
#   tool call, or searches with a vaguer query than the Thought promised. The stated
#   plan and the actual action drift apart. That gap is the whole lesson: a Thought
#   trace tells you what the model SAID it would do, not what it did.


# ─── CHUNK 4B: Plan-and-execute — and break it ───────────────────────────────
def run_plan_execute_agent(task, max_steps=10):
    # Phase 1 — plan only, no tools.
    plan = client.messages.create(
        model=MODEL, max_tokens=1024,
        system="Create a numbered step-by-step plan. Do not execute it. Be specific.",
        messages=[{"role": "user", "content": task}])
    plan_text = plan.content[0].text
    print("PLAN:\n" + plan_text + "\n")

    # Phase 2 — execute the fixed plan. Seed tokens with the planning call.
    result = agent_loop([{"role": "user", "content": task}],
                        f"Execute this plan step by step:\n\n{plan_text}", max_steps=max_steps)
    result["tokens"] += plan.usage.input_tokens + plan.usage.output_tokens
    result["quality"] = "great for fixed tasks; blind when reality diverges"
    return result

# CHALLENGE ANSWER:
#   Task: framework -> its latest version -> is that version <1 year old?
#   The plan is written ONCE, up front, before any step has run — so it bakes in a
#   guess about what step 2 will return. When the real result differs, the executor
#   usually keeps marching down the pre-written steps instead of re-planning, and
#   states a confident-but-wrong final answer. It diverges at the first step whose
#   input depends on a previous step's actual result (here, step 3's "<1 year old?"
#   judgement built on whatever version step 2 produced).


# ─── CHUNK 4C: Multi-agent — orchestrator and sub-agent ──────────────────────
def call_subagent(task):
    # A fresh, self-contained loop with its OWN context window (starts empty).
    messages = [{"role": "user", "content": task}]
    result = agent_loop(messages, "You are a focused research assistant.", max_steps=8)
    print(f"  [sub-agent done in {result['steps']} steps, context = {len(messages)} msgs]")
    return result["answer"]


SUBAGENT_TOOL = [{
    "name": "call_subagent",
    "description": "Delegate ONE focused research task to a sub-agent",
    "input_schema": {"type": "object",
                     "properties": {"task": {"type": "string"}},
                     "required": ["task"]}}]


def run_multi_agent(task, max_steps=8):
    # The orchestrator is just agent_loop with a different toolset: its ONLY tool
    # is call_subagent. Same machinery, different wiring.
    messages = [{"role": "user", "content": task}]
    result = agent_loop(
        messages,
        "You are an orchestrator. Break the task into focused sub-tasks, delegate each "
        "one with call_subagent, then combine their answers into a final recommendation.",
        tools=SUBAGENT_TOOL, max_steps=max_steps)
    print(f"[orchestrator context = {len(messages)} msgs]")
    result["quality"] = "sub-agents stay short; orchestrator sees only summaries"
    return result

# CHALLENGE ANSWER:
#   Task: research Rust, Go, Python -> recommend one for a CLI tool.
#   Each sub-agent starts from an EMPTY context and sees only its own one-language
#   task, so its message list stays short (a handful of msgs). A single agent doing
#   all three would carry every search result for all three languages in one growing
#   context. The orchestrator's own context only ever holds three short sub-agent
#   ANSWERS, not their raw research — that's why splitting the work keeps each
#   context small and focused.


# ─── COMPARE: one task, all three patterns (the deliverable) ─────────────────
def compare(task):
    rows = {
        "react":        run_react_agent(task),
        "plan_execute": run_plan_execute_agent(task),
        "multi_agent":  run_multi_agent(task),
    }
    print(f"\n{'pattern':<14}{'steps':>7}{'tokens':>9}  quality")
    for name, r in rows.items():
        print(f"{name:<14}{r['steps']:>7}{r['tokens']:>9}  {r['quality']}")
    return rows

# CHALLENGE ANSWER (run each pattern 3x to fill this in for real):
#   plan_execute is usually the most CONSISTENT step count — the plan fixes the number
#   of steps in advance. react is the most VARIABLE — it decides each step live, so a
#   stray extra search changes the count. The best single result often comes from the
#   more variable pattern, because adapting live beats following a stale plan. When the
#   most consistent pattern isn't the highest-quality one, that's the reliability-vs-
#   quality tradeoff: predictable cost vs. best-case answer. For this task I'd pick
#   multi_agent — independent, comparable sub-results map cleanly onto "research N
#   things, then recommend one."


if __name__ == "__main__":
    print("=== 4A: ReAct ===")
    run_react_agent("Find the current population of Tokyo, then convert it to "
                    "millions rounded to one decimal.")

    print("\n=== COMPARE: three patterns, one task ===")
    compare("Find 3 recent Python libraries for building REST APIs, compare their "
            "GitHub star counts, and write a brief recommendation to api-libraries.md.")
