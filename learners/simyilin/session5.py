"""
Session 5 — Memory & Retrieval
Give your agent knowledge that doesn't fit in the context window.

Requires: pip install sentence-transformers
Run with: python session5.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import os

client = anthropic.Anthropic()


# ─── WARM-UP: Feel semantic similarity ───────────────────────────────────────
# Embeddings turn text into vectors whose directions encode meaning.
#
# TODO: pip install sentence-transformers, then:
#   from sentence_transformers import SentenceTransformer
#   model = SentenceTransformer('all-MiniLM-L6-v2')   # downloads ~80MB once
# Encode "The cat sat on the mat", "A feline rested on a rug", and
# "The stock market crashed yesterday". Print the dot product of the first with
# each of the others. The similar pair should score much higher.


# ─── CHUNK 5A: Cosine similarity from scratch ────────────────────────────────
# The dot product alone isn't reliable — longer vectors produce bigger values
# regardless of direction. Cosine similarity normalizes for magnitude.
#
# TODO: implement cosine_similarity(a, b) yourself, no library:
#   dot = sum(x*y for x, y in zip(a, b))
#   mag_a = sum(x**2 for x in a) ** 0.5 ; mag_b = sum(x**2 for x in b) ** 0.5
#   return dot / (mag_a * mag_b)
# TODO: build a small KB (a list of sentences) and find_nearest(query, chunks,
# embeddings) -> (chunk_text, score). Test it with a literal query and a
# rephrased one — does the same chunk win when the words change?


# ─── CHUNK 5B: RAG as a tool ─────────────────────────────────────────────────
# Wire your retrieval function into your agent as a callable tool.
#
# TODO: implement retrieve_context(query) -> str that encodes the query, scores
# it against your KB embeddings, and returns the top 2 chunks joined by newline.
# Define the matching retrieve_context tool schema.


# ─── CHUNK 5C: Push the edges ────────────────────────────────────────────────
# Test retrieval behavior on tricky inputs.
#
# TODO: run find_nearest on queries that are (a) rephrased, (b) not in the KB,
# and (c) ambiguous, e.g.:
#   "How much money has Acme taken from investors?"   # rephrased
#   "What is Acme's annual revenue?"                  # not in KB
#   "Tell me about Acme's leadership."                # ambiguous
# For the ambiguous one, which chunk wins? Print scores and matches.
# OBSERVATION:


# ─── MINI PROJECT: RAG wired into the research agent ─────────────────────────
# Add retrieve_context as a tool to the research agent from Session 3, so it has
# two knowledge sources: web search (live) and the KB (static). Push to GitHub.
#
# TODO: define search + retrieve_context tools and execute_tool(name, args), then
# build the agent with both. Run task 1 (answerable from the KB) and task 2
# (where KB and web might conflict). Observe which source the agent prefers.
