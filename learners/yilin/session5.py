"""
Session 5 — Memory & Retrieval
Give your agent knowledge that doesn't fit in the context window.

Each chunk is CONCEPT -> TODO -> CHALLENGE (see session1.py).
Requires: pip install sentence-transformers
Run with: python session5.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import os

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"


# A small, fixed knowledge base so every query below is reproducible. Use these
# EXACT five chunks for the tasks and challenges in this session:
#   KB = [
#     "Acme Corp was founded in 2019 in Austin by two former robotics engineers.",
#     "Acme raised a $12M Series A led by Foundry Ventures in 2022.",
#     "Maria Chen is Acme's CEO; she previously led hardware at a self-driving startup.",
#     "James Wu is Acme's CTO and architected the company's core inference engine.",
#     "Acme's flagship product is an on-device speech recognition SDK.",
#   ]


# ─── WARM-UP: Feel semantic similarity ───────────────────────────────────────
# Embeddings turn text into vectors whose DIRECTION encodes meaning.
#
# TODO: pip install sentence-transformers, then:
#   from sentence_transformers import SentenceTransformer
#   embed = SentenceTransformer('all-MiniLM-L6-v2')   # downloads ~80MB once
# Encode these EXACT three sentences:
#   "The cat sat on the mat" / "A feline rested on a rug" /
#   "The stock market crashed yesterday"
# Print the dot product of the first with each of the other two. The paraphrase
# pair should score far higher than the unrelated pair.


# ─── CHUNK 5A: Cosine similarity & semantic search ───────────────────────────
# CONCEPT
#   A raw dot product favors longer vectors regardless of meaning. Cosine
#   similarity divides out magnitude, so it measures direction only — that's the
#   number that actually tracks "same meaning". Semantic search = embed everything,
#   then return the chunk whose embedding is most cosine-similar to the query.
#
# TODO (a): implement cosine_similarity(a, b) yourself, no library:
#       dot   = sum(x*y for x, y in zip(a, b))
#       mag_a = sum(x*x for x in a) ** 0.5
#       mag_b = sum(x*x for x in b) ** 0.5
#       return dot / (mag_a * mag_b)
# TODO (b): embed the 5 KB chunks once. Implement find_nearest(query, chunks,
#   embeddings) -> (chunk_text, score) using cosine_similarity.
#
# CHALLENGE (write the answers in comments):
#   Search the founding chunk two ways: literally ("Acme was founded in 2019") and
#   rephrased ("When did Acme get started?"). Does the SAME chunk win both times,
#   even though the rephrase shares almost no words? That is semantic search.


# ─── CHUNK 5B: RAG as a tool — and its edges ─────────────────────────────────
# CONCEPT
#   Wire retrieval in as a TOOL the agent chooses to call (retrieve_context). The
#   agent decides when it needs the KB. Where it gets interesting is the edges:
#   paraphrases, questions with no answer in the KB, and ambiguous questions that
#   two chunks match. Whether it answers, declines, or fabricates depends on those.
#
# TODO: implement retrieve_context(query) -> str that embeds the query, scores it
#   against the KB embeddings, and returns the top 2 chunks joined by newlines.
#   Define the matching retrieve_context tool schema.
#
# CHALLENGE (write the answers in comments) — run find_nearest on these EXACT
# queries and log the winning chunk + score for each:
#   (a) rephrased:  "How much money has Acme taken from investors?"
#   (b) not in KB:  "What is Acme's annual revenue?"
#   (c) ambiguous:  "Tell me about Acme's leadership."
#   For (b), is the top score noticeably lower than for (a)? Could you use a score
#   THRESHOLD to make the agent say "I don't know" instead of returning junk?
#   For (c), does the Maria Chen or the James Wu chunk win — and why might the
#   embeddings prefer one for the word "leadership"?


# ─── MINI PROJECT: RAG wired into the research agent ─────────────────────────
# Give the Session 3 agent two knowledge sources. Push to GitHub when it passes.
#
#   ☐ Tools: search (live web, Session 3) AND retrieve_context (static KB).
#   ☐ execute_tool dispatches to both; the agent picks which to call.
#   ☐ Run TASK 1 (answerable from the KB):
#         "Who founded Acme and when?"
#     and confirm it uses retrieve_context, not web search.
#   ☐ Run TASK 2 (KB and web could disagree):
#         "What is Acme Corp's latest product, and what do recent news articles
#          say about it?"
#     and note which source the agent trusts when both are available.
#
# Done when: Task 1 is answered from the KB and Task 2 visibly consults both tools;
#   write one sentence on which source won and whether the tool descriptions nudged it.
#
# TODO: assemble the two-source agent and run both tasks.
