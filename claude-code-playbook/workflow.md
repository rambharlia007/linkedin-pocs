# The workflow — where context goes wrong and how the gates catch it

A diagram-as-text of the spec → plan → test → build → review → verify → ship loop, with annotations at every gate showing **what fails if you skip it** and which research finding warns about that failure.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 0 — Trigger                                                           │
│  "Fix the auth refresh bug" / "Build the CSV export" / "Change scope of X"   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 1 — GRILL ME  (skills/rmb-grill-me.md)                                │
│  Senior-engineer interview. One question at a time. Recommended answer for   │
│  each. Output → spec.md.                                                     │
│                                                                              │
│  Skip this and you get: cold-prompt failure. Anthropic: "Jumping into code   │
│  without discussion" is failure mode #1.                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼ ── GATE 1 ── human approves spec.md ──
                                     │
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 2 — PLAN  (skills/rmb-plan.md)                                        │
│  Convert spec into concrete steps: file paths, function names, test cases.   │
│  Output → plan.md.                                                           │
│                                                                              │
│  Skip this and you get: model rewrites scope mid-flight. Anthropic: the      │
│  plan is editable in Ctrl+G *before* approval. Edit it like a PR.            │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼ ── GATE 2 ── human edits + approves plan.md ──
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │  per pending step:    │
                         └───────────┬───────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 3a — TEST  (skills/rmb-test.md) — RED phase                           │
│  Write failing tests for the next step. Run them. Confirm they fail for the  │
│  right reason. Commit.                                                       │
│                                                                              │
│  Skip this and you get: the agent has no oracle. It declares victory by      │
│  vibes. Willison: the agent *executes code* — give it something to execute   │
│  against.                                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 3b — BUILD  (skills/rmb-build.md) — GREEN phase                       │
│  Make the tests pass. Nothing more.                                          │
│                                                                              │
│  Skip "nothing more" and you get: over-eager refactoring. GitClear:          │
│  refactor rate collapsed 24.1% → 9.5% under AI; cloning rose 8.3% → 12.3%.   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼ ── loop until all plan steps done ──
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 4 — REVIEW  (skills/rmb-review.md)                                    │
│  Adversarial reviewer subagent. Fresh context. Flags ONLY correctness gaps,  │
│  not nice-to-haves.                                                          │
│                                                                              │
│  Skip the "only correctness" constraint and you get: over-engineering.       │
│  Anthropic: "A reviewer prompted to find gaps will usually report some."     │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 5 — VERIFY  (skills/rmb-verify.md)                                    │
│  Run the actual app. Click the button. Watch the screen.                     │
│                                                                              │
│  Skip this and green tests will lie to you. GitClear: 7.9% of new code is    │
│  revised within two weeks (vs 5.5% in 2020). The macroscopic fingerprint     │
│  of "tests passed, behaviour wrong."                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼ ── GATE 3 ── human approves push ──
                                     │
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 6 — SHIP                                                              │
│  git push. Open PR.                                                          │
│                                                                              │
│  Per-push approval. NOT in Anthropic's official guide. Practitioner          │
│  consensus only. The friction is the feature.                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Where context loss is most likely

Three points on this graph cause >80% of the "agent went sideways" incidents in my experience:

1. **Between STAGE 1 and STAGE 2** — if you carry the grill conversation into planning, the plan inherits every false start. Start STAGE 2 in a fresh session with the spec as the only carryover. (Anthropic: spec → fresh session → implement.)

2. **Inside the STAGE 3 loop** — after 2 failed attempts at making a test pass, the context is poisoned. Don't try a third correction. `/clear` and re-prompt with what the failures revealed. (Anthropic: two-correction rule.)

3. **Between STAGE 5 and STAGE 6** — the temptation to skip verification because "it compiled" is the strongest temptation in the loop. This is where the GitClear churn comes from. Run the app.

## What this workflow does *not* claim

- It does not claim to make you faster. METR's RCT suggests it might make you slower. It claims to make the failures **visible** instead of silent.
- It does not claim to work without your attention. The gates are where you intervene. Skip the gates and the workflow is theatre.
- It does not generalize unmodified to your codebase. Adapt the gates to your risk surface.
