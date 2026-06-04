# Case study — one real piece of work walked through the playbook

> **Status: placeholder.** This file is the Stage 3 (Measure) artifact for the LinkedIn post. Ram and Claude fill it together after picking one real piece of work to walk through.

## Candidate work to document

Pick one. The case should be small enough to write up tightly but real enough to expose at least one failure mode.

- A recent **critical bug fix** where the workflow caught a wrong-direction attempt at one of the gates.
- A **feature build** where spec → plan → test → build kept the agent inside scope.
- A **scope change** to an already-shipped feature where reading call sites first prevented a regression.

## Walkthrough template

When this is filled in, each stage gets:

1. **What the gate caught** (or didn't catch).
2. **The actual prompt or artifact** (sanitized) — spec.md excerpt, plan.md excerpt, failing test, etc.
3. **Token cost** for that stage if available — `claude` reports session token use, or use a custom status line.
4. **Time spent** — wall clock, human + agent combined.
5. **What would have gone wrong without this gate** — be specific, honest, falsifiable.

## What this is NOT

- This is not a benchmark. n=1.
- This is not a productivity claim. METR's RCT (cited in `evidence.md`) suggests AI tools *slow down* experienced developers on familiar codebases. A single case study cannot refute that.
- This is the **receipt** that the workflow exists and is run. Not proof that it's optimal.

## Honest caveat for the post

The case study's job is to make the workflow concrete, not to make a numerical claim. If the post implies "this saved me N hours," the post is making a claim the case study cannot support. Stick to qualitative ("at gate 2, the plan called for editing a controller that did not need editing — I caught it") and let readers calibrate from there.
