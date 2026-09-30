# NAACL-2027 addendum campaign

Started 2026-09-29 on branch `addendum-oct2026`. Everything the paper needs
from this campaign lives here; the paper's own tables (`campaign/tables/*.csv`,
`campaign/results/*.csv`) are never touched.

| file | what |
|---|---|
| `manifest.csv` | single source of truth: one row per (step, condition, dataset, method, alpha, seed) arm; `n_done` is recounted from `runs/` every cycle |
| `PROGRESS.md` | append-only action log (UTC); "Needs Bill" at the top |
| `lanes/<lane>.json` | the ordered work list each Nibi lane runs (regenerated every cycle) |
| `lanes/<lane>_status.jsonl` | copy of the lane's own journal on Nibi (item start/end, job, elapsed) |
| `lanes/state.json` | Slurm job chain per lane |
| `analysis/` | step 1 (zero-GPU) CSVs, each with a sibling line in `analysis/README.md` |
| `seeds/`, `tables/`, `best_setting.csv`, `aime24_repeats.csv` | steps 2-6 outputs |
| `RESULTS.md` | every number the paper will quote, with its CSV path and row |

## How it runs

- `scripts/addendum_campaign.py cycle` (Mac): pull finished runs back ->
  recount -> rewrite `manifest.csv` and the lane work lists -> push code and
  work lists to Nibi -> keep every lane's Slurm chain supplied -> commit
  (one commit per completed arm) and push the branch.
- `cascade/cluster/addendum_lane.sbatch` -> `scripts/addendum_lane.py`
  (Nibi, one H100 per job, `--time` 12 h, chained `afterany`): runs the
  lane's work list through `scripts/persistent_arm_replay.py` (one server
  per arm+seed, `--no-trace-proposals`), skip-if-done per case.
- Two lanes (user request 2026-09-29: "like 2 GPUs"), each with its own repo
  + `.venv-vllm` copy and a disjoint node set (`remote/stop_server.sh` kills
  every vLLM process of the user on a node; knob files are node-local):
  lane A = `~/projects/def-hongyanz/billxby/lossy-token-eff`, nodes g1-g14;
  lane B = `.../lossy-token-eff-lane2`, nodes g15-g28.

## Run roots and provenance

Each lane writes only to its own run root, `/scratch/billxby/lossy-addendum/lane<L>/runs`,
laid out exactly like the repo's `runs/`. Finished run dirs (run.json with
`status: ok`) are pulled into the repo's `runs/` tree only where the target
directory does not exist yet (staged, then moved; never merged, never
overwritten). Failed or interrupted run dirs on Nibi are moved to
`<lane root>/quarantine/`, not deleted.

Why not the repo copies' own `runs/` on Nibi: they already hold September
cascade-workspace runs (E1/E1F/E1P, `cascade/RESULTS.md`) at the same paths
as the campaign tree -- e.g. `gsm8k/strict/strict/case_*/seed_{0,1,2}` -- that
are different runs from the Mac's (old-box) seed-0 data. Running there would
make skip-if-done silently reuse them. The addendum therefore produces all of
its own runs; the E1P runs stay untouched on Nibi.

- `runs/<dataset>/<method>/<params>/case_NNN/seed_<k>/`: new seeds (steps 2, 5.2, 6) and the
  missing step-5.1 alphas (seed 0), exactly where the campaign's tree puts them.
- `runs/addendum/<condition>/<dataset>/...`: server-setting changes --
  `nspec<k>` (step 3), `temp<T>` (step 4.1), `qwenT0.6` (step 4.2), `lmdraft` (step 4.3),
  `nibiref` (step 0.5, below).

## Settings (unchanged from the campaign)

EAGLE-3 drafters, N_draft 6, temperature 1.0, top-p 1.0, server seed 0 (the
request seed is the `seed_<k>` value), vLLM 0.26.0 with the repo patches,
Qwen3 YaRN 65,536 via `MODEL_FAMILIES`, the campaign token budgets and case
counts. Loosest alpha per rule = the maximum alpha in
`campaign/results/<dataset>.csv` for that method (every rule loosens as its
alpha grows).

## Additions and deviations (each also logged in PROGRESS.md)

1. **Step 0.5, Nibi hardware reference (added).** All existing seed-0 data
   ran on the old box's H100 PCIe; Nibi's H100 SXM is ~3x faster per token
   (measured: 7.1 vs 2.2-2.4 ms/token on the same strict cases). Wall-time
   ratios of cells produced on Nibi need a Nibi strict baseline: `nibiref` =
   strict, seed 0, campaign settings, all cases. It is the N_draft = 6 row of
   step 3, the T = 1.0 row of step 4.1, and the time denominator for the step
   5.1 cells in step 5.2. Step-2 and step-6 ratios compare arms of the same
   seed, all produced on Nibi, so they need no reference.
2. **`patches/apply.sh`: `APPLY_SKIP_TEST_IF_APPLIED`.** Opt-in (set only by
   `addendum_lane.sbatch`): when the requested patch is already installed
   with a matching sha256, its self-test is skipped (~2.5 min of GPU per
   arm). Any fresh apply or switch still runs the test. Default behaviour
   unchanged.
3. **No lane C: Qwen3 runs on lanes A and B.** /project has a 500K-file
   quota (288K used); a third repo + venv copy is ~100K files, and Bill asked
   for two GPUs. Once the V2 sampler arrived (2026-09-30 00:36Z, installed in
   both lane venvs; the V2 file is not touched by GPT-OSS, which runs V1) the
   Qwen3 rows were spread over lanes A/B by estimated hours, in the plan's
   lane-C order (2.1 -> 0.5 -> 3 -> 4.1 -> 4.2 -> 5.1 -> 4.3 / 6 / 2.2 -> 5.2
   -> 7). Reordered with Bill on 2026-09-30 19:35Z, when the Nibi queue
   slowed: 2.1 -> 2.2 / 6 (AIME24 seeds) -> 4.2 -> 4.3 -> 0.5 -> 3 -> 4.1 ->
   5.1 -> 5.2 -> 7, so the rows the two-model claims rest on finish first.
4. **Step 2.2 aime24 seeds 1-2 are the same runs as step 6 seeds 1-2** (one
   manifest row each, step `2.2`, noted "shared by step 6").
5. **`patches/test_mentored_dec.py`: `MENTORED_DEC_TEST_V1_ONLY`.** The
   mentored-dec self-test also checks the V2 module, whose consolidated state
   is not on Nibi (D8), so every switch *to* mentored-dec failed there (job
   22880871, 06:23Z: V1 patch installed, V1 kernel checks all ok, only the V2
   plumbing check failed). GPT-OSS-20B runs V1 only, so the lanes set this
   variable for GPT-OSS items: with it set *and* the V2 module pristine the
   plumbing check covers V1 only. Qwen3 items never set it.
6. **`remote/run_server_vllm.sh` `SPEC_METHOD`** (default `eagle3`, spec
   JSON byte-identical otherwise) for step 4.3, and an optional `--top-k`
   in the client/replay scripts (sent and recorded only when given) for
   step 4.2.
7. **Runs come back with tar over ssh, not rsync** (`addendum_campaign.py
   collect`): macOS ships openrsync, and the guarantee needed here is
   directory-level no-clobber (never merge two runs' files into one
   `seed_N/`), which a staged tar extract + `os.rename` into a
   not-yet-existing target gives directly. Only run dirs whose run.json says
   `ok` are pulled; the lane's `status.jsonl` journal comes back every cycle.
8. **Step 7 (SPEED-Bench, added 2026-09-29 from Prof. Zhang) runs on both
   GPT-OSS lanes, not lane B alone.** Lane B takes the budget pilot first,
   then `strict`, `spec_casc_opt`, `mentored_dec`; lane A takes `cactus`,
   `r_fuzzy`, `spec_casc_tok` (Bill: "like 2 GPUs"). The step text does not
   define "the lane budget"; it is taken as one 12 h job on each of the two
   lanes, 24 GPU-h (`SB_BUDGET_H` in `scripts/addendum_campaign.py`).
9. **SPEED-Bench prompts** (`scripts/build_speedbench_prompts.py`): the
   qualitative parquet at revision `454f8845...` (sha256 `4f76bc45...`);
   the 494 placeholder rows are resolved with NVIDIA's own code
   (Model-Optimizer `examples/specdec_bench`, commit `834c90d7...`,
   `SPEEDBench._fetch_all_turns_data`). Case order is SPEED-Bench's own
   stratified interleaving (round-robin over categories), so case_001..case_040
   is the time-estimate sample and case_001..case_440 is exactly 40 per
   category. Turn 1 only, as for the repo's MT-Bench (167 rows are
   multi-turn; the later turns stay in `metadata.json`), rendered as the same
   Harmony conversation as MT-Bench (the renderer reproduces
   `prompts/mtbench/case_001` byte for byte). **Not committed:** the repo is
   public, the data is under the NVIDIA Evaluation Dataset License and its
   rows come from third-party sources (HLE asks that its questions stay off
   the open web), so `prompts/speedbench*/` is gitignored and
   `campaign/addendum/speedbench/cases.csv` records case -> question_id,
   category, source, src_id, token count and the sha256 of every rendered
   prompt. The 208 rows from `cais/hle` (gated) wait for a Hugging Face token
   (PROGRESS.md Needs Bill 4); every other category is complete.
10. **Step 7 mechanics.** The token-budget pilot (strict at 8192 on the first
   20 Reasoning and first 20 Math cases) writes to its own run root,
   `runs/addendum/speedbench_pilot/gpt-oss-20b/`, because a category whose
   budget is raised to 16384 is run again at the new budget and run
   directories are never overwritten. An arm whose cases need two budgets
   runs as two work items (one server session each). "The first 40 prompts
   of each arm" = the first 40 cases in case order that are runnable when the
   pilot finishes (prompt built, category budget decided), which leaves Math
   out: 16 of its first 20 cases are HLE, so its budget waits for the token.
   In the full phase Math's 18 non-HLE rows (Spec-Bench's GSM8K-style
   problems; at most 636 completion tokens in the pilot, so neither cap can
   bind) run at 8192 anyway; the 62 HLE Math rows wait for the Math pilot's
   decision. The reasoning pilot found 0/20 cap-outs, so every non-Math
   category runs at 8192 (`tables/speedbench_pilot__gpt-oss-20b.csv`). The per-arm
   estimate and the full-vs-440 decision are written to the manifest notes
   and PROGRESS.md before the rest is queued. While step 7 waits between
   these phases, a lane that runs out of work keeps its GPU for up to 40 min
   (`hold_minutes` in the work list, `scripts/addendum_lane.py`) instead of
   exiting, so the next phase does not wait in the Slurm queue.
   Qwen3-8B gets its own pilot and phases under the same rules (thinking
   lengths differ from GPT-OSS, so its budgets are decided on its own strict
   runs, in `runs/addendum/speedbench_pilot/qwen3-8b/`). Its step 7 starts
   once GPT-OSS has nothing runnable left (the cais/hle cases may still be
   missing); its short pilot and first-40 items run ahead of other work on
   their lane, the full arms after every other Qwen3 row (lane C order).
   Its prompts (`prompts/speedbench_qwen3/`, gitignored) come from
   `scripts/build_prompts_qwen3.py` on the GPT-OSS set, which reproduces the
   existing Qwen3 prompt sets byte for byte.
11. **3 h lane jobs from 2026-09-30 19:20Z (the plan allows up to 12 h).**
   After the first 12 h Qwen3 jobs timed out at 13:24Z, their chained
   successors sat PENDING for 6 h: ~850 H100 jobs were pending on Nibi and our
   fair-share had dropped to 0.23 after two days of continuous use, and a
   12 h job fits almost no backfill window. Those six pending jobs were
   cancelled and every lane now chains 3 h jobs (`JOB_TIME` in
   `scripts/addendum_campaign.py`); a job ending mid-arm loses only the case
   in progress (its partial dir is quarantined, the rest is skip-if-done).
