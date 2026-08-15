# Campaign: 6 datasets x 5 lossy methods, l̄-matched completion-length comparison

Started 2026-08-15. See `campaign/JOURNAL.md` for the running log of what's
actually been done; this file is the design, written once up front and
updated only when a real decision changes.

## Ask (restated)

Datasets: GSM8K, AIME24, HumanEval, LiveCodeBench, MT-Bench, LongBench(-v2).
Methods: `spec_casc_opt`, `spec_casc_tok`, `cactus`, `mentored_dec`, `r_fuzzy`
(the 5 taxonomy methods only -- no guard variants, no strict/baseline arm in
the deliverable). Per (dataset, method): a per-case run-metrics table, and a
sweep of each method's own alpha to find 3 mean-accepted-length (l̄) points
that all 5 methods can reach, so completion length is compared at matched l̄.
Final deliverable: one graph per dataset, 5 lines (one per method), x=l̄,
y=mean completion length, plus the underlying data.

## Why this is NOT a repeat of the existing AIME/HumanEval tables

The existing `old_runs/` data (see `old_runs/readme.md`) is one alpha per
method (the paper-anchored "reference" value), not a matched-l̄ sweep --
exactly the gap this campaign fills. It's also full-dataset (30/164 cases);
this campaign trades case count for alpha-sweep breadth (see "Scale" below).

## Scale decisions (mine to make, per the user's ask)

**Disk**: root disk was at 96% full / 4.2G free when this started -- a real,
pre-existing constraint (large `.venv-vllm`s, HF cache, uv cache, other
repos), not something to work around by writing elsewhere by default. Fix:
`fresh_server_replay.py --no-trace-proposals` -- this campaign needs
`run.json`'s summary fields (`l_bar`, `mean_accept_length`,
`output_tokens`), never the per-token `proposals.jsonl` trace, so tracing
is off. That drops a run dir from ~1-1.5MB to ~25KB, so the full campaign
(~1,200 runs) costs **~30MB**, not several GB -- comfortably fits on the
existing disk with tracing off, so `/srv/data` and `/ephemeral` (both
root-owned, no write access for this user) turned out not to be needed.

**Per-dataset case count**: **12 full-sweep cases + 3 of those held out as
the calibration probe subset** (so calibration cost is reused, not extra).
Reasoning: this campaign runs 3 alphas x 5 methods per dataset (15 arm
configs) instead of the old tables' 1 alpha x 1 method -- a ~3x
multiplier on run count per case already, before calibration. Fresh-server
overhead is ~90-100s/run *before* any generation happens (see
`old_runs/../aime24_fresh_sweep_stdout.log`: `L=1711 ... wall=5.56s` but
`ok in 101s` -- the gap is server start/stop), so run *count* dominates
wall time far more than per-dataset token budget does. 12 was picked as the
largest count that keeps the full 6-dataset campaign inside a few days on
one H100 (see "Time budget" below), not because 12 is a natural number --
if it finishes faster than expected, cases 13+ get appended to widen the
per-case table rather than left idle (see JOURNAL for whether that
happened).

**Case selection**: AIME24/HumanEval reuse their own existing
`case_001..NNN` prompts (already-curated 30/164-case sets), first 12 by
index. GSM8K/LiveCodeBench/MT-Bench/LongBench-v2 select 12 **evenly-strided**
across whatever superset was fetched -- not the first 12 -- because
MT-Bench's 80 cases are ordered in 8 solid 10-case category blocks (first
12 would be only `writing`+`roleplay`); striding at ~80/12 keeps rough
category spread. Same rule applied uniformly to the other three for
consistency even where it matters less.

**Per-method alpha calibration grid** (4 points each, anchored to the
existing single-alpha-per-method table in `old_runs/readme.md` and widened
towards strict since every existing reference alpha already gave l̄ well
above strict's ~2.2 -- the low end of the shared range needs weaker
relaxation than any of the existing single-point runs used):

| method | domain | existing reference (AIME, l̄) | this campaign's grid |
|---|---|---|---|
| `mentored_dec` | `[0, 1)` | 0.37 -> 2.67 | 0.15, 0.35, 0.55, 0.75 |
| `cactus` | `[0, inf)` | 0.25 -> 4.17 | 0.03, 0.08, 0.18, 0.35 |
| `spec_casc_opt` | `(-inf, inf)`, strict -inf | 0.05 -> 3.41 | -0.3, -0.1, -0.02, 0.05 |
| `r_fuzzy` | `(-inf, inf)`, strict -inf (JSD, bounded [0, ln2]) | 0.3 -> 4.13 | 0.03, 0.08, 0.15, 0.25 |
| `spec_casc_tok` | `(-inf, 1]`, strict -inf, **not 0.0** | 0.3 -> 2.42 | 0.15, 0.35, 0.55, 0.8 |

**Target-selection rule**: after the 4-point grid runs (3 probe cases each),
compute each method's achievable l̄ range on that dataset. The shared band is
`[max of per-method minimums, min of per-method maximums]` (typically capped
by `spec_casc_tok`, whose l̄ stays narrow even at high alpha -- see the
existing table). Pick 3 targets at roughly the 20th/55th/90th percentile of
that band, then for each method pick the grid alpha whose measured l̄ is
closest to each target (nearest-neighbour from the 4 already-run points --
no extra calibration runs). If two targets collapse onto the same grid
point for a method with a narrow range, that method's 3rd point falls back
to its own grid extremes so every method still contributes 3 distinct
alphas. Precision is deliberately loose: the graph's x-axis is each run's
*actual measured* l̄, not the nominal target, so approximate alignment
(same neighbourhood, not exact match) is enough for a legible comparison --
exact bisection to hit a target l̄ was considered and dropped as
disproportionate engineering for what the graph actually needs.

**Per-dataset token budget (`--max-new-tokens`)**, chosen by output-length
character of the task (short-answer vs. long-form vs. bounded by
`--max-model-len 65536` minus context):

| dataset | budget | why |
|---|---:|---|
| GSM8K | 2048 | grade-school arithmetic, short chains |
| AIME24 | 32768 | matches the existing table exactly (unchanged) |
| HumanEval | 9000 | matches the existing table exactly (unchanged) |
| LiveCodeBench | 12000 | harder than HumanEval (competitive programming), shorter than AIME |
| MT-Bench | 4096 | chat-length answers, not competition reasoning |
| LongBench-v2 | 8192 | context up to ~45K tokens against a 65536 model-len leaves headroom; answer itself is one MC letter + reasoning, not long-form |

## Time budget (self-estimated, see JOURNAL for how it actually tracked)

Per (dataset, method): 4-point calibration (3 cases) = 12 runs, full sweep
at 3 chosen alphas x 9 remaining cases = 27 runs -> ~39 runs. x5 methods =
~195 runs/dataset. x6 datasets ~= **1,170 runs total**. At ~90-100s fixed
overhead per run plus generation (dominated by AIME's long completions),
ballpark **~2-2.5 days** of continuous single-GPU wall time -- inside the
user's "might take a few days" expectation with margin for retries/cap-hits.
No parallelism: one H100, fresh-server-per-measurement is a hard
requirement (see `remote/ENVIRONMENT.md`), so this is inherently serial.

## Directory layout (kept parallel to the existing convention)

```
prompts/<dataset>/case_NNN/{rendered_prompt.txt,metadata.json,source.json,token_count.txt}
prompts/<dataset>/candidate_index.jsonl, selection_summary.json
runs/<dataset>/<method>/alpha<value>/case_NNN/seed_0/{config,request,response,run}.json + output.txt
  (untracked in git -- see .gitignore; ~25KB/run with tracing off)
campaign/
  PLAN.md              this file
  JOURNAL.md            append-only log, updated every work session
  calibration/<dataset>.json      raw grid results + chosen targets, per dataset
  tables/<dataset>_<method>.csv   per-case run-metrics table
  results/<dataset>.csv           aggregated (method, alpha, mean l̄, mean completion length) points used for the graph
  graphs/<dataset>.png            the deliverable graph
scripts/
  build_gsm8k_prompts.py          new
  campaign_run.py                 orchestrator: calibrate -> pick targets -> full sweep, one dataset at a time, resumable
  campaign_report.py              builds tables/results/graphs from runs/
```

## Grading / correctness

Explicitly **not** part of this deliverable -- the ask is run metrics (l̄,
completion length) only, not accuracy. No LLM-judge infrastructure is stood
up for MT-Bench, no test-execution harness for LiveCodeBench. (GSM8K and
LongBench-v2 references are still captured in `metadata.json`/`source.json`
in case they're wanted later -- free, since the prompt builders already
carry them -- but nothing here reads them.)

## Sources for the 4 new prompt sets

- GSM8K: built fresh by `scripts/build_gsm8k_prompts.py`
  (`openai/gsm8k`, config `main`, split `test`, via the HF datasets-server
  rows API -- same mechanism `build_humaneval_prompts.py`/`build_aime24_prompts.py`
  already use here).
- LiveCodeBench, MT-Bench, LongBench-v2: copied from the sibling repo
  `~/lossy-spec-decode-repetition/prompts/{livecodebench,mtbench,longbench_v2}`
  (already fetched there by the equivalent `build_*_prompts.py` scripts, and
  verified complete here: candidate_index.jsonl line count matches case-dir
  count, all 4 required files present and non-empty in every case dir, no
  truncation at the end of a sampled `rendered_prompt.txt`) -- reusing them
  avoids re-fetching and matches an already-audited artifact contract, per
  the user's "see if those are the complete prompts" check.
