"""
Session 7 — Capstone · REFERENCE SKELETON

The capstone is design-your-own, so there is no single right answer. This is ONE
minimal agent that satisfies every 7B checklist box, to show how the pieces from
Sessions 2-6 snap together. Read it for the wiring, then build YOUR own thing.

Checklist shown here:
  [x] a REAL tool (file read/write actually touches disk — not a fake string).
      For a truly EXTERNAL tool, drop in Session 3's Brave search; it's a one-line add.
  [x] context compression at a token threshold      (maybe_compress, Session 3)
  [x] max_steps AND token budget enforced           (the loop header)
  [x] structured JSON log, one event per line       (log, Session 3)
  [x] retry with exponential backoff                (call_with_retry, Session 6)

Run with: python session7.py
"""

import env  # auto-loads .env — no manual `export` needed
import sys
import json
import time
import anthropic

sys.stdout.reconfigure(encoding="utf-8")

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"

MAX_STEPS = 12
TOKEN_BUDGET = 60_000
COMPRESS_THRESHOLD = 4000


# ─── Reused building blocks ──────────────────────────────────────────────────
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


def maybe_compress(messages, threshold=COMPRESS_THRESHOLD, log_file=None):
    approx = sum(len(str(m)) for m in messages) // 4
    if approx < threshold:
        return messages
    r = call_with_retry(lambda: client.messages.create(
        model=MODEL, max_tokens=512,
        messages=[{"role": "user", "content": f"Summarize in 2-3 sentences: {str(messages[:-4])}"}]))
    summary = r.content[0].text.strip()
    compressed = [{"role": "user", "content": f"[Earlier context]: {summary}"}] + messages[-4:]
    if log_file is not None:
        log(log_file, "compression", tokens_before=approx,
            tokens_after=sum(len(str(m)) for m in compressed) // 4)
    return compressed


# ─── Tools (real disk I/O — swap in Brave search for a real external tool) ────
def read_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: file '{filename}' not found."


def write_file(filename, content):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return f"wrote {filename}"


def execute_tool(name, args):
    if name == "read_file":
        return read_file(**args)
    if name == "write_file":
        return write_file(**args)
    return f"Error: unknown tool '{name}'"


TOOLS = [
    {"name": "read_file", "description": "Read a file from disk",
     "input_schema": {"type": "object", "properties": {"filename": {"type": "string"}},
                      "required": ["filename"]}},
    {"name": "write_file", "description": "Write text to a file on disk",
     "input_schema": {"type": "object",
                      "properties": {"filename": {"type": "string"}, "content": {"type": "string"}},
                      "required": ["filename", "content"]}},
]


# ─── The agent: compression + limits + logging + retry, all wired in ──────────
def run_agent(task, log_path="agent.log"):
    messages = [{"role": "user", "content": task}]
    step, total_tokens = 0, 0
    with open(log_path, "w", encoding="utf-8") as f:
        while step < MAX_STEPS and total_tokens < TOKEN_BUDGET:
            messages = maybe_compress(messages, log_file=f)
            r = call_with_retry(lambda: client.messages.create(
                model=MODEL, max_tokens=1024, messages=messages, tools=TOOLS))
            total_tokens += r.usage.input_tokens + r.usage.output_tokens
            log(f, "step", step=step, stop_reason=r.stop_reason, total_tokens=total_tokens)
            messages.append({"role": "assistant", "content": r.content})

            if r.stop_reason != "tool_use":
                print("Final:", r.content[0].text)
                log(f, "done", step=step, total_tokens=total_tokens)
                return
            for block in r.content:
                if block.type == "tool_use":
                    print(f"  -> {block.name}({block.input})")
                    messages.append({"role": "user", "content": [{
                        "type": "tool_result", "tool_use_id": block.id,
                        "content": execute_tool(block.name, block.input)}]})
            step += 1
        log(f, "halted_by_limit", step=step, total_tokens=total_tokens)
        print(f"Halted by a limit at step {step}, ~{total_tokens} tokens.")


if __name__ == "__main__":
    with open("notes.md", "w", encoding="utf-8") as f:
        f.write("- TODO: file the expense report\n- Coffee\n- TODO: renew the domain\n")
    run_agent("Read 'notes.md', extract only the action items, and write them to 'todo.txt'.")
