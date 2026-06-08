# Graphify + Claude Code — the setup that changed how Claude reads my codebases

When Claude Code greps a fifteen-hundred-file repo to answer a structural question, it reads twenty files, costs three dollars, and still misses the obscure middleware your last engineer added without docs.

When Claude Code queries a knowledge graph of the same repo, it answers in three calls — and surfaces edges you would never have known to grep for.

This is the setup I now use on every non-trivial codebase.

---

## What is Graphify

[Graphify](https://github.com/safishamsi/graphify) is an open-source tool (MIT, 60k+ stars) that turns any folder of code, docs, papers, or images into a queryable knowledge graph. Tree-sitter for code (free, local, deterministic). LLM semantic extraction for docs (optional, routed through your Claude Code session — no separate API key needed).

The output is a graph with nodes (functions, classes, files, concepts) and edges (calls, imports, references, "uses"). You query it with `graphify explain`, `path`, `affected`, `query`. It is the structural map of your repo, persistent across sessions.

---

## Why this matters more than "faster grep"

The first time I used it on a real repo, I expected speed. What I got was completeness.

Ask `graphify explain "AuthMiddleware"` and you get every inbound and outbound edge of that node — including:

- Service-to-service token validation paths
- Tenant isolation checks
- Resource caps applied to user input
- Internal record-activity endpoints
- The middleware your team added six months ago and forgot to document

Grep finds only what you ask for. The graph surfaces what you did not know to ask. That is the real win — fewer missed edge cases, not faster answers.

---

## Installation

There are three install steps — two one-time (machine + user-global) and one per-project.

```powershell
# 1. Install the CLI — machine-wide, one time
#    PyPI package is "graphifyy" (double-y); CLI command is "graphify"
uv tool install graphifyy

# 2. Register Graphify as a Claude Code skill — user-global, one time
#    Writes ~/.claude/skills/graphify/ and adds a trigger line to ~/.claude/CLAUDE.md
graphify install

# 3. Wire Graphify into a specific project — per project, run from inside the repo
#    Adds a PreToolUse hook so Claude auto-checks the graph before search-style tool calls
cd <your-repo>
graphify claude install
```

Step 3 is what makes Graphify "always-on" for that project — without it, Claude only reaches for the graph if your CLAUDE.md tells it to (see the [graph-first navigation snippet](./examples/CLAUDE.md.snippet) for that alternative).

Alternative installers if you do not have `uv`:

```powershell
pipx install graphifyy
# OR
pip install graphifyy   # may need to add Python's Scripts dir to PATH
```

Verify:

```powershell
graphify --version
```

### Other AI assistants

If you use Codex, OpenCode, OpenClaw, or Factory Droid alongside (or instead of) Claude Code, swap step 3 for the matching install command — these platforms do not support PreToolUse hooks, so Graphify falls back to writing the rules into `AGENTS.md` in your project root:

| Platform        | Command                       | Mechanism                          |
|-----------------|-------------------------------|------------------------------------|
| Claude Code     | `graphify claude install`     | CLAUDE.md + PreToolUse hook        |
| Codex           | `graphify codex install`      | AGENTS.md                          |
| OpenCode        | `graphify opencode install`   | AGENTS.md                          |
| OpenClaw        | `graphify claw install`       | AGENTS.md                          |
| Factory Droid   | `graphify droid install`      | AGENTS.md                          |

Codex users also need `multi_agent = true` under `[features]` in `~/.codex/config.toml` for parallel extraction.

---

## Building a graph for a repo

### Step 1 — Drop a `.graphifyignore` (do this first on any non-trivial repo)

Graphify's built-in defaults skip `node_modules`, `__pycache__`, `.git`, `venv`, `dist`. But they do NOT skip:

- `.venv` (dot-prefixed — the modern Python convention)
- `bin/`, `obj/` (the .NET artifact dirs)
- Large knowledge corpora in `knowledge/` folders
- K8s / Helm / deploy manifests

Without an ignore file, a typical mid-sized polyglot repo balloons from ~1500 useful files to 10k+ files scanned. See [`examples/.graphifyignore`](./examples/.graphifyignore) for a battle-tested template covering Python, .NET, Node, and infra.

```powershell
# Copy the template into your repo root before building:
cp graphify-claude-code/examples/.graphifyignore <your-repo>/.graphifyignore
```

### Step 2 — Centralize the output (don't pollute the repo)

By default Graphify writes to `<cwd>/graphify-out/`, which leaves a 30+ MB folder inside your repo. Instead, centralize per-repo:

```powershell
# One-time: pick a root for all graphs
mkdir D:\graphify

# Per repo: cd to the centralized location, point at the repo source
cd D:\graphify\<repo-name>
graphify C:\path\to\your\repo
```

This nests outputs at `D:\graphify\<repo-name>\graphify-out\` — never inside the repo itself.

### Step 3 — Build

```powershell
graphify .            # full build of cwd
graphify <path>       # full build of an explicit path
graphify . --update   # incremental — only re-process changed files (no LLM needed)
graphify . --watch    # auto-rebuild on file changes
```

On Windows PowerShell, use `graphify .` (no leading slash — PowerShell parses `/` as a path).

For a 1500-file polyglot repo: ~2 minutes for AST extraction (free, local). Semantic extraction of docs is dispatched through Claude Code subagents — no extra API key.

### Step 4 — Verify

```powershell
graphify explain "<some core abstraction in your repo>"
```

If you get a node summary back with inbound/outbound edges, the graph works.

---

## Using it in normal Claude Code queries

This is the highest-leverage setup. One line in your global CLAUDE.md and Claude reaches for the graph on every structural question, no slash command needed.

See [`examples/CLAUDE.md.snippet`](./examples/CLAUDE.md.snippet) for the exact block to append to `~/.claude/CLAUDE.md`.

The short version:

```markdown
## Graph-first code navigation

When working in a repo, FIRST check whether a Graphify graph exists.
If it does, prefer graph queries over grep/glob/read for structural questions:

| Question                              | Use this, not grep                    |
|---------------------------------------|---------------------------------------|
| "What calls X / affected by X?"       | graphify affected "X" --depth 2       |
| "How does X work / what does it touch?" | graphify explain "X"                |
| "How does A connect to B?"            | graphify path "A" "B"                 |
| "What is the pattern for Y?"          | graphify query "<natural-language>"   |

Fall back to grep/read only for line-level content inside files.
```

Once that is in place, ask Claude something like "how does authentication wire into our endpoints" in any session. Watch it run `graphify query` or `graphify explain` instead of grep. It is jarring the first time.

---

## A reusable `/build-graph` slash command

Building a graph involves four small decisions every time: where to put the output, which `.graphifyignore` to use, whether to do a fresh build or an incremental `update`, and how to handle the first-run subagent dispatch. After doing it manually a few times, I wrapped it in a slash command so I never have to remember any of that again.

See [`examples/build-graph.md`](./examples/build-graph.md) — drop it into `~/.claude/commands/build-graph.md` and run:

```
/build-graph                       # graphs cwd
/build-graph <repo-path>           # graphs the given path
```

The skill:

- Centralizes output to `~/graphs/<repo-name>/` (configurable in the file)
- Writes a stack-appropriate `.graphifyignore` if one doesn't already exist
- Detects whether a graph is already there → runs `graphify update` if yes (incremental, free), full build if no
- Reports the GRAPH_REPORT path and prints the top God Nodes when done

Idempotent. Stop worrying about ignore files and output paths.

---

## Best practices I picked up the hard way

| Practice | Why |
|---|---|
| Always drop a `.graphifyignore` before the first build | Avoid scanning 10k+ noise files from `.venv` and knowledge corpora |
| Centralize graphs to `D:\graphify\<repo>\` (or `~/graphs/<repo>/`) | Keeps the repo working tree clean, makes cross-repo merging easier |
| For AST-only repos (no docs to extract), build runs in ~2 minutes free | Tree-sitter parsing is local and deterministic, no LLM cost |
| Use the Claude Code skill route, not bare `graphify .` from PowerShell, when docs need semantic extraction | The skill routes through Claude Code subagents — no API key required |
| Read `GRAPH_REPORT.md` first on a new repo | It lists God Nodes, communities, import cycles, weakly-connected nodes — instant orientation |
| Use `graphify update` after code changes | Incremental, free, no LLM |
| For huge repos (>10k files), narrow to subfolders | `graphify <repo>/backend` instead of the whole monorepo |

---

## Gotchas

**1. `.graphifyignore` is ignored by `collect_files()` ([issue #188](https://github.com/safishamsi/graphify/issues/188))**

The bug is real but only affects the bare `graphify extract` CLI flow. The official skill flow (which uses `detect()` first) respects `.graphifyignore`. If you hit it, run via the skill or use `graphify update` instead.

**2. `query` / `path` / `explain` / `affected` ignore `GRAPHIFY_OUT` ([issue #756](https://github.com/safishamsi/graphify/issues/756))**

These subcommands hardcode `./graphify-out/graph.json` relative to cwd. To query a centralized graph, `cd D:\graphify\<repo>` first, then run the query.

**3. `.venv` (dot-prefixed) is NOT in built-in skips**

Only `venv` (no dot) is. If your repo uses `.venv` (modern Python convention), add it to `.graphifyignore` explicitly.

**4. Bare CLI prompts for ANTHROPIC_API_KEY when docs are present**

That prompt is misleading. The skill flow uses Claude Code's session for semantic extraction — no key needed. Run via the `/graphify` slash command in Claude Code, not from bare PowerShell.

**5. 1594 communities on a real repo? Yes.**

Communities scale with codebase complexity. The labeling step is optional — skip it (or use `--no-cluster`) if you only care about God Nodes and the graph's queryability.

---

## What I shipped on top

- **CLAUDE.md addition** — see [`examples/CLAUDE.md.snippet`](./examples/CLAUDE.md.snippet). Once installed, Claude reaches for graph queries automatically on structural questions.
- **Generic skill template** — see [`examples/skill-template.md`](./examples/skill-template.md). Adapt it for your own context-aware slash commands.
- **`.graphifyignore` template** — see [`examples/.graphifyignore`](./examples/.graphifyignore). Covers Python, .NET, Node, infra.

---

## References

- Graphify repo: https://github.com/safishamsi/graphify (MIT, 60k+ stars)
- Claude Code integration page: https://graphify.net/graphify-claude-code-integration.html
- CLI reference: https://graphify.net/graphify-cli-commands.html
- Issue #188 (`.graphifyignore` bypass): https://github.com/safishamsi/graphify/issues/188
- Issue #756 (`GRAPHIFY_OUT` not respected by query subcommands): https://github.com/safishamsi/graphify/issues/756
