"""
Section D — Plugins & MCP (Model Context Protocol)
MCP is the standard protocol for connecting tools and data sources to Claude.
Build a server that exposes your tools as MCP capabilities.

Each section is CONCEPT -> TODO -> CHALLENGE (see session1.py).
Prerequisites: pip install fastmcp   (install separately from the main deps)
Run the server: python mcp_server.py   |   Test the tools: python mcp_server.py --test
"""

import requests
from sentence_transformers import SentenceTransformer

import env  # auto-loads .env — no manual `export` needed

# ─── What is MCP? ────────────────────────────────────────────────────────────
# An open standard for connecting AI models to tools and data. Instead of wiring
# tools into your agent code, you run an MCP server that exposes them — and any
# MCP-aware client (Claude Code, Claude Desktop, your own agent) can use them.
#
#   MCP Client  <->  JSON-RPC (stdio/HTTP)  <->  MCP Server (your code)  <->  tools/data
#
# A server can expose three things:
#   Tools:     functions the model can CALL (like tool_use in the API)
#   Resources: data the model can READ by URI (files, DB rows, API responses)
#   Prompts:   reusable prompt templates with arguments
# FastMCP handles the protocol; you just write decorated functions.

import os
import json

BRAVE_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")

# TODO: create the server, wrapping the import with a friendly hint:
try:
    from fastmcp import FastMCP
except ImportError:
    print("Install fastmcp first: pip install fastmcp"); exit(1)
mcp = FastMCP("AI Learning Agent Tools")


# ─── WARM-UP: Hello-world MCP server ─────────────────────────────────────────
# TODO: define a hello(name: str) -> str tool with @mcp.tool() that returns a
# greeting confirming the server is up. Run `python mcp_server.py --test` (or connect from
# Claude Code via /mcp) and call it. Note: the tool looks just like a Session 2 tool
# schema — MCP only standardizes how it's discovered and called.
# To register in claude code: claude mcp add ai-learning-tools -- python C:\Users\simyi\projects\ai-learning\learners\yilin\mcp_server.py
@mcp.tool
def hello(name: str) -> str:
    """A simple greeting tool"""
    return f"Hello, {name}! The MCP server is up and running."

# ─── SECTION D1: Expose tools via MCP ────────────────────────────────────────
# CONCEPT
#   MCP tools are decorated Python functions. @mcp.tool() publishes them over
#   JSON-RPC; clients discover them automatically via a tools/list call. No schema
#   hand-writing — FastMCP derives it from your type hints + docstring.
#
# TODO: expose search_web(query), write_file(path, content), and read_file(path) as
#   @mcp.tool() functions (reuse earlier logic; search_web falls back to fake
#   results when BRAVE_KEY is unset). Add word_count(text: str) -> str.
#   Run `python mcp_server.py --test` to confirm they work, then call word_count from
#   Claude Code on the EXACT input "the quick brown fox jumps over the lazy dog".
#
# CHALLENGE (write the answers in comments):
#   In Claude Code's tool list, how do your tool's name, description, and schema
#   appear compared to what you wrote in Python? Did anything get lost or renamed in
#   translation, or is it exactly your docstring + type hints?
# ANSWER: exactly the docstring + type hints

@mcp.tool
def search_web(query: str) -> str:
    """Search the web for the given query."""
    if not BRAVE_KEY:
        return f"Fake search results for: {query}"
    r = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={"X-Subscription-Token": BRAVE_KEY},
        params={"q": query, "count": 3},
    )
    results = r.json().get("web", {}).get("results", [])
    return "\n".join(f"- {x['title']}: {x['description']}" for x in results)

@mcp.tool
def word_count(text: str) -> str:
    """Count the number of words in the given text."""
    return str(len(text.split()))

@mcp.tool
def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    with open(path, "w") as f:
        f.write(content)
    return f"File written: {path}"

@mcp.tool
def read_file(path: str) -> str:
    """Read content from a file."""
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {path}"

# ─── SECTION D2: Resources & prompts ─────────────────────────────────────────
# CONCEPT
#   Resources are read-only DATA the model fetches by URI (vs tools, which are
#   ACTIONS). Prompts are reusable parameterized TEMPLATES any client can invoke.
#   Both pull shared context out of inline strings and into the server, so improving
#   one place updates every agent that uses it.
#
# TODO (a) — resources:
#   Define the Acme KB as a dict and expose:
#       @mcp.resource("knowledge://acme/{chunk_id}")  -> one chunk by id
#       @mcp.resource("knowledge://acme/all")         -> the whole KB joined
#   Add @mcp.resource("logs://agent/latest") returning agent.log (Session 3) if it
#   exists, else "No logs found."
# TODO (b) — prompts:
#   Add @mcp.prompt() templates:
#       compare_options(a: str, b: str)        -> a structured comparison prompt
#       research_report(topic, word_count=300) -> research + write-to-file instruction
#   Test compare_options through Claude Code's MCP interface.
#
# /mcp__ai-learning-tools__compare_options apples oranges
#
# CHALLENGE (write the answers in comments):
#   1. Name one thing from Sessions 1-6 that would have been better modeled as a
#      RESOURCE (data) than a tool (action), and why.
#   2. If THREE agents all need a structured comparison, how many files change to
#      improve the prompt when it's an MCP prompt vs an inline string in each agent?
# ANSWERS:
# 1. The Acme KB in session5 — it's static read-only data (facts to fetch, not actions to call).
#    A resource URI (knowledge://acme/{id}) is cleaner than wrapping it in a retrieve_context tool.
# 2. MCP prompt: 1 file (the server). Inline strings: 3 files — one per agent, all need editing.

Acme_KB = {
    "1": "Acme Corp was founded in 2019 in Austin by two former robotics engineers.",
    "2": "Acme raised a $12M Series A led by Foundry Ventures in 2022.",
    "3": "Maria Chen is Acme's CEO; she previously led hardware at a self-driving startup.",
    "4": "James Wu is Acme's CTO and architected the company's core inference engine.",
    "5": "Acme's flagship product is an on-device speech recognition SDK.",
}

@mcp.resource("knowledge://acme/{chunk_id}")
async def get_chunk(chunk_id: str) -> str:
    """Get details for a specific chunk."""
    return Acme_KB.get(chunk_id, "Chunk not found")

@mcp.resource("knowledge://acme/all")
async def get_all_chunks():
    """Get all chunks."""
    return "\n".join(Acme_KB.values())

@mcp.resource("logs://agent/latest")
def get_latest_logs():
    try:
        with open("agent.log", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "No logs found."
    
@mcp.prompt()
def compare_options(a: str, b: str) -> str:
    """Compare two options."""
    return (
        f"Compare the following two options in a structured table covering key differences:\n"
        f"Option A: {a}\n"
        f"Option B: {b}\n"
        f"Provide a recommendation at the end."
    )

@mcp.prompt()
def research_report(topic: str, word_count: int = 300) -> str:
    """Generate a research report on a topic."""
    return f"Research report on {topic} with {word_count} words."

# ─── DELIVERABLE ─────────────────────────────────────────────────────────────
# Add a __main__ block with two branches:
#   python mcp_server.py        -> mcp.run()   (starts the server for Claude Code)
#   python mcp_server.py --test -> call each tool directly and print results
#
# Then add retrieve_context(query) @mcp.tool() that does cosine-similarity search
# over the KB (reuse cosine_similarity from session5.py).
#
# Done when: `python mcp_server.py --test` exercises all tools including retrieve_context,
# AND you can call retrieve_context from Claude Code via /mcp on a real query.
# /mcp__ai-learning-tools__retrieve_context "Acme Corp was founded in 2019."
#
# TODO: implement retrieve_context and the __main__/--test block.

def cosines_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x * x for x in a) ** 0.5
    mag_b = sum(x * x for x in b) ** 0.5
    return dot / (mag_a * mag_b)

_embed = None

def _get_embed():
    global _embed
    if _embed is None:
        print("Loading embedding model...")
        _embed = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed

def find_nearest(query, chunks):
    embeddings = _get_embed().encode(chunks)
    query_embedding = _get_embed().encode([query])[0]
    best_score = -1
    best_chunk = None
    for chunk, embedding in zip(chunks, embeddings):
        score = cosines_similarity(query_embedding, embedding)
        if score > best_score:
            best_score = score
            best_chunk = chunk
    return best_chunk, best_score

@mcp.tool()
def retrieve_context(query: str) -> str:
    """Retrieve nearest context for a query."""
    chunk, score = find_nearest(query, list(Acme_KB.values()))
    return f"Context: {chunk} (score: {score:.2f})"

import sys

if __name__ == "__main__":
    if "--test" in sys.argv:
        # print(hello("World"))
        # print(search_web("Python"))
        # print(word_count("the quick brown fox jumps over the lazy dog"))
        # print(write_file("test.txt", "Hello, World!"))
        # print(read_file("test.txt"))
        print("Starting test")
        print(retrieve_context("Acme Corp was founded in 2019."))
    else:
        mcp.run()
