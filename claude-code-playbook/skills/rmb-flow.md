---
name: rmb-flow
description: Super-skill orchestrator. Chains /rmb-grill-me → /rmb-plan → user approval gate → /rmb-test + /rmb-build (looped per step) → /rmb-review → /rmb-verify → /rmb-ship. Maintains state in .claude/flow-state.json so it can resume after interruption. Designed for "set and walk away" usage after the planning phase.
arguments:
  - name: work
    description: One-line description of the work
    required: false
  - name: resume
    description: Pass --resume to continue from saved flow-state.json
    required: false
---

# Skill: rmb-flow

Orchestrate the full workflow. Two phases — interactive (you decide), autonomous (you walk away).

## Phase Map

```
PHASE 1 — Interactive (with user)
  1.1  /rmb-grill-me <work>     → spec.md
  1.2  /rmb-plan                → plan.md
  1.3  USER APPROVAL GATE       → "go" or "amend"

PHASE 2 — Autonomous (no user interruption)
  2.1  /rmb-test (Step 1)
  2.2  /rmb-build (Step 1)
  2.3  Loop 2.1+2.2 for every step in plan.md (+ delta if exists)
  2.4  /rmb-review
  2.5  /rmb-verify
  2.6  /rmb-ship

ANY-TIME OFFRAMP
  /rmb-amend                    → patches spec + delta plan, then resumes Phase 2
```

## State management

`.claude/flow-state.json` in the current repo:

```json
{
  "slug": "csv-export",
  "phase": "phase2",
  "step": "build",
  "current_step_number": 3,
  "completed_steps": [1, 2],
  "started": "<iso>",
  "last_activity": "<iso>",
  "approval_gate_passed": true,
  "build_attempts_for_current_step": 0
}
```

Updated after every skill completes. If `--resume` is passed, read this and pick up where we left off.

## Step 1 — Bootstrap

1. Detect repo + slug.
2. If `--resume`:
   - Read flow-state.json
   - Print: `Resuming flow: slug=<slug>, phase=<phase>, step=<step>`
   - Jump to the appropriate phase
3. Else (fresh start):
   - If `work` argument provided, pass it to `/rmb-grill-me`. Else, `/rmb-grill-me` will ask.
   - Initialize flow-state.json with phase=phase1, step=grill

## Phase 1 — Interactive

### 1.1 Invoke /rmb-grill-me
Run the grill-me skill. When it completes successfully (spec.md exists), update state: `step=plan`.

### 1.2 Invoke /rmb-plan
Run plan skill. When done (plan.md exists), update state: `step=approval_gate`.

### 1.3 Approval gate

Print:
```
══════════════════════════════════════════════════
PHASE 1 COMPLETE — Review before autonomous build

📄 Spec:  D:\plans\<repo>\<slug>\spec.md
📋 Plan:  D:\plans\<repo>\<slug>\plan.md

Plan has <N> steps, estimated <X> commits.

Type one of:
  go              → start autonomous build
  amend "<what>"  → modify spec/plan before building
  cancel          → exit, keep artifacts
══════════════════════════════════════════════════
```

Wait for user input.

- `go` → mark `approval_gate_passed=true`, proceed to Phase 2
- `amend "<what>"` → invoke `/rmb-amend` with the change, then re-enter approval gate
- `cancel` → save state, exit cleanly

## Phase 2 — Autonomous (no questions)

In this phase, the flow MUST NOT ask the user any questions. All sub-skills inherit this rule. If a sub-skill genuinely needs user input, it should log to DECISIONS.md and pick the most defensible option.

### 2.1 / 2.2 — Per-step TDD loop

For each pending step in plan.md (+ plan.delta.md if present):

1. Update state: `current_step_number=<N>, step=test`
2. Invoke `/rmb-test` — should write tests + commit (red)
3. If test phase fails (e.g., test framework error): escalate (see Escalation)
4. Update state: `step=build`
5. Invoke `/rmb-build` — should make tests pass + commit (green)
6. If build phase escalates (3 retries exhausted): escalate (see Escalation)
7. Mark step as completed in `completed_steps`. Move to next step.

### 2.3 — Loop end check

After last step:
- Run full test suite once more. Expect green.
- If red, escalate.

### 2.4 Invoke /rmb-review
- Update state: `step=review`
- Run review skill
- If review flags blockers → escalate (don't auto-ship through blockers)
- If review only has minor/nit (auto-fixed) → proceed

### 2.5 Invoke /rmb-verify
- Update state: `step=verify`
- Run verify skill
- If verify FAILS → escalate
- If PARTIAL → escalate with note (manual follow-up needed)
- If PASS → proceed

### 2.6 Invoke /rmb-ship
- Update state: `step=ship`
- Run ship skill
- Note: ship has its own confirmation prompts (auto-merge, reviewers). flow will pass those through.
- On success → mark state: `phase=done`

## Escalation (from Phase 2)

When any sub-skill escalates back to flow:

1. Update state: `step=escalated`, capture reason
2. Print:
   ```
   ⚠️ FLOW PAUSED at step: <step>
   Reason: <summary>
   Artifact: <path to relevant log / decisions>

   Options:
     /rmb-amend "<change>"   → patch spec/plan, then /rmb-flow --resume
     /rmb-flow --resume      → retry from saved state
     manual fix              → fix yourself, then /rmb-flow --resume
   ```
3. Exit cleanly. Don't loop, don't retry without user direction.

## Long-running support

If a single step's build phase takes more than one turn (large diff, lots of files), the flow may use `ScheduleWakeup` to re-invoke itself after a short delay, picking up from state. State must be persisted before any wakeup.

## Close out

Phase 2 success:
```
🎉 Flow complete for slug=<slug>
PR: <url>
Total commits: <N>
Total steps: <M>
Time: <elapsed>
```

## Hard Rules

- **Phase 2 = no user questions.** Period.
- **State always persisted** before sleep, wait, or escalation.
- **Never skip approval gate.** Even if user typed "go" once, fresh runs need fresh approval.
- **Never auto-amend mid-flow.** Amendments require explicit user invocation.
- **Never run two phases simultaneously.** One step at a time.

## What NOT to do

- Don't bypass any sub-skill's safety gates (ship's review check, verify's app readiness check)
- Don't ship with verify=FAIL even if all earlier phases passed
- Don't keep retrying past sub-skill escalation
- Don't delete flow-state.json on failure — leave for resume
- Don't ask user questions in Phase 2
