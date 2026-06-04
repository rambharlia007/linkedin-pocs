---
name: rmb-plan
description: Reads spec.md and produces a detailed step-by-step plan.md alongside it. Every step is concrete — file paths, function names, test cases, acceptance criteria. Plan is the contract that /rmb-test and /rmb-build execute against. Loads global rules + repo knowledge before planning.
---

# Skill: rmb-plan

Read the spec, design the implementation, output `plan.md` with **detailed, executable steps**. Don't write code. Don't run anything. Just plan.

@~/.claude/rules/common.md

## Operating Principles

1. **Spec is the contract.** Plan must satisfy every acceptance criterion in the spec. Nothing more, nothing less.
2. **Repo patterns win.** Consult repo knowledge — match existing patterns, don't introduce new ones.
3. **Concrete steps.** Each step has: action, files affected, functions/classes touched, tests required, acceptance check. Vague steps like "implement service" are rejected.
4. **Right-sized steps.** Each step should be 1–3 commits of work (~30–90 min). Too big = break it down. Too small = combine.
5. **Test-first ordering.** For each step, the test step comes before the implementation step (TDD).
6. **No code in plan.** Plan describes *what* and *where*. Code goes in `/rmb-test` and `/rmb-build`.

## Step 1 — Load inputs

1. Detect repo name + work slug (same logic as `/rmb-grill-me`).
2. Read `D:\plans\<repo>\<slug>\spec.md`. If missing, abort: **"No spec found. Run `/rmb-grill-me` first."**
3. Read `D:\repo-knowledge\<repo>.md` if exists. If missing, warn user but proceed:
   **"Warning: no repo knowledge. Plan may not match existing patterns. Consider running `/rmb-scan` first."**
4. Detect stack from cwd:
   - Python/FastAPI → also load `@~/.claude/rules/python-fastapi.md`
   - .NET → also load `@~/.claude/rules/dotnet.md`
5. Check for repo override `<repo>/.claude/RULES.md`. If exists, load and let it override conflicting global rules.

## Step 2 — Design (think before writing)

Internally answer (don't ask user):

- **Data layer changes**: schema migrations, new tables, new columns?
- **API surface**: new endpoints, modified contracts?
- **Service layer**: new services, modified business logic?
- **Infrastructure**: new dependencies, config changes, env vars?
- **Tests**: unit, integration, E2E — what's needed at each level?
- **Sequencing**: what blocks what? Migration before model? Repository before service?

## Step 3 — Write plan.md

Path: `D:\plans\<repo>\<slug>\plan.md`

If exists, ask: **"Plan exists. Overwrite (o), append delta (d), or cancel (c)?"** If user picks delta, use `/rmb-amend` flow instead.

Structure:

```markdown
# Plan: <work-title>

**Repo:** <repo>
**Slug:** <slug>
**Spec:** ./spec.md
**Date:** <YYYY-MM-DD>
**Stack:** <Python+FastAPI | .NET | ...>

## Architecture Decisions

<2–4 bullets — key design choices, with one-line rationale for each. Example:
- Use repository pattern matching existing UserRepository — for consistency
- Add new domain exception ExportFailedError — fits existing error layering
- No new dependencies — pandas already available for CSV generation>

## File Inventory

### New files
| Path | Purpose |
|------|---------|
| ...  | ...     |

### Modified files
| Path | What changes |
|------|--------------|
| ...  | ...          |

## Steps

### Step 1: <Short title>
- **Type:** Test | Implementation | Migration | Refactor
- **Files:** <list>
- **Functions/Classes:** <names>
- **What:** <1–2 sentence description>
- **Tests to write/update:** <test file + test names>
- **Acceptance:** <how do we know this step is done? Concrete check.>
- **Depends on:** <prior step numbers, or "none">
- **Estimated commits:** <1–3>

### Step 2: ...

<repeat for all steps. Plans typically have 5–15 steps.>

## Step Dependency Graph

```
Step 1 → Step 2 → Step 3
            ↓
         Step 4 → Step 5
```

<ASCII or bullet list showing which steps unblock which>

## Test Strategy

- **Unit tests**: <list of behaviors covered>
- **Integration tests**: <list of API/DB-level scenarios>
- **E2E / verification**: <how `/rmb-verify` will prove this works>

## Rollback Plan

<if this work touches data or external systems, how do we undo it? Often "revert the merge" is fine. Migrations need an explicit reverse.>

## Open Questions

<anything that needs user input before /rmb-test/build. If empty, plan is ready to execute.>

## Acceptance Criteria Mapping

<table mapping each acceptance criterion from spec to the step that fulfills it>

| Spec criterion | Step(s) |
|----------------|---------|
| ...            | ...     |
```

## Step 4 — Validate

Before saving, self-check:

- [ ] Every acceptance criterion from spec maps to at least one step?
- [ ] Every step has concrete files/functions/tests?
- [ ] Steps are ordered respecting dependencies (no forward references)?
- [ ] Test steps come before implementation steps where applicable?
- [ ] No step is vague (e.g., "implement the feature")?
- [ ] Plan matches repo patterns from repo-knowledge?

If any check fails, revise before writing the file.

## Step 5 — Close out

1. Print path: `Plan saved: D:\plans\<repo>\<slug>\plan.md`
2. Print step count + estimated total commits
3. Print the dependency graph
4. Suggest: `Ready for /rmb-test? It will start Step 1 (test phase).`

## What NOT to do

- Don't write code or pseudo-code in the plan
- Don't ask the user questions — the spec already answered them. If you find a gap, flag it in "Open Questions" and stop.
- Don't auto-trigger `/rmb-test`
- Don't include steps that aren't justified by the spec
- Don't introduce new design patterns that contradict repo knowledge
