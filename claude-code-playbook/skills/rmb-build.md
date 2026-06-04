---
name: rmb-build
description: TDD green phase — AUTONOMOUS. Implements production code until all failing tests pass for the current step in plan.md. Never asks the user questions. Logs decisions to DECISIONS.md. Retries up to 3 times on failure before escalating. Stops only when tests pass + lint clean + step's acceptance criterion met.
---

# Skill: rmb-build

Make the failing tests pass. Autonomously. Don't ask the user anything.

@~/.claude/rules/common.md

## Autonomous Mode — Hard Rules

1. **No clarifying questions.** Spec + plan + repo knowledge + rules are the source of truth. If you're unsure, pick the option most consistent with repo patterns and log the decision.
2. **Log every non-trivial decision** to `D:\plans\<repo>\<slug>\DECISIONS.md` with `## <ISO timestamp>` heading and 2–4 sentences of reasoning.
3. **Max 3 retry attempts per step.** If after 3 attempts tests still fail, stop and escalate (see Escalation section).
4. **Never modify tests to make them pass.** The test is the contract. Make the code satisfy it.
5. **Never skip rules** to make things faster. Repo knowledge + rules files are mandatory inputs.

## Step 1 — Load context

1. Detect repo + slug.
2. Read `D:\plans\<repo>\<slug>\spec.md`, `plan.md`, and `plan.delta.md` if present.
3. Read `D:\repo-knowledge\<repo>.md`.
4. Load stack rules:
   - Python → `@~/.claude/rules/python-fastapi.md`
   - .NET → `@~/.claude/rules/dotnet.md`
5. Check repo override `<repo>/.claude/RULES.md`.

## Step 2 — Find next implementation step

1. Read `.claude/flow-state.json` if it exists.
2. Find lowest-numbered step where:
   - Type is `Implementation`, `Migration`, or `Refactor`
   - Its corresponding `Test` step is done (tests exist, failing)
   - This step itself is not yet done
3. If no pending step, run full test suite. If green, report: **"All steps complete. Suggest /rmb-review."** If red, find what broke and fix it.

## Step 3 — Implement

For the current step:

1. Re-read the step's `What`, `Files`, `Functions/Classes`, `Acceptance` from plan.
2. Open all files listed in `Files`.
3. Make the changes:
   - Match existing patterns from repo knowledge (DI style, layering, error handling)
   - Follow stack rules (Pydantic models, async, ILogger, etc.)
   - Keep functions ≤30 lines unless purely declarative
   - Add structured logs at boundaries
   - No `print()` / `Console.WriteLine`
4. Don't touch files outside the step's `Files` list unless absolutely necessary. If you must, log it in DECISIONS.md.

## Step 4 — Run tests

1. Run only the tests for this step first (fast feedback).
2. If passing → run the full suite to check for regressions.
3. If failing:
   - Read the failure output carefully
   - Diagnose root cause (not just the symptom)
   - Fix the production code (NEVER the test, unless test has an objective bug like wrong import)
   - Re-run

## Step 5 — Lint + format

Run repo's lint + format commands (from repo knowledge):
- Python: `ruff check --fix` + `ruff format` (or `black` + `isort` + `flake8`/`mypy`)
- .NET: `dotnet format`

Fix all warnings unless they're false positives. If false positive, suppress with a tightly-scoped inline directive + comment explaining why.

## Step 6 — Acceptance check

Re-read the step's `Acceptance` field from plan. Manually verify the criterion is met:
- "Endpoint returns 201 with user ID" → test exercises this; confirm test asserts it
- "Migration runs without error" → run the migration command, confirm

If the acceptance check is more than just "tests pass" (e.g., needs DB inspection, file generation), do that verification now. Log proof to DECISIONS.md.

## Step 7 — Commit

```
git add <changed files>
git commit -m "feat/fix/refactor: <step title> (green)"
```

Type prefix:
- `feat:` — new functionality
- `fix:` — bug fix
- `refactor:` — restructuring without behavior change
- `chore:` — non-code (config, deps)
- `migrate:` — schema migrations

## Step 8 — Decide next action

- More pending steps in plan? → Loop back to Step 2 (next step)
- All steps done? → Run full suite one more time. If green, report:
  ```
  Build complete for slug=<slug>.
  Steps completed: <N>
  Commits: <list of short hashes>
  Suggest: /rmb-review
  ```
- If at any point you've done 3+ retry attempts on the same step → ESCALATE

## Retry / Escalation

After each failed attempt on a step, increment a counter (track in flow-state.json or DECISIONS.md):

- **Attempt 1 failed** → analyze the failure differently, try again
- **Attempt 2 failed** → revisit the plan step; maybe the design needs adjustment. Log a "design concern" in DECISIONS.md and try a different approach
- **Attempt 3 failed** → STOP. Print:
  ```
  ⚠️ Stuck on Step <N>: <title>
  Attempts: 3
  Last error: <summary>
  See: D:\plans\<repo>\<slug>\DECISIONS.md
  Suggested action: review the plan step, then /rmb-amend if design needs to change.
  ```
  Exit. Don't continue.

## DECISIONS.md format

```markdown
# Decisions Log: <slug>

## <YYYY-MM-DDTHH:MM> — <Step N>: <decision title>

**Context:** <what was ambiguous>
**Options considered:** <2-3 bullets>
**Chose:** <picked option>
**Why:** <reasoning, references rules/repo patterns>

---
```

Append every meaningful decision. This is the audit trail for `/rmb-review` to check.

## What NOT to do

- Don't ask the user any question, ever
- Don't modify tests to pass
- Don't skip lint/format
- Don't commit broken builds
- Don't continue past 3 failed attempts on a step
- Don't introduce dependencies not justified by the spec
- Don't refactor outside the step's scope
- Don't touch unrelated files
- Don't auto-trigger `/rmb-review` — let the user (or `/rmb-flow`) decide
