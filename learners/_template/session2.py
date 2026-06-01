"""
Session 2 — Give the Model Hands
Turn a chatbot into something that acts.

Work top to bottom. Fill in every # TODO: to complete each chunk.
Run with: python session2.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic

client = anthropic.Anthropic()


# ─── WARM-UP: Define a tool — see what comes back ────────────────────────────
# Add tools to the API call. Notice what's missing from the response.
#
# TODO: define a get_weather tool schema (name, description, input_schema with a
# "city" string property) and pass it as tools=[...] in a call asking
# "What's the weather in Tokyo?". Print r.stop_reason and r.content — notice the
# model returns a tool_use block, not text.


# ─── CHUNK 2A: The tool_use block ────────────────────────────────────────────
# Parse what the model returned. content holds a ToolUseBlock, not a text block.
#
# TODO: loop over r.content; for the block where block.type == "tool_use",
# print block.id, block.name, and block.input.
# TODO: also make a call that does NOT need a tool ("What's 2 + 2?") and print
# its stop_reason to see the difference.


# ─── CHUNK 2B: Closing the loop ──────────────────────────────────────────────
# The model asked you to call a function. Call it (fake the result) and report back.
#
# TODO: build a messages list — the original user turn, then the assistant's
# r.content, then a tool_result user message:
#   {"role": "user", "content": [{
#       "type": "tool_result",
#       "tool_use_id": <the tool_use block id>,
#       "content": "Sunny, 24°C, light wind."
#   }]}
# Then make a second API call and print the final text.


# ─── CHUNK 2C: The agent loop ────────────────────────────────────────────────
# Wrap the tool cycle in a while loop. Keep running until stop_reason == "end_turn".
#
# TODO: define two tools — a fake search(query) and a real write_file(filename,
# content) — and an execute_tool(name, args) that runs them.
# TODO: build the agent loop for the task "Search for the history of Python and
# save a summary to python_history.txt":
#   while True:
#       call the API with the tools and messages
#       print f"Step {step}: stop_reason={r.stop_reason}"
#       if stop_reason == "end_turn": print final text and break
#       append the assistant response, run each tool_use block via execute_tool(),
#       append each tool_result back to messages


# ─── CHUNK 2D: Break it — always fail ────────────────────────────────────────
# Replace search with a function that always returns an error. Run 5+ steps.
#
# TODO: make search always return "Error: permission denied..." and run the agent
# loop for at least 5 steps. Log each step's stop_reason and any text.
# Observe: does the model loop forever, give up, ask for help, or fabricate?


# ─── CHUNK 2E: Safety valves ─────────────────────────────────────────────────
# Add hard limits so the loop can't run forever.
#
# TODO: rewrite the loop with MAX_STEPS = 10 and TOKEN_BUDGET = 30_000:
#   while step < MAX_STEPS and total_tokens < TOKEN_BUDGET:
#       call API; total_tokens += r.usage.input_tokens + r.usage.output_tokens; ...
# Then report which limit stopped it.


# ─── MINI PROJECT: File agent with real tools ─────────────────────────────────
# Build an agent with two real tools: read_file and write_file.
# Add max_steps and a token budget. Handle FileNotFoundError. Push to GitHub.
#
# TODO: implement read_file(path) (catch FileNotFoundError, return an error string)
# and write_file(path, content). Define their tool schemas. Then run the agent on:
#   "Read the file 'tasks.md', extract all action items, and write them to 'actions.txt'"
# First create a sample tasks.md with action items mixed into bullet points.
# Then run it again with a path that doesn't exist and observe the behavior.
