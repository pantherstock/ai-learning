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

tools = [{
    "name": "get_weather",
    "description": "Get the current weather for a city.",
    "input_schema": {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"]
    }
}]

r = client.messages.create(
    model="claude-haiku-4-5-20251001", max_tokens=200,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}]
)
print("Warm-up:")
print("stop_reason:", r.stop_reason)
print("content:", r.content)
print()


# ─── CHUNK 2A: The tool_use block ────────────────────────────────────────────
# Parse what the model returned. content holds a ToolUseBlock, not a text block.
# Task: extract and print block.id, block.name, and block.input.

print("2A — parsing the tool_use block:")
for block in r.content:
    if block.type == "tool_use":
        # TODO: print block.id, block.name, block.input
        pass

# TODO: also make a call that does NOT need a tool ("What's 2 + 2?")
# and print its stop_reason to see the difference
print()


# ─── CHUNK 2B: Closing the loop ──────────────────────────────────────────────
# The model asked you to call a function. Call it (fake the result) and report back.
# Task: append the assistant response, then a tool_result message, then call again.

print("2B — closing the tool loop:")
messages = [{"role": "user", "content": "What's the weather in Tokyo?"}]
messages.append({"role": "assistant", "content": r.content})

tool_block = None
for block in r.content:
    if block.type == "tool_use":
        tool_block = block
        break

# TODO: append a tool_result user message:
#   {
#       "role": "user",
#       "content": [{
#           "type": "tool_result",
#           "tool_use_id": tool_block.id,
#           "content": "Sunny, 24°C, light wind."
#       }]
#   }

# TODO: make the second API call and print r2.content[0].text
print()


# ─── CHUNK 2C: The agent loop ────────────────────────────────────────────────
# Wrap the tool cycle in a while loop. Keep running until stop_reason == "end_turn".
# Task: give the model a fake search() and real write_file(). Ask it to find and save.

agent_tools = [
    {
        "name": "search",
        "description": "Search the web for information.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["filename", "content"]
        }
    }
]

def execute_tool(name, args):
    if name == "search":
        return f"Top result for '{args['query']}': [fake result about the topic]"
    if name == "write_file":
        with open(args["filename"], "w") as f:
            f.write(args["content"])
        return "File written successfully."
    return f"Unknown tool: {name}"

print("2C — agent loop:")
messages_2c = [{"role": "user", "content": "Search for the history of Python and save a summary to python_history.txt"}]
step = 0

# TODO: build the agent loop:
#   while True:
#       call the API with agent_tools and messages_2c
#       step += 1
#       print f"Step {step}: stop_reason={r.stop_reason}"
#       if stop_reason == "end_turn": print final text and break
#       append assistant response to messages_2c
#       for each tool_use block: call execute_tool(), append tool_result to messages_2c
print()


# ─── CHUNK 2D: Break it — always fail ────────────────────────────────────────
# Replace search with a function that always returns an error. Run 5+ steps.
# Observe: does the model loop forever, give up, ask for help, or fabricate?

def search_always_fails(query):
    return "Error: permission denied. Access to external resources is blocked."

print("2D — always-failing search:")
messages_2d = [{"role": "user", "content": "Search for Python tutorials and summarize what you find."}]

# TODO: run an agent loop for at least 5 steps using search_always_fails
# Log each step's stop_reason and any text the model produces
# (Replace the search tool's execution with search_always_fails)
print()


# ─── CHUNK 2E: Safety valves ─────────────────────────────────────────────────
# Add hard limits so the loop can't run forever.

MAX_STEPS = 10
TOKEN_BUDGET = 30_000

print("2E — safety valves:")
messages_2e = [{"role": "user", "content": "Research the history of machine learning and write a detailed report to ml_history.txt"}]
step = 0
total_tokens = 0

# TODO: rewrite the agent loop with safety checks:
#   while step < MAX_STEPS and total_tokens < TOKEN_BUDGET:
#       call API
#       total_tokens += r.usage.input_tokens + r.usage.output_tokens
#       step += 1
#       ... rest of loop ...
#   if step >= MAX_STEPS: print(f"Stopped: hit {MAX_STEPS} steps")
#   elif total_tokens >= TOKEN_BUDGET: print(f"Stopped: budget exhausted ({total_tokens:,} tokens)")
print()


# ─── MINI PROJECT: File agent with real tools ─────────────────────────────────
# Build an agent with two real tools: read_file and write_file.
# Add max_steps and token budget. Handle FileNotFoundError.
# Push to GitHub when done.

def read_file(path: str) -> str:
    # TODO: open and return the file contents
    # catch FileNotFoundError and return an error string instead of raising
    pass

def write_file(path: str, content: str) -> str:
    # TODO: write content to path, return "File written: {path}"
    pass

file_agent_tools = [
    {
        "name": "read_file",
        "description": "Read the contents of a file.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
    }
]

if __name__ == "__main__":
    print("\n─── Mini Project: File Agent ───")
    # TODO: run the agent with this task:
    # "Read the file 'tasks.md', extract all action items, and write them to 'actions.txt'"
    # First create a sample tasks.md with bullet points and some action items mixed in.
    # Then run. Then test with a path that doesn't exist and observe the behavior.
    pass
