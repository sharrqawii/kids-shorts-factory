# Architecture for five original episodes per day

**Prepared, not enabled.** Phase 1 implements and tests one strawberry episode.
The other four catalog entries are original story blueprints, not rendered
videos. No schedule or YouTube upload is active. Nothing claims that five
different videos per day have already been proved on GitHub's free runners.

## Implemented foundation

`config/production.json` holds the daily target (5), disabled scheduling state,
production timezone, concurrency limit (1), per-episode CPU budget, and disabled
upload flag. `episodes/catalog.json` contains five distinct original stories.
`factory/batch.py` prepares a deterministic daily manifest with stable job IDs,
seeds, renderer readiness, and explicit blockers. It will not fill a shortage
by repeating previously completed story IDs. Planning performs no network
calls, starts no renders, and spends no cloud resources.

```bash
python -m factory.batch --date 2026-10-13 --out build/daily-plan.json
```

An optional `--ledger completed.json` accepts a JSON array of previously
completed story IDs. A missing ledger means a fresh planning demonstration,
not durable production history. The CLI reports that the initial five-story
batch is blocked because four renderers still need implementation.

## Next implementation steps

1. Extract the garden and `make_pip` into an asset library; keep the character
   version fixed. Add a renderer registry and episode-specific props/actions.
2. Implement and individually verify the bubble, sunflower, puddle, and firefly
   stories. The current render CLI deliberately accepts only the proven first
   episode; unimplemented catalog entries cannot be passed through as aliases.
3. Maintain an approved backlog of fresh stories. Five videos every day needs
   five genuinely new approved stories per day, not five random seeds of one
   clip. Fail closed when the unused backlog is too small.
4. Store durable job state (`planned → rendering → verified → completed`, or
   `failed`) with atomic updates. Persist the completed-story ledger and output
   hashes. Use job IDs for retry safety and never count a failed render as one
   of the five. The current JSON planner is the input contract for that queue.
5. Benchmark a five-episode batch on the actual free runner. Keep rendering
   serial at first, cap CPU time, and preserve explicit fallback reports.
6. Review current host terms and capacity before enabling recurring production.
   GitHub Actions supports this software's build/tests; it is not an unlimited
   media render farm. If ongoing production does not fit permitted free use,
   leave it disabled and report that limitation. Do not silently add a paid
   host, billing account, GPU rental, or subscription.
7. Keep YouTube credentials and publishing entirely outside this phase. A
   future publisher would only consume verified outputs after separate setup.

For planning, total daily compute is approximately five times measured
episode runtime plus installation/encoding overhead. The 75-minute per-episode
ceiling is a safety cap, not a claim that five such jobs are an acceptable daily
workload. Only a real cloud run can establish practical capacity.
