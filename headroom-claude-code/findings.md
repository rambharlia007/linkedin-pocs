# Findings — Headroom on Claude Code

**Session:** 2026-06-05
**Repo tested:** private Firebase / Node.js project (`spend-tracker`)
**Duration of real-work session:** ~2 hours
**Headroom version:** 0.23.0
**Claude Code:** subscription / OAuth (browser login)
**Container model image:** `headroom-code:v3` (custom — `ghcr.io/chopratejas/headroom:latest` + `[code]` + torch CPU + ast-grep-cli force-reinstall)

## Final aggregate (from `/stats`)

```
api_requests:        128
primary_model:       claude-opus-4-7   (+ haiku-4-5 subagents)
requests_compressed: 89   (70%)

tokens before:       7,642,336
tokens removed:      2,240,642
overall reduction:   29.32%
avg compression:     27.3%  (compressed requests only)
best compression:    43.7%  (88,427 -> 49,754 tokens on one request)

uncompressed buckets:
  prefix_frozen:           ~35  (cache prefixes correctly preserved by CacheAligner)
  too_small:                1
  passthrough:              1
  no_compressible_content:  ~3

cost (HR's own estimate):
  without_headroom_usd:  $23.02
  with_headroom_usd:     $12.13
  total_saved_usd:       $10.89  (47.3%)
  (compression + preserved cache hits both contribute)
```

## Top 10 single-request compressions (from proxy.log PERF lines)

```
tok_before  ->  tok_after   saved      pct
 92,255         53,582    38,673   41.9%
 92,665         53,992    38,673   41.7%
 93,279         54,606    38,673   41.5%
 94,052         55,379    38,673   41.1%
 94,779         56,106    38,673   40.8%
 95,252         56,446    38,806   40.7%
 95,927         57,121    38,806   40.5%
 95,974         57,168    38,806   40.4%
 96,683         57,877    38,806   40.1%
 88,427         49,754    38,673   43.7%   <- best by ratio
```

## One canonical PERF line decoded

```
[hr_1780693720_000095] PERF
  model=claude-opus-4-7
  msgs=137              (a long iterative conversation)
  tok_before=96,683
  tok_after=57,877
  tok_saved=38,806      (40.1% reduction)
  cache_read=173,971    (huge prefix cache hit)
  cache_write=897       (only 897 new entries written — minimal cache invalidation)
  cache_hit_pct=99
  opt_ms=145
  transforms=
    read_lifecycle:stale*3              <- collapsed 3 stale Read outputs
    router:tool_result:kompress         <- ModernBERT compressed a tool_result
    router:protected:user_message*8     <- 8 user messages left alone
    router:excluded:tool*15             <- 15 tool-call blocks not compressed
```

## Transform frequency (across the session)

```
102 transforms=none                 (prefix-frozen / subscription poller / etc.)
 49 transforms=router:noop          (looked, found nothing worth touching)
 17 transforms=router:excluded:tool
 14 transforms=read_lifecycle:stale*3
  9 transforms=router:protected:user_message
  7 transforms=router:excluded:tool*2
  ... long tail
   2 transforms=router:tool_result:kompress
```

Note: `router:tool_result:kompress` only appears explicitly 2 times in the transforms summary, but it's also packaged into the compound transforms like `read_lifecycle:stale*3 router:tool_result:kompress ...` on the high-savings requests. The big-saver requests apply Kompress to a single large tool_result while also doing stale-Read detection on others.

## CacheAligner explicit log lines

```
Pipeline: freezing first 1/2   messages (prefix cached by provider)
Pipeline: freezing first 3/131 messages (prefix cached by provider)
Pipeline: freezing first 134/135 messages (prefix cached by provider)
Pipeline: freezing first 3/133 messages (prefix cached by provider)
Pipeline: freezing first 3/137 messages (prefix cached by provider)
```

These are explicit acknowledgements from headroom that the prefix is cached at the provider and should not be rewritten. Headroom's job is then to compress only the un-frozen suffix. This is the core mechanism that lets it shrink content without torching the 99% cache hit rate.

## Lifetime (across all sessions today, including failed experiments)

```
requests:                216
total_input_tokens:    5,802,617
tokens_saved:          1,263,285
total_input_cost_usd:    $17.94
compression_savings:      $6.01
savings_percent:         17.88%   <- dragged down by earlier broken-PyTorch runs that
                                     compressed 0%; this session alone is 29.2%
```

## Configurations tried and their outcomes (the journey)

| # | Config | Result | Reason |
|---|---|---|---|
| 1 | `--mode token` (default), no `[code]`, no `[ml]`, no `--intercept-tool-results` | 0% compression, +13% cost on a small probe (cache invalidation on the few attempts) | Compressor disabled (no PyTorch / no [code]); the few rewrites that happened broke cache |
| 2 | `--mode cache --memory --code-graph --intercept-tool-results`, no `[ml]` | 0% compression, **+171% cost** (subagent dispatch killed) | `--memory` injected a tool block that broke Claude Code's Haiku routing heuristic |
| 3 | `--mode cache --intercept-tool-results` (no memory, no code-graph), no `[ml]` | 0% compression, ~baseline cost | `cache` mode froze every request as designed; nothing compressed |
| 4 | `--mode token --intercept-tool-results --code-graph` (no memory), **with PyTorch + [code] installed** | **29.2% compression, $6 saved, 99% cache hit rate, subagents preserved** | The working recipe |
