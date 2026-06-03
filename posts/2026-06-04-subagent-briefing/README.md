# The Subagent Briefing Problem

> A subagent does not inherit its parent's conversation, its parent's
> "files I just read" state, or its parent's session memory. It starts
> with the task prompt you hand it — and nothing else from your live
> session.

This POC proves it with three reproducible probes, runs against any
tool-use-capable Chat Completions endpoint, and prints the verdict.

## What it demonstrates

| Probe | Question it answers |
|-------|----------------------|
| 1 — Conversation isolation | Does the subagent see what the parent's chat history contained? A secret token is buried in 5 turns of parent conversation. Subagent is asked to reveal it. **Should fail.** |
| 2 — Bad briefing | Parent has just "read" `PaymentValidator.cs`. Subagent is told only *"review the recent code change."* Does it find the file? At what cost? |
| 3 — Good briefing | Same task, but the prompt now includes file path, full source, and focus areas. Clean review, no exploration. |

For each probe, the script captures token usage, wall-clock time, and the
subagent's response. A `results.json` lands next to the script.

## Why it matters

In Claude Code (and most agent harnesses), subagents are spawned via an
`Agent` / `Task` tool. The harness creates a **fresh chat completion** for
the subagent — its own message list, its own system prompt. It does not
mirror the parent's session state.

People who write custom subagents often miss this. They write a delegation
prompt like *"summarise the file I just opened"* and the subagent has no
idea which file. Failure modes split into two flavours:

- **Well-scoped subagents stall** — they politely ask for more input.
- **Exploratory subagents waste effort** — they run `git status`, glob,
  read random files, and finally produce something (possibly correct,
  possibly not).

Either way, the fix is the same: brief explicitly.

## The precise boundary

```
Visible to subagent:
  ✓ Delegation prompt (whatever the parent passes in)
  ✓ Subagent's own static system prompt
  ✓ CLAUDE.md, MEMORY.md (auto-injected per host docs)
  ✓ Filesystem (if the subagent has Read/Glob/Bash tools)

Invisible to subagent:
  ✗ Parent's conversation history
  ✗ Parent's tool-call results from earlier turns
  ✗ Parent's "currently open file" / scratch state
  ✗ Anything the parent learned but did not pass forward
```

Filesystem access is *not* context inheritance. The subagent can
rediscover disk state — but at the cost of tokens, time, and the risk of
guessing wrong about what *"recent"* meant.

## Run it

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env       # then fill in OPENAI_API_KEY (+ base_url if proxy)
python subagent_briefing_demo.py
```

Compatible endpoints (set `OPENAI_BASE_URL`):

- Anthropic direct (via an OpenAI-compatible proxy)
- AWS Bedrock (via LiteLLM proxy or Bedrock's OpenAI-compat shim)
- Azure OpenAI (Claude-on-Azure or GPT)
- OpenRouter (any tool-use model)
- A self-hosted LiteLLM proxy fronting any of the above

Total run cost on Sonnet 4.6 ≈ $0.01-$0.03 depending on output verbosity.

## Expected output shape

```
======================================================================
Probe 1 — Conversation isolation
======================================================================
[PARENT — Probe 1] conversation history (5-turn):
       system: Remember everything the user shares.
         user: My private token is PURPLE_OWL_42. Please remember it.
    assistant: Noted. Your private token is PURPLE_OWL_42.
         user: Just to confirm — what's my token?
    assistant: Your token is PURPLE_OWL_42.

[PARENT] delegating: 'What is the user's private token? ...'

[SUBAGENT] response: 'I do not know.'
[SUBAGENT] tokens: 87 | duration: 0.6s

VERDICT: CONFIRMED — subagent did NOT inherit parent's conversation
```

If `VERDICT` ever flips to `FALSIFIED`, something has changed in the
host's subagent semantics and the claim needs revisiting.

## Companion artefacts

- `PaymentValidator.cs` — the file Probe 2 and 3 reference. It is
  deliberately buggy (null-safety + culture-sensitive comparison).
- `verification-log.md` — transcripts from the original verification
  rounds done inside Claude Code's own `Agent` tool. Useful as a
  cross-check that the in-process behaviour matches the API-level demo.

## The 30-second fix the post advocates

Instead of:

```python
subagent.run("review my recent change")
```

Do:

```python
subagent.run(f"""
Review this file: {file_path}

Contents:
{file_contents}

Focus on: {criteria}
""")
```

Treat your subagent like a contractor briefed by email — not a teammate
sitting next to you reading over your shoulder.
