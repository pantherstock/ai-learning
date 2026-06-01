"""
Session 1 — First Contact
Learn the shape of the API by touching it directly.

Work top to bottom. Fill in every # TODO: to complete each chunk.
Run with: python session1.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

MODEL = "claude-haiku-4-5-20251001"

def call_llm(messages, max_tokens=100, system=None):
    kwargs = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": messages
    }
    if system is not None:
        kwargs["system"] = system
    return client.messages.create(**kwargs)

# ─── WARM-UP: Your first API call ────────────────────────────────────────────
# TODO: call client.messages.create() with model="claude-haiku-4-5-20251001",
# max_tokens=100, and a single user message "Say hello!". Print the full response
# object and notice its structure (content, usage, stop_reason).
response = call_llm([{"role": "user", "content": "Say hello!",}])
print("Warm Up")
print(response)


# ─── CHUNK 1A: Reading the response ──────────────────────────────────────────
# The response object contains more than just the reply text.
#
# TODO: print response.content, response.stop_reason, and response.usage separately.
# Then write extract(r) that returns a dict with these four keys:
#   "text"          -> r.content[0].text
#   "input_tokens"  -> r.usage.input_tokens
#   "output_tokens" -> r.usage.output_tokens
#   "stop_reason"   -> r.stop_reason

def extract(r):
    return {
        "text": r.content[0].text,
        "input_tokens": r.usage.input_tokens,
        "output_tokens": r.usage.output_tokens,
        "stop_reason": r.stop_reason,
    }
print("Chunk 1A")
print(extract(response))
# stop_reason is end_turn


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

texts = [
    "Alex", 
    "def add(a, b):\n    return a + b", 
    '{"name": "Alice", "age": 30, "city": "NYC"}',
    "antidisestablishmentarianism",
    "🎉"
]
print("Chunk 1B")
for text in texts:
    r = call_llm([{ "role": "user", "content": text }], 1)
    print(f"{repr(text[:35])}: {r.usage.input_tokens} tokens")

# Most tokens per character: emoji
# Fewest tokens per character: antidisestablishmentarianism


# ─── CHUNK 1C: Statelessness — break it ──────────────────────────────────────
# Every API call is fully independent. The model has no memory between calls.
#
# TODO: Call 1 — tell the model your name:
#   messages=[{"role": "user", "content": "My name is Jordan."}]
# TODO: Call 2 — in a SEPARATE call, ask "What's my name?" WITHOUT including
#   call 1's messages. Print the reply — the model should not know your name.

response_1 = call_llm([{"role": "user", "content": "My name is Jordan."}])
response_2 = call_llm([{"role": "user", "content": "What's my name?"}])
print("Response 1", extract(response_1)['text'])
print("Response 2", extract(response_2)['text'])


# ─── CHUNK 1D: Building history ──────────────────────────────────────────────
# Fix statelessness: send every previous turn on every new call.
#
# TODO: maintain a messages list and loop 5 times using input("You: "):
#   1. append {"role": "user", "content": user_text} to messages
#   2. call the API with the full messages list
#   3. append {"role": "assistant", "content": reply} and print f"Claude: {reply}"
#   4. print f"  [turn {i+1}: {r.usage.input_tokens} input tokens, {len(messages)} messages]"
# Watch the input token count climb every turn.

messages = []
for i in range(5):
    user_text = input("You: ")
    messages.append({"role": "user", "content": user_text})
    reply = call_llm(messages)
    r = extract(reply)
    messages.append({"role": "assistant", "content": r["text"]})
    print(f"Claude: {r['text']}")
    print(f"[turn {i+1}: {r['input_tokens']} input tokens, {len(messages)} messages]")


# ─── CHUNK 1E: System prompt as a dial ───────────────────────────────────────
# The system prompt is the highest-authority instruction in every API call.
#
# TODO: send the same user message ("Explain what you are in one sentence.")
# with three different system prompts and compare the replies:
#   None
#   "You are a pirate."
#   'You are a terse CLI tool. Reply only with valid JSON: {"answer": "..."}'
# (Skip the system param when it's None.)

print("Chunk 1E")
system_prompts = [None, "You are a pirate.", 'You are a terse CLI tool. Reply only with valid JSON: {"answer": "..."}']
for system in system_prompts:
    response = call_llm([{"role": "user", "content": "Explain what you are in one sentence."}], 100, system)
    print(f"Response: {extract(response)["text"]}")


# ─── MINI PROJECT: Chatbot class ─────────────────────────────────────────────
# Build a Chatbot class with conversation history and per-turn token logging.
# Run 10 turns. Print the token log at the end. Push to GitHub.
# This class is the starting point for every session that follows.

class Chatbot:
    def __init__(self):
        self.client = client
        self.history = []
        self.token_log = []

    def chat(self, message):
        # Append user message to history
        self.history.append({"role": "user", "content": message})

        # Call API with full history
        response = call_llm(self.history, max_tokens=200)

        # Record input tokens
        self.token_log.append(response.usage.input_tokens)

        # Extract reply and append to history
        reply = extract(response)["text"]
        self.history.append({"role": "assistant", "content": reply})

        return reply

if __name__ == "__main__":
    chatbot = Chatbot()
    # Run 10 turns. Print the token log at the end. Push to GitHub. This class is the starting point for every session that follows.
    for i in range(10):
        user_text = input("You: ")
        response_text = chatbot.chat(user_text)
        print(f"Claude: {response_text}")
        
    print(f"Token log: {chatbot.token_log}")
    
