# Headroom on Claude Code (subscription) — what the official docs miss

Pointing the [chopratejas/headroom](https://github.com/chopratejas/headroom) compression proxy at Claude Code with the official Docker image gives you **zero compression**. The proxy logs a quiet `PyTorch was not found` and a `Code-Aware: DISABLED` and otherwise looks healthy. Every request lands in the `prefix_frozen` bucket. Hours of debug later, the gap turns out to be five undocumented (or scattered-across-five-pages) fixes.

After applying all five, on a ~2.5-hour real-work session against a Firebase / JS project on Claude Code subscription:

| Metric | Value |
|---|---|
| Requests through proxy | 128 |
| Requests compressed | 89 (70%) |
| Input tokens (pre-compression) | 7,642,336 |
| Tokens removed | 2,240,642 |
| **Overall token reduction** | **29.3%** (stable as the session grew from 95 to 128 requests) |
| Best single request | **43.7%** (88,427 -> 49,754) |
| Avg compression (compressed requests only) | 27.3% |
| Prompt cache hit rate | 99-100% (CacheAligner working) |
| **Total cost saved** | **$10.89 on $23.02 -> 47.3%** |
| - of which direct compression | ~$10.89 |
| - of which cache-hit savings preserved | additional |
| Subagent dispatch (Haiku) | preserved (with the right flag combination) |

These are Patterson-range numbers ([Andrew Patterson reported](https://andrewpatterson.dev/posts/token-savings-rtk-headroom/) 31-59% per-model + 96% cache hit rate over a month of production use).

---

## The five things missing from the default Docker setup

1. **PyTorch is not in the image.** The official image ships with the `[proxy]` extra only. The `[ml]` extra (which pulls torch + ModernBERT for the Kompress text compressor) is not pre-installed. Without it, headroom's main compression model can't load. The boot banner mentions this in one line of warning that's easy to miss.

2. **The `[code]` extra is not in the image either.** Code-aware AST compression (tree-sitter-based) needs `pip install "headroom-ai[code]"` inside the container. Until you install it, the boot banner shows `Code-Aware: DISABLED`.

3. **`ast-grep-cli` needs a force-reinstall after `[code]` installs.** The wheel for `ast-grep-cli` ships the binary as a separate platform-tag-matched file. On the first install, the binary doesn't land in `/usr/local/bin/`. A `pip install --force-reinstall --no-cache-dir ast-grep-cli` fixes it. Until then, `headroom tools doctor` reports `unsupported-platform`.

4. **`--intercept-tool-results` is OFF by default.** This is the flag that lets headroom open `tool_result` blocks (Read / Bash / Grep outputs from Claude Code) and compress them. The CLI help text marks it `"Off by default while this feature ships."` Without it, headroom sees the requests but never inspects the compressible payload.

5. **`--memory` breaks Claude Code's Haiku subagent dispatch.** The README's compatibility matrix recommends `--memory --code-graph` for Claude Code. But `--memory` injects a `memory_20250818` tool block into every request, which mutates Claude Code's prompt shape, which trips its internal model-routing heuristic. Result: Claude Code stops dispatching to Haiku subagents and runs everything on Opus. Cost spikes ~170%. **Do not enable `--memory` on Claude Code subscription.**

---

## Working recipe (Windows + Rancher Desktop / Docker Desktop)

```bash
# 1. Pull the official image
docker pull ghcr.io/chopratejas/headroom:latest

# 2. Bootstrap into a temporary container so we can install missing pieces
docker run -d --name hr-tmp ghcr.io/chopratejas/headroom:latest
docker exec hr-tmp pip install --upgrade "headroom-ai[code]"
docker exec hr-tmp pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
docker exec hr-tmp pip install --force-reinstall --no-cache-dir ast-grep-cli

# 3. Verify the fixes landed
docker exec hr-tmp python -c "import torch; print(torch.__version__)"
docker exec hr-tmp headroom tools doctor

# 4. Snapshot the fixed container into a reusable image
docker commit hr-tmp headroom-code:v3
docker rm -f hr-tmp

# 5. Run the real proxy — mount your project at /workspace
MSYS_NO_PATHCONV=1 docker run -d --name headroom \
  -p 8787:8787 \
  -e HEADROOM_CODE_AWARE_ENABLED=1 \
  -v "D:/your/project/path:/workspace" \
  -v hr-memory:/root/.headroom \
  -w /workspace \
  headroom-code:v3 \
  --host 0.0.0.0 \
  --mode token \
  --intercept-tool-results \
  --code-graph
```

(`MSYS_NO_PATHCONV=1` is only needed when running from Git Bash on Windows. PowerShell and macOS / Linux shells can drop it.)

The four flags you want:

- **`--mode token`** (not `cache`). With PyTorch installed, the CacheAligner keeps prefix cache hits at 99%+ even while compressing. `--mode cache` is too defensive and freezes every request.
- **`--intercept-tool-results`** to let headroom touch `tool_result` blocks.
- **`--code-graph`** for stale-Read detection (works without breaking subagent dispatch).
- **`-e HEADROOM_CODE_AWARE_ENABLED=1`** to enable AST-based compression.

Do **not** add `--memory` until you measure its cost on your workflow.

---

## Point Claude Code at it

```powershell
# Windows PowerShell
$env:ANTHROPIC_BASE_URL = "http://localhost:8787"
cd D:\your\project\path
claude
```

Subscription OAuth (browser login) survives the proxy hop. The proxy forwards your `Authorization: Bearer` header verbatim. No API key required.

---

## How to verify compression is actually happening

The boot banner alone is not enough. Check three places:

```bash
# 1. /stats — aggregate counters
curl http://localhost:8787/stats | jq '.summary.compression'

# Look for: requests_compressed > 0, total_tokens_removed > 0

# 2. /metrics — Prometheus counters
curl http://localhost:8787/metrics | grep tokens_saved

# 3. The PERF lines in the proxy log — per-request before/after
docker exec headroom grep "PERF" /root/.headroom/logs/proxy.log | grep -vE "tok_saved=0 " | tail
```

A working PERF line looks like this (one real request from our session):

```
PERF model=claude-opus-4-7 msgs=137
  tok_before=96,683
  tok_after=57,877
  tok_saved=38,806           (40.1% reduction)
  cache_read=173,971
  cache_write=897            (CacheAligner doing its job — minimal cache invalidation)
  cache_hit_pct=99
  opt_ms=145
  transforms=read_lifecycle:stale*3
             router:tool_result:kompress
             router:protected:user_message*8
             router:excluded:tool*15
```

If your PERF lines all show `tok_saved=0` and `transforms=router:noop` or `transforms=none`, one of the five fixes above is still missing.

---

## What the transforms mean

| Transform | What it does |
|---|---|
| `router:tool_result:kompress` | Runs the ModernBERT-based Kompress compressor on a tool_result block |
| `read_lifecycle:stale*N` | Detects N file Reads where the same file was Read earlier in the session with unchanged content; collapses the stale copies to a reference |
| `router:protected:user_message*N` | Leaves N user messages alone (correct, user input is sacred) |
| `router:excluded:tool*N` | Leaves N tool-call blocks alone (correct, tool definitions are sacred) |
| `router:noop` | Headroom looked at the request, found nothing it should touch |
| `none` | Request fell out of the compression pipeline entirely (subscription poller, prefix-frozen, etc.) |

`prefix_frozen` is healthy in moderation; it means Claude Code's `cache_control` breakpoints are being respected. You want about 30-40% of requests in this bucket, not 100%.

---

## Caveats and what we didn't test

1. **API key billing not verified.** We tested on subscription OAuth only. The `/cost` numbers reported by Claude Code on subscription are consistent with the proxy's /stats, but pay-per-token API users may see different routing behavior.
2. **One repo, one workflow.** Numbers are from a 2-hour iterative dev session on a Firebase / Node.js project. Repo size, file types, edit patterns all matter. A different codebase (large Java monorepo, embedded C, ML notebooks) will produce different numbers.
3. **PyTorch CPU only.** The container has `torch==2.12.0+cpu`. GPU acceleration would speed up the ~145ms `opt_ms` overhead per request but doesn't change the savings ratio.
4. **The `--memory` flag may have legitimate uses.** Our session showed it suppresses Haiku dispatch on Claude Code, but on agents that don't have subagent routing (LangChain, CrewAI), it might be net positive. Did not test.
5. **No long-running production data.** Patterson's blog reports a month of usage with 96% cache hit rate. Our window was hours. Long-term behavior unverified.

---

## Raw artifacts in this folder

| File | What it is |
|---|---|
| `stats.json` | The proxy's own `/stats` JSON, captured at session end. Authoritative source for the numbers above. |
| `stats-history.json` | Cumulative `/stats-history` endpoint output. Includes display_session + lifetime counters. |
| `stats.html` | Single-file dashboard rendering of the same numbers. Open in a browser to screenshot. |
| `findings.md` | PERF lines decoded, the four-config journey, transform-frequency breakdown. |

## Sources

- [chopratejas/headroom](https://github.com/chopratejas/headroom) (Apache 2.0)
- [extraheadroom.com](https://extraheadroom.com/) (marketing site)
- [headroom-docs.vercel.app](https://headroom-docs.vercel.app/docs)
- [Andrew Patterson's blog](https://andrewpatterson.dev/posts/token-savings-rtk-headroom/) — independent third-party measurements
- [chopratejas/headroom#425](https://github.com/chopratejas/headroom/issues/425) — open issue documenting the same "routed but not compressed" pattern on Codex

## License

Apache 2.0 (the upstream project). This repo's notes and recipes: MIT.
