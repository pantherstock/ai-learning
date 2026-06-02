"""
Session 2 — Give the Model Hands · REFERENCE ANSWERS

One worked solution per chunk. Read AFTER you've tried session2.py yourself.
search() is FAKE on purpose — the agent loop is the lesson, not real web data.

Run with: python session2.py
"""

import env  # auto-loads .env — no manual `export` needed
import sys
import anthropic

sys.stdout.reconfigure(encoding="utf-8")  # tool output may contain emoji

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"


# ─── Tools: schemas + functions + dispatcher ─────────────────────────────────
def search(query):
    return f"[fake search result for '{query}']"


def read_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: file '{filename}' not found."  # return the error; never crash the loop


def write_file(filename, content):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return f"wrote {filename}"


def execute_tool(name, args):
    if name == "search":
        return search(**args)
    if name == "read_file":
        return read_file(**args)
    if name == "write_file":
        return write_file(**args)
    return f"Error: unknown tool '{name}'"


def schema(name, description, **props):
    return {"name": name, "description": description,
            "input_schema": {"type": "object",
                             "properties": {k: {"type": "string"} for k in props},
                             "required": list(props)}}


SEARCH = schema("search", "Search the web for recent information", query=1)
READ = schema("read_file", "Reads the content of a file", filename=1)
WRITE = schema("write_file", "Writes content to a file", filename=1, content=1)


# ─── WARM-UP + 2A: tool_use -> close the loop ────────────────────────────────
def warmup_and_close_loop():
    get_weather = schema("get_weather", "Gets the weather for a city", city=1)
    r = client.messages.create(model=MODEL, max_tokens=200, tools=[get_weather],
                               messages=[{"role": "user", "content": "What's the weather in Tokyo?"}])
    print("weather stop_reason:", r.stop_reason)  # "tool_use" — a REQUEST, not an answer
    tool_use = next(b for b in r.content if b.type == "tool_use")
    print("id/name/input:", tool_use.id, tool_use.name, tool_use.input)

    no_tool = client.messages.create(model=MODEL, max_tokens=200, tools=[get_weather],
                                     messages=[{"role": "user", "content": "What's 2 + 2?"}])
    print("no-tool stop_reason:", no_tool.stop_reason)  # "end_turn" — answered directly

    # Close the loop: feed a tool_result back referencing the tool_use id.
    messages = [{"role": "user", "content": "What's the weather in Tokyo?"},
                {"role": "assistant", "content": r.content},
                {"role": "user", "content": [{"type": "tool_result",
                                              "tool_use_id": tool_use.id,
                                              "content": "Sunny, 24C, light wind."}]}]
    final = client.messages.create(model=MODEL, max_tokens=200, tools=[get_weather], messages=messages)
    print("final answer:", final.content[0].text)

# CHALLENGE ANSWER:
#   1. "tool_use" = the model wants you to run a tool; "end_turn" = it answered.
#   2. Changing one char of tool_use_id gives a 400 "tool_result block(s) ... without
#      corresponding tool_use" error. The id is the only link between a request and
#      its result; with two parallel tool_use blocks, mismatched ids would pair
#      results to the wrong calls.


# ─── CHUNK 2B: the agent loop ────────────────────────────────────────────────
def agent_loop(task, tools, max_steps=10, token_budget=30_000):
    messages = [{"role": "user", "content": task}]
    step, total_tokens = 0, 0
    while step < max_steps and total_tokens < token_budget:
        r = client.messages.create(model=MODEL, max_tokens=1024, messages=messages, tools=tools)
        total_tokens += r.usage.input_tokens + r.usage.output_tokens
        print(f"Step {step}: stop_reason={r.stop_reason}")
        messages.append({"role": "assistant", "content": r.content})
        if r.stop_reason != "tool_use":
            print("Final:", r.content[0].text)
            break
        for block in r.content:
            if block.type == "tool_use":
                messages.append({"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": block.id,
                    "content": execute_tool(block.name, block.input)}]})
        step += 1
    else:
        print(f"Stopped by a limit: step={step}, tokens={total_tokens}")
    return step, total_tokens

# CHALLENGE ANSWER:
#   The stop_reason sequence on a 3-call task is the loop's pulse:
#     tool_use -> tool_use -> tool_use -> end_turn
#   Each "tool_use" is one act-then-observe cycle; "end_turn" is the model deciding
#   it has enough to answer.


# ─── CHUNK 2C: failure modes & safety valves ─────────────────────────────────
def broken_search_demo():
    global search
    good = search
    search = lambda query: "Error: search service unavailable (503)"  # noqa: E731
    print("--- always-failing search ---")
    agent_loop("Find today's top news story and save it to news.txt", [SEARCH, WRITE], max_steps=5)
    search = good

# CHALLENGE ANSWER:
#   1. With search always 503-ing, the model neither loops forever nor crashes: after
#      a couple of retries it gives up gracefully and reports it couldn't find the
#      story (sometimes offering to try later) — it does NOT fabricate a headline.
#   2. MAX_STEPS=50 + TOKEN_BUDGET=5_000 -> the TOKEN budget fires first (a few big
#      turns blow 5k fast). MAX_STEPS=3 + TOKEN_BUDGET=200_000 -> STEPS fires first.
#      Lesson: cap BOTH — steps guard short tasks, the token budget guards long ones.


# ─── MINI PROJECT: file agent with real tools ────────────────────────────────
def mini_project():
    with open("tasks.md", "w", encoding="utf-8") as f:
        f.write("- Met with design team\n- TODO: send the Q3 report to finance\n"
                "- Lunch\n- TODO: book the offsite venue\n")
    print("--- extract action items ---")
    agent_loop("Read the file 'tasks.md', extract only the action items, and write "
               "them to 'actions.txt'.", [READ, WRITE])
    print("\n--- missing file (must not crash) ---")
    agent_loop("Read the file 'does_not_exist.md' and summarize it.", [READ, WRITE])

# Done when: actions.txt holds only the two TODO lines, and the missing-file run
#   finishes with a sensible message (the read_file error string flows back as a
#   tool_result, so the model explains it instead of throwing a traceback).


if __name__ == "__main__":
    warmup_and_close_loop()
    print("\n=== 2B ===")
    agent_loop("Search for the inventor of Python, then search for the year Python 1.0 "
               "was released, then write both facts to python_facts.txt.", [SEARCH, WRITE])
    print("\n=== 2C ===")
    broken_search_demo()
    print("\n=== MINI PROJECT ===")
    mini_project()
