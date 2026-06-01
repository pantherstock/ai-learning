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

import os
import json

BRAVE_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")

# TODO: create the server. Wrap the import so a missing dep prints a friendly hint:
#   try:
#       from fastmcp import FastMCP
#   except ImportError:
#       print("Install fastmcp first: pip install fastmcp"); exit(1)
#   mcp = FastMCP("AI Learning Agent Tools")


# ─── WARM-UP: Hello-world MCP server ─────────────────────────────────────────
# Run this file and connect to it from Claude Code (run /mcp and add a local
# server pointing here), or test it programmatically with mcp.Client.
#
# TODO: define a hello(name) -> str tool with the @mcp.tool() decorator that
# returns a greeting confirming the server is running.


# ─── SECTION D1: Expose tools via MCP ────────────────────────────────────────
# Same tools as your agent loops, now exposed as MCP. Any Claude client can
# discover and call these automatically.
#
# TODO: expose search_web(query), write_file(path, content), and read_file(path)
# as @mcp.tool() functions (reuse the logic from earlier sessions; search_web can
# fall back to fake results when BRAVE_KEY is unset).
# TODO: add a word_count tool that takes text and returns the word count.


# ─── SECTION D2: Resources — expose data for the model to read ───────────────
# Resources are like read-only endpoints. The model can request them by URI.
# Use them for context that changes over time (current state, docs, DB records).
#
# TODO: define the Acme knowledge base as a dict and expose it as resources:
#   @mcp.resource("knowledge://acme/{chunk_id}")  -> one chunk by id
#   @mcp.resource("knowledge://acme/all")         -> the whole KB joined
# TODO: add a resource "logs://agent/latest" that returns agent.log if it exists,
# else "No logs found."


# ─── SECTION D3: Prompts — reusable templates ─────────────────────────────────
# Prompts are predefined instructions with parameters. Claude clients can list
# them and invoke them by name.
#
# TODO: define reusable @mcp.prompt() templates:
#   research_report(topic, word_count=300) — research + write-to-file instruction
#   code_review(language="Python")          — a code-review system prompt
#   compare_options(a, b)                   — a structured comparison prompt


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
# The tradeoff: MCP adds a network hop (stdio or HTTP). For local tools, this is
# negligible. For high-frequency calls in tight loops, measure first.
#
# OBSERVATION: take one of your agent loops from sessions 2–4 and imagine
# replacing its tool execution with MCP calls. What changes in the code?
# What stays the same? Write your answer here:


# ─── MINI PROJECT: RAG knowledge base as MCP server ─────────────────────────
# Expose the Session 5 knowledge base as a real MCP server with:
#   - A retrieve_context tool that does cosine-similarity search
#   - A resource for each KB chunk (URI: knowledge://acme/{id})
#   - A research_report prompt
# Then connect it to your Session 3 research agent so the agent calls
# retrieve_context via the MCP tool rather than a directly-wired Python function.
# Push to GitHub when done.
#
# TODO: add a retrieve_context(query) @mcp.tool() that imports cosine_similarity
# from session5.py (or re-implements it) and returns the top 2 matching chunks.
# TODO: add a __main__ block — run mcp.run() as a server, or a --test branch that
# calls the tools directly (hello, write_file, read_file, get_all_kb).
