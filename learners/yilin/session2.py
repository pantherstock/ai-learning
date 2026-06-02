"""
Session 2 — Give the Model Hands
Turn a chatbot into something that acts.

Work top to bottom. Each chunk is CONCEPT -> TODO -> CHALLENGE (see session1.py).
Run with: python session2.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"


# ─── WARM-UP: Define a tool — see what comes back ────────────────────────────
# TODO: define a get_weather tool schema (name, description, and input_schema with
# a "city" string property), pass it as tools=[get_weather_schema] in a call asking
# "What's the weather in Tokyo?", and print r.stop_reason and r.content.
# Notice: the model did NOT answer. It returned a tool_use block — a REQUEST to
# call your function. Declaring intent, not producing the result, is the whole point.
# get_weather_schema = {
#     "name": "get_weather",
#     "description": "Gets the weather for a city",
#     "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}},
# }
# messages = [{"role": "user", "content": "What's the weather in Tokyo?"}]
# r = client.messages.create(
#     model=MODEL, max_tokens=100, messages=messages, tools=[get_weather_schema]
# )
# print(r.stop_reason)
# print(r.content)

# ─── CHUNK 2A: tool_use → close the loop ─────────────────────────────────────
# CONCEPT
#   The content list holds a ToolUseBlock with three fields you care about:
#       block.id     -> a unique id you must echo back
#       block.name   -> which tool to run
#       block.input  -> the arguments (a dict)
#   You run the function yourself and report the result back as a tool_result that
#   references block.id. The cycle  tool_use -> execute -> tool_result  is the
#   mechanical core of every agent ever built.
#
# TODO (a): loop over r.content; for the block where block.type == "tool_use",
#   print block.id, block.name, block.input.
# TODO (b): make a call that needs NO tool — messages=[{"role":"user",
#   "content":"What's 2 + 2?"}], tools=[get_weather_schema] — and print its
#   stop_reason next to the weather call's stop_reason.
# TODO (c): close the loop. Build messages = [the original user turn,
#   {"role":"assistant","content": r.content}, then a tool_result user turn]:
#       {"role": "user", "content": [{
#           "type": "tool_result",
#           "tool_use_id": <block.id from the weather call>,
#           "content": "Sunny, 24C, light wind."
#       }]}
#   Call the API again and print the final text answer.
#
# CHALLENGE (write the answers in comments):
#   1. What are the two stop_reason values you saw — one for the weather question,
#      one for "What's 2 + 2?" — and what does each mean?
#   2. Change ONE character in the tool_use_id before sending the tool_result and
#      re-run. Paste the exact error. Why must the id match — what breaks in a
#      response that returns two tool_use blocks at once if ids don't line up?


# ─── CHUNK 2B: The agent loop ────────────────────────────────────────────────
# CONCEPT
#   One tool call isn't an agent. Wrap the cycle in a while loop that keeps going
#   until stop_reason == "end_turn". Each pass: call the API, run any tool_use
#   blocks, append their tool_results, repeat. That repetition is the heartbeat.
#
# TODO: define two tools and an executor:
#       search(query)            -> return a FAKE one-line result string
#       write_file(filename, c)  -> really write the file with open(); return "ok"
#       execute_tool(name, args) -> dispatch to the right function
#   Then run this loop on the EXACT task:
#       "Search for the history of Python and save a summary to python_history.txt"
#     while True:
#         r = client.messages.create(model=MODEL, max_tokens=1024,
#                                    messages=messages, tools=tools)
#         print(f"Step {step}: stop_reason={r.stop_reason}")
#         if r.stop_reason == "end_turn": print(r.content[0].text); break
#         messages.append({"role": "assistant", "content": r.content})
#         for block in r.content:
#             if block.type == "tool_use":
#                 result = execute_tool(block.name, block.input)
#                 messages.append({"role": "user", "content": [{
#                     "type": "tool_result", "tool_use_id": block.id,
#                     "content": result}]})
#         step += 1
#
# CHALLENGE (write the answers in comments):
#   Run this EXACT multi-step task (it forces at least 3 tool calls):
#       "Search for the inventor of Python, then search for the year Python 1.0
#        was released, then write both facts to python_facts.txt."
#   Log stop_reason on every iteration and write down the exact sequence of values
#   you see from step 0 to the end. That sequence is the agent loop's pulse.


# ─── CHUNK 2C: Failure modes & safety valves ─────────────────────────────────
# CONCEPT
#   Tools fail in production. And a loop with no brakes can run forever or burn an
#   unbounded amount of money. You need to SEE the failure behavior, then cap it.
#
# TODO (a) — break it: replace search so it ALWAYS returns
#       "Error: search service unavailable (503)"
#   Run the loop for at least 5 steps on the task:
#       "Find today's top news story and save it to news.txt"
#   Log every step's stop_reason and any text.
# TODO (b) — add brakes: rewrite the loop header as
#       MAX_STEPS = 10
#       TOKEN_BUDGET = 30_000
#       while step < MAX_STEPS and total_tokens < TOKEN_BUDGET:
#           ... ; total_tokens += r.usage.input_tokens + r.usage.output_tokens
#   After the loop, print which limit stopped it.
#
# CHALLENGE (write the answers in comments):
#   1. With the always-failing search, which does the model do: loop forever, give
#      up gracefully, ask for help, or fabricate a plausible answer? Quote what it did.
#   2. Set MAX_STEPS=50, TOKEN_BUDGET=5_000 on the working task from 2B — which
#      limit fires? Now set MAX_STEPS=3, TOKEN_BUDGET=200_000 — which fires now?
#      What does that tell you about choosing defaults for short vs long tasks?


# ─── MINI PROJECT: File agent with real tools ────────────────────────────────
# Push to GitHub when the checklist passes.
#
#   ☐ read_file(path): open() the file; catch FileNotFoundError and RETURN an
#     error string (never crash the loop).
#   ☐ write_file(path, content): really write it with open().
#   ☐ Both have correct tool schemas; the loop enforces MAX_STEPS and TOKEN_BUDGET.
#   ☐ First create a sample tasks.md containing action items mixed into bullets, e.g.:
#         - Met with design team
#         - TODO: send the Q3 report to finance
#         - Lunch
#         - TODO: book the offsite venue
#     Run the agent on the EXACT task:
#         "Read the file 'tasks.md', extract only the action items, and write them
#          to 'actions.txt'."
#   ☐ Then run it again pointing read_file at 'does_not_exist.md' and confirm the
#     agent receives the error string and responds instead of crashing.
#
# Done when: actions.txt contains only the two TODO lines, AND the missing-file run
#   finishes with a sensible message (no traceback).
#
# TODO: implement read_file, write_file, their schemas, and both runs.


def read_file(filename):
    try:
        with open(filename, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: file '{filename}' not found."


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)


tools = [
    {
        "name": "read_file",
        "description": "Reads the content of a file",
        "input_schema": {
            "type": "object",
            "properties": {"filename": {"type": "string"}},
        },
    },
    {
        "name": "write_file",
        "description": "Writes content to a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
        },
    },
]

messages = [
    {
        "role": "user",
        "content": "Read the file 'does_not_exist.md', extract only the action items, and write them to 'actions.txt'.",
    }
]

while True:
    r = client.messages.create(
        model=MODEL, max_tokens=1024, messages=messages, tools=tools
    )
    messages.append({"role": "assistant", "content": r.content})
    print(f"Stop reason: {r.stop_reason}")
    if r.stop_reason == "end_turn":
        print(f"Claude: {r.content[0].text}")
        break
    for block in r.content:
        if block.type == "tool_use":
            if block.name == "read_file":
                result = read_file(**block.input)
            elif block.name == "write_file":
                result = write_file(**block.input)
            else:
                result = f"Error: unknown tool '{block.name}'"
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    ],
                }
            )
