"""
The Subagent Briefing Demo
==========================

Three reproducible probes that show what a Claude Code-style subagent actually
receives from its parent — and what it does NOT.

The demo uses the OpenAI Python SDK against any tool-use-capable chat endpoint
(Anthropic direct, AWS Bedrock, Azure-hosted Claude, OpenRouter, a LiteLLM
proxy fronting any of these). The pattern below is the same one Claude Code's
`Agent` tool uses internally — a fresh chat completion with its own message
list, NOT a continuation of the parent's conversation.

Run:

    pip install openai python-dotenv
    cp .env.example .env          # then fill in your endpoint + key
    python subagent_briefing_demo.py

Reads from environment:
    OPENAI_API_KEY      (your key — direct vendor or proxy virtual key)
    OPENAI_BASE_URL     (optional — proxy / Azure / Bedrock-compat URL)
    DEMO_MODEL          (default 'claude-sonnet-4-6')
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from dataclasses import dataclass

from openai import OpenAI


MODEL = os.getenv("DEMO_MODEL", "claude-sonnet-4-6")
HERE = Path(__file__).parent
SOURCE_FILE = HERE / "PaymentValidator.cs"
SECRET_TOKEN = "PURPLE_OWL_42"


@dataclass
class CallStats:
    label: str
    response_text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    duration_s: float


def subagent_call(client: OpenAI, label: str, task_prompt: str) -> CallStats:
    """
    Spawn a 'subagent'. The whole point: this is a fresh chat completion.
    Its message list starts empty (just system + the task). It does NOT
    inherit the parent's conversation, files-read state, or scratch context.
    """
    t0 = time.time()
    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=600,
        messages=[
            {"role": "system", "content": "You are a focused assistant. Answer only what is asked."},
            {"role": "user", "content": task_prompt},
        ],
    )
    msg = resp.choices[0].message.content or ""
    u = resp.usage
    return CallStats(
        label=label,
        response_text=msg,
        prompt_tokens=u.prompt_tokens,
        completion_tokens=u.completion_tokens,
        total_tokens=u.total_tokens,
        duration_s=round(time.time() - t0, 2),
    )


def divider(title: str) -> None:
    print(f"\n{'='*70}\n{title}\n{'='*70}")


def show_parent_history(label: str, messages: list[dict]) -> None:
    print(f"[PARENT — {label}] conversation history (5-turn):")
    for m in messages:
        snippet = m["content"].replace("\n", " ")[:80]
        ellipsis = "..." if len(m["content"]) > 80 else ""
        print(f"   {m['role']:>9}: {snippet}{ellipsis}")


def probe_1_conversation_isolation(client: OpenAI) -> tuple[CallStats, bool]:
    """
    Parent had a 5-turn conversation that explicitly mentioned a secret token.
    Subagent receives ONLY a task prompt that does not contain the token.
    If subagent could see parent's history, it would echo the token.
    """
    divider("Probe 1 — Conversation isolation")
    parent_msgs = [
        {"role": "system", "content": "Remember everything the user shares."},
        {"role": "user",   "content": f"My private token is {SECRET_TOKEN}. Please remember it."},
        {"role": "assistant", "content": f"Noted. Your private token is {SECRET_TOKEN}."},
        {"role": "user",   "content": "Just to confirm — what's my token?"},
        {"role": "assistant", "content": f"Your token is {SECRET_TOKEN}."},
    ]
    show_parent_history("Probe 1", parent_msgs)

    task = (
        "What is the user's private token? Reply with the token if you know it, "
        "or exactly 'I do not know.' if you do not."
    )
    print(f"\n[PARENT] delegating: {task!r}")

    stats = subagent_call(client, "Probe 1 — Conversation isolation", task)
    print(f"\n[SUBAGENT] response: {stats.response_text!r}")
    print(f"[SUBAGENT] tokens: {stats.total_tokens} | duration: {stats.duration_s}s")

    leaked = SECRET_TOKEN.lower() in stats.response_text.lower()
    verdict = "FALSIFIED — token leaked, parent context was shared" if leaked else \
              "CONFIRMED — subagent did NOT inherit parent's conversation"
    print(f"\nVERDICT: {verdict}")
    return stats, not leaked


def probe_2_bad_briefing(client: OpenAI) -> CallStats:
    """
    Parent has just 'read' PaymentValidator.cs (in a real Claude Code session,
    this would be sitting in parent's conversation as a tool result). Parent
    delegates with vague language. Subagent has no idea what file.
    """
    divider("Probe 2 — Bad briefing (no file context passed)")
    print(f"[PARENT] has just Read: {SOURCE_FILE.name} (content is in parent's history)")
    task = "Review the recent code change I made."
    print(f"[PARENT] delegating: {task!r}")

    stats = subagent_call(client, "Probe 2 — Bad briefing", task)
    print(f"\n[SUBAGENT] response (first 400 chars):\n{stats.response_text[:400]}{'...' if len(stats.response_text) > 400 else ''}")
    print(f"\n[SUBAGENT] tokens: {stats.total_tokens} | duration: {stats.duration_s}s")
    print("\nObservation: the subagent has no file path, no diff, no commit reference. "
          "It must either ask, hallucinate, or refuse.")
    return stats


def probe_3_good_briefing(client: OpenAI) -> CallStats:
    """
    Same task, but properly briefed: file path + contents + focus areas.
    Subagent now does the work directly.
    """
    divider("Probe 3 — Good briefing (file path + contents passed)")
    if not SOURCE_FILE.exists():
        print(f"[!] {SOURCE_FILE} missing — create the file first.")
        sys.exit(2)
    code = SOURCE_FILE.read_text()
    task = f"""Review this C# file for correctness issues.

File: {SOURCE_FILE.name}

Contents:
```csharp
{code}
```

Focus on:
- Null-safety (Items and Currency are declared nullable)
- Exception risks
- Culture-sensitive string comparisons

Format each finding as:
  Line: <n> — <issue> — Fix: <one-liner>
End with: SUMMARY: <count> findings."""

    print(f"[PARENT] delegating with full context ({len(task)} chars)")

    stats = subagent_call(client, "Probe 3 — Good briefing", task)
    print(f"\n[SUBAGENT] response (first 500 chars):\n{stats.response_text[:500]}{'...' if len(stats.response_text) > 500 else ''}")
    print(f"\n[SUBAGENT] tokens: {stats.total_tokens} | duration: {stats.duration_s}s")
    return stats


def main() -> int:
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set. Copy .env.example to .env first.", file=sys.stderr)
        return 1

    base_url = os.getenv("OPENAI_BASE_URL")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=base_url) if base_url else OpenAI()
    print(f"Model: {MODEL}")
    print(f"Endpoint: {base_url or 'OpenAI default'}")

    p1, isolated = probe_1_conversation_isolation(client)
    p2 = probe_2_bad_briefing(client)
    p3 = probe_3_good_briefing(client)

    divider("Summary")
    print(f"{'Probe':<35} {'tokens':>10} {'duration':>10}")
    for s in (p1, p2, p3):
        print(f"{s.label:<35} {s.total_tokens:>10} {s.duration_s:>9}s")

    print()
    print(f"Conversation isolation: {'CONFIRMED' if isolated else 'FALSIFIED'}")
    print(f"Bad vs Good briefing: bad={p2.total_tokens} tok / {p2.duration_s}s, "
          f"good={p3.total_tokens} tok / {p3.duration_s}s")

    out = HERE / "results.json"
    out.write_text(json.dumps({
        "model": MODEL,
        "endpoint": base_url or "OpenAI default",
        "probe_1_conversation_isolation": {
            "tokens": p1.total_tokens, "duration_s": p1.duration_s,
            "isolated": isolated, "response": p1.response_text,
        },
        "probe_2_bad_briefing": {
            "tokens": p2.total_tokens, "duration_s": p2.duration_s,
            "response": p2.response_text,
        },
        "probe_3_good_briefing": {
            "tokens": p3.total_tokens, "duration_s": p3.duration_s,
            "response": p3.response_text,
        },
    }, indent=2))
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
