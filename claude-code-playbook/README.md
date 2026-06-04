# Claude Code Playbook — what the evidence actually says

Companion repo to a LinkedIn post on **best practices for working with Claude Code, OpenCode, and Copilot on real engineering work** — critical bug fixes, feature builds, and scope changes to features already shipped.

This is not a "tips & tricks" repo. It is a research-anchored playbook. Every practice in `practices.md` is tied to either:

- Anthropic's own primary documentation, OR
- An independent randomized study or longitudinal telemetry report, OR
- Strong consensus across three or more named practitioners (Willison, Ronacher, Reed, Huntley, Böckeler, Osmani).

Where the evidence is thin, `evidence.md` says so. Where the research **contradicts** practices I was personally running, `critique.md` says so.

## What's in here

| File | Purpose |
|---|---|
| `practices.md` | The 10 practices, evidence-ranked |
| `evidence.md` | Citations, study summaries, where the data is thin |
| `critique.md` | Honest self-review — what I changed about my own workflow after this research |
| `workflow.md` | The gates and where context loss happens |
| `skills/` | Sanitized copies of the slash-command skills I run (`rmb-grill-me`, `rmb-plan`, etc.) |
| `case-study.md` | One real piece of work walked through the playbook |

## How to adapt

The skills in `skills/` reference paths and conventions specific to my machine (`D:\plans\…`, `D:\repo-knowledge\…`, my voice patterns). Treat them as a starting template, not a drop-in. The `NOTICE.md` inside `skills/` lists every assumption you should review before adopting.

## Honest caveats

- **No claim of speedup numbers.** The only credible RCT on the topic (METR, July 2025) found experienced developers were *19% slower* with AI tools on familiar codebases — while predicting and self-reporting *faster*. Anyone selling you a percentage is selling you a feeling.
- **No claim that my specific workflow is the right one.** It's an instance of practices that have evidence behind them. Yours will look different.
- **This repo is the post's receipt.** If a practice is in the post, an artifact for it is in this repo. If you can't find one, file an issue.

— Ram Avatar S
