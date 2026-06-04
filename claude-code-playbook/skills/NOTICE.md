# NOTICE — read before adopting these skills

These files are verbatim copies of slash commands I run on my own machine. They are not a clean library — they are field equipment with my fingerprints on them. Adapt before adopting.

## Things you must change

1. **Paths.** The skills reference:
   - `D:\plans\<repo>\<slug>\spec.md` — where specs land
   - `D:\plans\<repo>\<slug>\plan.md` — where plans land
   - `D:\repo-knowledge\<repo>.md` — per-repo knowledge files
   - `.claude/flow-state.json` — flow-state checkpoint

   Change these to whatever fits your machine. The mechanism is what matters; the paths are arbitrary.

2. **Voice.** Several skills contain Hinglish prompts (`"haan"`, `"kuch bhi"`, `"tu decide kar"`). That is my voice — it makes the agent feel like talking to me. Replace with whatever conversational style fits you. Generic English works fine.

3. **Stack assumptions.** Some rules in my global `CLAUDE.md` (loaded alongside these skills) are .NET-specific. The skills themselves are stack-agnostic, but `rmb-build` and `rmb-test` will be more useful if you also have a `repo-knowledge` file describing your stack's test runner, build command, and conventions.

4. **The grilling intensity.** `rmb-grill-me` is deliberately relentless ("vague answers are not acceptable"). If you prefer a softer interview, dial it down. The principle (one question at a time, recommended answer per question, decision-tree depth-first) survives style changes.

## Things you should NOT change (these encode the practices)

| Skill | Don't change | Why |
|---|---|---|
| `rmb-grill-me` | One question at a time | Batching questions is what produces vague answers — see `practices.md` §3 |
| `rmb-grill-me` | Recommended-answer-per-question | Without it, you do the work the model should be doing |
| `rmb-plan` | Plan as separate file, opened in editor | The plan is a contract — `practices.md` §4 |
| `rmb-test` | RED phase before BUILD phase | The agent needs an oracle — `practices.md` §5 |
| `rmb-flow` | Human gates between stages | Skipping the gates defeats the workflow — `workflow.md` |
| `rmb-review` | "Flag only correctness, not nice-to-haves" | Anthropic's own warning — see Reviewer note in `evidence.md` |
| `rmb-verify` | Behavioural run, not just tests | `practices.md` §6 — green tests lie |

## A warning about copy-paste

These skills compose. `rmb-flow` invokes the others; the others write to shared file paths; `flow-state.json` persists state between sessions. If you cherry-pick one skill, you'll get partial value. Either adopt the workflow or skip it.

## License

Use freely. Attribution appreciated. No warranty — these have been tuned for my workflow on a particular kind of work (.NET / EF Core / Cloud Platform engineering). They may behave differently on your codebase.
