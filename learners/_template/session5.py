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
# Install: pip install sentence-transformers
# Embed two sentences and compute their dot product.

from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')  # downloads ~80MB once

a = model.encode("The cat sat on the mat")
b = model.encode("A feline rested on a rug")
c = model.encode("The stock market crashed yesterday")

dot_ab = sum(x * y for x, y in zip(a, b))
dot_ac = sum(x * y for x, y in zip(a, c))

print("Warm-up — semantic similarity:")
print(f"Similar sentences dot product:   {dot_ab:.4f}")
print(f"Unrelated sentences dot product: {dot_ac:.4f}")
print(f"Vector dimensions: {len(a)}")
print()


# ─── CHUNK 5A: Cosine similarity from scratch ────────────────────────────────
# The dot product alone isn't reliable — longer vectors produce bigger values
# regardless of direction. Cosine similarity normalizes for magnitude.
# Task: implement it yourself, no library.

def cosine_similarity(a, b):
    # TODO: implement cosine similarity
    #   dot   = sum(x * y for x, y in zip(a, b))
    #   mag_a = sum(x**2 for x in a) ** 0.5
    #   mag_b = sum(x**2 for x in b) ** 0.5
    #   return dot / (mag_a * mag_b)
    pass

KB_CHUNKS = [
    "Acme Corp was founded in 2018 by Maria Chen and James Wu.",
    "The company's main product is an AI-powered scheduling tool.",
    "Acme raised $12M Series A in 2021 led by Sequoia.",
    "The engineering team uses Python, Go, and React.",
    "CEO Maria Chen previously worked at Google Brain."
]
KB_EMBEDDINGS = model.encode(KB_CHUNKS)

def find_nearest(query: str, chunks, embeddings):
    # TODO: encode the query, compute cosine_similarity against each embedding,
    # return the best matching chunk and its score
    # Return: (chunk_text, score)
    pass

print("5A — cosine similarity search:")
result, score = find_nearest("Who started the company?", KB_CHUNKS, KB_EMBEDDINGS)
print(f"Score: {score:.4f}")
print(f"Match: {result}")

# Try: "What's the company's founding story?" — same chunk, different words?
result2, score2 = find_nearest("What's the company's founding story?", KB_CHUNKS, KB_EMBEDDINGS)
print(f"\nRephrased query score: {score2:.4f}")
print(f"Match: {result2}")
print()


# ─── CHUNK 5B: RAG as a tool ─────────────────────────────────────────────────
# Wire your retrieval function into your agent as a callable tool.

FULL_KB_CHUNKS = [
    "Acme Corp was founded in 2018 by Maria Chen and James Wu in Seattle.",
    "The flagship product, ScheduleAI, is used by 500+ enterprise customers.",
    "Acme raised $12M Series A in 2021 and $40M Series B in 2023.",
    "The engineering team is 45 people, primarily Python and Go.",
    "CEO Maria Chen was previously a research scientist at Google Brain.",
    "CTO James Wu led infrastructure at Stripe before co-founding Acme.",
    "ScheduleAI integrates with Google Calendar, Outlook, and Zoom.",
    "The company is headquartered in Seattle with a London office."
]
FULL_KB_EMBEDDINGS = model.encode(FULL_KB_CHUNKS)

def retrieve_context(query: str) -> str:
    # TODO: encode the query, compute similarity against FULL_KB_EMBEDDINGS,
    # return the top 2 matching chunks joined by newline
    pass

retrieve_tool = {
    "name": "retrieve_context",
    "description": "Search the internal knowledge base for information about Acme Corp.",
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "What to look up"}},
        "required": ["query"]
    }
}

print("5B — retrieval test:")
print(retrieve_context("Who are the founders?"))
print()


# ─── CHUNK 5C: Push the edges ────────────────────────────────────────────────
# Test retrieval behavior on tricky inputs.

print("5C — edge cases:")

test_queries = [
    "How much money has Acme taken from investors?",   # rephrased
    "What is Acme's annual revenue?",                   # not in KB
    "Tell me about Acme's leadership.",                 # ambiguous
]

for q in test_queries:
    result, score = find_nearest(q, FULL_KB_CHUNKS, FULL_KB_EMBEDDINGS)
    print(f"Query: {q}")
    print(f"  Score: {score:.4f}  Match: {result[:60]}...")
    print()

# For the leadership query: which chunk wins — Maria Chen or James Wu?
# Write your observation here:
# OBSERVATION:


# ─── MINI PROJECT: RAG wired into the research agent ─────────────────────────
# Add retrieve_context as a tool to the research agent from Session 3.
# The agent now has two knowledge sources: web search (live) and KB (static).
# Push to GitHub when done.

BRAVE_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")

def search(query: str) -> str:
    if not BRAVE_KEY:
        return f"[fake search: {query}]"
    import requests
    r = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={"X-Subscription-Token": BRAVE_KEY},
        params={"q": query, "count": 3}
    )
    results = r.json().get("web", {}).get("results", [])
    return "\n".join(f"- {x['title']}: {x['description']}" for x in results)

search_tool = {
    "name": "search",
    "description": "Search the web for real-time information.",
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"]
    }
}

def execute_tool(name, args):
    if name == "search": return search(args["query"])
    if name == "retrieve_context": return retrieve_context(args["query"])
    return f"Unknown tool: {name}"

if __name__ == "__main__":
    print("─── Mini Project: RAG + Search Agent ───")
    # TODO: build an agent with both search_tool and retrieve_tool
    # Run task 1: something answerable from the KB
    # Run task 2: something where KB and web might give conflicting info
    # Observe which source the agent prefers
    pass
