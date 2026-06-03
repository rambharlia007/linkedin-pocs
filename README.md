# agent-lab

A workbench for small, reproducible experiments at the intersection of
agentic AI frameworks, .NET, and EF Core. Each folder is one experiment:
a problem, a runnable POC, raw transcripts, and the lessons.

## Experiments

| Date | Topic | Folder |
|------|-------|--------|
| 2026-06-04 | The Subagent Briefing Problem | [`subagent-briefing/`](./subagent-briefing/) |

## How each experiment is laid out

```
<topic-slug>/
├── README.md           # problem, how to run, what the numbers mean
├── <code files>        # the runnable POC
├── verification-log.md # transcripts captured during testing
├── results.json        # gitignored, generated when you run
└── raw-exchange.jsonl  # gitignored, full request+response per call
```

Every experiment is self-contained. Clone the repo, `cd` into a folder,
read the README, run the code.

## Running an experiment

Most experiments are Python with a single `requirements.txt`:

```powershell
cd <topic-slug>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env       # fill in your API key / endpoint
python <main_script>.py
```

.NET experiments will appear later and follow a similar pattern with
`dotnet run`.

## Why this exists

Most posts about agentic frameworks repeat the same surface claims. The
goal here is to test those claims directly and publish the receipts —
code, transcripts, numbers, raw API exchanges — so anyone can reproduce
or refute.
