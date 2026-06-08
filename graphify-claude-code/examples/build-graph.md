---
name: build-graph
description: Build a Graphify knowledge graph for a repo, with centralized output (~/graphs/<repo>/ convention), .graphifyignore safety, and AST-only mode by default. Idempotent — re-runs use --update.
arguments:
  - name: repo-path
    description: Path to the repo to graph. Defaults to current working directory.
    required: false
---

# /build-graph

Drop this file into `~/.claude/commands/build-graph.md` (or your project's `commands/`) so you can run `/build-graph <repo-path>` from any Claude Code session.

## What it does

1. Resolves `<repo-path>` — uses the argument if given, otherwise cwd.
2. Verifies it's a repo root (has `.git/`, or a `*.sln` / `*.csproj` / `pyproject.toml` / `package.json`). If not, asks the user to confirm.
3. Derives `<repo-name>` from `git remote get-url origin` (preferred) or the folder name as fallback.
4. Centralized output path: `~/graphs/<repo-name>/`. The skill creates the directory if missing.
5. Ensures `<repo-path>/.graphifyignore` exists. If missing, copies a sensible default for the stack (Python `.venv`, `__pycache__`; .NET `bin`, `obj`, `.vs`; Node `node_modules`, `dist`, `.next`; plus `graphify-out/`, `*.log`, lock files, and large knowledge corpora under `knowledge/`).
6. Checks whether `~/graphs/<repo-name>/graphify-out/graph.json` already exists.
   - **Yes** → runs `graphify update <repo-path>` (incremental, free, no LLM).
   - **No** → runs `graphify <repo-path>` for a fresh build.
7. Reports the path to `GRAPH_REPORT.md` and prints the top God Nodes (most connected abstractions).

## How to invoke

```
/build-graph                                  # graphs the current cwd
/build-graph C:\path\to\repo                  # graphs the given path
/build-graph ~/code/backend                   # graphs a path via tilde
```

## Implementation

The skill's body, in plain instructions to Claude — adapt the centralized output convention if you use a different root than `~/graphs/`:

```markdown
**Step 1 — Resolve repo path.** If a `repo-path` argument was provided, use it. Otherwise use cwd. If the path doesn't look like a repo root (no `.git/`, no `*.sln`, no `pyproject.toml`, no `package.json`), ask the user once: "Path `<path>` doesn't look like a repo root. Use it anyway? (y/n)".

**Step 2 — Derive repo name.** Try `git -C <repo-path> remote get-url origin` and parse the repo slug from the URL. If it fails, fall back to the folder name. Store as `<repo-name>`.

**Step 3 — Resolve output path.** `<out-path>` = `~/graphs/<repo-name>`. Create the directory if it doesn't exist.

**Step 4 — Ensure `.graphifyignore` exists in the repo root.** If `<repo-path>/.graphifyignore` is missing, write a default tailored to the stack. Detect the stack by looking for `*.csproj`/`*.sln` (.NET), `pyproject.toml`/`requirements.txt` (Python), `package.json` (Node) and combine the relevant blocks. Always include `graphify-out/`, `*.log`, lock files, and `knowledge/` (large doc corpora).

**Step 5 — Build or update.** Check whether `<out-path>/graphify-out/graph.json` exists.
- If it exists → `cd <out-path>; graphify update <repo-path>` (incremental, free, no LLM).
- If it doesn't → invoke the `/graphify` Skill tool with `args: "<repo-path>"` from inside `<out-path>` so the output lands at `<out-path>/graphify-out/`. The skill routes semantic extraction through Claude Code subagents — no API key needed.

**Step 6 — Report.** Print: `Graph ready: <out-path>/graphify-out/GRAPH_REPORT.md`. Then read the report and paste the God Nodes section (top 10 most-connected abstractions) so the user can immediately see what the graph found. Offer to run a follow-up query: "Want me to trace the most interesting question this graph can answer?"

## What NOT to do

- Don't write to `<repo-path>/graphify-out/` — that pollutes the working tree. Always centralize.
- Don't run `--mode deep` without explicit user opt-in — it dispatches LLM subagents which cost tokens.
- Don't skip the `.graphifyignore` check — without it, Graphify can scan 10k+ noise files from `.venv` and bundled docs.
- Don't auto-trigger any follow-up skill (`/rmb-grill-me`, etc.). Build the graph, report, stop.
```

## Why this design

- **One command, one job** — build a graph. Doesn't grill, doesn't review, doesn't write specs. Other skills consume the graph; this one produces it.
- **Idempotent** — if you re-run it, you get a `graphify update` (fast, incremental) instead of a full rebuild.
- **Stack-aware default ignore** — most teams never write a `.graphifyignore`. The skill writes a sensible one so the first build doesn't balloon.
- **Centralized output** — keeps `graphify-out/` out of every repo working tree. Easier to gitignore globally and easier to query across multiple graphs.

## Adapt the convention to your setup

The example uses `~/graphs/<repo-name>/`. Pick whatever fits — `/Users/<you>/code-graphs/<repo>/`, `D:\graphs\<repo>\`, `~/.cache/graphify/<repo>/`. Just be consistent: any skill that *reads* a graph should expect the same convention.
