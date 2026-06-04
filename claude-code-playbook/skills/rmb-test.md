---
name: rmb-test
description: TDD red phase. Writes failing tests for the next pending step in plan.md, runs them to confirm they fail for the right reason, then commits. No production code is touched. Hands off to /rmb-build to make them pass.
---

# Skill: rmb-test

Write the failing tests for the next pending step in plan.md. Confirm they fail correctly. Commit. Stop.

@~/.claude/rules/common.md

## Step 1 — Load context

1. Detect repo + slug.
2. Read `D:\plans\<repo>\<slug>\spec.md` and `plan.md`. If delta exists, also read `plan.delta.md`.
3. Read `D:\repo-knowledge\<repo>.md`.
4. Load stack-specific rules:
   - Python → `@~/.claude/rules/python-fastapi.md`
   - .NET → `@~/.claude/rules/dotnet.md`
5. Check for repo override `<repo>/.claude/RULES.md`.

## Step 2 — Find next test step

1. Read existing branch state. Look for a `.claude/flow-state.json` (created by `/rmb-flow`) for current step pointer.
2. If no state, find the lowest-numbered step in plan.md (and delta if present) where:
   - Type is `Test`, or
   - Type is `Implementation` but its corresponding test step hasn't been done
3. Identify the test files this step requires (from the step's "Tests to write/update" field).
4. If no pending test step, report: **"All test steps complete. Run `/rmb-build` for implementation."** and stop.

## Step 3 — Write the tests

For each test file listed:

1. If file exists, read it. Add new test functions/methods, don't overwrite existing tests.
2. If file doesn't exist, create it following the repo's test conventions (location, naming, imports).
3. Each test must:
   - Have a name that describes the behavior under test (not the implementation)
   - Be hermetic (no external network, no shared state)
   - Cover one behavior — multiple `assert` lines OK if they describe the same behavior
   - Use the same test framework + fixture style as existing tests (from repo knowledge)
4. Use Pydantic models / DTOs from the actual codebase when constructing inputs. Don't invent shapes.
5. For integration tests, use the same `TestClient` / `WebApplicationFactory` pattern the repo already uses.

## Step 4 — Run the tests

Detect the test command from repo knowledge or:
- Python: `pytest <path-to-new-tests> -xvs`
- .NET: `dotnet test --filter "FullyQualifiedName~<TestClassName>"`

Expected outcome: **tests FAIL**. That's the point.

- If a test passes unexpectedly → the implementation already covers this case (rare). Note it, mark the test as `@pytest.mark.skip(reason="pre-existing behavior, no impl needed")` OR delete it if redundant. Add a note to plan.md.
- If a test fails for the WRONG reason (import error, syntax error, fixture broken) → fix the test, re-run. Don't proceed until tests fail for the RIGHT reason (assertion failure / NotImplementedError).
- If a test errors due to missing module/function → that's expected — the impl doesn't exist yet. Treat as a correct red.

## Step 5 — Commit

```
git add <test files>
git commit -m "test: <step title> (red)"
```

Commit message format:
- `test: <step-title> (red)` — for new test additions
- `test: amend <test-name>` — for tweaks to existing tests

## Step 6 — Close out

1. Print summary:
   ```
   Step N: <title>
   Tests added: <count>
   Files: <list>
   All failing as expected: yes
   Commit: <short hash>
   ```
2. Suggest: `Ready for /rmb-build to make these pass.`
3. If part of `/rmb-flow`, update `.claude/flow-state.json` to mark test phase done for this step.

## What NOT to do

- Don't write any production code — implementation is `/rmb-build`'s job
- Don't write tests for steps not yet started
- Don't proceed with a passing-when-it-should-fail test — investigate first
- Don't commit if any test fails for the wrong reason (import error, fixture issue)
- Don't ask the user questions — the spec/plan already answered them. If genuinely stuck, log to `DECISIONS.md` and pick the most defensible option.
