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
# Run this first — it should work with no changes.

response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=100,
    messages=[{"role": "user", "content": "Say hello!"}]
)
print("Warm-up response:")
print(response)
print()


# ─── CHUNK 1A: Reading the response ──────────────────────────────────────────
# The response object contains more than just the reply text.
# Task: print response.content, response.stop_reason, and response.usage separately.
# Then write extract(r) that returns a clean dict.

def extract(r):
    # TODO: return a dict with these four keys:
    #   "text"          -> r.content[0].text
    #   "input_tokens"  -> r.usage.input_tokens
    #   "output_tokens" -> r.usage.output_tokens
    #   "stop_reason"   -> r.stop_reason
    pass

print("1A — extract():", extract(response))
print()


# ─── CHUNK 1B: Tokens aren't words ───────────────────────────────────────────
# Cost, limits, and speed are all in tokens — not words or characters.
# Task: call the API with max_tokens=1 for each input and log the input_token count.

inputs = [
    "Alex",
    "def add(a, b):\n    return a + b",
    '{"name": "Alice", "age": 30, "city": "NYC"}',
    "antidisestablishmentarianism",
    "🎉"
]

print("1B — token counts:")
for text in inputs:
    # TODO: create a message with max_tokens=1 and print:
    #   f"{repr(text[:35])}: {r.usage.input_tokens} tokens"
    pass
print()


# ─── CHUNK 1C: Statelessness — break it ──────────────────────────────────────
# Every API call is fully independent. The model has no memory between calls.
# Task: tell the model your name, then in a separate call ask what your name is
# WITHOUT including the first exchange.

print("1C — stateless test:")

# TODO: Call 1 — tell the model your name
#   messages=[{"role": "user", "content": "My name is Jordan."}]

# TODO: Call 2 — ask what your name is, but do NOT include call 1's messages
#   messages=[{"role": "user", "content": "What's my name?"}]
#   print the response — the model should not know your name
print()


# ─── CHUNK 1D: Building history ──────────────────────────────────────────────
# Fix statelessness: send every previous turn on every new call.
# Task: maintain a messages list, run 5 turns, print token counts each turn.

print("1D — conversation with history (type 'quit' to exit early):")
messages = []

# TODO: loop 5 times using input("You: ")
#   1. append {"role": "user", "content": user_text} to messages
#   2. call the API with the full messages list
#   3. get the reply text and append {"role": "assistant", "content": reply}
#   4. print f"Claude: {reply}"
#   5. print f"  [turn {i+1}: {r.usage.input_tokens} input tokens, {len(messages)} messages]"
print()


# ─── CHUNK 1E: System prompt as a dial ───────────────────────────────────────
# The system prompt is the highest-authority instruction in every API call.
# Task: send the same user message with three different system prompts.

user_message = "Explain what you are in one sentence."
system_prompts = [
    None,
    "You are a pirate.",
    'You are a terse CLI tool. Reply only with valid JSON: {"answer": "..."}'
]

print("1E — system prompt comparison:")
for sp in system_prompts:
    # TODO: call the API with each system prompt (skip system param when sp is None)
    # print f"System: {repr(sp)}\nReply: {text}\n"
    pass


# ─── MINI PROJECT: Chatbot class ─────────────────────────────────────────────
# Build a Chatbot class with history and per-turn token logging.
# Push to GitHub when done.

class Chatbot:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.history = []
        self.token_log = []  # list of input_token counts per turn

    def chat(self, message: str) -> str:
        # TODO:
        #   1. append {"role": "user", "content": message} to self.history
        #   2. call the API with self.history and max_tokens=200
        #   3. append r.usage.input_tokens to self.token_log
        #   4. get reply text, append {"role": "assistant", "content": reply} to self.history
        #   5. return reply
        pass


if __name__ == "__main__":
    print("\n─── Mini Project: Chatbot ───")
    bot = Chatbot()
    for i in range(10):
        user_input = input("You: ")
        if user_input.lower() == "quit":
            break
        reply = bot.chat(user_input)
        print(f"Claude: {reply}")
    print("\nToken log:", bot.token_log)
