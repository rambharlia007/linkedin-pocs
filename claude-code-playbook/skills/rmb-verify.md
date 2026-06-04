---
name: rmb-verify
description: End-to-end proof that the feature works. Spins up the app (background), exercises endpoints / CLI / UI per spec acceptance criteria, inspects DB state, captures evidence. Writes verify.md with logs, responses, screenshots. Stack-aware (Python/FastAPI, .NET). Independent of /rmb-review — review is static, verify is dynamic.
---

# Skill: rmb-verify

Prove the feature works by running it. Not unit tests — actual end-to-end exercise.

@~/.claude/rules/common.md

## Step 1 — Load context

1. Detect repo + slug.
2. Read spec.md (specifically acceptance criteria) and plan.md.
3. Read repo knowledge — specifically the `Common Commands` section for run/test commands.
4. Detect stack from cwd files.

## Step 2 — Pre-flight

Before starting the app:

1. Check dependencies installed:
   - Python: `pip list | grep <key-dep>` or `uv sync` if uv.lock exists
   - .NET: `dotnet restore`
2. Check DB is available (if needed):
   - Read connection string from config
   - Try `psql -c "SELECT 1"` or equivalent for SQL Server
   - If DB down, attempt `docker-compose up -d db` if docker-compose.yml exists
3. Run migrations if any are pending:
   - Python: `alembic upgrade head`
   - .NET: `dotnet ef database update`
4. If anything fails, capture error and write to verify.md with status `BLOCKED — preflight`. Stop.

## Step 3 — Start the app (background)

Use the project's standard run command from repo knowledge:
- Python FastAPI: `uvicorn app.main:app --host 127.0.0.1 --port 8765 --log-level info` (background)
- .NET: `dotnet run --project <ApiProject> --urls http://127.0.0.1:8765` (background)

Capture stdout/stderr to a log file: `D:\plans\<repo>\<slug>\verify-app.log`.

Wait for readiness:
- Poll `http://127.0.0.1:8765/health` or `/docs` (FastAPI) or `/swagger` (.NET) up to 30 seconds
- If not ready in 30s, capture last 50 lines of app log, status `FAILED — startup`, stop

## Step 4 — Exercise the feature

For each acceptance criterion in spec.md, do at least one concrete exercise:

### If feature is an API endpoint
- Use `curl` or `httpx` (Python) / `Invoke-RestMethod` (PowerShell) — match the OS
- Call the endpoint with valid input → capture response (status, headers, body)
- Call with invalid input → confirm correct error response
- Capture every request/response to verify.md

### If feature involves DB writes
- Before the call, snapshot relevant table state (`SELECT COUNT(*), MAX(id)` etc.)
- After the call, snapshot again and diff
- Capture: before → call → after

### If feature involves background jobs / queues
- Trigger the job
- Watch the queue/log for completion
- Verify side effects (DB row, file written, email sent, etc.)

### If feature is CLI
- Run with realistic inputs, capture stdout/stderr/exit code

### If feature is UI
- Note: full UI verification needs chrome-devtools-mcp. If UI changes detected, recommend running `/ui-data-flow-debug` or `/run` skill separately.
- For this skill, focus on backend; mark UI verification as "manual follow-up needed" if relevant.

## Step 5 — Inspect DB state

If the feature touches the database:
- Run targeted SELECT queries on affected tables
- Capture row counts, key column values
- Compare against expected end state from spec

## Step 6 — Tear down

1. Stop background app process (capture exit cleanly)
2. Don't drop DB or roll back data — leave state for human inspection unless plan says otherwise
3. Clean up only temp files we created

## Step 7 — Write verify.md

Path: `D:\plans\<repo>\<slug>\verify.md`

```markdown
# Verify: <slug>

**Verified:** <YYYY-MM-DD HH:MM>
**Stack:** <Python+FastAPI | .NET | ...>
**App start:** <success | failed>
**Overall result:** ✅ PASS | ❌ FAIL | ⚠️ PARTIAL

## Preflight

- Deps installed: ✅
- DB reachable: ✅
- Migrations applied: ✅ (<N migrations>)

## App Startup

- Command: `<run command>`
- Ready in: <Xs>
- Health check: ✅ <url> → 200

## Acceptance Criteria Verification

<for each criterion from spec:>

### ✅ Criterion 1: <text from spec>

**Exercise:**
```
<the actual curl / call>
```

**Result:**
```http
HTTP/1.1 201 Created
Content-Type: application/json

{"id": 42, "status": "created"}
```

**DB state:**
- Before: `users` row count = 100
- After:  `users` row count = 101, new row id=42 with email=test@example.com

**Verdict:** PASS

---

### ❌ Criterion 2: ...

<show the failure clearly — expected vs actual>

---

## Observations

<anything not covered by criteria but worth noting — perf, logs, warnings>

## Artifacts

- App log: ./verify-app.log
- Captured responses: inline above

## Manual Follow-up Needed

<anything that this skill can't verify, e.g., UI rendering, email delivery, browser behavior>

## Recommended Next Action

<one of:
- "All criteria pass — `/rmb-ship`"
- "N criteria failed — `/rmb-build` to fix"
- "Partial — manual UI check needed before ship">
```

## Step 8 — Close out

1. Print verify.md path
2. Print overall result + criteria pass count
3. Print recommended next action

## Hard Rules

- **Never modify production code** during verify. If something's broken, report it.
- **Never destroy data** without explicit user approval (no `DROP`, no `DELETE *`, no `TRUNCATE`).
- **Always stop background processes** before exiting, even on failure.
- **If the app won't start, don't fake success.** Status FAILED.
- **Don't ask user questions** — capture what happened, write the report.

## What NOT to do

- Don't run unit tests — that's separate
- Don't deploy anywhere — only localhost
- Don't talk to production DBs, real third-party APIs, or anything with cost. Mock/stub external deps if needed.
- Don't keep running app indefinitely — always tear down
