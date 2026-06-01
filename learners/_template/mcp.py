"""
Section D — Plugins & MCP (Model Context Protocol)
MCP is the standard protocol for connecting tools and data sources to Claude.
Build a server that exposes your tools as MCP capabilities.

Prerequisites: pip install fastmcp   (install separately from the main deps)
Run the server: python mcp.py
"""

import env  # auto-loads .env — no manual `export` needed

# ─── What is MCP? ─────────────────────────────────────────────────────────────
#
# MCP (Model Context Protocol) is an open standard for connecting AI models
# to tools and data. Instead of wiring tools directly into your agent code,
# you build an MCP server that exposes them — then any MCP-aware client
# (Claude Code, Claude Desktop, your own agent) can use them.
#
# Architecture:
#   MCP Client (Claude Code, your agent)
#       ↕  JSON-RPC over stdio or HTTP
#   MCP Server (your Python code)
#       ↕
#   Your tools / databases / APIs
#
# Three things an MCP server can expose:
#   - Tools:     functions the model can call (like tool_use in the API)
#   - Resources: data the model can read (files, DB rows, API responses)
#   - Prompts:   reusable prompt templates with arguments
#
# FastMCP is a Python library that handles the protocol for you.
# You just write decorated functions.


# ─── WARM-UP: Hello-world MCP server ─────────────────────────────────────────
# Run this file and connect to it from Claude Code.
# To connect: in Claude Code, run /mcp and add a local server pointing here.
# Or test it programmatically with mcp.Client.

try:
    from fastmcp import FastMCP
except ImportError:
    print("Install fastmcp first: pip install fastmcp")
    print("Then re-run this file.")
    exit(1)

mcp = FastMCP("AI Learning Agent Tools")

@mcp.tool()
def hello(name: str) -> str:
    """Say hello — confirms the MCP server is working."""
    return f"Hello, {name}! MCP server is running."

# To test immediately:
#   python mcp.py --test
# Or to run as a persistent server:
#   python mcp.py


# ─── SECTION D1: Expose tools via MCP ────────────────────────────────────────
# Same tools as your agent loops, now exposed as MCP.
# Any Claude client can discover and call these automatically.

import os
import json

BRAVE_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")

@mcp.tool()
def search_web(query: str) -> str:
    """Search the web for real-time information."""
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

@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    with open(path, "w") as f:
        f.write(content)
    return f"Written {len(content)} chars to {path}"

@mcp.tool()
def read_file(path: str) -> str:
    """Read a file's contents."""
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: '{path}' not found"

# TODO: add a word_count tool that takes text and returns the word count
# Use the @mcp.tool() decorator


# ─── SECTION D2: Resources — expose data for the model to read ───────────────
# Resources are like read-only endpoints. The model can request them by URI.
# Use them for context that changes over time (current state, docs, DB records).

# Knowledge base from Session 5 (static chunks)
KB_CHUNKS = {
    "founding":     "Acme Corp was founded in 2018 by Maria Chen and James Wu in Seattle.",
    "product":      "The flagship product, ScheduleAI, is used by 500+ enterprise customers.",
    "funding":      "Acme raised $12M Series A in 2021 and $40M Series B in 2023.",
    "engineering":  "The engineering team is 45 people, primarily Python and Go.",
    "ceo":          "CEO Maria Chen was previously a research scientist at Google Brain.",
    "cto":          "CTO James Wu led infrastructure at Stripe before co-founding Acme.",
}

@mcp.resource("knowledge://acme/{chunk_id}")
def get_kb_chunk(chunk_id: str) -> str:
    """Retrieve a specific knowledge base entry about Acme Corp."""
    return KB_CHUNKS.get(chunk_id, f"No chunk found for '{chunk_id}'")

@mcp.resource("knowledge://acme/all")
def get_all_kb() -> str:
    """Retrieve the full Acme Corp knowledge base."""
    return "\n".join(f"[{k}] {v}" for k, v in KB_CHUNKS.items())

# TODO: add a resource that returns the contents of agent.log if it exists
# URI: "logs://agent/latest"
# If no log file exists, return "No logs found."


# ─── SECTION D3: Prompts — reusable templates ─────────────────────────────────
# Prompts are predefined instructions with parameters.
# Claude clients can list them and invoke them by name.

@mcp.prompt()
def research_report(topic: str, word_count: int = 300) -> str:
    """Generate a research report prompt for a given topic."""
    return (
        f"Research '{topic}' thoroughly and write a {word_count}-word summary. "
        f"Include: key concepts, real-world applications, and current limitations. "
        f"Write to {topic.lower().replace(' ', '_')}_report.md when done."
    )

@mcp.prompt()
def code_review(language: str = "Python") -> str:
    """Generate a code review system prompt."""
    return (
        f"You are an expert {language} code reviewer. "
        f"For any code provided, check: correctness, edge cases, idiomatic style, "
        f"performance, and security. Give specific, actionable feedback."
    )

# TODO: add a prompt called "compare_options" that takes two options (a: str, b: str)
# and generates a structured comparison prompt


# ─── OBSERVE: What changed? ───────────────────────────────────────────────────
# Before MCP: your tools were wired directly into your agent loop.
#   - Adding a new tool meant editing agent code.
#   - Tools couldn't be shared across different agents or clients.
#   - Tool logic was tangled with loop logic.
#
# After MCP: your tools live in a server.
#   - Any MCP client can discover and use them.
#   - Claude Code, Claude Desktop, and your agents all share the same toolset.
#   - You can update tools without touching agent code.
#
# The tradeoff: MCP adds a network hop (stdio or HTTP). For local tools,
# this is negligible. For high-frequency calls in tight loops, measure first.
#
# OBSERVATION: take one of your agent loops from sessions 2–4 and imagine
# replacing its tool execution with MCP calls. What changes in the code?
# What stays the same? Write your answer here:


# ─── MINI PROJECT: RAG knowledge base as MCP server ─────────────────────────
# Expose the Session 5 knowledge base as a real MCP server with:
#   - A retrieve_context tool that does cosine similarity search
#   - A resource for each KB chunk (URI: knowledge://acme/{id})
#   - A research_report prompt
#
# Then connect it to your Session 3 research agent.
# The agent should be able to call retrieve_context via the MCP tool
# rather than the directly-wired Python function.
#
# Push to GitHub when done.

# TODO: add a retrieve_context tool below that imports cosine_similarity
# from session5.py (or re-implements it here) and searches KB_CHUNKS

try:
    from sentence_transformers import SentenceTransformer
    _model = SentenceTransformer('all-MiniLM-L6-v2')
    _kb_texts = list(KB_CHUNKS.values())
    _kb_embeddings = _model.encode(_kb_texts)

    @mcp.tool()
    def retrieve_context(query: str) -> str:
        """Search the Acme Corp knowledge base using semantic similarity."""
        # TODO: implement cosine_similarity and return top 2 matching chunks
        return "[retrieve_context not implemented — fill in the TODO]"

except ImportError:
    pass  # sentence-transformers not installed, skip this tool


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        print("Testing MCP server tools directly:")
        print(hello("learner"))
        print(write_file("mcp_test.txt", "hello from mcp"))
        print(read_file("mcp_test.txt"))
        print(get_all_kb())
    else:
        print("Starting MCP server (stdio transport)...")
        print("Connect with Claude Code: add this file as a local MCP server")
        mcp.run()
