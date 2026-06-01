"""
Session 7 — Capstone
Design and ship something real.

Before writing any code, complete DESIGN.md (see chunk 7A).
This file is a stub — you build it from scratch based on your design.
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import json
import time

client = anthropic.Anthropic()


# ─── WARM-UP: Design before you code ─────────────────────────────────────────
# Before opening your editor, answer these five questions in DESIGN.md.
# Actual answers — not "TBD".
#
#   1. Which architecture pattern from Session 4?
#   2. What external tools does it need?
#   3. Where does memory live — in-context, rolling summary, or vector store?
#   4. What are the three most likely failure modes?
#   5. What gets logged, and what would you look at first in a failed run?
#
# If you can't answer all five in 10 minutes, the design isn't ready yet.
# Come back here once DESIGN.md exists.


# ─── CHUNK 7A: Written design ─────────────────────────────────────────────────
# Save your design to DESIGN.md before writing any code.
# Cover: pattern choice, tools, memory strategy, failure modes, logging plan.
# The hardest design decision — write the tradeoff explicitly:
#   what you chose and what you gave up.


# ─── CHUNK 7B: Build it ───────────────────────────────────────────────────────
# Implement your design. Required checklist before marking complete:
#
#   [ ] At least one real external tool (not faked)
#   [ ] Context compression at a defined token threshold
#   [ ] max_steps and token budget enforced
#   [ ] Structured JSON log file
#   [ ] Retry with exponential backoff on API calls
#
# Write down any decision you made mid-build that wasn't in your design —
# those surprises are a key output of this chunk.
#
# ─── Your implementation starts here ─────────────────────────────────────────
#
# TODO: bring forward the helpers you've already built in earlier sessions —
#   - log(f, event_type, **data)          (Session 3)
#   - call_with_retry(fn, max_retries=3)  (Session 6)
# TODO: define your tools
# TODO: implement your tool execution function
# TODO: implement your agent loop
# TODO: add compression if your design calls for it


# ─── CHUNK 7C: Document it ────────────────────────────────────────────────────
# Write ARCHITECTURE.md and README.md.
#
# ARCHITECTURE.md covers:
#   - Which pattern and why you chose it over the others
#   - Where memory lives and when compression fires
#   - The failure modes you designed for
#   - One thing you'd do differently if rebuilding from scratch
#
# README.md covers:
#   - What the agent does (one paragraph)
#   - Setup (pip install, env vars)
#   - How to run it


# ─── CHUNK 7D: Ship it ────────────────────────────────────────────────────────
# git add .
# git commit -m "capstone: v1.0"
# git tag v1.0
# git push origin main --tags
#
# Then write your retrospective (4 sentences):
#   1. What clicked
#   2. What surprised you
#   3. What you'd do differently
#   4. One thing you want to learn next
#
# Write it here or in a RETRO.md:
# RETROSPECTIVE:
