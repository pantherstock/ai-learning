"""
Session 1 — First Contact · REFERENCE ANSWERS

One worked solution per chunk. Read AFTER you've tried session1.py yourself.
Runs unattended (uses a fixed script instead of input()). Each call is cheap.

Run with: python session1.py
"""

import env  # auto-loads .env — no manual `export` needed
import sys
import json
import anthropic

sys.stdout.reconfigure(encoding="utf-8")  # model replies may contain emoji; Windows cp1252 console would crash

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"


# ─── WARM-UP + 1A: read the response & count tokens ──────────────────────────
def extract(r):
    return {"text": r.content[0].text,
            "input_tokens": r.usage.input_tokens,
            "output_tokens": r.usage.output_tokens,
            "stop_reason": r.stop_reason}


def warmup_and_tokens():
    r = client.messages.create(model=MODEL, max_tokens=100,
                               messages=[{"role": "user", "content": "Say hello!"}])
    print("content:", r.content)
    print("stop_reason:", r.stop_reason)
    print("usage:", r.usage)
    print("extract():", extract(r))

    for text in ["Alex",
                 "def add(a, b):\n    return a + b",
                 '{"name": "Alice", "age": 30, "city": "NYC"}',
                 "antidisestablishmentarianism",
                 "🎉"]:
        r = client.messages.create(model=MODEL, max_tokens=1,
                                   messages=[{"role": "user", "content": text}])
        print(f"{repr(text[:35])}: {r.usage.input_tokens} input tokens")

# CHALLENGE ANSWER:
#   1. JSON and the code snippet pack the MOST tokens-per-char (punctuation/symbols
#      each cost a token); the plain name "Alex" the fewest.
#   2. "🎉" is usually 3-4 tokens (emoji are multi-byte) while the long real word
#      "antidisestablishment..." is ~6-7 — one visible glyph isn't one token.
#   3. A normal reply stops with "end_turn". Other values: "max_tokens",
#      "stop_sequence", and "tool_use" — that last one drives all of Session 2.


# ─── CHUNK 1B: statelessness — and the fix ───────────────────────────────────
def statelessness():
    # (a) two independent calls — the second has no memory of the first.
    client.messages.create(model=MODEL, max_tokens=100,
                           messages=[{"role": "user", "content": "My name is Jordan."}])
    r = client.messages.create(model=MODEL, max_tokens=100,
                               messages=[{"role": "user", "content": "What's my name?"}])
    print("No-history reply:", r.content[0].text)

    # (b) resend the FULL history every call — that is the entire fix.
    messages = []
    script = ["My name is Jordan.", "I like hiking.", "What's my name?",
              "What do I like?", "Summarize what you know about me."]
    for i, user_text in enumerate(script):
        messages.append({"role": "user", "content": user_text})
        r = client.messages.create(model=MODEL, max_tokens=200, messages=messages)
        reply = r.content[0].text
        messages.append({"role": "assistant", "content": reply})
        print(f"Claude: {reply}")
        print(f"  [turn {i+1}: {r.usage.input_tokens} input tokens, {len(messages)} messages]")

# CHALLENGE ANSWER:
#   1. input_tokens grow roughly LINEARLY — each turn resends everything before it.
#   2. Turn 3 answers "Jordan" correctly now, because turns 1-2 are in the messages
#      list we resend; in (a) that history was never sent, so it couldn't know.
#   3. If the trend held, turn 50 would cost thousands of input tokens — that
#      unbounded growth is exactly the problem Session 3 (compression) solves.


# ─── CHUNK 1C: system prompt as a dial ───────────────────────────────────────
def system_prompt_dial():
    msg = [{"role": "user", "content": "Explain what you are in one sentence."}]
    for system in [None,
                   "You are a pirate.",
                   'You are a terse CLI tool. Reply only with valid JSON: {"answer": "..."}']:
        kwargs = {"model": MODEL, "max_tokens": 200, "messages": msg}
        if system is not None:
            kwargs["system"] = system
        r = client.messages.create(**kwargs)
        print(f"\nsystem={system!r}\n  {r.content[0].text}")

# CHALLENGE ANSWER:
#   The JSON system prompt parses cleanly all 3 times; the pirate's TONE is reliable
#   but its FORMAT (length, punctuation) varies. Inside a program you trust the JSON
#   one — your code parses the output every time, so consistent SHAPE beats flair.


# ─── MINI PROJECT: Chatbot class with token logging ──────────────────────────
class Chatbot:
    def __init__(self):
        self.client = client
        self.history = []
        self.token_log = []

    def chat(self, message):
        self.history.append({"role": "user", "content": message})
        r = self.client.messages.create(model=MODEL, max_tokens=300, messages=self.history)
        text = r.content[0].text
        self.history.append({"role": "assistant", "content": text})
        self.token_log.append(r.usage.input_tokens)
        return text


def run_chatbot():
    bot = Chatbot()
    script = ["My name is Jordan.", "I like hiking.", "What's my name?",
              "What do I like?", "Recommend a trail.", "How long is it?",
              "What should I pack?", "Any safety tips?", "Summarize this chat.",
              "What's my name again?"]
    for msg in script:
        print("Claude:", bot.chat(msg))
    print("\ntoken_log:", bot.token_log)
    print("total input tokens:", sum(bot.token_log))


if __name__ == "__main__":
    warmup_and_tokens()
    statelessness()
    system_prompt_dial()
    run_chatbot()
