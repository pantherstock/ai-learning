"""
Section C — Subagents vs Skills
When does something belong in a tool, a skill module, or a subagent?
Learn to make that call, and refactor your code accordingly.

Prerequisites: complete Sessions 2 and 4 first.
Run with: python skills.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import os
import time

client = anthropic.Anthropic()


# ─── WARM-UP: Cost and latency comparison ────────────────────────────────────
# Solve the same task as (a) a direct tool call, (b) a subagent call.
# Measure tokens and wall-clock time for each.

def as_tool_call(query: str) -> str:
    """Directly call a Python function — no LLM involved."""
    # This is a "tool" in the sense that it's just code your agent calls
    return f"Word count for '{query}': {len(query.split())} words"

def as_subagent_call(query: str) -> str:
    """Delegate to a Claude instance — LLM involved, new context window."""
    r = client.messages.create(
        model="claude-haiku-4-5-20251001", max_tokens=50,
        messages=[{"role": "user", "content": f"Count the words in this text: {query}"}]
    )
    return r.content[0].text

test_input = "The quick brown fox jumped over the lazy dog"

print("Warm-up — tool vs subagent cost comparison:")
t = time.time()
result_a = as_tool_call(test_input)
print(f"  Tool:     {result_a!r}  ({(time.time()-t)*1000:.0f}ms, 0 tokens)")

t = time.time()
result_b = as_subagent_call(test_input)
print(f"  Subagent: {result_b!r}  ({(time.time()-t)*1000:.0f}ms, ~50 tokens)")

# Observe: for a task solvable by code alone, the tool call is faster and free.
# Subagents cost tokens and ~1–2 seconds of latency per call.
# OBSERVATION: when is paying that cost worth it?
print()


# ─── SECTION C1: The decision framework ──────────────────────────────────────
# Use this mental model when deciding how to implement a capability:
#
#   Tool (Python function):
#     - Deterministic, no reasoning needed
#     - Fast (< 1ms)
#     - Zero token cost
#     - Examples: file I/O, math, date parsing, API calls with fixed schemas
#
#   Skill module (Python class wrapping tools):
#     - Reusable across multiple agents
#     - Encapsulates related tools + their error handling
#     - Still zero LLM cost to run
#     - Examples: SearchSkill, MemorySkill, FileSkill
#
#   Subagent (Claude instance):
#     - Needs reasoning or language understanding
#     - Can use its own tools
#     - Has its own isolated context window
#     - Token cost + latency on every call
#     - Examples: code reviewer, research assistant, summarizer
#
#   Independent agent (top-level loop):
#     - Long-running autonomous task
#     - Manages its own context, compression, logging
#     - Examples: Session 3's research agent, capstone project

print("C1 — categorize these capabilities:")
capabilities = [
    "Parse a date string into a datetime object",
    "Decide whether a user's question is about billing or technical support",
    "Fetch a URL and return the HTML",
    "Write a three-paragraph summary of 5 search results",
    "Validate that a JSON object matches a schema",
    "Generate a code review for a Python function",
    "Retry an API call with exponential backoff",
    "Translate a user message to Spanish",
]
for cap in capabilities:
    # TODO: print each capability and your classification (tool / skill / subagent / agent)
    # Then explain in one sentence why.
    pass
print()


# ─── SECTION C2: Skill modules ───────────────────────────────────────────────
# A skill is a Python class that bundles related tools and their schemas.
# It gives you one consistent interface regardless of what's underneath.

class SearchSkill:
    """Encapsulates web search — works with Brave or falls back to fake results."""

    BRAVE_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")

    @property
    def tool_definition(self):
        return {
            "name": "search",
            "description": "Search the web for real-time information not in the model's training data.",
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }

    def run(self, query: str) -> str:
        if not self.BRAVE_KEY:
            return f"[fake search: {query}]"
        import requests
        r = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"X-Subscription-Token": self.BRAVE_KEY},
            params={"q": query, "count": 3}
        )
        results = r.json().get("web", {}).get("results", [])
        return "\n".join(f"- {x['title']}: {x['description']}" for x in results)


class FileSkill:
    """Encapsulates file I/O with error handling."""

    @property
    def tool_definitions(self):
        return [
            {
                "name": "read_file",
                "description": "Read the contents of a file.",
                "input_schema": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"]
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

    def read(self, path: str) -> str:
        try:
            with open(path) as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: file '{path}' not found"

    def write(self, path: str, content: str) -> str:
        with open(path, "w") as f:
            f.write(content)
        return f"Written to {path}"

    def run(self, name: str, args: dict) -> str:
        if name == "read_file":  return self.read(args["path"])
        if name == "write_file": return self.write(args["path"], args["content"])
        return f"Unknown file operation: {name}"


# TODO: build a MemorySkill class that wraps an in-memory list of past facts
# Interface should include:
#   - tool_definition property (single "remember_fact" tool)
#   - remember(fact: str) -> str
#   - recall_all() -> str (returns all stored facts as a string)

class MemorySkill:
    def __init__(self):
        self.facts = []

    @property
    def tool_definition(self):
        # TODO
        pass

    def remember(self, fact: str) -> str:
        # TODO: append to self.facts, return confirmation
        pass

    def recall_all(self) -> str:
        # TODO: return all facts as a newline-separated string, or "(empty)" if none
        pass


print("C2 — skill modules:")
search = SearchSkill()
files  = FileSkill()
memory = MemorySkill()

print("SearchSkill:", search.run("Python 3.13 features")[:80])
files.write("test_skill.txt", "Hello from FileSkill")
print("FileSkill read:", files.read("test_skill.txt"))
# TODO: test MemorySkill once implemented
print()


# ─── SECTION C3: Subagent specialization ─────────────────────────────────────
# Give each subagent different tools and a different system prompt.
# A researcher (search + memory) vs a writer (file I/O only) work better
# when each stays in their lane.

class ResearcherAgent:
    """Subagent specialized in gathering information."""

    def __init__(self):
        self.search = SearchSkill()
        self.memory = MemorySkill()

    @property
    def tools(self):
        return [self.search.tool_definition, self.memory.tool_definition]

    def run(self, task: str, max_steps=6) -> str:
        messages = [{"role": "user", "content": task}]
        system = "You are a research assistant. Search the web, remember key facts you find, and return a summary of what you learned."

        for _ in range(max_steps):
            r = client.messages.create(
                model="claude-haiku-4-5-20251001", max_tokens=400,
                system=system, tools=self.tools, messages=messages
            )
            messages.append({"role": "assistant", "content": r.content})
            if r.stop_reason == "end_turn":
                return r.content[0].text
            for block in r.content:
                if block.type == "tool_use":
                    if block.name == "search":
                        result = self.search.run(block.input["query"])
                    elif block.name == "remember_fact":
                        # TODO: call self.memory.remember() once MemorySkill is implemented
                        result = "[memory not implemented]"
                    else:
                        result = f"Unknown tool: {block.name}"
                    messages.append({"role": "user", "content": [{
                        "type": "tool_result", "tool_use_id": block.id, "content": result
                    }]})
        return "Researcher reached step limit."


class WriterAgent:
    """Subagent specialized in writing to files."""

    def __init__(self):
        self.files = FileSkill()

    @property
    def tools(self):
        return self.files.tool_definitions

    def run(self, task: str, context: str, max_steps=4) -> str:
        messages = [{"role": "user", "content": f"{task}\n\nContext to use:\n{context}"}]
        system = "You are a technical writer. Use the provided context to write clear, well-structured documents."

        for _ in range(max_steps):
            r = client.messages.create(
                model="claude-haiku-4-5-20251001", max_tokens=600,
                system=system, tools=self.tools, messages=messages
            )
            messages.append({"role": "assistant", "content": r.content})
            if r.stop_reason == "end_turn":
                return r.content[0].text
            for block in r.content:
                if block.type == "tool_use":
                    result = self.files.run(block.name, block.input)
                    messages.append({"role": "user", "content": [{
                        "type": "tool_result", "tool_use_id": block.id, "content": result
                    }]})
        return "Writer reached step limit."


# TODO: implement the observe_this challenge:
# Log the number of messages in ResearcherAgent's loop vs WriterAgent's loop.
# Why does keeping them separate keep each one's context smaller?
# OBSERVATION:

print("C3 — specialized subagents:")
researcher = ResearcherAgent()
writer = WriterAgent()

# TODO: run a two-phase pipeline:
#   1. researcher.run("Find 3 key facts about FastAPI") -> facts
#   2. writer.run("Write a short intro to fastapi.md", context=facts)
print()


# ─── MINI PROJECT: Refactor the Session 3 research agent ─────────────────────
# Session 3's research agent has all its tools and logic inline.
# Refactor it to use SearchSkill, FileSkill, and MemorySkill.
# Then compare: is the new code easier to test, read, and modify?
# Push to GitHub when done.

if __name__ == "__main__":
    print("─── Mini Project: Skill-based Research Agent ───")
    # TODO: wire SearchSkill + FileSkill + MemorySkill into an agent loop
    # The agent should: research a topic, remember key facts, write a summary file
    pass
