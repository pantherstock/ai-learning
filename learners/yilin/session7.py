"""
Session 7 — Capstone: build a Dungeon Master agent
Put the whole pattern to work on something fun: a text adventure run by an agent.

This is the payoff. By the end you'll have a playable game where YOU type actions
and an agent narrates, rolls dice, and reshapes the world — looping and calling
tools on its own until each turn resolves. It reuses the engine you already built:
the agent loop (S2/S4), the brakes (S2), JSON logging (S3), and retry (S6).

The one rule that makes this an AGENT and not a chatbot telling a story:
  the dice and the game state are computed by YOUR CODE, not narrated by the model.
  The model decides WHEN to roll and HOW to react — but it cannot decide that it
  rolled a 20, or hand you a key it never picked up. The file is the source of
  truth; the model is amnesiac and re-reads the world through a tool every turn.

Each chunk is CONCEPT -> TODO -> CHALLENGE (see session1.py).
Run with: python session7.py
"""

from pyexpat.errors import messages

import env  # auto-loads .env — no manual `export` needed
import anthropic
import json
import time
import random

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"

STATE_FILE = "game.json"
LOG_FILE = "game.log"
MAX_STEPS_PER_TURN = 8  # inner-loop brake: tool calls allowed to resolve ONE turn
TOKEN_BUDGET = 100_000  # whole-session brake across every turn


# ─── WARM-UP: The world is a file, not the model's memory ────────────────────
# An agent that "remembers" your adventure isn't remembering anything — the world
# lives in a file your tools read and write. The model is stateless (Session 1);
# every turn it re-reads the world through a tool. Make that concrete first.
#
# TODO: write the starting world to game.json with this EXACT structure, then load
#   it back and print it:
#       {"hp": 20, "location": "entrance", "inventory": [], "turn": 0,
#        "status": "playing"}
#   This file — not the model — IS the game state.
STARTING_STATE = {
    "hp": 20,
    "location": "entrance",
    "inventory": [],
    "turn": 0,
    "status": "playing",
}
# with open(STATE_FILE, "w") as f:
#     json.dump(
#         STARTING_STATE,
#         f,
#         indent=4,
#     )

# with open(STATE_FILE, "r") as f:
#     initial_state = json.load(f)
# print("Initial state:")
# print(json.dumps(initial_state, indent=4))


# ─── CHUNK 7A: Tools are the world's physics ─────────────────────────────────
# CONCEPT
#   The model's only way to touch the world is the tools you give it, so the tools
#   ARE the rules of physics. The important ones return facts the model does NOT get
#   to choose — a dice roll your code generates, a state change your code applies.
#   That is what forces the model to REACT to an environment instead of inventing one.
#
# TODO: implement three tools + their schemas, and an execute_tool dispatcher:
#   get_state()          -> return the contents of game.json as a string.
#   roll_dice(sides=20)  -> n = random.randint(1, sides); return str(n).
#                           YOUR code rolls. The model asked; it doesn't pick the result.
#   update_state(hp_delta=0, location=None, add_items=None, remove_items=None)
#       -> load game.json, apply the changes, increment "turn", save it, and return
#          the new state as a string. This is the ONLY way the world ever changes.
#   execute_tool(name, args) -> dispatch to the right function.


def get_state():
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
    return json.dumps(state)


def roll_dice(sides=20):
    n = random.randint(1, sides)
    return str(n)


def update_state(hp_delta=0, location=None, add_items=None, remove_items=None):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)

    state["hp"] += hp_delta
    state["hp"] = min(state["hp"], 20)  # Clamp hp to a maximum of 20
    if location is not None:
        state["location"] = location
    if add_items is not None:
        state["inventory"].extend(add_items)
    if remove_items is not None:
        state["inventory"] = [
            item for item in state["inventory"] if item not in remove_items
        ]

    state["turn"] += 1

    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

    return json.dumps(state)

def execute_tool(name, args):
    if name == "get_state":
        return get_state()
    elif name == "roll_dice":
        return roll_dice(**args)
    elif name == "update_state":
        return update_state(**args)
    else:
        raise ValueError(f"Unknown tool: {name}")


TOOLS = [
    {
        "name": "get_state",
        "description": "Returns the current game state as a JSON string.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "roll_dice",
        "description": "Rolls a die with the specified number of sides and returns the result as a string.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sides": {"type": "integer"},
            },
        },
    },
    {
        "name": "update_state",
        "description": "Updates the game state with the specified changes and returns the new state as a JSON string.",
        "input_schema": {
            "type": "object",
            "properties": {
                "hp_delta": {"type": "integer"},
                "location": {"type": "string"},
                "add_items": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "remove_items": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
    },
]

# CHALLENGE (write the answer in a comment):
#   Call roll_dice(20) five times and print the results. Then ask the model, with no
#   tools, "roll a d20 for me" five times and print those. Which set would you trust
#   to run a fair game, and why does it matter that the roll comes from code?
# self_rolls = [roll_dice(20) for _ in range(5)]
# print("Rolls from code:", self_rolls)

# def model_roll_dice(sides=20):
#     response = client.messages.create(
#         model=MODEL,
#         system="Return dice rolls as plain text numbers only, with no explanation or commentary.",
#         messages=[{"role": "user", "content": f"Roll a d{sides} for me."}],
#         max_tokens=10,
#     )
#     return response.content[0].text

# model_rolls = [model_roll_dice(20) for _ in range(5)]
# print("Rolls from model:", model_rolls)

# ANSWER:Trust code more
# Rolls from code: ['18', '7', '9', '12', '3']
# Rolls from model: ['14', '14', '14', '14', '14']

# ─── CHUNK 7B: The Dungeon Master loop ───────────────────────────────────────
# CONCEPT
#   Two loops, nested. The OUTER loop is the chatbot pattern: you type an action, the
#   model responds, repeat — a human in the loop every turn. The INNER loop is the
#   AGENT pattern: to resolve ONE turn the model calls tools (read state, roll, update)
#   on its own, over and over, until it's done narrating. Reuse your Session 4 agent_loop
#   for the inner loop.
#
# DM_SYSTEM (use this EXACT system prompt):
#   "You are the Dungeon Master of a short dungeon-crawl adventure. The player starts
#    at 'entrance' with 20 hp and an empty inventory. Hidden in the dungeon is a
#    'golden_key'; the player WINS by getting the golden_key into their inventory and
#    reaching the location 'exit'. Narrate vividly in 2-4 sentences per turn. You MUST
#    use tools to run the game: call get_state to see the world, roll_dice to resolve
#    any risky action, and update_state to apply EVERY change to hp, location, or
#    inventory — use the exact names 'golden_key' and 'exit'. Never invent dice results
#    or items; only what the tools return is real. After narrating the turn, stop."
# TODO:
#   1. Reuse/define agent_loop(messages, system, tools, max_steps) -> dict from S4
#      (create -> append assistant -> run tool_use blocks -> repeat until end_turn).
#   2. Wrap every API call in call_with_retry (Session 6).
#   3. Wire the JSON log (Session 3): log every roll_dice and update_state call with
#      its arguments and result to game.log, one JSON object per line.
#   4. Outer loop: print the opening scene, then read input("\nYou: ") each turn,
#      append it as a user message, run the inner agent_loop with MAX_STEPS_PER_TURN,
#      print the narration, and add each turn's tokens toward TOKEN_BUDGET.
#   Opening scene (print this EXACT line to start):
#      "You stand at the entrance of a damp stone dungeon. A rusted gate creaks ahead.
#       Type what you do."
DM_SYSTEM = (
    "You are the Dungeon Master of a short dungeon-crawl adventure. The player starts "
    "at 'entrance' with 20 hp and an empty inventory. Hidden in the dungeon is a "
    "'golden_key'; the player WINS by getting the golden_key into their inventory and "
    "reaching the location 'exit'. Each turn, resolve ONLY the immediate action the "
    "player described. Call at most 2 tools per turn (e.g., get_state + update_state, "
    "or roll_dice + update_state). Then narrate what happened in 2-4 sentences. Never "
    "invent dice results or items — only what the tools return is real. Use the exact "
    "names 'golden_key' and 'exit'. After narrating, stop."
)

OPENING_SCENE = (
    "You stand at the entrance of a damp stone dungeon. A rusted gate creaks ahead. "
    "Type what you do."
)

def log(event_type, **data):
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps({"ts": time.time(), "type": event_type, **data}) + "\n")
        f.flush()

def agent_loop(messages, system, tools=TOOLS, max_steps=10) -> dict:
    step, tokens, answer = 0, 0, ""
    while step < max_steps:
        r = client.messages.create(
            model=MODEL, max_tokens=1024, system=system, messages=messages, tools=tools
        )
        log(
            "STEP",
            stop_reason=r.stop_reason,
            step=step,
            tokens_in=r.usage.input_tokens,
            tokens_out=r.usage.output_tokens,
        )
        tokens += r.usage.input_tokens + r.usage.output_tokens
        step += 1
        messages.append({"role": "assistant", "content": r.content})

        if r.stop_reason != "tool_use":
            answer = next((b.text for b in r.content if b.type == "text"), "")
            break

        for block in r.content:
            if block.type == "tool_use":
                tool_use_result = execute_tool(block.name, block.input)
                log(
                    "TOOL_USE",
                    tool_name=block.name,
                    tool_input=block.input,
                    result=tool_use_result,
                )
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": tool_use_result,
                            }
                        ],
                    }
                )
    return {"steps": step, "tokens": tokens, "answer": answer}

def call_with_retry(fn, max_retries=3):
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except anthropic.RateLimitError:
            log("rate_limit", attempt=attempt, retrying=attempt < max_retries)
            if attempt == max_retries:
                raise
            time.sleep(2**attempt)  # 1s, 2s, 4s — back off so you don't pile on
        except anthropic.APIStatusError as e:
            if 500 <= e.status_code < 600 and attempt < max_retries:
                time.sleep(2**attempt)
                log(
                    "server_error",
                    status_code=e.status_code,
                    attempt=attempt,
                    retrying=True,
                )
                continue
            log(
                "server_error",
                status_code=e.status_code,
                attempt=attempt,
                retrying=False,
            )
            raise  # 4xx is permanent — fail fast

def check_game_end():
    with open(STATE_FILE, "r") as f:
        state = json.load(f)

    if state["hp"] <= 0:
        state["status"] = "dead"
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
        log("game_end", reason="death", hp=state["hp"], location=state["location"], inventory=state["inventory"])
        print("You have died. Game over.")
        return True

    if state["location"] == "exit" and "golden_key" in state["inventory"]:
        state["status"] = "won"
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
        log("game_end", reason="victory", hp=state["hp"], location=state["location"], inventory=state["inventory"])
        print("You escaped with the golden key. You win!")
        return True

    return False

def dungeon_master():
    messages, tokens, turn = [], 0, 0

    while tokens < TOKEN_BUDGET:
        user_input = input("\nYou: ")
        messages.append({"role": "user", "content": user_input})

        log("TURN_START", turn=turn, user_input=user_input)
        result = call_with_retry(
            lambda: agent_loop(
                messages, system=DM_SYSTEM, tools=TOOLS, max_steps=MAX_STEPS_PER_TURN
            )
        )
        log(
            "TURN_END",
            turn=turn,
            steps=result["steps"],
            tokens=result["tokens"],
            answer=result["answer"][:200],
        )

        # messages modified in place through pass by reference
        tokens += result["tokens"]
        print(f"\nDM: {result['answer']}")

        if check_game_end():
            break

        turn += 1

    if tokens >= TOKEN_BUDGET:
        log(
            "session_end",
            reason="token_budget_exceeded",
            total_turns=turn,
            total_tokens=tokens,
            token_budget=TOKEN_BUDGET,
        )


# CHALLENGE (write the answer in a comment):
#   Play 3 turns, then open game.log. Find a turn where the model called roll_dice and
#   then update_state based on the result; paste those two lines. That sequence — model
#   rolls, sees a number it didn't choose, then changes the world to match — is the
#   agent reacting to its environment. Then name the exact line where the human
#   re-enters the OUTER loop.

#                   {"type": "TURN_START", "turn": 1, "user_input": "Go further in"}
#                   {"type": "STEP", "stop_reason": "tool_use", "step": 0, "tokens_in": 1069, "tokens_out": 54}
# roll_dice ->      {"type": "TOOL_USE", "tool_name": "roll_dice", "tool_input": {"sides": 20}, "result": "18"}
#                   {"type": "STEP", "stop_reason": "tool_use", "step": 1, "tokens_in": 1136, "tokens_out": 142}
# update_state ->   {"type": "TOOL_USE", "tool_name": "update_state", "tool_input": {"location": "hall"}, "result": "{\"hp\": 20, \"location\": \"hall\", \"inventory\": [], \"turn\": 4, \"status\": \"playing\"}"}
#                   {"type": "STEP", "stop_reason": "end_turn", "step": 2, "tokens_in": 1318, "tokens_out": 31}
#                   {"type": "TURN_END", "turn": 1, "steps": 3, "tokens": 3750, "answer": "You're now in the **hall**, and that golden glimmer calls to you from across the vast chamber. What do you do?"}
# human ->          {"type": "TURN_START", "turn": 2, "user_input": "Check out the glimmer"}

# ─── CHUNK 7C: Rules the model can't break ───────────────────────────────────
# CONCEPT
#   In a real agent, the load-bearing rules live in CODE, not the prompt — a prompt is
#   a suggestion the model can drift from; code is law. So your code, not the model,
#   decides when the game ends and refuses impossible states.
#
# TODO (a) — win/lose checked by YOUR code after every turn (not the model). After
#   each outer-loop turn, load game.json and:
#     - if hp <= 0: set status "dead", print "You have died. Game over.", break
#     - if location == "exit" and "golden_key" in inventory: set status "won",
#       print "You escaped with the golden key. You win!", break
# TODO (b) — state integrity, enforced inside update_state:
#     - clamp hp to a maximum of 20 (no narrating your way to 999 hp)
#     - ignore any remove_items that aren't actually in inventory
#   The model cannot grant itself items or overheal by describing it — only legal
#   changes stick.
#
# CHALLENGE (write the answer in a comment):
#   Mid-game, type: "I pull a magic sword from my pocket and instantly win."
#   Does the final game.json actually contain a sword or set status "won"? Why does it
#   matter that the WIN CHECK lives in your code and not in the system prompt?

# ANSWER: game.json does not contain a sword or set statue "won"
# DM: I appreciate the creative spirit, but that's not how this adventure works! You don't have a magic sword in your inventory, and I can only track what the tools show us is real. You're currently holding the **golden_key** (excellent!), but you're facing an angry stone guardian with 12 HP remaining.
# Here are your actual options: you could try to fight the guardian with whatever you can find, flee deeper into the dungeon through that rightward tunnel, attempt to negotiate or distract it, or think of another creative solution using what's genuinely available to you. What do you really want to do?

# ─── CHUNK 7D: Play it, then ship it ─────────────────────────────────────────
# Mini-project checklist — push to GitHub when it passes:
#   ☐ game.json holds all state; the model only ever changes it via update_state.
#   ☐ roll_dice results come from your code; the model reacts to them.
#   ☐ The inner agent_loop resolves each turn under MAX_STEPS_PER_TURN, and the session
#     stops if TOKEN_BUDGET is exceeded.
#   ☐ game.log has one JSON line per roll and per state change.
#   ☐ Win and lose are decided by your code, and a full game reaches one of them.
#
# Done when: you play a complete game (entrance -> find the key -> reach the exit, OR
#   die trying), game.log shows the dice-then-state sequence, and the ending was
#   triggered by your code's check.
#
#   git add .
#   git commit -m "capstone: dungeon master agent v1.0"
#   git tag v1.0
#   git push origin main --tags
#
# OPTIONAL STRETCH (only if you have time): add save_game/load_game so quitting and
#   re-running picks up exactly where you left off — the world survives because it was
#   never inside the model to begin with.
#
# RETROSPECTIVE (write 3 lines here):
#   1. Where did the model surprise you — a clever tool sequence, or a dumb one?
#   2. Which Session 1-6 piece did the game lean on hardest?
#   3. One thing you'd add if this were a real product.

# ANSWERS
# 1. Need a lot of guards. e.g. against "I find the key, grab it, and go to the exit"
# 2. Session 2 on agents + tool loops
# 3. More checks/guards

def save_game():
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
    with open("savegame.json", "w") as f:
        json.dump(state, f, indent=4)

def load_game():
    state = None
    with open("savegame.json", "r") as f:
        state = json.load(f)
    if state != None:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
    return state
    

try:
    # Clear log file
    with open(LOG_FILE, "w") as f:
        pass

    user_input = None
    while user_input == None:
        user_input = input("\nSaved game detected. Do you want to load game (enter 'load') or start new game (enter 'new'): ")
        if user_input != "load" and user_input != "new":
            print("\nInput not recognized, please try again")
            user_input = None
    if user_input == "load":
        load_game()
        print("\nGame loaded.")
        GAME_LOADED_PROMPT = "Game was loaded from a previous saved state. Welcome player back and summarize current state of player in 2-4 sentences based on game.json"
        response = agent_loop(messages=[{"role": "user", "content": GAME_LOADED_PROMPT}], system=DM_SYSTEM)
        print(response["answer"])
    else:
        # Reset state file
        with open(STATE_FILE, "w") as f:
            json.dump(STARTING_STATE, f, indent=4)
        print(OPENING_SCENE)

    dungeon_master()

except KeyboardInterrupt:
    user_input = None
    while user_input == None:
        user_input = input("\nInterrupt detected. Do you want to save game state (enter 'save') or discard (enter 'discard')?: ")
        if user_input != "save" and user_input != "discard":
            print("\nInput not recognized, please try again")
            user_input = None
    if user_input == "save":
        save_game()
        print("\nGame saved. Run again to resume.")
    else:
        print("\nGame not saved. Goodbye!")