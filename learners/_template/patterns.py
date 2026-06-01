"""
Section B — Advanced Agentic Patterns
Four patterns that go beyond the basics in Session 4: reflection, parallel fan-out, routing, human-in-the-loop.

Prerequisites: complete Session 4 first.
Run with: python patterns.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import threading
import os

client = anthropic.Anthropic()
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


# ─── WARM-UP: Reflection in 3 lines ──────────────────────────────────────────
# Add a self-critique pass to any prior agent's output.
# The model reads its own response and identifies what could be improved.

print("Warm-up — instant reflection:")
response = client.messages.create(
    model="claude-haiku-4-5-20251001", max_tokens=200,
    messages=[{"role": "user", "content": "Explain what an API is in one sentence."}]
)
first_answer = response.content[0].text
print(f"First answer:\n{first_answer}\n")

# TODO: make a second call that shows first_answer and asks:
#   "Critique this explanation in one sentence. What's imprecise or misleading?"
# Print the critique.
print()


# ─── SECTION B1: Reflection loop ─────────────────────────────────────────────
# Systematic draft → critique → revise cycle. Stop when the model rates its
# own output as "good" or after N iterations — whichever comes first.

def reflection_loop(task: str, max_iterations=3) -> str:
    """Generate an answer, then iteratively critique and revise it."""
    messages = [{"role": "user", "content": task}]

    # Draft
    r = client.messages.create(
        model="claude-haiku-4-5-20251001", max_tokens=400, messages=messages
    )
    draft = r.content[0].text
    print(f"Draft:\n{draft[:200]}...\n")

    for i in range(max_iterations):
        # TODO: critique phase
        # Ask the model to critique draft with: "Rate this answer good/needs-work.
        # If needs-work, explain what's wrong in one sentence. If good, say DONE."
        # Parse: if "DONE" is in critique, break and return draft
        # Else: revise phase — ask model to rewrite draft addressing the critique
        # Update draft with the revision
        # Print iteration number and whether it continued or stopped
        pass

    return draft

print("B1 — reflection loop:")
result = reflection_loop("Explain the difference between synchronous and asynchronous programming.")
print(f"Final answer:\n{result[:300]}")
print()


# ─── SECTION B2: Parallel fan-out ────────────────────────────────────────────
# Fork work to multiple independent subagents running in parallel.
# Each has its own context window. Merge their results afterwards.
# Use Python's threading.Thread — simpler than asyncio for this use case.

def run_subagent(subtask: str, results: dict, key: str):
    """Run a subagent on subtask and store the result in results[key]."""
    # TODO: implement a simple agent loop (max 5 steps) for subtask
    # Store the final answer in results[key]
    results[key] = "not implemented"

print("B2 — parallel fan-out:")
research_task = "Compare Django vs FastAPI vs Flask for building a REST API"

# Decompose the task into independent subtasks
subtasks = {
    "django":  "Research Django as a Python web framework for REST APIs. What are its main strengths and weaknesses? 2–3 sentences.",
    "fastapi": "Research FastAPI as a Python web framework. What are its main strengths and weaknesses? 2–3 sentences.",
    "flask":   "Research Flask as a Python web framework for REST APIs. What are its main strengths and weaknesses? 2–3 sentences.",
}

# TODO: run all three subtasks in parallel using threading.Thread
# Each thread calls run_subagent(subtask, results, key)
# Wait for all threads to complete with thread.join()
# Then merge: call the API once more with all three results to write a comparison

results = {}
# TODO: spawn threads here

# TODO: merge results with a synthesis call:
#   messages=[{"role": "user", "content":
#     f"Synthesize these three research results into a comparison table:\n\n{results}"}]
print()


# ─── SECTION B3: Router pattern ──────────────────────────────────────────────
# A fast, cheap classifier model reads the user request and decides which
# specialist agent should handle it. The router itself does no domain work.

def classify_intent(user_message: str) -> str:
    """Return one of: 'research', 'code', 'summarize', 'other'"""
    r = client.messages.create(
        model="claude-haiku-4-5-20251001", max_tokens=10,
        system="Classify the user request. Reply with exactly one word: research, code, summarize, or other.",
        messages=[{"role": "user", "content": user_message}]
    )
    return r.content[0].text.strip().lower()

def research_agent(task: str) -> str:
    # TODO: agent loop with search tool
    return f"[research agent: {task[:50]}]"

def code_agent(task: str) -> str:
    # TODO: agent focused on writing/explaining code
    return f"[code agent: {task[:50]}]"

def summarize_agent(task: str) -> str:
    # TODO: single call to summarize provided text
    return f"[summarize agent: {task[:50]}]"

def route(user_message: str) -> str:
    intent = classify_intent(user_message)
    print(f"  Routed to: {intent}")
    if intent == "research": return research_agent(user_message)
    if intent == "code":     return code_agent(user_message)
    if intent == "summarize": return summarize_agent(user_message)
    return client.messages.create(
        model="claude-haiku-4-5-20251001", max_tokens=200,
        messages=[{"role": "user", "content": user_message}]
    ).content[0].text

print("B3 — router pattern:")
test_inputs = [
    "What are the latest Python 3.13 features?",
    "Write a function that reverses a linked list",
    "Summarize: The quick brown fox jumped over the lazy dog many times today.",
    "What's the weather like?"
]
for msg in test_inputs:
    result = route(msg)
    print(f"Input: {msg[:50]}")
    print(f"Result: {result[:80]}\n")


# ─── SECTION B4: Human-in-the-loop ───────────────────────────────────────────
# The agent pauses at key decision points and asks for human confirmation
# before taking an irreversible or risky action.
# Implement as a special tool: ask_human(question) -> human's typed response.

def ask_human(question: str) -> str:
    """Pause the agent and ask the human a question."""
    print(f"\n  [AGENT PAUSED] {question}")
    answer = input("  Your answer: ").strip()
    return answer or "no response"

hitl_tools = [
    {
        "name": "ask_human",
        "description": (
            "Pause and ask the human for confirmation or additional information. "
            "Use this before any irreversible action like deleting data, sending messages, "
            "or making purchases. Also use when you're uncertain about user intent."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"question": {"type": "string", "description": "The question to ask the human."}},
            "required": ["question"]
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

print("B4 — human-in-the-loop:")
# TODO: build an agent loop that uses hitl_tools
# Give it the task: "Write a summary of machine learning to ml_summary.txt,
# but ask the human how detailed it should be before writing."
# When the agent calls ask_human: invoke the ask_human function, return the answer
# as a tool_result, and continue the loop

# The observe: does the agent actually ask before writing, or does it just write anyway?
# Try rephrasing the system prompt to make it more or less likely to ask.
# OBSERVATION:
