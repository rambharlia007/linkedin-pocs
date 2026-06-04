---
name: rmb-review
description: Reviews the current branch diff against spec, plan, repo patterns, and rules. Outputs review.md with issues categorized by severity. Auto-fixes safe nits (formatting, naming, dead code). Flags non-trivial issues for the user. Standalone — works on any branch, even without spec/plan, but better with them.
---

# Skill: rmb-review

Read the branch diff. Check it against everything we know. Auto-fix what's safe. Report what's not.

@~/.claude/rules/common.md

## Step 1 — Load context

1. Detect repo + slug.
2. Read `D:\plans\<repo>\<slug>\spec.md`, `plan.md`, and `plan.delta.md` if present. Note: review still works without these — just skip the spec/plan compliance checks.
3. Read `D:\repo-knowledge\<repo>.md`.
4. Read `D:\plans\<repo>\<slug>\DECISIONS.md` if present — understand why certain choices were made.
5. Load stack rules:
   - Python → `@~/.claude/rules/python-fastapi.md`
   - .NET → `@~/.claude/rules/dotnet.md`
6. Repo override → `<repo>/.claude/RULES.md`.

## Step 2 — Compute the diff

1. Find merge base: `git merge-base HEAD <main-branch>` (try `main`, `master`, `develop` in order)
2. `git diff <base>...HEAD` — full diff of changes since branching
3. List changed files. For each, note: added, modified, deleted, lines changed.

## Step 3 — Review across 5 dimensions

For each changed file, evaluate against:

### 3.1 SPEC compliance
- Does the change implement what spec asks for?
- Does it stay within scope (no out-of-scope additions)?
- Is every acceptance criterion in spec satisfied somewhere in the diff?

### 3.2 PLAN coverage
- Does every plan step (including delta) show up in the diff?
- Are there changes that DON'T correspond to any plan step? → Flag as scope creep.
- Are there plan steps with no corresponding diff? → Flag as incomplete.

### 3.3 Rules compliance
For each violation of `common.md` + stack rules + repo override:
- File + line
- Rule violated (quote it)
- Severity: blocker | major | minor | nit
- Suggested fix

### 3.4 Repo pattern consistency
- Does new code match existing patterns from repo knowledge?
- New abstractions where existing ones would work?
- New dependencies that duplicate existing libs?
- Naming consistent with repo conventions?

### 3.5 Code quality (universal)
- Functions too long
- Duplicate logic (DRY)
- Dead code / commented-out code
- Magic numbers/strings
- Bad error handling (silent catch, swallowed exceptions)
- Missing tests for new behaviors
- Security: SQL injection, XSS, unescaped input at boundaries
- Performance: N+1 queries, sync I/O in async paths, missing indexes

## Step 4 — Categorize and auto-fix

For each issue, assign severity:

| Severity | Action |
|----------|--------|
| **Blocker** | Bug, security issue, broken functionality, missing required logic | Report only — never auto-fix critical paths |
| **Major** | Rule violation that affects correctness or maintainability | Report. Auto-fix only if 100% safe (e.g., remove unused import) |
| **Minor** | Style, naming, structure — doesn't affect behavior | Auto-fix if mechanical (formatting, renaming, dead code removal) |
| **Nit** | Preference, polish | Auto-fix |

**Auto-fix means: edit the file, stage the change, commit with `chore: review auto-fixes (rmb-review)`. Don't push.**

## Step 5 — Write review.md

Path: `D:\plans\<repo>\<slug>\review.md` (if no slug, write to `<repo>\.claude\review-<date>.md`)

```markdown
# Review: <slug or branch name>

**Reviewed:** <YYYY-MM-DD>
**Base:** <merge-base hash>
**HEAD:** <head hash>
**Files changed:** <count>
**Lines:** +<added> / -<removed>

## Summary

<2–3 sentences on overall verdict: "ready to ship" / "needs fixes" / "major rework">

## Spec & Plan Compliance

- [x] All acceptance criteria from spec covered
- [ ] One plan step missing (Step 5: error logging)
- [x] No out-of-scope changes detected

<flag any gaps with specific references>

## Issues by Severity

### 🚫 Blockers (N)
<for each:>
**[file:line]** <one-line title>
- Issue: <description>
- Why it matters: <impact>
- Suggested fix: <action>

### ⚠️ Major (N)
...

### 📝 Minor (N)
...

### ✅ Auto-fixed (N)
<list of nits/minors that were automatically corrected, with commit hash>

## Repo Pattern Consistency

<observations — what matches, what diverges. Each divergence: file:line + suggestion>

## Test Coverage

- New behaviors: <count>
- Behaviors with tests: <count>
- Behaviors without tests: <list with file references>

## Security / Performance Notes

<anything flagged in 3.5 that warrants attention even if not strictly a blocker>

## Decisions Audit

<for each entry in DECISIONS.md, sanity-check: was the decision sound given what we now see in code? If any decision is now questionable, flag it.>

## Recommended Next Action

<one of:
- "Ship — `/rmb-verify` and `/rmb-ship`"
- "Address N blockers before shipping. Suggested order: [list]"
- "Major rework needed. Consider `/rmb-amend` to revise the plan.">
```

## Step 6 — Close out

1. Print review path
2. Print issue counts by severity
3. If auto-fixes were committed, print the commit hash
4. Suggest next action explicitly

## What NOT to do

- Don't auto-fix anything in `Blocker` or `Major` severity categories that touches business logic
- Don't run tests — that's `/rmb-verify`'s job. Review is static analysis.
- Don't suggest improvements unrelated to spec/plan/rules (no "while we're here" cleanups)
- Don't approve a diff that contradicts a decision in DECISIONS.md without flagging it
- Don't ask the user questions — produce the report, let them decide
