"""
Section B — Advanced Agentic Patterns
Four patterns beyond Session 4: reflection, parallel fan-out, routing, human-in-the-loop.

Each section is CONCEPT -> TODO -> CHALLENGE (see session1.py).
Prerequisites: complete Session 4 first.
Run with: python patterns.py
"""

import env  # auto-loads .env — no manual `export` needed
import anthropic
import threading
import time

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# ─── WARM-UP: Reflection in 3 lines ──────────────────────────────────────────
# TODO: make one call to get first_answer for "Explain what an API is in one
# sentence.", then a second call showing that answer and asking: "Critique this
# explanation in one sentence. What's imprecise or misleading?" Print both. One
# extra call already makes the output better — that's the whole idea of reflection.


def llm_call(messages):
    response = client.messages.create(model=MODEL, messages=messages, max_tokens=100)
    return response.content


# messages = []
# first_answer = llm_call([{"role": "user", "content": "Explain what an API is in one sentence."}])
# messages.append({"role": "assistant", "content": first_answer})
# critique = llm_call(messages + [{"role": "user", "content": "Critique this explanation in one sentence. What's imprecise or misleading?"}])
# print("First answer:", first_answer)
# print("Critique:", critique)


# ─── SECTION B1: Reflection loop ─────────────────────────────────────────────
# CONCEPT
#   Draft -> critique -> revise, repeating until the model rates its own output
#   "good" or a max-iteration cap is hit. The stopping criterion is what keeps it
#   from looping forever.
#
# TODO: implement reflection_loop(task, max_iterations=3) -> str:
#   - draft an answer
#   - each iteration: ask the model to rate it. Use this EXACT rubric in the prompt:
#       "Rate the draft. If it is good, reply exactly DONE. Otherwise reply
#        NEEDS-WORK: <one sentence on what's wrong>."
#     If it replies DONE, break; else ask it to rewrite addressing the critique.
#   - print whether each iteration continued or stopped; return the final draft.
#
# CHALLENGE (write the answers in comments):
#   Run reflection_loop on this EXACT task 3 times: "Write a 2-sentence product
#   description for a waterproof hiking backpack." How many iterations until DONE
#   each time? Is it consistent? When is the extra token cost of reflection worth it?
#
# ANSWER:
#   1 iteration until DONE all 3 times — consistent across runs.
#   Note: the rating call always fires even when DONE on iteration 1, so the cost
#   floor is 1 draft + 1 rating, not just 1 draft. The rewrite is what's skipped.
#   The backpack task is actually a bad test: it's simple enough that the model
#   rates itself DONE immediately, so reflection adds a call with no quality gain.
#   Extra token cost is worth it when the first draft is reliably imperfect —
#   complex creative writing, code refactoring, persuasive text — especially when
#   you have a clear, evaluable rubric. Not worth it for simple factual or
#   descriptive tasks where the draft is almost always acceptable.

# def reflection_loop(task, max_iterations=3) -> str:
#     messages = [{"role": "user", "content": task}]
#     draft = llm_call(messages)
#     messages.append({"role": "assistant", "content": draft})
#     print("Draft:", draft)

#     for i in range(max_iterations):
#         rating = llm_call(messages + [{"role": "user", "content": "Rate the draft. If it is good, reply exactly DONE. Otherwise reply NEEDS-WORK: <one sentence on what's wrong>."}])
#         rating = rating[0].text.strip()
#         print(f"Iteration {i+1} rating:", rating)

#         if rating == "DONE":
#             print("Stopping criterion met. Final draft accepted.")
#             break
#         else:
#             critique = rating.replace("NEEDS-WORK:", "")
#             print(f"Critique received: {critique}")
#             draft = llm_call(messages + [{"role": "user", "content": f"Rewrite the draft addressing this critique: {critique}"}])
#             print(f"Iteration {i+1} revised draft:", draft)

#     return draft

# for _ in range(3):
#     final_description = reflection_loop("Write a 2-sentence product description for a waterproof hiking backpack.")
#     print("Final product description:", final_description)
#     print("-" * 50)

# ─── SECTION B2: Parallel fan-out ────────────────────────────────────────────
# CONCEPT
#   Fork work to N independent subagents in parallel threads — each with its own
#   context — then merge with one synthesis call. threading.Thread is simpler than
#   asyncio here. The speedup is rarely exactly Nx.
#
# TODO: implement run_subagent(subtask, results, key) — a SINGLE call (not a loop)
#   storing its answer in results[key]. Use these EXACT three subtasks, one per
#   thread: "Summarize Django for REST APIs", "Summarize FastAPI for REST APIs",
#   "Summarize Flask for REST APIs". Join the threads, then make ONE synthesis call
#   that merges results into a comparison.
#
# CHALLENGE (write the answers in comments):
#   Time the parallel run, then run the SAME three subtasks sequentially and time
#   that. What's the speedup — exactly 3x, less, or more? What caps it (think about
#   the synthesis call and per-call latency)?
#
# ANSWER: ~1.7x (parallel: 3.54s, sequential: 5.96s) — less than 3x. Two caps:
#   1. Synthesis call runs sequentially in both cases, adding equal overhead that
#      dilutes the ratio: speedup = (3t + s) / (t_slowest + s). The larger s is
#      relative to t, the closer to 1x the speedup gets.
#   2. Parallel run waits for the SLOWEST thread, not the average. API latency
#      varies per call, so one slow response drags the whole parallel batch.

# def run_subagent(subtask, results, key):
#     response = client.messages.create(
#         model=MODEL,
#         messages=[{"role": "user", "content": subtask}],
#         max_tokens=100
#     )
#     results[key] = response.content

# results = {}
# subtasks = [
#     "Summarize Django for REST APIs",
#     "Summarize FastAPI for REST APIs",
#     "Summarize Flask for REST APIs"
# ]
# threads = []
# start_time = time.time()
# for i, subtask in enumerate(subtasks):
#     thread = threading.Thread(target=run_subagent, args=(subtask, results, i))
#     threads.append(thread)
#     thread.start()

# # Wait for all threads to complete
# for thread in threads:
#     thread.join()
# synthesis_input = "\n".join([f"Subtask {i+1}: {results[i]}" for i in range(len(subtasks))])
# synthesis_response = client.messages.create(
#     model=MODEL,
#     messages=[{"role": "user", "content": f"Compare these API frameworks based on the following summaries:\n{synthesis_input}"}],
#     max_tokens=150
# )
# print("Synthesis response:", synthesis_response.content)
# end_time = time.time()
# print(f"Total time taken (parallel): {end_time - start_time:.2f} seconds")

# start_time = time.time()
# sequential_results = []
# for subtask in subtasks:
#     response = client.messages.create(
#         model=MODEL,
#         messages=[{"role": "user", "content": subtask}],
#         max_tokens=100
#     )
#     sequential_results.append(response.content)
# synthesis_input = "\n".join([f"Subtask {i+1}: {sequential_results[i]}" for i in range(len(subtasks))])
# synthesis_response = client.messages.create(
#     model=MODEL,
#     messages=[{"role": "user", "content": f"Compare these API frameworks based on the following summaries:\n{synthesis_input}"}],
#     max_tokens=150
# )
# print("Synthesis response (sequential):", synthesis_response.content)
# end_time = time.time()
# print(f"Total time taken (sequential): {end_time - start_time:.2f} seconds")

# ─── SECTION B3: Router pattern ──────────────────────────────────────────────
# CONCEPT
#   A fast, cheap classifier reads the request and routes it to a specialist. The
#   router does NO domain work — classification only. The craft is fixing one
#   category's misroutes without creating new ones.
#
# TODO: implement classify_intent(user_message) -> one of research/code/summarize/
#   other (a max_tokens=10 call). Implement research_agent / code_agent /
#   summarize_agent as plain single Claude calls (no tools needed — the point is
#   routing, not agent sophistication), and route(user_message) dispatching on the
#   intent, with a plain call for "other".
#
# CHALLENGE (write the answers in comments) — run route() on these EXACT 8 inputs
# and log which specialist each hit:
#   "What's the latest version of Python?"            (expect research)
#   "Write a function to reverse a linked list."      (expect code)
#   "Summarize this paragraph: <paste any 3 lines>"   (expect summarize)
#   "Fix the bug in my for loop"                      (expect code)
#   "Who won the 2022 World Cup?"                     (expect research)
#   "tl;dr the plot of Hamlet"                        (expect summarize)
#   "What's the weather like?"                        (other)
#   "Tell me a joke"                                  (other)
#   Which input gets misrouted? Tweak the classifier prompt to fix it — does your
#   fix break any of the others?
# ANSWER: All routed correctly but needed to tweak the classifier prompt to add system prompt to enforce output as only a single word for the classifications

# def classify_intent(user_message):
#     response = client.messages.create(
#         model=MODEL,
#         system="Answer with only one word from this list: research, code, summarize, other.",
#         messages=[{"role": "user", "content": f"Classify the intent of this message into one of: research, code, summarize, other.\nMessage: {user_message}"}],
#         max_tokens=10
#     )
#     return response.content[0].text.strip().lower()

# def research_agent(user_message):
#     response = client.messages.create(
#         model=MODEL,
#         messages=[{"role": "user", "content": f"Research and answer this question: {user_message}"}],
#         max_tokens=100
#     )
#     return response.content

# def code_agent(user_message):
#     response = client.messages.create(
#         model=MODEL,
#         messages=[{"role": "user", "content": f"Write code to solve this problem: {user_message}"}],
#         max_tokens=100
#     )
#     return response.content

# def summarize_agent(user_message):
#     response = client.messages.create(
#         model=MODEL,
#         messages=[{"role": "user", "content": f"Summarize this text: {user_message}"}],
#         max_tokens=100
#     )
#     return response.content

# def route(user_message):
#     intent = classify_intent(user_message)
#     print(f"Classified intent: {intent}")
#     if intent == "research":
#         return research_agent(user_message)
#     elif intent == "code":
#         return code_agent(user_message)
#     elif intent == "summarize":
#         return summarize_agent(user_message)
#     else:
#         response = client.messages.create(
#             model=MODEL,
#             messages=[{"role": "user", "content": f"Handle this message that doesn't fit other categories: {user_message}"}],
#             max_tokens=100
#         )
#         return response.content

# test_inputs = [
#     {"prompt": "What's the latest version of Python?", "expected_intent": "research"},
#     {"prompt": "Write a function to reverse a linked list.", "expected_intent": "code"},
#     {"prompt": "Summarize this paragraph: Python is a popular programming language known for its readability and versatility. It is widely used in web development, data analysis, artificial intelligence, and scientific computing. Python's extensive libraries and supportive community make it a great choice for both beginners and experienced developers.", "expected_intent": "summarize"},
#     {"prompt": "Fix the bug in my for loop", "expected_intent": "code"},
#     {"prompt": "Who won the 2022 World Cup?", "expected_intent": "research"},
#     {"prompt": "tl;dr the plot of Hamlet", "expected_intent": "summarize"},
#     {"prompt": "What's the weather like?", "expected_intent": "ambiguous"},
#     {"prompt": "Tell me a joke", "expected_intent": "other"}
# ]

# for test_input in test_inputs:
#     prompt = test_input["prompt"]
#     expected_intent = test_input["expected_intent"]
#     print(f"\nInput: {prompt}")
#     response = route(prompt)
#     print(f"Expected intent: {expected_intent}")


# ─── SECTION B4: Human-in-the-loop ───────────────────────────────────────────
# CONCEPT
#   The agent pauses at a decision point and asks a human before acting. Implement
#   it as a tool: ask_human(question) prints the question and returns input(). The
#   hard part is getting it to reliably pause BEFORE acting, not after.
#
# TODO: implement ask_human(question). Define ask_human + write_file schemas and a
#   loop that runs this EXACT task:
#       "Write a summary of machine learning to ml_summary.txt, but ask the human
#        how detailed it should be BEFORE writing."
#   Feed the human's answer back as a tool_result.
#
# CHALLENGE (write the answers in comments):
#   Update task to: "Write a summary of machine learning to ml_summary.txt."
#   Does it ask before writing, or write first and ask later? Try these two system
#   prompt lines and note which reliably makes it pause:
#     (a) "You may ask the human if helpful."
#     (b) "You MUST call ask_human and wait for the answer before any write_file."
#   Why does phrasing change the behavior so much?

# ANSWER:
#   With "BEFORE writing" in the task: both (a) and (b) work — the task itself
#   encodes the ordering, so system prompt phrasing doesn't matter.
#
#   With a neutral task ("Write a summary to ml_summary.txt"):
#   - System prompt alone (even "MUST call ask_human"): unreliable. Claude skips
#     ask_human since the task is self-contained and gives no reason to ask.
#   - disable_parallel_tool_use: prevents batching both calls, but Claude can
#     still skip ask_human altogether.
#   - tool_choice={"type":"tool","name":"ask_human"} on first call: deterministic.
#     Claude is forced to call ask_human before anything else.
#
#   Lesson: system prompts express intent; tool_choice enforces structure. True
#   human-in-the-loop blocking requires the structural guarantee, not just wording.

def ask_human(question):
    print("HUMAN QUESTION:", question)
    return input("HUMAN ANSWER: ")


def write_file(filename, content):
    with open(filename, "w") as f:
        f.write(content)


def execute_tool(tool_name, args):
    if tool_name == "ask_human":
        return ask_human(**args)
    elif tool_name == "write_file":
        write_file(**args)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


TOOLS = [
    {
        "name": "ask_human",
        "description": "Ask the human a question and get their input.",
        "input_schema": {
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file. Generate the full text content yourself and pass it as 'content'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["filename", "content"],
        }
    },
]


def agent_loop(task, max_steps=5):
    step = 0
    messages = [{"role": "user", "content": task}]
    while step < max_steps:
        r = client.messages.create(
            system="You MUST call ask_human and wait for the answer before any write_file.",
            model=MODEL,
            tools=TOOLS,
            tool_choice={"type": "auto", "disable_parallel_tool_use": True},
            messages=messages,
            max_tokens=4096
        )
        messages.append({"role": "assistant", "content": r.content})

        tool_use_blocks = [b for b in r.content if b.type == "tool_use"]
        if not tool_use_blocks:
            break

        tool_results = []
        for block in tool_use_blocks:
            print(f"{block.name}({block.input})")
            result = execute_tool(block.name, block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": str(result) if result is not None else "done",
            })
        messages.append({"role": "user", "content": tool_results})
        step += 1

agent_loop("Write a summary of machine learning to ml_summary.txt.")