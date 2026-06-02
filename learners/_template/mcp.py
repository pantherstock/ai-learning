"""
Section D — Plugins & MCP (Model Context Protocol)
MCP is the standard protocol for connecting tools and data sources to Claude.
Build a server that exposes your tools as MCP capabilities.

Each section is CONCEPT -> TODO -> CHALLENGE (see session1.py).
Prerequisites: pip install fastmcp   (install separately from the main deps)
Run the server: python mcp.py   |   Test the tools: python mcp.py --test
"""

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
#   try:
#       from fastmcp import FastMCP
#   except ImportError:
#       print("Install fastmcp first: pip install fastmcp"); exit(1)
#   mcp = FastMCP("AI Learning Agent Tools")


# ─── WARM-UP: Hello-world MCP server ─────────────────────────────────────────
# TODO: define a hello(name: str) -> str tool with @mcp.tool() that returns a
# greeting confirming the server is up. Run `python mcp.py --test` (or connect from
# Claude Code via /mcp) and call it. Note: the tool looks just like a Session 2 tool
# schema — MCP only standardizes how it's discovered and called.


# ─── SECTION D1: Expose tools via MCP ────────────────────────────────────────
# CONCEPT
#   MCP tools are decorated Python functions. @mcp.tool() publishes them over
#   JSON-RPC; clients discover them automatically via a tools/list call. No schema
#   hand-writing — FastMCP derives it from your type hints + docstring.
#
# TODO: expose search_web(query), write_file(path, content), and read_file(path) as
#   @mcp.tool() functions (reuse earlier logic; search_web falls back to fake
#   results when BRAVE_KEY is unset). Add word_count(text: str) -> str.
#   Run `python mcp.py --test` to confirm they work, then call word_count from
#   Claude Code on the EXACT input "the quick brown fox jumps over the lazy dog".
#
# CHALLENGE (write the answers in comments):
#   In Claude Code's tool list, how do your tool's name, description, and schema
#   appear compared to what you wrote in Python? Did anything get lost or renamed in
#   translation, or is it exactly your docstring + type hints?


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
# CHALLENGE (write the answers in comments):
#   1. Name one thing from Sessions 1-6 that would have been better modeled as a
#      RESOURCE (data) than a tool (action), and why.
#   2. If THREE agents all need a structured comparison, how many files change to
#      improve the prompt when it's an MCP prompt vs an inline string in each agent?


# ─── MINI PROJECT: RAG knowledge base as MCP server ──────────────────────────
# Push to GitHub when the checklist passes.
#
#   ☐ retrieve_context(query) @mcp.tool() does cosine-similarity search over the KB
#     (reuse cosine_similarity from session5.py).
#   ☐ Each KB chunk exposed as a resource: knowledge://acme/{id}.
#   ☐ A __main__ block: mcp.run() as a server, plus a `--test` branch that calls the
#     tools directly (hello, write_file, read_file, retrieve_context).
#   ☐ Wire this server into your Session 3 research agent so it calls retrieve_context
#     via MCP instead of a directly-wired Python function.
#
# Done when: retrieve_context returns the right chunks via MCP, AND the Session 3
#   agent works through the server. Note whether the agent's behavior changed and
#   whether the code got cleaner or messier.
#
# TODO: implement retrieve_context, the resources, and the __main__/--test block.
