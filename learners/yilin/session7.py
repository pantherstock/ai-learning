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

import env  # auto-loads .env — no manual `export` needed
import anthropic
import json
import time
import random

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"

STATE_FILE = "game.json"
LOG_FILE = "game.log"
MAX_STEPS_PER_TURN = 8      # inner-loop brake: tool calls allowed to resolve ONE turn
TOKEN_BUDGET = 100_000      # whole-session brake across every turn


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
#
# CHALLENGE (write the answer in a comment):
#   Call roll_dice(20) five times and print the results. Then ask the model, with no
#   tools, "roll a d20 for me" five times and print those. Which set would you trust
#   to run a fair game, and why does it matter that the roll comes from code?


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
#
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
#
# CHALLENGE (write the answer in a comment):
#   Play 3 turns, then open game.log. Find a turn where the model called roll_dice and
#   then update_state based on the result; paste those two lines. That sequence — model
#   rolls, sees a number it didn't choose, then changes the world to match — is the
#   agent reacting to its environment. Then name the exact line where the human
#   re-enters the OUTER loop.


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
