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
from sentence_transformers import SentenceTransformer
import requests

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"
BRAVE_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")


# A small, fixed knowledge base so every query below is reproducible. Use these
# EXACT five chunks for the tasks and challenges in this session:
KB = [
    "Acme Corp was founded in 2019 in Austin by two former robotics engineers.",
    "Acme raised a $12M Series A led by Foundry Ventures in 2022.",
    "Maria Chen is Acme's CEO; she previously led hardware at a self-driving startup.",
    "James Wu is Acme's CTO and architected the company's core inference engine.",
    "Acme's flagship product is an on-device speech recognition SDK.",
]


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
embed = SentenceTransformer("all-MiniLM-L6-v2")
# embeddings = embed.encode(["The cat sat on the mat", "A feline rested on a rug", "The stock market crashed yesterday"])
# dot_product_paraphrase = embeddings[0] @ embeddings[1]
# dot_product_unrelated = embeddings[0] @ embeddings[2]
# print(f"Dot product (paraphrase): {dot_product_paraphrase:.4f}")
# print(f"Dot product (unrelated): {dot_product_unrelated:.4f}")

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

# ANSWER: Same chunk wins both times, with a higher score for literal than rephrased.


def cosines_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x * x for x in a) ** 0.5
    mag_b = sum(x * x for x in b) ** 0.5
    return dot / (mag_a * mag_b)


KB_embeddings = embed.encode(KB)


def find_nearest(query, chunks, embeddings):
    query_embedding = embed.encode([query])[0]
    best_score = -1
    best_chunk = None
    for chunk, embedding in zip(chunks, embeddings):
        score = cosines_similarity(query_embedding, embedding)
        if score > best_score:
            best_score = score
            best_chunk = chunk
    return best_chunk, best_score


# print(find_nearest("Acme was founded in 2019", KB, KB_embeddings))
# print(find_nearest("When did Acme get started?", KB, KB_embeddings))

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

# ANSWER (b, threshold): NOT noticeably lower — the unanswerable revenue query (0.5678)
#   landed within 0.03 of the real paraphrase hit (funding, 0.5983). That tiny gap is
#   why a single global cosine threshold can't reliably gate "I don't know": cosine
#   ranks by TOPIC, not by whether the answer is actually present. "revenue/money/
#   investors" all sit near the funding chunk regardless of whether it answers.
#
# ANSWER (c, ambiguous): neither leader chunk won — the founding chunk did (0.4668),
#   but it's a ~0.005 three-way photo-finish: founding 0.4668 / CTO 0.4619 / CEO 0.4597,
#   with funding (0.4218) and product (0.3792) well behind. So embeddings DID cluster the
#   three "who-runs-the-company" chunks on top, but can't tell founder-engineers from
#   CEO/CTO — no chunk says "leadership". The winner is noise; the real tell is the
#   uniformly LOW score (~0.46 vs 0.57-0.60 above), i.e. retrieval is weak here.


def retrieve_context(query, embeddings=KB_embeddings):
    query_embedding = embed.encode([query])[0]
    best_score = -1
    second_best_score = -1
    best_chunk = None
    second_best_chunk = None
    for chunk, embedding in zip(KB, embeddings):
        score = cosines_similarity(query_embedding, embedding)
        if score > best_score:
            second_best_score = best_score
            second_best_chunk = best_chunk
            best_score = score
            best_chunk = chunk
        elif score > second_best_score:
            second_best_score = score
            second_best_chunk = chunk
    return best_chunk + "\n" + second_best_chunk


retrieve_context_schema = {
    "name": "retrieve_context",
    "description": "Retrieves relevant information from the knowledge base to answer questions. "
    "Use this tool when the user asks a question that can be answered with the information in the KB. "
    "Return the most relevant chunks from the knowledge base.",
    "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}},
}

# print(find_nearest("How much money has Acme taken from investors?", KB, KB_embeddings))
# print(find_nearest("What is Acme's annual revenue?", KB, KB_embeddings))
# print(find_nearest("Tell me about Acme's leadership.", KB, KB_embeddings))


# ─── MINI PROJECT: RAG wired into the research agent ─────────────────────────
# Give the Session 4 agent two knowledge sources. Push to GitHub when it passes.
#
#   ☐ Tools: search (live web, Session 4) AND retrieve_context (static KB).
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
#
# ANSWER (mini-project): with the Brave key SET, real web search broke the intended
#   behavior — the KB's "Acme Corp" is FICTIONAL, but the live web has many real "Acme"
#   companies, so the web noise collided with the KB entity.
#   - Task 1 ("Who founded Acme?"): the agent called BOTH tools and blended the correct
#     KB answer (2019, Austin, robotics) with real-web hits (Acme Markets 1891 grocery,
#     ACME Communications), then asked for clarification — instead of answering from the
#     KB via retrieve_context ONLY, as intended.
#   - Task 2 ("latest product + recent news"): the agent called search TWICE and NEVER
#     called retrieve_context, so it missed the KB's "on-device speech recognition SDK"
#     and returned real companies (the "Feb 2026 sales" figure proves it's live web data).
#   WHICH SOURCE WON: the WEB — the agent trusted it and never even checked the KB. The
#   tool descriptions did NOT nudge correctly: "latest/recent news" reads as web-flavored,
#   so it skipped the KB even though the KB held the answer.
#   ROOT CAUSE: agent_loop passes NO system prompt, so nothing grounds "Acme" to the KB.
#   FIX: add a system prompt grounding "Acme" to the KB entity and saying "check
#   retrieve_context FIRST; use web only to supplement, and ignore hits about other Acmes."


def search(query):
    # Real Brave Search when a key is set; otherwise a fake one-liner so the
    # structural lessons still run with no key and no network.
    if not BRAVE_KEY:
        return f"[fake search result for '{query}']"
    r = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={"X-Subscription-Token": BRAVE_KEY},
        params={"q": query, "count": 3},
    )
    results = r.json().get("web", {}).get("results", [])
    return "\n".join(f"- {x['title']}: {x['description']}" for x in results)


search_schema = {
    "name": "search",
    "description": "Search the web for recent information",
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
}

def execute_tool(name, args):
    if name == "search":
        return search(**args)
    if name == "retrieve_context":
        return retrieve_context(**args)
    return f"Error: unknown tool '{name}'"

TOOLS = [retrieve_context_schema, search_schema]

def agent_loop(messages):
    steps, tokens, answer = 0, 0, ""
    while True:
        r = client.messages.create(model=MODEL, max_tokens=1024, messages=messages, tools=TOOLS)
        tokens += r.usage.input_tokens + r.usage.output_tokens
        steps += 1
        messages.append({"role": "assistant", "content": r.content})

        if r.stop_reason == "end_turn":
            answer = r.content[0].text
            break

        for block in r.content:
            if block.type == "tool_use":
                print(f"  -> {block.name}({block.input})")
                messages.append({"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": block.id,
                    "content": execute_tool(block.name, block.input)}]})

    return {"steps": steps, "tokens": tokens, "answer": answer}


task1 = "Who founded Acme and when?"
task2 = "What is Acme Corp's latest product, and what do recent news articles say about it?"

print("=== Task 1 (KB) ===")
print(agent_loop([{"role": "user", "content": task1}]))

print("=== Task 2 (KB + Web) ===")
print(agent_loop([{"role": "user", "content": task2}]))