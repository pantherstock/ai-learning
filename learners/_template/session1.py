"""
Session 1 — First Contact
Learn the shape of the API by touching it directly.

The web page is just a map. The real lesson is here. Work top to bottom and
fill in every # TODO:. Each chunk has three parts:
  CONCEPT   — what's going on; read it once.
  TODO      — the code to write.
  CHALLENGE — a concrete experiment with exact inputs. Run it, then write the
              answer in a comment so future-you can see what you learned.
Run with: python session1.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic

client = anthropic.Anthropic()      # reads ANTHROPIC_API_KEY from env
MODEL = "claude-haiku-4-5-20251001"  # fast + cheap; fine for everything in Session 1


# ─── WARM-UP: Your first API call ────────────────────────────────────────────
# TODO: call client.messages.create(model=MODEL, max_tokens=100, messages=[...])
# with a single user message "Say hello!". Print the whole response object and
# notice its structure: .content (a list of blocks), .usage, .stop_reason.


# ─── CHUNK 1A: Read the response & count tokens ──────────────────────────────
# CONCEPT
#   A response is more than reply text. It carries:
#     .content      -> a list of blocks; .content[0].text is the reply
#     .stop_reason   -> WHY it stopped ("end_turn" for a normal reply)
#     .usage         -> .input_tokens / .output_tokens
#   Cost, context limits, and speed are all measured in TOKENS, not words or
#   characters. A token is roughly 3-4 characters of English — but code, JSON,
#   and emoji tokenize very differently.
#
# TODO (a): print r.content, r.stop_reason, and r.usage separately for the
#   warm-up response, then write extract(r) returning this dict:
#       {"text": r.content[0].text,
#        "input_tokens": r.usage.input_tokens,
#        "output_tokens": r.usage.output_tokens,
#        "stop_reason": r.stop_reason}
#
# TODO (b): for EACH input below, call the API with max_tokens=1 and print
#   f"{repr(text[:35])}: {r.usage.input_tokens} input tokens". Use these exact 5:
#       "Alex"
#       "def add(a, b):\n    return a + b"
#       '{"name": "Alice", "age": 30, "city": "NYC"}'
#       "antidisestablishmentarianism"
#       "🎉"
#
# CHALLENGE (write the answers in comments):
#   1. Of the 5 inputs, which has the MOST tokens-per-character? Which the fewest?
#   2. Is "🎉" (one visible character) more or fewer tokens than the long word
#      "antidisestablishmentarianism"? Note the actual numbers.
#   3. What is .stop_reason on a normal reply? List every value you think it could
#      take — one of them shows up in Session 2 and changes how you read responses.


# ─── CHUNK 1B: Statelessness — and the fix ───────────────────────────────────
# CONCEPT
#   Every API call is fully independent. The model has NO memory between calls.
#   The fix is mechanical: resend the entire conversation on every call. History
#   lives in YOUR code (a messages list), not on the server. Every "agent memory"
#   technique in later sessions is a workaround for exactly this fact.
#
# TODO (a) — feel the statelessness:
#   Call 1: messages=[{"role": "user", "content": "My name is Jordan."}]
#   Call 2: a SEPARATE call with messages=[{"role": "user", "content":
#           "What's my name?"}] — do NOT include call 1. Print the reply; the
#           model should not know your name.
#
# TODO (b) — build history:
#   Keep a messages list. Loop 5 times reading input("You: "):
#     1. append {"role": "user", "content": user_text}
#     2. call the API with the FULL messages list
#     3. reply = r.content[0].text; append {"role": "assistant", "content": reply}
#     4. print f"Claude: {reply}"
#     5. print f"  [turn {i+1}: {r.usage.input_tokens} input tokens, "
#              f"{len(messages)} messages]"
#   To test without typing, you may use this fixed 5-line script instead of input():
#       ["My name is Jordan.", "I like hiking.", "What's my name?",
#        "What do I like?", "Summarize what you know about me."]
#
# CHALLENGE (write the answers in comments):
#   1. In TODO (b), how do input_tokens change each turn — flat, linear, or faster?
#   2. Turn 3 asks "What's my name?" — does it answer correctly now? Why, when the
#      identical question failed in TODO (a)?
#   3. Roughly how many input tokens would turn 50 cost if the trend continued?
#      (This number is why Session 3 exists.)


# ─── CHUNK 1C: System prompt as a dial ───────────────────────────────────────
# CONCEPT
#   The system prompt is the highest-authority instruction in every call. It
#   shapes tone and format more than anything else. For an APPLICATION, output
#   that is CONSISTENTLY shaped matters more than output that is occasionally
#   brilliant — your code has to parse it every time.
#
# TODO: send the SAME user message — "Explain what you are in one sentence." —
#   with each of these three system prompts and print the three replies:
#       None                       (omit the system= param entirely)
#       "You are a pirate."
#       'You are a terse CLI tool. Reply only with valid JSON: {"answer": "..."}'
#
# CHALLENGE (write the answers in comments):
#   Run the JSON system prompt 3 times. How many of the 3 replies are valid,
#   parseable JSON? Run the "pirate" one 3 times — is its FORMAT as predictable?
#   Which system prompt would you trust inside a program, and why?


# ─── MINI PROJECT: Chatbot class with token logging ──────────────────────────
# Build the class every later session extends. Push to GitHub when the checklist
# passes.
#
#   ☐ Chatbot.__init__ creates the client, sets an empty history list, and an
#     empty token_log list.
#   ☐ chat(message) appends the user turn, calls the API with full history, appends
#     the assistant reply, records r.usage.input_tokens in token_log, returns text.
#   ☐ Run exactly 10 turns (reuse/extend the 5-line script from 1B, or type your
#     own) so the conversation actually builds on itself.
#   ☐ After the run, print token_log and the total input tokens across all turns.
#
# Done when: 10 turns run end-to-end, token_log has 10 entries, and the printed
#   counts visibly grow turn over turn (proving history is being resent).
#
# TODO: implement the Chatbot class and the 10-turn run.
