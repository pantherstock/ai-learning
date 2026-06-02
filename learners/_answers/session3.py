"""
Session 3 — Context is Your Budget · REFERENCE ANSWERS

One worked solution per chunk. Read AFTER you've tried session3.py yourself.
The 3B run makes ~18 API calls — it only fires under __main__, not on import.

Run with: python session3.py
"""

import env  # auto-loads .env — no manual `export` needed
import json
import time
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"


# ─── CHUNK 3A: summarize the old, keep the recent ────────────────────────────
def maybe_compress(messages, threshold=4000, log_file=None):
    approx = sum(len(str(m)) for m in messages) // 4  # ~4 chars per token
    if approx < threshold:
        return messages
    r = client.messages.create(model=MODEL, max_tokens=512, messages=[{
        "role": "user",
        "content": f"Summarize this conversation in 2-3 sentences: {str(messages[:-4])}"}])
    summary = r.content[0].text.strip()
    compressed = [{"role": "user", "content": f"[Earlier context]: {summary}"}] + messages[-4:]
    after = sum(len(str(m)) for m in compressed) // 4
    print(f"Compressed {len(messages) - 4} msgs -> 1 summary "
          f"(~{approx} -> ~{after} tokens, ratio {after / approx:.2f})")
    if log_file is not None:
        log(log_file, "compression", msgs_before=len(messages), msgs_after=len(compressed),
            tokens_before=approx, tokens_after=after)
    return compressed

# CHALLENGE ANSWER:
#   The ratio lands around 0.2-0.4: a 2-3 sentence summary stands in for a dozen
#   turns. The deeper the run, the bigger the win — more history collapses to one line.


# ─── CHUNK 3C: structured logging (defined here; used by 3A and 3B) ───────────
def log(f, event_type, **data):
    # One JSON object per line ("JSON Lines") — greppable, trivial to parse later.
    f.write(json.dumps({"ts": time.time(), "type": event_type, **data}) + "\n")
    f.flush()

# CHALLENGE ANSWER:
#   `Get-Content agent.log | Select-String compression` finds the first compression
#   line; its tokens_before/after show where the window first overflowed and how hard
#   it got squeezed — reconstructed entirely from the file, no console needed.


# ─── CHUNK 3B: the cost of forgetting ────────────────────────────────────────
def research_loop(first_message, steps=18, compress_threshold=1500, log_path="agent.log"):
    messages = [{"role": "user", "content": first_message}]
    with open(log_path, "w", encoding="utf-8") as f:
        for step in range(steps):
            messages = maybe_compress(messages, threshold=compress_threshold, log_file=f)
            tokens_in = sum(len(str(m)) for m in messages) // 4
            log(f, "step", step=step, tokens_in=tokens_in)
            print(f"Step {step}: ~{tokens_in} tokens in messages")

            if step == steps - 1:  # the deterministic recall probe
                messages.append({"role": "user",
                                 "content": "What was the reference number I gave you at the very start?"})

            r = client.messages.create(model=MODEL, max_tokens=1024, messages=messages)
            text = r.content[0].text
            messages.append({"role": "assistant", "content": r.content})

            if step == steps - 1:
                print(f"\nFinal answer: {text}")
                log(f, "final_answer", step=step, answer=text[:200])
            else:
                messages.append({"role": "user",
                                 "content": "Keep going — cover the next part of this topic in more depth."})

# CHALLENGE ANSWER:
#   The agent forgets. Once compression summarized the first turn away, it replies
#   that no reference number was given — it neither recalls RX-4417 nor invents one.
#   The fact was real, then it was gone. That is the tradeoff compression buys you.


# ─── MINI PROJECT: research agent with compression + logging + brakes ─────────
def mini_project():
    MAX_STEPS, TOKEN_BUDGET = 15, 50_000
    messages = [{"role": "user",
                 "content": "Research the history of reinforcement learning. We'll build "
                            "toward a 300-word summary — start with the earliest ideas."}]
    total_tokens, step = 0, 0
    with open("agent.log", "w", encoding="utf-8") as f:
        while step < MAX_STEPS and total_tokens < TOKEN_BUDGET:
            messages = maybe_compress(messages, threshold=4000, log_file=f)
            log(f, "step", step=step, tokens_in=sum(len(str(m)) for m in messages) // 4)
            r = client.messages.create(model=MODEL, max_tokens=1024, messages=messages)
            total_tokens += r.usage.input_tokens + r.usage.output_tokens
            messages.append({"role": "assistant", "content": r.content})
            messages.append({"role": "user", "content": "Continue with the next era in more depth."})
            step += 1
        messages.append({"role": "user", "content": "Now write a single ~300-word summary "
                                                    "of the history of reinforcement learning."})
        r = client.messages.create(model=MODEL, max_tokens=1024, messages=messages)
        with open("research.md", "w", encoding="utf-8") as out:
            out.write(r.content[0].text)
        log(f, "done", step=step, total_tokens=total_tokens)
    print(f"Stopped at step {step}, ~{total_tokens} tokens. Wrote research.md.")


if __name__ == "__main__":
    research_loop("Remember this reference number for later: RX-4417. Now help me "
                  "research the history of the internet.")
    # mini_project()  # uncomment for the capstone (another ~15 calls)
