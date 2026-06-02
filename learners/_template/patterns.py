"""
Section B — Advanced Agentic Patterns
Four patterns beyond Session 4: reflection, parallel fan-out, routing, human-in-the-loop.

Each section is CONCEPT -> TODO -> CHALLENGE (see session1.py).
Prerequisites: complete Session 4 first.
Run with: python patterns.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import threading
import time
import os

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"
BRAVE_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")

# TODO: bring forward search(query) from Session 3/4 (with the BRAVE_KEY fallback)
# — the patterns below reuse it.


# ─── WARM-UP: Reflection in 3 lines ──────────────────────────────────────────
# TODO: make one call to get first_answer for "Explain what an API is in one
# sentence.", then a second call showing that answer and asking: "Critique this
# explanation in one sentence. What's imprecise or misleading?" Print both. One
# extra call already makes the output better — that's the whole idea of reflection.


# ─── SECTION B1: Reflection loop ─────────────────────────────────────────────
# CONCEPT
#   Draft -> critique -> revise, repeating until the model rates its own output
#   "good" or a max-iteration cap is hit. The stopping criterion is what keeps it
#   from looping forever.
#
# TODO: implement reflection_loop(task, max_iterations=3) -> str:
#   - draft an answer
#   - each iteration: ask the model to rate it. Use this EXACT rubric in the prompt:
#       "Rate the draft. If it is good, reply exactly DONE. Otherwise reply
#        NEEDS-WORK: <one sentence on what's wrong>."
#     If it replies DONE, break; else ask it to rewrite addressing the critique.
#   - print whether each iteration continued or stopped; return the final draft.
#
# CHALLENGE (write the answers in comments):
#   Run reflection_loop on this EXACT task 3 times: "Write a 2-sentence product
#   description for a waterproof hiking backpack." How many iterations until DONE
#   each time? Is it consistent? When is the extra token cost of reflection worth it?


# ─── SECTION B2: Parallel fan-out ────────────────────────────────────────────
# CONCEPT
#   Fork work to N independent subagents in parallel threads — each with its own
#   context — then merge with one synthesis call. threading.Thread is simpler than
#   asyncio here. The speedup is rarely exactly Nx.
#
# TODO: implement run_subagent(subtask, results, key) — a small loop (max 5 steps)
#   storing its answer in results[key]. Use these EXACT three subtasks, one per
#   thread: "Summarize Django for REST APIs", "Summarize FastAPI for REST APIs",
#   "Summarize Flask for REST APIs". Join the threads, then make ONE synthesis call
#   that merges results into a comparison.
#
# CHALLENGE (write the answers in comments):
#   Time the parallel run, then run the SAME three subtasks sequentially and time
#   that. What's the speedup — exactly 3x, less, or more? What caps it (think about
#   the synthesis call and per-call latency)?


# ─── SECTION B3: Router pattern ──────────────────────────────────────────────
# CONCEPT
#   A fast, cheap classifier reads the request and routes it to a specialist. The
#   router does NO domain work — classification only. The craft is fixing one
#   category's misroutes without creating new ones.
#
# TODO: implement classify_intent(user_message) -> one of research/code/summarize/
#   other (a max_tokens=10 call). Implement research_agent / code_agent /
#   summarize_agent and route(user_message) dispatching on the intent, with a plain
#   call for "other".
#
# CHALLENGE (write the answers in comments) — run route() on these EXACT 8 inputs
# and log which specialist each hit:
#   "What's the latest version of Python?"            (expect research)
#   "Write a function to reverse a linked list."      (expect code)
#   "Summarize this paragraph: <paste any 3 lines>"   (expect summarize)
#   "Fix the bug in my for loop"                      (expect code)
#   "Who won the 2022 World Cup?"                     (expect research)
#   "tl;dr the plot of Hamlet"                        (expect summarize)
#   "What's the weather like?"                        (ambiguous)
#   "Tell me a joke"                                  (other)
#   Which input gets misrouted? Tweak the classifier prompt to fix it — does your
#   fix break any of the others?


# ─── SECTION B4: Human-in-the-loop ───────────────────────────────────────────
# CONCEPT
#   The agent pauses at a decision point and asks a human before acting. Implement
#   it as a tool: ask_human(question) prints the question and returns input(). The
#   hard part is getting it to reliably pause BEFORE acting, not after.
#
# TODO: implement ask_human(question). Define ask_human + write_file schemas and a
#   loop that runs this EXACT task:
#       "Write a summary of machine learning to ml_summary.txt, but ask the human
#        how detailed it should be BEFORE writing."
#   Feed the human's answer back as a tool_result.
#
# CHALLENGE (write the answers in comments):
#   Does it ask before writing, or write first and ask later? Try these two system
#   prompt lines and note which reliably makes it pause:
#     (a) "You may ask the human if helpful."
#     (b) "You MUST call ask_human and wait for the answer before any write_file."
#   Why does phrasing change the behavior so much?
