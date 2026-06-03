# Phase A — Live Verification Log

Date: 2026-06-04
Session: same Claude Code instance, `PaymentValidator.cs` was Read into parent context immediately before both experiments.

Both subagents are the same type (`dotnet-code-reviewer`). The only variable is the briefing.

---

## Experiment A — Bad briefing

**Prompt sent to subagent:**

> Review the recent code change I made.

**Subagent response:**

> I cannot review your recent code change because you have not shared any code, file path, or diff with me. I also do not have access to your git history or any record of what you recently modified.
>
> To proceed, please provide one of the following:
>
> 1. **Absolute file path(s)** of the file(s) you changed (e.g., `D:\repos\linkedin-pocs\src\Services\UserService.cs`), and I will read and review them.
> 2. **A diff or patch** (e.g., output of `git diff` or the before/after snippets) pasted directly into the chat.
> 3. **A repository path** where I should look — and tell me which files or commit you want reviewed.
>
> Once you share any of the above, I will perform a full review per the standard format (Summary, Critical, Major, Minor, Suggestions, Positive Highlights, Framework & Package Best Practices), including detection of your `.csproj` target framework and NuGet packages.

**Metrics:**
- Tokens: 26,877
- Tool calls: 0
- Duration: 7.4 s
- Useful output: zero — review stalled

---

## Experiment B — Good briefing

**Prompt sent to subagent:** file path + verbatim contents + focus areas + output format. Full prompt preserved in the post draft.

**Subagent response:** 9 concrete findings with line numbers and fixes, in the requested format.

**Sample findings (verbatim):**

> FINDING #1
> Line: 9
> Issue: `payment.Items.Count` throws NullReferenceException because `Items` is declared nullable (`List<PaymentItem>?`) and is never null-checked.
> Fix: Guard with `if (payment.Items is null || payment.Items.Count == 0) return false;`.

> FINDING #4
> Line: 13
> Issue: `firstItem.Currency` is nullable (`string?`) — calling `.ToUpper()` will throw NullReferenceException when Currency is null.
> Fix: Null-check first, e.g. `if (firstItem.Currency is null) return false;` before comparing.

> FINDING #5
> Line: 13
> Issue: `Currency.ToUpper() == "USD"` is culture-sensitive (Turkish "I" problem) and allocates a new string for every comparison.
> Fix: Use `string.Equals(firstItem.Currency, "USD", StringComparison.OrdinalIgnoreCase)`.

(9 findings total — full list in the run output.)

**Metrics:**
- Tokens: 28,028
- Tool calls: 0
- Duration: 14.3 s
- Useful output: complete, actionable review

---

## Verdict — what this proves and what it doesn't

### Proved (with this single run)

1. **Subagent did not inherit parent's live context.** I (parent) had just Read `PaymentValidator.cs` literally seconds before. If the subagent had access to parent's session state, it would have known what "recent change" meant. It did not — it asked.

2. **Briefing quality drives output quality on the same model.** Same subagent type, same compute budget — bad briefing produced zero findings, good briefing produced nine.

3. **The cost shape may surprise:** tokens were similar across the two runs (27K vs 28K). The bad-briefing failure mode here was a **stall** (asked for input), not wasted tokens. In production, stalls are worse than waste — they break automation.

### Nuance (avoid overclaiming)

The `dotnet-code-reviewer` subagent is well-behaved — it refused to hallucinate or wander. A different subagent (e.g., a general-purpose agent with default exploratory behavior) might respond to "review my recent change" by running `git diff`, globbing for `*.cs`, and burning tokens before producing maybe-wrong output. So:

- **Well-scoped subagents** stall politely on bad briefing.
- **Exploratory subagents** waste effort on bad briefing.
- **Both** thrive on explicit briefing.

A second experiment with a `general-purpose` subagent on the same bad prompt — see Experiment C below — rounds this out.

---

## Experiment C — Bad briefing, general-purpose subagent

Same bad prompt ("Review the recent code change I made."), different subagent type (`general-purpose` instead of `dotnet-code-reviewer`).

**Subagent response:** Ran 5 tool calls — discovered the untracked file via filesystem exploration, read both `PaymentValidator.cs` and `verification-log.md` (this file), and produced 8 findings as a JSON array.

Notably, it even spotted the meta-context: *"verification-log.md is prose (no code findings) ... the file appears to be a teaching artifact for the post."* It cross-validated several findings against the ones the post claims the good-briefing subagent produced.

**Metrics:**
- Tokens: 37,625
- Tool calls: 5
- Duration: 45.3 s
- Useful output: 8 findings (largely overlapping with Experiment B)

---

## Three-way summary

| Subagent | Briefing | Tool calls | Tokens | Duration | Findings | Failure mode |
|----------|----------|-----------|--------|----------|----------|--------------|
| dotnet-code-reviewer | Bad | 0 | 26,877 | 7.4 s | 0 (stalled, asked for input) | **Stall** |
| dotnet-code-reviewer | Good | 0 | 28,028 | 14.3 s | 9 | — (target case) |
| general-purpose | Bad | 5 | 37,625 | 45.3 s | 8 (correct but wasteful) | **Exploratory waste** |

vs the good-briefing run:
- General-purpose bad briefing burned **34%** more tokens
- Took **3.2×** longer wall-clock
- Used **5 extra tool calls** to rediscover what the parent already knew

---

## Updated implications for the post

The boundary the subagent crosses is **session/conversation state**, not the filesystem. Crucially:

- ✅ **Filesystem**: subagents with Read/Glob/Bash tools can see anything on disk — they can find files, run git commands, explore.
- ✅ **CLAUDE.md / MEMORY.md**: auto-injected per docs.
- ❌ **Parent's conversation history**: invisible.
- ❌ **Parent's "what I just read this session"**: invisible.
- ❌ **Parent's open files / scratch mental state**: invisible.

So "isolation" is the wrong word. The honest framing is: **subagents start with a fresh context. They can rediscover disk state — but at the cost of tokens, time, and the risk of guessing wrong about what 'recent' or 'the file I was looking at' meant.**

The fix is the same regardless of subagent type: **brief explicitly.** Don't make the subagent rediscover what you already know.

### Not yet tested

- Whether CLAUDE.md / MEMORY.md content surface inside the subagent (would need an in-subagent probe)
- The 200-line / 25KB MEMORY.md truncation claim — needs a probe that reads its own injected context
- Whether subagent tool calls / observations leak back to parent — observed indirectly (the parent only saw the final message + a metrics summary), consistent with the docs

---

## Implications for the post

The post will frame this as **"the briefing problem"**, not "subagents are blind". The honest claim is:

> A subagent gets your delegation prompt plus its static config — and nothing else from your live session. Treat it like a contractor briefed by email, not a teammate sitting next to you.

The 9-vs-0 finding count and 14 s vs 7 s (with zero useful output) numbers anchor the post.
