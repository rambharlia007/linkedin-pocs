# The 10 practices

Evidence-ranked. Tag legend:
- **[primary]** — Anthropic's published documentation.
- **[study]** — Independent randomized trial or longitudinal telemetry.
- **[consensus]** — Strong agreement across three or more named practitioners.
- **[folklore]** — Repeated by experienced practitioners, no published study. Use, but do not quote numbers.

---

## 1. Treat context as a budget, not a window — **[primary]**

Anthropic's own guidance opens with this: *"Most best practices are based on one constraint: Claude's context window fills up fast, and performance degrades as it fills."* Every other practice on this list is a consequence.

**Mechanics:** `/clear` between unrelated tasks. `/compact "focus on X"` when you can't clear. `/btw` for one-off questions whose answer must not enter history. Custom status line to track tokens — if you don't measure it, you won't manage it.

## 2. The two-correction rule — **[primary]**

After two failed corrections on the same issue, the context is poisoned with failed approaches. A third correction usually does not work. `/clear` and rewrite the prompt with what you learned in the failed attempts.

**Why:** the model's reasoning is now anchored on its own wrong premises plus your pushback. RLHF rewards conversational harmony, so it will tend to flip rather than reason — *"retracts findings faster than it launches them."* Distrust the flip.

## 3. Spec in one session, implement in another — **[consensus]**

The two-session pattern: in session A, interview the model and produce `spec.md` (Matt Pocock-style grilling; Anthropic's "interview me" recipe; Harper Reed's spec phase). Discard session A. In session B, hand the spec to a fresh model and implement.

**Why:** the conversation that produced the spec is *not* the right context for implementation. It carries every false start and clarification. The spec carries only the conclusions.

## 4. The plan is a contract, not a draft — **[primary]**

After spec, generate a plan with concrete file paths, function names, test cases. Open it in your text editor (Claude Code: `Ctrl+G`). Edit it like a PR description. *Then* approve.

**Why:** if you let the model rewrite the plan during implementation, you don't have a contract — you have a moving target. The plan's job is to make scope changes visible.

## 5. Provide a runnable check, or you become the check — **[primary]**

*"Claude stops when the work looks done. Without a check it can run, 'looks done' is the only signal available."* Provide tests, build exit codes, linter output, fixture diffs, screenshots — anything binary. Then gate the stop on it (Stop hook, `/goal`, or in-prompt iteration).

If you don't, you become the verification loop. Every mistake waits on you to notice. That's the slowdown the METR study measured.

## 6. Behavioural verification beats green tests — **[study]**

Tests are necessary, not sufficient. Run the actual app. Click the button. Watch the screen. The "compiles but wrong" failure class is what GitClear's 2024–2025 churn data fingerprints: AI-touched code is revised within two weeks at 7.9% vs 5.5% in 2020.

For .NET specifically: green xUnit + Testcontainers does not prove a SignalR hub still works end-to-end. Run it.

## 7. Subagents for reads, main session for writes — **[primary + practitioner]**

Anthropic: delegate exploration to subagents so the main context stays clean. Ronacher (production user): *"subagents don't parallelize well, especially mixing reads and writes."*

**Rule:** parallel investigation is fine. Parallel writes to the same tree race and corrupt each other's assumptions. Worktrees solve this for genuinely independent writes; default to single-writer otherwise.

## 8. Push is a privileged boundary — **[folklore — strong practitioner consensus, no formal study]**

Every `git push`, every `dotnet ef database update`, every deploy needs a fresh human approval per action. Session-level trust does not transfer to irreversible actions.

This is **not in Anthropic's official best-practices doc**. It comes from practitioners who learned it once and never forgot. If your tooling can't enforce it (most can't out of the box), wire it via a hook or a slash command — the friction is the feature.

## 9. Read every diff. Accept-all is a category error — **[study + consensus]**

Birgitta Böckeler's framing: the actual skill is *"intervene, correct, steer."* Accept-all is not a workflow, it's a surrender.

GitClear data:
- Cloned/copy-paste lines: 8.3% → 12.3% (2021–2024).
- Refactored ("moved") lines: 24.1% → 9.5%.
- 2-week revision rate: 5.5% → 7.9%.

The macroscopic fingerprint of teams that stopped reading diffs.

## 10. Verify every AI-suggested dependency — **[study]**

Slopsquatting is real. Snyk and Trend Micro document 5–38% of LLM-suggested package names are hallucinations; attackers now pre-register the common ones. Bar Lanyado's PoC package (`huggingface-cli`, hallucinated) got 30,000+ real downloads from real engineers.

Before `dotnet add package` / `pip install` / `npm install`: check the package exists, has download history matching its claimed age, and isn't a one-character typo of a real one.

---

## Practices I deliberately did *not* include

- **"Build elaborate hooks."** Ronacher (Claude Code daily): *"negligible efficiency gains."* Anthropic recommends them only for things that must happen with zero exceptions. Useful for push-gate and lint; oversold otherwise.
- **"Build a big slash-command library."** Ronacher abandoned `/fix-bug`, `/commit`, `/add-tests`, `/fix-nits`. They didn't stick. Slash commands earn their keep when they encode genuine multi-step workflows with arguments — not as wrappers around one-line prompts.
- **"Use AI for the hard design problems."** Addy Osmani's 70% problem: AI gets you 70% fast, the last 30% (edge cases, security, integration) is slower than writing from scratch for seniors. Use AI for the boring 80%; humans own architecture and integration boundaries.
- **"More context = better."** Bloated `CLAUDE.md` causes rules to be ignored. Anthropic's own test: *"Would removing this line cause Claude to make mistakes? If not, cut it."*

See `critique.md` for which of these I personally used to over-invest in.
