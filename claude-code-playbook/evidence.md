# Evidence

Every numeric claim or named practice in `practices.md` and `critique.md` traces back to a source here. Where the evidence is thin, this file says so explicitly.

## Primary sources (Anthropic)

- **Best practices for Claude Code** — https://code.claude.com/docs/en/best-practices
  - The single most important read. Every section in `practices.md` tagged **[primary]** is sourced here.
- **Claude Code overview** — https://code.claude.com/docs/en/overview
- The 4-phase loop (Explore → Plan → Implement → Commit), the `/clear` and `/compact` semantics, `Esc + Esc` rewind, Stop hooks, subagents, skills (`SKILL.md`), and `Ctrl+G` plan editing are all defined here.

## Independent studies

### METR — "Measuring the Impact of Early-2025 AI on Experienced OS Developer Productivity"
- **Result:** developers were 19% *slower* with AI tools; predicted 24% faster; self-reported 20% faster after.
- **n=16** experienced OSS maintainers, **246 tasks**, randomized at task level, average **5 years on the codebase**.
- Tools: Cursor Pro + Claude 3.5/3.7 Sonnet.
- **Caveats** (be honest about these): population narrow; OSS-only; early-2025 tools (frontier has moved); follow-up RCT in early 2026 failed because too many devs refused to participate without AI.
- Sources: https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/ ; https://arxiv.org/abs/2507.09089 ; commentary https://www.seangoedecke.com/impact-of-ai-study/

### GitClear — AI Copilot Code Quality 2025
- **Result:** cloned code 8.3% → 12.3%; refactored code 24.1% → 9.5%; 2-week revision rate 5.5% → 7.9%; 8x growth in duplicated-block frequency in 2024.
- **n = 211M lines** of code changes.
- **Caveat:** GitClear sells a code-analytics product. Directionality aligns with DORA's independent findings, but treat exact magnitudes cautiously.
- Source: https://www.gitclear.com/ai_assistant_code_quality_2025_research

### Stack Overflow Developer Survey 2025 — AI section
- **n = 49,000+** respondents, 177 countries.
- AI use: 84% (↑ from 76%).
- Trust accuracy: 29% (↓ from 40%); active distrust: 46% (↑ from 31%).
- Top frustration ("almost right but not quite"): 45%.
- 66% say they spend *more* time fixing AI code.
- Source: https://survey.stackoverflow.co/2025/ai

### DORA 2024 — State of DevOps
- AI adoption associated with -1.5% throughput, **-7.2% stability**.
- 75.9% use AI; 39% report little/no trust in AI-generated code.
- "Vacuum Hypothesis": reclaimed time gets absorbed by low-value work.
- **Caveat:** correlational, not causal.
- Source: https://dora.dev/research/2024/dora-report/

### Snyk + Trend Micro — Slopsquatting
- 5–38% of LLM-suggested package names are hallucinations.
- ~440k hallucinated package names catalogued in one study.
- Bar Lanyado's `huggingface-cli` PoC package: 30,000+ real downloads.
- Sources: https://snyk.io/articles/slopsquatting-mitigation-strategies/ ; https://www.trendmicro.com/vinfo/us/security/news/cybercrime-and-digital-threats/slopsquatting-when-ai-agents-hallucinate-malicious-packages

## Practitioner sources

| Author | Most-cited piece | Why it matters |
|---|---|---|
| **Simon Willison** | https://simonwillison.net/tags/claude-code/ ; "Engineering practices that make coding agents work" talk | Most prolific public journal of working with Claude Code; coined "vibe engineering" framing |
| **Armin Ronacher** | "Agentic Coding Recommendations" https://lucumr.pocoo.org/2025/6/12/agentic-coding/ ; "Things That Didn't Work" https://lucumr.pocoo.org/2025/7/30/things-that-didnt-work/ | The most-honest critique of what doesn't deliver — hooks, slash commands, subagent parallelism for writes |
| **Harper Reed** | "My LLM codegen workflow atm" https://harper.blog/2025/02/16/my-llm-codegen-workflow-atm/ | The canonical spec → plan → execute template, now mirrored in Anthropic's docs |
| **Geoffrey Huntley** | "Everything Is a Ralph Loop" https://ghuntley.com/loop/ | Context-window discipline; one task per window |
| **Birgitta Böckeler** | https://martinfowler.com/articles/exploring-gen-ai/ | "Intervene, correct, steer" framing; the skill is review, not prompting |
| **Addy Osmani** | "The 70% Problem" https://addyo.substack.com/p/the-70-problem-hard-truths-about | Why AI helps juniors more than seniors; the last-30% asymmetry |
| **Hamel Husain** | https://hamel.dev/blog/posts/evals-faq/ | Eval discipline; the "use a different model as critic" pattern |
| **Peter Harrison** | "Pitfalls of Claude Code" https://dev.to/cheetah100/pitfalls-of-claude-code-1nb6 | Concrete failure-mode catalogue |

## Honest gaps — claims I am NOT making

- **"Plan-first reduces rework by N%."** No published RCT measures this. It is intuition plus strong consensus. The mechanism is well-argued; the magnitude is not measured.
- **"Subagents save N tokens on average."** Anecdotal. Not formally measured by Anthropic or any third party.
- **"This specific workflow generalizes to your codebase."** It doesn't, by default. METR shows the same tools that help one population hurt another. Generalize cautiously.
- **"Hooks save N hours per week."** No study. Ronacher's anecdote (negligible) is the strongest data point we have, and it's an anecdote.
- **Numbers for `CLAUDE.md` context degradation.** Anthropic states it qualitatively; the exact curve isn't published.
- **Scope-change (brownfield modification) benchmarks** barely exist in the academic literature. Most evals are greenfield bug-fix style. The production case is undermeasured.
