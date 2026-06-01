"""
Session 1 — First Contact
Learn the shape of the API by touching it directly.

Work top to bottom. Fill in every # TODO: to complete each chunk.
Run with: python session1.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env


# ─── WARM-UP: Your first API call ────────────────────────────────────────────
# TODO: call client.messages.create() with model="claude-haiku-4-5-20251001",
# max_tokens=100, and a single user message "Say hello!". Print the full response
# object and notice its structure (content, usage, stop_reason).


# ─── CHUNK 1A: Reading the response ──────────────────────────────────────────
# The response object contains more than just the reply text.
#
# TODO: print response.content, response.stop_reason, and response.usage separately.
# Then write extract(r) that returns a dict with these four keys:
#   "text"          -> r.content[0].text
#   "input_tokens"  -> r.usage.input_tokens
#   "output_tokens" -> r.usage.output_tokens
#   "stop_reason"   -> r.stop_reason


# ─── CHUNK 1B: Tokens aren't words ───────────────────────────────────────────
# Cost, limits, and speed are all in tokens — not words or characters.
#
# TODO: for each input below, call the API with max_tokens=1 and print
# f"{repr(text[:35])}: {r.usage.input_tokens} tokens". Compare the counts.
#   "Alex"
#   "def add(a, b):\n    return a + b"
#   '{"name": "Alice", "age": 30, "city": "NYC"}'
#   "antidisestablishmentarianism"
#   "🎉"


# ─── CHUNK 1C: Statelessness — break it ──────────────────────────────────────
# Every API call is fully independent. The model has no memory between calls.
#
# TODO: Call 1 — tell the model your name:
#   messages=[{"role": "user", "content": "My name is Jordan."}]
# TODO: Call 2 — in a SEPARATE call, ask "What's my name?" WITHOUT including
#   call 1's messages. Print the reply — the model should not know your name.


# ─── CHUNK 1D: Building history ──────────────────────────────────────────────
# Fix statelessness: send every previous turn on every new call.
#
# TODO: maintain a messages list and loop 5 times using input("You: "):
#   1. append {"role": "user", "content": user_text} to messages
#   2. call the API with the full messages list
#   3. append {"role": "assistant", "content": reply} and print f"Claude: {reply}"
#   4. print f"  [turn {i+1}: {r.usage.input_tokens} input tokens, {len(messages)} messages]"
# Watch the input token count climb every turn.


# ─── CHUNK 1E: System prompt as a dial ───────────────────────────────────────
# The system prompt is the highest-authority instruction in every API call.
#
# TODO: send the same user message ("Explain what you are in one sentence.")
# with three different system prompts and compare the replies:
#   None
#   "You are a pirate."
#   'You are a terse CLI tool. Reply only with valid JSON: {"answer": "..."}'
# (Skip the system param when it's None.)


# ─── MINI PROJECT: Chatbot class ─────────────────────────────────────────────
# Build a Chatbot class with conversation history and per-turn token logging.
# Push to GitHub when done.
#
# TODO: implement Chatbot with:
#   - __init__: a client, an empty history list, an empty token_log list
#   - chat(message): append the user message, call the API with the full history
#     and max_tokens=200, record r.usage.input_tokens in token_log, append the
#     assistant reply to history, return the reply text
#   - a __main__ block that loops on input("You: "), breaks on "quit", and prints
#     the token_log at the end
