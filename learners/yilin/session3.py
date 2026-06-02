"""
Session 3 — Context is Your Budget
Your history grows every turn. Learn to compress it — and feel what that costs.

Each chunk is CONCEPT -> TODO -> CHALLENGE (see session1.py).
Run with: python session3.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import json
import time

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"


# ─── WARM-UP: Watch the tokens climb ─────────────────────────────────────────
# Every turn you send the ENTIRE history back to the model. Add this line at the
# top of any multi-step loop, before the API call:
#   print(f"Step {step}: ~{sum(len(str(m)) for m in messages)//4} tokens in messages")
# The number grows EVERY step, even when nothing important happened. That growing
# number is your context window filling up — the problem this whole session solves.


# ─── CHUNK 3A: Summarize the old, keep the recent ────────────────────────────
# CONCEPT
#   When history gets too big, replace the OLDEST turns with a short summary and
#   keep only the last few verbatim. You trade precision for space, on purpose.
#   The "// 4" is the rule of thumb that ~4 characters ≈ 1 token.
#
# TODO: implement maybe_compress(messages, threshold=4000):
#   - approx = sum(len(str(m)) for m in messages) // 4   (rough token count)
#   - if approx < threshold: return messages unchanged
#   - else: summarize messages[:-4] in ONE API call into 2-3 sentences, then return
#       [{"role":"user","content": f"[Earlier context]: {summary}"}] + messages[-4:]
#   - print the message count collapsed and the token count before -> after
#
# CHALLENGE (answer in a comment):
#   Print the approx token count right before and right after each compression.
#   What's the rough compression ratio (after / before)?


def maybe_compress(messages, threshold=4000, log_file=None):
    approx = sum(len(str(m)) for m in messages) // 4
    if approx < threshold:
        return messages

    summary_prompt = [{
        "role": "user",
        "content": f"Summarize this conversation in 2-3 sentences: {str(messages[:-4])}",
    }]
    r = client.messages.create(model=MODEL, max_tokens=512, messages=summary_prompt)
    summary = r.content[0].text.strip()

    compressed = [{"role": "user", "content": f"[Earlier context]: {summary}"}] + messages[-4:]
    after = sum(len(str(m)) for m in compressed) // 4
    print(f"Compressed {len(messages) - 4} messages -> 1 summary "
          f"(~{approx} -> ~{after} tokens, ratio {after / approx:.2f})")
    if log_file is not None:
        log(log_file, "compression", msgs_before=len(messages),
            msgs_after=len(compressed), tokens_before=approx, tokens_after=after)
    return compressed

# CHALLENGE ANSWER:
#   Ratio lands around 0.2–0.4: a 2–3 sentence summary stands in for a dozen turns.
#   The deeper the run, the bigger the win — more history collapses into one line.


# ─── CHUNK 3B: The cost of forgetting ────────────────────────────────────────
# CONCEPT
#   Compression isn't free. A fact from the very FIRST turn can survive, vanish, or
#   get confabulated once it's been summarized away. There's no fix — only a
#   tradeoff you choose. This experiment is deterministic so anyone can reproduce it.
#
# TODO:
#   1. First user message, EXACTLY:
#        "Remember this reference number for later: RX-4417. Now help me research
#         the history of the internet."
#   2. Run an 18-step loop. Before every API call, run maybe_compress with a low
#      threshold (so compression definitely fires). Each step, nudge the model to
#      keep going so the history grows. No tools — plain text is enough to fill
#      the window.
#   3. LAST user message, EXACTLY:
#        "What was the reference number I gave you at the very start?"
#
# CHALLENGE (answer in a comment):
#   Does the agent return RX-4417, admit it doesn't know, or invent a number? Paste it.


def log(f, event_type, **data):
    # 3C: one JSON object per line ("JSON Lines") — greppable, trivial to parse.
    f.write(json.dumps({"ts": time.time(), "type": event_type, **data}) + "\n")
    f.flush()


def research_loop(first_message, steps=18, compress_threshold=1500, log_path="agent.log"):
    messages = [{"role": "user", "content": first_message}]

    with open(log_path, "w") as f:
        for step in range(steps):
            messages = maybe_compress(messages, threshold=compress_threshold, log_file=f)
            tokens_in = sum(len(str(m)) for m in messages) // 4
            log(f, "step", step=step, tokens_in=tokens_in)

            # Last step: the deterministic recall probe.
            if step == steps - 1:
                messages.append({
                    "role": "user",
                    "content": "What was the reference number I gave you at the very start?",
                })

            r = client.messages.create(model=MODEL, max_tokens=1024, messages=messages)
            text = r.content[0].text
            print(f"Step {step}: ~{tokens_in} tokens in messages")
            messages.append({"role": "assistant", "content": r.content})

            if step == steps - 1:
                print(f"\nFinal answer: {text}")
                log(f, "final_answer", step=step, answer=text[:200])
            else:
                messages.append({
                    "role": "user",
                    "content": "Keep going — cover the next part of this topic in more depth.",
                })


research_loop(
    "Remember this reference number for later: RX-4417. Now help me research "
    "the history of the internet."
)

# CHALLENGE ANSWER:
#   The agent forgot. Once compression summarized the first turn away, it replied:
#   "You didn't give me a reference number — your first message was a summary of
#    earlier context." It didn't recall RX-4417 and didn't invent one; it confidently
#   denied ever seeing it. The fact was real, then it was gone. That's the tradeoff.


# ─── CHUNK 3C: Structured logging ────────────────────────────────────────────
# CONCEPT
#   When an 18-step run misbehaves, the console scrollback is useless. One JSON
#   object per line lets you reconstruct exactly what happened, later, with grep.
#   (log() is defined above and already wired into research_loop + maybe_compress.)
#
# TODO: log(f, event_type, **data) appends one line:
#       f.write(json.dumps({"ts": time.time(), "type": event_type, **data}) + "\n")
#   Open agent.log once, pass the handle in, and log every step (step, tokens_in)
#   and every compression event (msgs_before, msgs_after, tokens_before/after).
#
# CHALLENGE (answer in a comment):
#   Using ONLY agent.log (not the console), find the FIRST step where compression
#   fired and its ratio. Try:  Get-Content agent.log | Select-String compression
#
# CHALLENGE ANSWER:
#   The "compression" lines carry tokens_before/after, so the first one shows where
#   the window first overflowed and how hard it got squeezed — all without the console.


# ─── MINI PROJECT: Research agent with compression + logging ─────────────────
# Everything combined, with real brakes. Push to GitHub when the checklist passes.
#
#   ☐ maybe_compress(messages, threshold=4000) called before EVERY API call.
#   ☐ Loop stops at MAX_STEPS = 15 OR TOKEN_BUDGET = 50_000 (whichever first),
#     counting real tokens via r.usage.input_tokens + r.usage.output_tokens.
#   ☐ Every step and every compression event written to agent.log (3C).
#   ☐ Task: research the history of reinforcement learning across the loop, then
#     write a ~300-word summary to research.md with plain open() (no tools needed).
#
# Done when: research.md exists with a ~300-word summary, agent.log has one JSON
#   line per event, and you can point to the step where compression first fired.


def mini_project():
    MAX_STEPS = 15
    TOKEN_BUDGET = 50_000
    messages = [{
        "role": "user",
        "content": "Research the history of reinforcement learning. We'll build "
                   "toward a 300-word summary — start with the earliest ideas.",
    }]
    total_tokens = 0
    step = 0

    with open("agent.log", "w") as f:
        while step < MAX_STEPS and total_tokens < TOKEN_BUDGET:
            messages = maybe_compress(messages, threshold=4000, log_file=f)
            log(f, "step", step=step, tokens_in=sum(len(str(m)) for m in messages) // 4)

            r = client.messages.create(model=MODEL, max_tokens=1024, messages=messages)
            total_tokens += r.usage.input_tokens + r.usage.output_tokens
            messages.append({"role": "assistant", "content": r.content})
            messages.append({"role": "user", "content": "Continue with the next era in more depth."})
            step += 1

        # Capstone: one final summary, written to disk with plain open() — no tools.
        messages.append({"role": "user", "content": "Now write a single ~300-word summary "
                                                     "of the history of reinforcement learning."})
        r = client.messages.create(model=MODEL, max_tokens=1024, messages=messages)
        with open("research.md", "w") as out:
            out.write(r.content[0].text)
        log(f, "done", step=step, total_tokens=total_tokens)

    print(f"Stopped at step {step}, ~{total_tokens} tokens. Wrote research.md.")


# mini_project()  # uncomment to run the capstone
