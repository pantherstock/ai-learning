"""
Section C — Subagents vs Skills
When does something belong in a tool, a skill module, or a subagent? Learn to make
that call, and refactor your code accordingly.

Each section is CONCEPT -> TODO -> CHALLENGE (see session1.py).
Prerequisites: complete Sessions 2 and 4 first.
Run with: python skills.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import os
import time

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"


# ─── WARM-UP: Cost and latency comparison ────────────────────────────────────
# TODO: solve ONE task two ways and time both with time.time():
#   as_tool_call(text)     -> plain Python word count (0 tokens, <1ms)
#   as_subagent_call(text) -> ask Claude to count the words (tokens + ~1-2s)
# Use the EXACT input: "the quick brown fox jumps over the lazy dog". The numbers
# make the tradeoff obvious: only pay for a subagent when you need real reasoning.

# Time: 0.0000 seconds (tool)
# Tool call result: 9
# Time: 0.7233 seconds (subagent)
# Subagent call result: 9

# def as_tool_call(text):
#     """Count the words in text using a Python tool."""
#     start = time.time()
#     word_count = len(text.split())
#     print(f"Time: {time.time() - start:.4f} seconds (tool)")
#     return word_count

# def as_subagent_call(text):
#     """Count the words in text by asking Claude."""
#     start = time.time()
#     response = client.messages.create(
#         model=MODEL,
#         max_tokens=10,
#         system="You are a helpful assistant that counts words. Respond with only the number.",
#         messages=[
#             {"role": "user", "content": f"How many words are in this text? '{text}'"},
#         ],
#     )
#     word_count = int(response.content[0].text.strip())
#     print(f"Time: {time.time() - start:.4f} seconds (subagent)")
#     return word_count

# text = "the quick brown fox jumps over the lazy dog"
# print(f"Tool call result: {as_tool_call(text)}")
# print(f"Subagent call result: {as_subagent_call(text)}")


# ─── SECTION C1: The decision framework ──────────────────────────────────────
# CONCEPT — four levels of capability:
#   Tool (Python fn):     deterministic, no reasoning, <1ms, 0 tokens.
#                         e.g. file I/O, math, date parsing, fixed-schema API calls.
#   Skill module (class): reusable bundle of related tools + schemas + error
#                         handling; 0 LLM cost. e.g. SearchSkill, MemorySkill.
#   Subagent (Claude):    needs language understanding; own context; tokens + latency.
#                         e.g. code reviewer, summarizer.
#   Independent agent:    long-running autonomous loop managing its own context.
#                         e.g. the Session 3 research agent, the capstone.
#
# TODO: classify each capability below as tool / skill / subagent / agent, with one
#   sentence of why:
#     - Parse a date string into a datetime object
#           tool, deterministic
#     - Decide whether a question is about billing or technical support
#           subagent, language understanding
#     - Fetch a URL and return the HTML
#           tool, deterministic
#     - Write a three-paragraph summary of 5 search results
#           subagent, language understanding
#     - Validate that a JSON object matches a schema
#           tool, deterministic
#     - Generate a code review for a Python function
#           subagent, language understanding
#     - Retry an API call with exponential backoff
#           tool, deterministic
#     - Translate a user message to Spanish
#           subagent, language understanding
#
# CHALLENGE (write the answers in comments):
#   Which two from that list are genuinely AMBIGUOUS (both tool and subagent could
#   work)? Write the exact condition that tips you one way — that condition is your
#   personal decision rule.
# "Decide whether a question is about billing or technical support" and "Translate a user message to Spanish" are both ambiguous: 
# each could use a rule-based tool (fast, cheap) or an LLM-powered subagent (robust, higher quality). 
# The decision rule: use a tool when you need speed and can tolerate errors; 
# use a subagent when you need reasoning or quality and can afford the latency/tokens.


# ─── SECTION C2: Skill modules & specialization ──────────────────────────────
# CONCEPT
#   A skill is a class bundling related tools, schemas, and error handling behind
#   one interface. Specialized subagents that hold ONLY the skills they need keep
#   their context small and their behavior predictable.
#
# TODO (a) — build three skills:
#   SearchSkill: tool_definition property + run(query) (Brave search, fake-result
#                fallback when BRAVE_SEARCH_API_KEY is unset)
#   FileSkill:   tool_definitions property + read(path) (handle FileNotFoundError)
#                + write(path, content) + run(name, args) dispatcher
#   MemorySkill: wraps a list of facts — tool_definition for "remember_fact",
#                remember(fact) -> confirmation, recall_all() -> facts or "(empty)"
#   Smoke-test each one.

class SearchSkill:
    def __init__(self):
        self.tool_definitions = [
            {
                "name": "search",
                "description": "Search the web for information",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query"}
                    }
                }
            }
        ]

    def run(self, name, args):
        if name == "search":
            return f"Search results for '{args["query"]}': FastAPI uses async/await, has automatic OpenAPI docs, and is built on Starlette + Pydantic."
        else:
            return f"Unknown tool: {name}"
    
class FileSkill:
    def __init__(self):
        self.tool_definitions = [
            {
                "name": "read_file",
                "description": "Read the contents of a file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "The path to the file"}
                    },
                }
            },
            {
                "name": "write_file",
                "description": "Write content to a file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "The path to the file"},
                        "content": {"type": "string", "description": "The content to write"}
                    }
                }
            }
        ]

    def read(self, path):
        try:
            with open(path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return f"File not found: {path}"

    def write(self, path, content):
        with open(path, 'w') as f:
            f.write(content)
        return f"Content written to {path}"

    def run(self, name, args):
        if name == "read_file":
            return self.read(args["path"])
        elif name == "write_file":
            return self.write(args["path"], args["content"])
        else:
            return f"Unknown tool: {name}"
        
class MemorySkill:
    def __init__(self):
        self.tool_definitions = [
            {
                "name": "remember_fact",
                "description": "Remember a fact",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "fact": {"type": "string", "description": "The fact to remember"}
                    }
                }
            },
            {
                "name": "recall_all",
                "description": "Recall all remembered facts",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
        self.facts = []

    def remember(self, fact):
        self.facts.append(fact)
        return f"Fact remembered: {fact}"

    def recall_all(self):
        return self.facts if self.facts else "(empty)"
    
    def run(self, name, args):
        if name == "remember_fact":
            return self.remember(args["fact"])
        elif name == "recall_all":
            return self.recall_all()
        else:
            return f"Unknown tool: {name}"

# search = SearchSkill() 
# file = FileSkill()
# memory = MemorySkill()
# print(f"Search: {search.run("What is FastAPI?")}")
# file.write("skill.md", "This is a file write")
# print(f"File: {file.read("skill.md")}")
# print(f"Memory (empty): {memory.recall_all()}")
# memory.remember("This is a memory")
# print(f"Memory: {memory.recall_all()}")

# TODO (b) — specialize: build ResearcherAgent (SearchSkill + MemorySkill) and
#   WriterAgent (FileSkill only), each with its own loop and system prompt. Run a
#   two-phase pipeline with these EXACT calls:
#     facts = researcher.run("Find 3 key facts about FastAPI")
#     writer.run("Write a short intro to fastapi.md", context=facts)
#   Log len(messages) for each loop.

# Running ResearcherAgent
# len(messages): 8
# Running Writer
# len(messages): 5

class Agent:
    def __init__(self, skills):
        self.skills = skills
        self.client = client

    def process_tool_block(self, block, messages):
        for skill in self.skills:
            tool_definitions = [d for skill in self.skills for d in skill.tool_definitions]
            tool_names = [d["name"] for d in tool_definitions]
            if block.name in tool_names:
                tool_use_result = skill.run(block.name, block.input)
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": tool_use_result,
                        }
                    ],
                })
                return

    def run(self, task, context=None, max_steps=10):
        print(f"Running {self.name}")
        messages = []
        answer = ""
        if context is not None:
            messages.append({"role": "user", "content": f"Context: {context}"})
        messages.append({"role": "user", "content": task})
        step = 0
        tool_definitions = [d for skill in self.skills for d in skill.tool_definitions]
        while step < max_steps:
            print(f"--- Step {step}")
            r = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                tools=tool_definitions,
                messages=messages
            )
            messages.append({"role": "assistant", "content": r.content})

            if r.stop_reason != "tool_use":
                print(f"Stopped: {r.stop_reason}")
                answer = r.content[0].text
                break

            for block in r.content:
                if block.type == "tool_use":
                    print(f"Tool use: {block.name} ({block.input})")
                    self.process_tool_block(block, messages)

            step += 1
        print(f"len(messages): {len(messages)}")
        return answer
    
class ResearcherAgent(Agent):
    def __init__(self):
        self.name = "ResearcherAgent"
        super().__init__([SearchSkill(), MemorySkill()])

class WriterAgent(Agent):
    def __init__(self):
        self.name = "Writer"
        super().__init__([FileSkill()])

researcher = ResearcherAgent()
writer = WriterAgent()
facts = researcher.run("Find 3 key facts about FastAPI")
writer.run("Write a short intro to fastapi.md", context=facts)

# CHALLENGE (write the answers in comments):
#   How many messages does the researcher accumulate vs the writer? Estimate how
#   much LARGER one combined agent's context would be doing both phases. Did
#   splitting them help or hurt the final fastapi.md?
#   Then: swap SearchSkill's run(query) to return a different hardcoded fake result
#   WITHOUT changing any line in ResearcherAgent. Does it still work? That swap
#   test is the whole point of the skill interface.
#
# Researcher: 8 messages (task + search round-trip + 3 remember_fact round-trips + final reply)
# Writer:     5 messages (context + task as 2 user msgs + write_file round-trip + final reply)
# Combined estimate: ~11 messages, but the writer would also see all raw search/memory tool
#   calls in its context — noisier and less focused than receiving a clean summary.
#   Splitting reduces each agent's context and keeps the writer's input clean.
# fastapi.md: splitting helped — the writer received concise facts and produced good output.
#   A combined agent would carry all researcher tool noise into the write step.
#
# Swap test: changed SearchSkill.run to return richer hardcoded text above.
#   ResearcherAgent is untouched and still works — it calls skill.run() without
#   knowing or caring what's inside. That's the skill interface: swap the impl, not the caller.