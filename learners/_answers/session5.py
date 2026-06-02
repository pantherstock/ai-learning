"""
Session 5 — Memory & Retrieval · REFERENCE ANSWERS

One worked solution per chunk. Read AFTER you've tried session5.py yourself.
Requires: pip install sentence-transformers  (downloads ~80MB on first run).

Run with: python session5.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
from sentence_transformers import SentenceTransformer

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"
embed_model = SentenceTransformer("all-MiniLM-L6-v2")  # downloads once, then cached

# The fixed KB — use these EXACT five chunks so every query is reproducible.
KB = [
    "Acme Corp was founded in 2019 in Austin by two former robotics engineers.",
    "Acme raised a $12M Series A led by Foundry Ventures in 2022.",
    "Maria Chen is Acme's CEO; she previously led hardware at a self-driving startup.",
    "James Wu is Acme's CTO and architected the company's core inference engine.",
    "Acme's flagship product is an on-device speech recognition SDK.",
]
KB_EMB = [embed_model.encode(c) for c in KB]  # embed the KB once, reuse everywhere


# ─── WARM-UP: feel semantic similarity ───────────────────────────────────────
def warmup():
    a, b, c = (embed_model.encode(s) for s in
               ["The cat sat on the mat", "A feline rested on a rug",
                "The stock market crashed yesterday"])
    dot = lambda x, y: sum(i * j for i, j in zip(x, y))  # noqa: E731
    print("paraphrase dot:", dot(a, b))   # high — same meaning
    print("unrelated dot: ", dot(a, c))   # much lower


# ─── CHUNK 5A: cosine similarity & semantic search ───────────────────────────
def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x * x for x in a) ** 0.5
    mag_b = sum(x * x for x in b) ** 0.5
    return dot / (mag_a * mag_b)  # divide out magnitude -> direction (meaning) only


def find_nearest(query, chunks=KB, embeddings=KB_EMB):
    q = embed_model.encode(query)
    scored = [(cosine_similarity(q, e), c) for c, e in zip(chunks, embeddings)]
    score, chunk = max(scored)
    return chunk, score

# CHALLENGE ANSWER:
#   "Acme was founded in 2019" and "When did Acme get started?" both return the SAME
#   founding chunk, even though the rephrase shares almost no words. Cosine works on
#   meaning (vector direction), not word overlap — that is semantic search.


# ─── CHUNK 5B: RAG as a tool — and its edges ─────────────────────────────────
def retrieve_context(query):
    q = embed_model.encode(query)
    ranked = sorted(KB, key=lambda c: cosine_similarity(q, embed_model.encode(c)), reverse=True)
    return "\n".join(ranked[:2])  # top 2 chunks


RETRIEVE = {"name": "retrieve_context",
            "description": "Look up relevant facts about Acme Corp from the knowledge base",
            "input_schema": {"type": "object",
                             "properties": {"query": {"type": "string"}},
                             "required": ["query"]}}

# CHALLENGE ANSWER:
#   (a) "How much money has Acme taken from investors?" -> the Series A chunk wins,
#       high score (a clean paraphrase).
#   (b) "What is Acme's annual revenue?" -> top score is noticeably LOWER; nothing in
#       the KB answers it. A score THRESHOLD lets the agent say "I don't know" instead
#       of returning the closest-but-irrelevant chunk.
#   (c) "Tell me about Acme's leadership." -> CEO (Maria Chen) and CTO (James Wu)
#       chunks both match; whichever the embedding ties "leadership" closer to wins.


# ─── MINI PROJECT: RAG wired into the research agent ─────────────────────────
def search(query):
    return f"[fake live web result for '{query}']"  # stands in for Session 3's web search


def execute_tool(name, args):
    if name == "retrieve_context":
        return retrieve_context(**args)
    if name == "search":
        return search(**args)
    return f"Error: unknown tool '{name}'"


SEARCH = {"name": "search", "description": "Search the live web for recent information",
          "input_schema": {"type": "object",
                           "properties": {"query": {"type": "string"}},
                           "required": ["query"]}}


def rag_agent(task, max_steps=8):
    messages = [{"role": "user", "content": task}]
    for _ in range(max_steps):
        r = client.messages.create(model=MODEL, max_tokens=1024,
                                   messages=messages, tools=[RETRIEVE, SEARCH])
        messages.append({"role": "assistant", "content": r.content})
        if r.stop_reason != "tool_use":
            print("Final:", r.content[0].text)
            return
        for block in r.content:
            if block.type == "tool_use":
                print(f"  -> {block.name}({block.input})")
                messages.append({"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": block.id,
                    "content": execute_tool(block.name, block.input)}]})

# Done when: Task 1 ("Who founded Acme and when?") is answered from retrieve_context,
#   and Task 2 visibly consults both tools. The tool DESCRIPTIONS nudge the choice:
#   KB questions hit retrieve_context, "recent news" questions hit search.


if __name__ == "__main__":
    warmup()
    print("\n5A:", find_nearest("When did Acme get started?"))
    print("\n=== Task 1 (KB) ===")
    rag_agent("Who founded Acme and when?")
    print("\n=== Task 2 (KB + web) ===")
    rag_agent("What is Acme Corp's latest product, and what do recent news articles say about it?")
