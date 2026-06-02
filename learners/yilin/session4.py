"""
Session 4 — Architecture Patterns
There are several ways to structure an agent. Each one wins in different situations.

Each chunk is CONCEPT -> TODO -> CHALLENGE (see session1.py).
Run with: python session4.py

The big idea: all three patterns reuse ONE loop. Build it once (below), then each
pattern is just a different system prompt + toolset. Stuck? See ../_answers/session4.py.
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"

# TODO: reuse search + write_file + execute_tool (and their schemas) from Session 2.
# Copy them here. Keep the FAKE one-line search — no API key needed; the structural
# lessons below show up no matter what the search returns.
#
# TODO: factor the Session 2 agent loop into ONE reusable function — this is the
#   whole point of the session, so every pattern shares it:
#     def agent_loop(messages, system, tools, max_steps=10) -> dict:
#         # loop: create() -> append assistant -> run tool_use blocks -> repeat
#         # until stop_reason != "tool_use" or max_steps; tally r.usage tokens.
#         # return {"steps": ..., "tokens": ..., "answer": ...}
#   ReAct, plan-execute, and the multi-agent sub-agent are all just calls to this.

# ─── Shared tools (the same ones from Session 2) ─────────────────────────────
def search(query):
    if "Tokyo" in query:
        return "[Search result: Tokyo has 37.3 million people as of last year]"
    return f"[fake search result for '{query}']"


def write_file(filename, content):
    print(f"--------------- WRITING TO FILE: {filename}")
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


# ─── WARM-UP: Turn on Thought lines ──────────────────────────────────────────
# ReAct is literally one sentence in the system prompt. Run any Session 3 task with:
#   "You are a research assistant. Before every tool call, write a line starting
#    with 'Thought:' explaining what you're about to do and why."
# Read the Thought lines as they stream. You just turned on the ReAct pattern.


# ─── CHUNK 4A: ReAct — thinking before acting ────────────────────────────────
# CONCEPT
#   Reason + Act: the model states a Thought: before each action. This tends to
#   improve decisions AND gives you a trace to debug. But stated reasoning and the
#   tool actually chosen don't always agree — that gap is worth seeing.
#
# TODO: run_react_agent(task) — just call agent_loop with the warm-up system prompt
#   ("...write a line starting with 'Thought:' before every tool call..."). Print each
#   Thought: line as it streams. Add your own "quality" judgement to the result dict.
#
# CHALLENGE (write the answers in comments):
#   Run this EXACT task: "Find the current population of Tokyo, then convert it to
#   millions rounded to one decimal." Find one step where the Thought: correctly
#   describes the need but the tool call (or its arguments) is wrong. Quote both
#   lines. What was the mismatch?

# task = "Find the current population of Tokyo, then convert it to millions rounded to one decimal."
REACT_SYSTEM = "You are a research assistant. Before every tool call, write a line starting with 'Thought:' explaining what you're about to do and why."
def run_react_agent(task, max_steps=10):
    result = agent_loop([{"role": "user", "content": task}], REACT_SYSTEM, max_steps=max_steps)
    return result

# print(run_react_agent(task))


# ─── CHUNK 4B: Plan-and-execute — and break it ───────────────────────────────
# CONCEPT
#   Two phases instead of one loop: first produce a plan, then execute it. Great
#   for well-defined tasks; fragile when reality diverges from the plan mid-run.
#
# TODO: run_plan_execute_agent(task) — two phases:
#   Phase 1 — one call, NO tools, system "Create a numbered step-by-step plan. Do
#     not execute it. Be specific." Capture the plan text.
#   Phase 2 — agent_loop with system f"Execute this plan step by step:\n\n{plan}".
#   Add the planning call's usage to the loop's token count.
#
# CHALLENGE (write the answers in comments):
#   Run this EXACT task, designed so step 3 depends on step 2's result:
#     "Find the most popular Python web framework. Then look up its latest version.
#      Then state whether that version is less than a year old."
#   When execution reaches a step whose assumption the plan got wrong, does the
#   executor adapt, skip ahead, or proceed blindly to a wrong answer? Note the exact
#   step where it diverges and what it did.

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
                        f"Execute this plan step by step. If any step fails, continue with the next step and ensure all steps are completed:\n\n{plan_text}", max_steps=max_steps)
    result["tokens"] += plan.usage.input_tokens + plan.usage.output_tokens
    return result

# task = "Find the most popular Python web framework. Then look up its latest version. Then state whether that version is less than a year old."
# print(run_plan_execute_agent(task))


# ─── CHUNK 4C: Multi-agent — orchestrator and sub-agent ──────────────────────
# CONCEPT
#   The orchestrator's ONLY tool is call_subagent(task). The sub-agent is your
#   Session 2 loop. Key insight: each agent has its OWN context window, so the
#   sub-agent's context stays short and focused — a feature, not a limitation.
#
# TODO: call_subagent(task) -> str — agent_loop on a FRESH messages list (its own
#   context), returning the answer; print len(sub_messages) so you can see it stays
#   short. Add call_subagent to execute_tool. Then run_multi_agent(task) is just
#   agent_loop with the orchestrator system prompt and ONLY the call_subagent tool.
#
# CHALLENGE (write the answers in comments):
#   Run this EXACT task: "Research three programming languages — Rust, Go, and
#   Python — and recommend one for a new CLI tool." Print len(messages) for the
#   orchestrator and len(sub_messages) for each sub-agent call. Why does each
#   sub-agent stay shorter than a single agent doing all three would?

def call_subagent(task):
    print(f"  [sub-agent tasked with: {task}]")
    # A fresh, self-contained loop with its OWN context window (starts empty).
    messages = [{"role": "user", "content": task}]
    result = agent_loop(messages, "You are a focused research assistant.", max_steps=8)
    print(f"  [sub-agent done in {result['steps']} steps, context = {len(messages)} msgs]")
    return result["answer"]

def run_multi_agent(task, max_steps=8):
    # The orchestrator is just agent_loop with a different toolset: its ONLY tool
    # is call_subagent. Same machinery, different wiring.
    messages = [{"role": "user", "content": task}]
    result = agent_loop(
        messages,
        "You are an orchestrator. Break the task into focused sub-tasks, delegate each one with call_subagent, then combine their answers into a final recommendation.",
        tools=[{
            "name": "call_subagent",
            "description": "Delegate ONE focused research task to a sub-agent",
            "input_schema": {"type": "object",
                             "properties": {"task": {"type": "string"}},
                             "required": ["task"]}}
        ], max_steps=max_steps)
    print(f"[orchestrator answer = {result['answer']}]")
    print(f"[orchestrator context = {len(messages)} msgs]")
    print("-------")
    print(messages)
    return result

# run_multi_agent("Research three programming languages — Rust, Go, and Python — and recommend one for a new CLI tool.")

# ─── COMPARE: one task, all three patterns (this session's deliverable) ──────
# CONCEPT
#   There is no universal best pattern. You build intuition by running ONE task
#   through all three and comparing cost, consistency, and quality.
#
# TODO: run react / plan_execute / multi_agent on this EXACT shared task:
#     "Find 3 recent Python libraries for building REST APIs, compare their GitHub
#      star counts, and write a brief recommendation to api-libraries.md."
#   Print a table of steps / tokens / your-quality-rating for each pattern.
#
# CHALLENGE (the deliverable — keep the table + notes):
#   Run each pattern 3 times on the task. Which pattern has the most CONSISTENT
#   step count across its 3 runs? Which produced the best single result? If those
#   are different patterns, what does that say about reliability vs. quality?
#
# Done when: you have a 3x3 (pattern x metric) table and a one-paragraph note on
#   which pattern you'd pick for this task and why.


def compare():
    rows = {
        # "react":        run_react_agent(task = "Find 3 recent Python libraries for building REST APIs, compare their GitHub star counts, and write a brief recommendation to api-libraries-react.md."),
        "plan_execute": run_plan_execute_agent(task = "Find 3 recent Python libraries for building REST APIs, compare their GitHub star counts, and write a brief recommendation to api-libraries-plan_execute.md."),
        # "multi_agent":  run_multi_agent(task = "Find 3 recent Python libraries for building REST APIs, compare their GitHub star counts, and write a brief recommendation to api-libraries-multi_agent.md."),
    }
    print(f"\n{'pattern':<14}{'steps':>7}{'tokens':>9}")
    for name, r in rows.items():
        print(f"{name:<14}{r['steps']:>7}{r['tokens']:>9}")
    return rows

compare()