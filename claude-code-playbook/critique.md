# Critique — what I changed about my own workflow

This document exists because the research that produced this playbook **disagreed with how I had been running Claude Code**. Publishing the practices without naming the disagreements would be dishonest.

## What I was doing before

I leaned heavily on three things, all driven by skills/commands:

1. **A large slash-command library.** `/rmb-grill-me`, `/rmb-plan`, `/rmb-test`, `/rmb-build`, `/rmb-review`, `/rmb-verify`, `/rmb-ship`, `/rmb-amend`, `/rmb-scan`, `/rmb-system-design`, `/rmb-flow` — and more. Almost every action was a slash command.
2. **A workflow skill (`/rmb-flow`) that chained them.** Grill → plan → user gate → test + build loop → review → verify → ship. State persisted in `.claude/flow-state.json`. Designed for "set and walk away."
3. **A heavy global `CLAUDE.md`** with PBI rules, .NET rules, Python/FastAPI rules, common rules — all loaded every turn.

The intuition: discipline scales when it is encoded. If the agent runs through gates, I cannot skip them by accident.

## What the research said

| Research finding | What it implied about my workflow |
|---|---|
| Ronacher (production daily user): "elaborate slash commands didn't stick — `/fix-bug`, `/commit`, `/add-tests`, `/fix-nits` got abandoned." | My slash library is on the edge of this critique. It survives only to the extent it encodes genuine multi-step gates, not because slashing helps. |
| Anthropic: "Bloated `CLAUDE.md` files cause Claude to ignore your actual instructions." | My global CLAUDE.md was approaching the size where rules start getting silently dropped. |
| Ronacher: "Subagents don't parallelize well — especially mixing reads and writes." | I was tempted to fan out subagents for everything. Restraint required. |
| Ronacher: hooks delivered "negligible efficiency gains." | I had wired hooks for things they didn't earn. |
| METR: experienced devs were *19% slower* with AI, while *predicting* 24% faster. | The biggest lesson. The feeling of speed and the measurement of speed are different variables. Every workflow optimization needs to be evaluated against actual outcomes, not how productive it *feels*. |

## What I changed

1. **Pruned the slash library.** Kept only the commands that encode multi-step workflows with state: `/rmb-grill-me`, `/rmb-plan`, `/rmb-test`, `/rmb-build`, `/rmb-flow`. Retired the rest — for those, plain prompts work as well or better.
2. **CLAUDE.md on a diet.** Moved conditional, sometimes-relevant content into skills (loaded on demand). The global CLAUDE.md now carries only rules that must be active every turn.
3. **Hooks reserved for the push gate and lint.** Not for things the model can be reminded about in-prompt.
4. **Subagents only for reads.** Investigation, code search, research. Writes stay in the main session unless worktree-isolated.
5. **Replaced "set and walk away" with "set and check at every gate."** `/rmb-flow` still chains the stages, but I no longer treat the chain as a fire-and-forget. The gates are where I catch the agent going sideways — skipping the gates defeats the workflow.

## What I did *not* change

- **Spec-first, plan-as-contract, test-first.** All three are corroborated by both Anthropic's primary docs and Harper Reed's published workflow. Strongest evidence on the list.
- **Per-push approval.** Not in Anthropic's official guide, but practitioner consensus is unanimous. I had this right.
- **Reading every diff.** GitClear's churn data is the macroscopic argument for it. I had this right.

## What I am still uncertain about

- **Skills vs slash commands** as the right form factor for a workflow. Anthropic introduced skills (`SKILL.md`) as on-demand alternatives to slash commands. My current library is half-slash, half-skill, with no clear principle. Worth a future post.
- **How much of the perceived speedup is real.** I have not run my own measurement. METR has *one* high-quality RCT — narrow population. My confidence interval on "this workflow makes me faster on real work" is wider than my feelings suggest. So is yours.
