# Campaign journal

Append-only. One entry per work session. See `campaign/PLAN.md` for the design.

## 2026-08-15 (session 1)

- Explored the repo (`runs/readme.md`, `patches/README.md`, `remote/ENVIRONMENT.md`,
  `scripts/run_experiment_vllm.py`, `scripts/fresh_server_replay.py`,
  `scripts/lossy_methods.py`) to understand the existing fresh-server-per-
  measurement infrastructure before building anything new on top of it.
  `scripts/fresh_server_replay.py` already does everything the "run the
  sweep" half of this task needs (server lifecycle, patch switching, per-run
  alpha via CLI, resumable skip-if-done, trace on/off) -- reused as-is, not
  reimplemented.
- Found disk at 96% full / 4.2G free on the root filesystem (pre-existing,
  not caused by this task). Initially planned to route new run data to
  `/srv/data` (934G free) but that's root-owned with no write access for
  this user and no sudo available -- worked around it instead by disabling
  per-token tracing (`--no-trace-proposals`), which was never needed for
  this deliverable anyway (only `run.json`'s summary fields are), dropping
  per-run disk cost from ~1-1.5MB to ~25KB. Full campaign now costs ~30MB.
  Flagged in `campaign/PLAN.md`; no user action needed unless a future task
  here genuinely needs the trace files at scale.
- `git mv runs old_runs` (13,585 tracked files, clean rename, all existing
  AIME24/HumanEval data including the guard-variant pilots preserved).
  Fresh `runs/` created, added to `.gitignore` (not tracked going forward --
  avoids growing the already-full root disk's `.git`, and the data is
  regeneratable from `campaign/` scripts + `prompts/`). Committed as
  `172e755b`.
- Checked the sibling repo `~/lossy-spec-decode-repetition` for LiveCodeBench/
  MT-Bench/LongBench-v2: it already has `build_livecodebench_prompts.py`,
  `build_mtbench_prompts.py`, `build_longbench_v2_prompts.py` and their
  fetched output (90/80/153 cases respectively). Verified completeness
  directly (per the user's ask): `candidate_index.jsonl` line counts match
  case-dir counts exactly for all three (90/90, 80/80, 153/153), every case
  dir has all 4 required files non-empty, and a sampled `rendered_prompt.txt`
  (livecodebench case_001) ends cleanly at `<|start|>assistant` with no
  truncation. No GSM8K there -- building it fresh here.
- Wrote `campaign/PLAN.md`: case counts (12 full-sweep + 3 calibration-probe
  cases per dataset), per-method alpha calibration grids (4 points each,
  anchored to the existing single-alpha reference table), target-selection
  rule (nearest-grid-point to 3 percentiles of the cross-method-achievable
  l̄ band), and per-dataset `--max-new-tokens` budgets (gsm8k 2048, aime24
  32768, humaneval 9000, livecodebench 12000, mtbench 4096, longbench_v2
  8192) -- picked from each task's output-length character, not copied
  from one dataset to all. Time budget self-estimate: ~1,170 runs total,
  ~2-2.5 days of continuous single-GPU wall time (no parallelism possible --
  fresh-server-per-measurement is a hard requirement here, see
  `remote/ENVIRONMENT.md`).
- Next: build `scripts/build_gsm8k_prompts.py`, copy+subset the 3 borrowed
  prompt sets, write `scripts/campaign_run.py` (calibrate -> pick targets ->
  full sweep, resumable, one dataset at a time) and
  `scripts/campaign_report.py` (tables + graphs), then kick off the actual
  GPU campaign in the background.
- Built `scripts/build_gsm8k_prompts.py` (12 cases, `openai/gsm8k`), and
  `scripts/subset_borrowed_prompts.py` to evenly-stride 12 cases each out of
  the sibling repo's livecodebench/mtbench/longbench_v2 sets. All 6 prompt
  sets now have exactly 12 `case_NNN` dirs available (aime24/humaneval reuse
  their own first 12 of their larger existing sets).
- Wrote `scripts/campaign_run.py` and `scripts/campaign_report.py`, dry-run
  validated the plumbing, then ran a real 2-case smoke test on gsm8k/
  spec_casc_tok. Caught a real resumability bug this way: a run killed
  mid-flight (by the smoke test's own `timeout 300` wrapper) leaves a
  partial run directory (config/request/server_info.json but no run.json),
  and `run_experiment_vllm.py`'s own overwrite guard would make every future
  retry of that exact (method, alpha, case) fail identically forever --
  silently, since `fresh_server_replay.py` logs a failure and moves on
  rather than stopping. Fixed by adding `clean_partial_runs()` to
  `campaign_run.py`, run automatically before every dataset's stage 1 --
  confirmed it correctly cleaned up the smoke test's own leftover partial
  dir on the very next invocation. The 2 completed smoke-test runs
  (gsm8k/spec_casc_tok/alpha0.15, case_001+case_002) produced well-formed
  `run.json` (l_bar 3.57/3.23, output_tokens 160/144, status ok) and are
  real data, not discarded -- alpha 0.15 is genuinely part of
  spec_casc_tok's real calibration grid, so they count toward the real
  campaign's calibration mean.
- No `matplotlib` in either `.venv-vllm` or system python3, and system pip3
  is PEP-668-externally-managed with no `python3-venv` package installed (no
  sudo to fix that). Built a separate `.venv-report` via `uv venv` (avoids
  needing the broken system `ensurepip`) with matplotlib -- kept fully
  separate from `.venv-vllm` on purpose, since that env's exact package set
  is load-bearing for the patched-kernel tests (see `remote/ENVIRONMENT.md`'s
  hardlink-trap warning) and has no reason to carry plotting deps.
  `campaign_report.py` verified against the smoke-test data (writes
  `campaign/tables/gsm8k.csv` correctly; correctly no-ops on the graph until
  a `campaign/calibration/<dataset>.json` exists).
- Loaded the `dataviz` skill before writing the graph code. Static
  matplotlib PNG, not an interactive artifact, so only the medium-agnostic
  rules apply: fixed categorical color order (skill's validated slots 1-5,
  never cycled), and since 5 series exceeds the palette's own 3-series
  all-pairs-safe cap, added marker shape + linestyle as secondary encoding
  per method plus direct end-of-line labels, not color/legend alone.
- **Launched the real campaign**: `nohup bash scripts/campaign_all.sh` (all
  6 datasets, sequential, detached from this session so it survives
  independent of this conversation) ->
  `logs/campaign_all_stdout.log`. Started with gsm8k (fastest dataset --
  short completions, ~1-2s generation per run, so wall time is almost
  entirely the ~90-100s fresh-server overhead). Order: gsm8k, aime24,
  humaneval, livecodebench, mtbench, longbench_v2.
- Set up a self-paced `/loop` to check in periodically (aiming for
  20-30 min between checks while runs are actively landing), update this
  journal, and run `campaign_report.py` for any dataset whose full sweep
  finishes, until all 6 are done.
- User asked for the per-token trace after all: turned tracing back on
  (dropped `--no-trace-proposals` from `campaign_run.py`'s
  `fresh_server_replay.py` invocation -- tracing is that script's own
  default). At that point gsm8k's `mentored_dec` calibration grid had
  finished (14 runs) and `cactus` calibration had just started -- cleanly
  killed the running driver + server (`kill -TERM` on `campaign_run.py`/
  `fresh_server_replay.py`, then `remote/stop_server.sh`, confirmed 0MiB GPU
  used afterwards), deleted `runs/gsm8k` entirely (14 small untraced runs,
  ~110s/run to redo -- cheaper and cleaner than leaving a traced/untraced
  split in the same dataset's table), and relaunched
  `scripts/campaign_all.sh` from a clean gsm8k start. Disk was still 4.1G
  free at this point (the untraced runs cost ~25KB each, negligible either
  way) -- re-checked the contingency plan (`runs_old_backup/`, 2.3G, is the
  first thing to recycle if tracing's real disk cost turns out to matter)
  and documented it in `campaign/PLAN.md`, but haven't needed to touch it
  yet.
- **Session recovered after SSH disconnect**: the monitoring session died
  around 2026-08-15T04:42Z mid-check-in (last message was confirming the
  first traced `proposals.jsonl` landed). `scripts/campaign_all.sh` itself
  was launched via `nohup` and kept running the whole time, unaffected --
  at recovery it was still on gsm8k's `spec_casc_tok` calibration sweep
  (alpha0.8, case_007/9), ~5h20m of continuous uptime. gsm8k run counts at
  recovery: cactus 39, mentored_dec 39, r_fuzzy 39, spec_casc_opt 39,
  spec_casc_tok 27 (of 39) -- no dataset has a finished calibration+sweep
  yet, so nothing new for `campaign_report.py` to do this check-in.
  Restarted the self-paced check-in loop (same ~20-30 min cadence as
  before) to pick back up where it left off.
- **gsm8k finished** (2026-08-15T10:05:08Z, ~5h25m total for this dataset).
  `campaign_report.py --dataset gsm8k` ran automatically at the end of
  `campaign_all.sh`'s gsm8k stage: `campaign/tables/gsm8k.csv` (186 rows,
  raw per-run data across all 5 methods' calibration grids),
  `campaign/results/gsm8k.csv` (14 rows -- the picked 3-target-alpha
  comparison points per method), and `campaign/graphs/gsm8k.png` (the
  5-line mean-accept-length-vs-completion-length graph) all written, report
  script exited 0. Campaign auto-advanced straight into **aime24**
  (started same second, mentored_dec calibration alpha0.15/0.35 first --
  aime24's 32768-token budget makes each run much slower than gsm8k's,
  e.g. case_002/alpha0.15 alone took 231s of generation).
