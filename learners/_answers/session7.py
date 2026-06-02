"""
Session 7 — Capstone · REFERENCE SOLUTION (Dungeon Master agent)

One worked, runnable version of the capstone. Read it AFTER you've attempted your
own. It is deliberately minimal — just enough to show how the Sessions 2-6 pieces
snap together into a playable game an agent runs by itself.

The load-bearing idea: dice and state are computed HERE, in code. The model decides
WHEN to roll and HOW to react, but the file `game.json` is the only source of truth.
That is what makes this an agent reacting to a world, not a chatbot narrating one.

Pieces reused:
  agent loop (S2/S4) · MAX_STEPS + TOKEN_BUDGET brakes (S2) · JSON log (S3) ·
  call_with_retry (S6)

Run with:  python session7.py
Quit any time with Ctrl-C; the world persists in game.json.
"""

import env  # auto-loads .env — no manual `export` needed
import sys
import json
import time
import random
import anthropic

sys.stdout.reconfigure(encoding="utf-8")  # Windows console emits emoji-safe output

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"

STATE_FILE = "game.json"
LOG_FILE = "game.log"
MAX_STEPS_PER_TURN = 8
TOKEN_BUDGET = 100_000
MAX_HP = 20

DM_SYSTEM = (
    "You are the Dungeon Master of a short dungeon-crawl adventure. The player starts "
    "at 'entrance' with 20 hp and an empty inventory. Hidden in the dungeon is a "
    "'golden_key'; the player WINS by getting the golden_key into their inventory and "
    "reaching the location 'exit'. Narrate vividly in 2-4 sentences per turn. You MUST "
    "use tools to run the game: call get_state to see the world, roll_dice to resolve "
    "any risky action, and update_state to apply EVERY change to hp, location, or "
    "inventory — use the exact names 'golden_key' and 'exit'. Never invent dice results "
    "or items; only what the tools return is real. After narrating the turn, stop."
)


# ─── Reused building blocks (S3, S6) ─────────────────────────────────────────
def log(f, event_type, **data):
    f.write(json.dumps({"ts": time.time(), "type": event_type, **data}) + "\n")
    f.flush()


def call_with_retry(fn, max_retries=3):
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except anthropic.RateLimitError:
            if attempt == max_retries:
                raise
            time.sleep(2 ** attempt)
        except anthropic.APIStatusError as e:
            if 500 <= e.status_code < 600 and attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            raise


# ─── The world: a file, plus the tools that are its only physics ─────────────
def new_world():
    return {"hp": MAX_HP, "location": "entrance", "inventory": [], "turn": 0,
            "status": "playing"}


def load_state():
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_state():
    return json.dumps(load_state())


def roll_dice(sides=20):
    return str(random.randint(1, int(sides)))  # the result is the code's, not the model's


def update_state(hp_delta=0, location=None, add_items=None, remove_items=None):
    state = load_state()
    # integrity rules the model cannot narrate its way around:
    state["hp"] = min(MAX_HP, state["hp"] + int(hp_delta))     # clamp; no overheal
    if location is not None:
        state["location"] = location
    for item in (add_items or []):
        if item not in state["inventory"]:
            state["inventory"].append(item)
    for item in (remove_items or []):
        if item in state["inventory"]:                          # ignore phantom removes
            state["inventory"].remove(item)
    state["turn"] += 1
    save_state(state)
    return json.dumps(state)


def execute_tool(name, args):
    if name == "get_state":
        return get_state()
    if name == "roll_dice":
        return roll_dice(**args)
    if name == "update_state":
        return update_state(**args)
    return f"Error: unknown tool '{name}'"


TOOLS = [
    {"name": "get_state", "description": "Read the current game state (hp, location, inventory).",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "roll_dice", "description": "Roll an N-sided die to resolve a risky action.",
     "input_schema": {"type": "object",
                      "properties": {"sides": {"type": "integer", "description": "die size, e.g. 20"}}}},
    {"name": "update_state", "description": "Apply a change to hp, location, or inventory.",
     "input_schema": {"type": "object", "properties": {
         "hp_delta": {"type": "integer"},
         "location": {"type": "string"},
         "add_items": {"type": "array", "items": {"type": "string"}},
         "remove_items": {"type": "array", "items": {"type": "string"}}}}},
]


# ─── Inner loop: the agent resolving ONE turn on its own (S2/S4) ──────────────
def agent_loop(messages, system, tools, log_file, max_steps=MAX_STEPS_PER_TURN):
    tokens, narration = 0, ""
    for _ in range(max_steps):
        r = call_with_retry(lambda: client.messages.create(
            model=MODEL, max_tokens=1024, system=system, messages=messages, tools=tools))
        tokens += r.usage.input_tokens + r.usage.output_tokens
        messages.append({"role": "assistant", "content": r.content})
        narration = "".join(b.text for b in r.content if b.type == "text") or narration
        if r.stop_reason != "tool_use":
            break
        for block in r.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                if block.name in ("roll_dice", "update_state"):
                    log(log_file, block.name, args=block.input, result=result)
                messages.append({"role": "user", "content": [{
                    "type": "tool_result", "tool_use_id": block.id, "content": result}]})
    return {"tokens": tokens, "answer": narration}


# ─── Code-owned rules: who wins, who dies (not the model) ─────────────────────
def check_end(state):
    if state["hp"] <= 0:
        return "dead", "You have died. Game over."
    if state["location"] == "exit" and "golden_key" in state["inventory"]:
        return "won", "You escaped with the golden key. You win!"
    return None, None


# ─── Outer loop: the human in the loop, one typed action per turn ─────────────
def play():
    save_state(new_world())
    print("You stand at the entrance of a damp stone dungeon. A rusted gate creaks "
          "ahead. Type what you do.")
    messages = []
    total_tokens = 0
    with open(LOG_FILE, "w", encoding="utf-8") as logf:
        while total_tokens < TOKEN_BUDGET:
            action = input("\nYou: ").strip()       # <-- the human re-enters the loop HERE
            if not action:
                continue
            messages.append({"role": "user", "content": action})
            result = agent_loop(messages, DM_SYSTEM, TOOLS, logf)
            total_tokens += result["tokens"]
            print("\nDM:", result["answer"])
            log(logf, "turn", tokens=total_tokens, state=load_state())

            status, message = check_end(load_state())  # CODE decides the ending
            if status:
                state = load_state(); state["status"] = status; save_state(state)
                log(logf, "end", status=status)
                print("\n" + message)
                return
        print("\n[Session token budget reached — the dungeon fades.]")


if __name__ == "__main__":
    try:
        play()
    except KeyboardInterrupt:
        print("\n[You step out of the dungeon. The world is saved in game.json.]")
