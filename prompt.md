Generate a self-contained HTML learning plan for building AI agents from scratch using the Anthropic API and Python. The output is a single `.html` file with all CSS and JavaScript embedded.

---

## Learner profile

Intermediate developer with some AI exposure — has chatted with Claude or ChatGPT, may have called a REST API before, but has never built anything serious with LLMs. Comfortable with Python, HTTP, and basic data structures. Doesn't need syntax hand-holding but benefits from seeing exactly what's happening under the hood.

---

## Pedagogical principles

These govern how every chunk and session is written:

**Do first, explain after.** Every concept is introduced through a concrete task. The learner runs code before they read an explanation. Two or three sentences of framing max before the task begins.

**Earn the concept.** Higher-level concepts (compression, patterns, RAG) are only introduced after the learner has hit the problem they solve. Don't teach rolling context compression before the learner has watched their own token count climb across 15 loop iterations.

**Break things deliberately.** Each major concept needs a task where the learner intentionally causes a failure and observes what happens. Failure builds intuitions that success can't. Seeing an agent loop forever, hallucinate success, or silently drop context is worth more than reading about those behaviors.

**Compare, don't just demonstrate.** When two approaches exist, have the learner implement and measure both. The comparison — token cost, behavior, edge cases — is the lesson. Don't just present the better way.

**One "observe this" per chunk.** Every chunk ends with a single specific question the learner can only answer by running the code. Not a comprehension check — a discovery prompt. It should be surprising or unintuitive if they haven't run it yet.

---

## Session structure

The plan is organized into **sessions** of 2–4 hours each. The learner decides how many sessions to do per day — one, two, or three. Sessions must be independently completable; starting mid-plan should require no mental context beyond what the code already contains.

Every session must include, in this order:

1. **Warm-up** (5–10 min): A tiny task that works on first run. Its only job is a quick win that orients the learner to the session's theme. It should feel effortless. Design it so a learner who is tired or hesitant still starts.

2. **Chunks** (3–5 per session, 15–30 min each): The actual content. Each chunk is one task with one "observe this" question. Include short code examples where they accelerate understanding. Keep framing text tight — the task carries the weight.

3. **Mini project** (one per session, except where noted): A small complete thing that synthesizes the session's chunks. Pushable to GitHub. Should feel like a real artifact, not an exercise.

---

## Curriculum

Cover these topics in this order. Use the descriptions as constraints on what to teach and what insight to land — not as content to copy verbatim. Design the actual warm-ups, tasks, and observations yourself.

**Session 1 — API fundamentals**
Topics: raw API calls, JSON response shape, what tokens are, statelessness, building conversation history by hand, system prompt behavior.
Key insight to land: the API is stateless — every call is fully independent. The learner must experience this by breaking something, not by reading about it. A multi-turn conversation where earlier messages are intentionally omitted is the core exercise.
Ends with: a `Chatbot` class with history and per-turn token logging.

**Session 2 — Tools and the agent loop**
Topics: tool definitions as JSON schema, the `tool_use` response block, the `tool_result` cycle, the `while` loop agent, `stop_reason`, max_steps guard.
Key insight to land: the model declares intent but does not act — the developer executes the tool and feeds the result back. This is the mechanical core of every agent. Must include a deliberate failure task: a tool that always returns an error, run for 5+ steps. The learner observes what the agent does under persistent failure — this is the most important debugging intuition in the plan.
Ends with: a file agent with real `read_file` and `write_file` tools.

**Session 3 — Context limits and compression**
Topics: context window as a finite budget, token growth across loop iterations, rolling summary compression, the precision vs. space tradeoff, structured logging.
Key insight to land: compression is lossy. After implementing it, the learner must ask the agent about something that got compressed and observe what's missing. The tradeoff should be felt, not described.
Do not introduce compression before the learner has seen their own token count climb. That growth motivates the solution.
Ends with: a research agent with a real search tool, compression, max_steps, token budget, and log file.

**Session 4 — Architecture patterns**
Topics: ReAct (thought before every tool call), plan-and-execute (two-phase: plan first, then execute), multi-agent (orchestrator + sub-agent with independent context windows).
Key insight to land: there is no universal best pattern. The learner discovers when each wins by running the same task through all three and comparing logs — steps taken, tokens used, correctness. Include a break-it task for plan-and-execute where mid-plan reality diverges from the plan.
No mini project — the logged comparison across all three patterns is the deliverable.

**Session 5 — Memory and retrieval**
Topics: embeddings as vectors, cosine similarity implemented from scratch without a library, a small knowledge base, RAG wired as an agent tool, edge cases (rephrased queries, out-of-scope queries, ambiguous matches).
Key insight to land: semantic similarity — not keyword matching — is what makes retrieval work. The learner must implement the math before using any library, so they understand what a vector store actually does.
Ends with: the RAG retrieval tool wired into the research agent from Session 3.

**Session 6 — Production basics**
Topics: retry with exponential backoff (transient vs. permanent error classification), streaming API, prompt caching with `cache_control`, structured output validation with self-correction.
Key insight to land: reliability and cost are engineering decisions, not afterthoughts. Each topic must be measured — before/after token cost for caching, recovery rate for retry, perceived responsiveness for streaming. The measurement is the chunk, not just the implementation.
No mini project — the before/after comparisons are the deliverable.

**Session 7 — Capstone**
The learner picks a real problem they'd actually use an agent for and designs before coding: which pattern, which tools, where memory lives, what failure modes exist, what gets logged. Written design must exist before any code is written. The build must incorporate everything from prior sessions. Ends with a GitHub push, `v1.0` tag, and a short retrospective.

---

## HTML format and UX

**Layout:**
- Fixed left sidebar listing all 7 sessions with a visual completion indicator (dot, checkmark, or similar) per session.
- Main content area where each session is a clearly separated section.
- Sticky header with plan title and overall progress (e.g., "3 of 7 sessions complete").
- On small screens, sidebar collapses to a top navigation or hamburger.

**Session rendering:**
- Warm-up is visually distinct from the rest of the session — different card style or background, labeled so it reads as the easy on-ramp.
- Chunks are numbered. Each "observe this" question is a styled callout, visually distinct from task text.
- Code snippets in monospace blocks with subtle background.
- At the session end: a single prominent "Mark complete" button. On click: sidebar indicator updates, and a short contextual message appears — something earned and specific to that session, not generic praise.

**Progress persistence:**
- Save completed sessions to `localStorage` on mark-complete. Restore state on page load.
- Unobtrusive "Reset progress" option in the footer.

**Aesthetic:**
- Clean, high typographic contrast between session titles, chunk titles, task body, and callouts.
- Readable at a glance — a learner should be able to open the page and immediately know where they left off and what to do next.
- Choose dark or light theme based on which makes code blocks and callouts look best.

---

## Tone

Direct and warm. Treat the learner as capable — skip filler encouragement, but when something genuinely lands (completing the agent loop, watching the first compression run, shipping the capstone) acknowledge it with something specific and earned. Short sentences. The tasks carry the content; prose sets them up.
