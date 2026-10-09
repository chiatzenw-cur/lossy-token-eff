# Step 9 goal: the 5 rules x 6 datasets grid for the five dedicated step-8 pairs

Branch `addendum-step9` off main 32517782d; merged into main when done, never pushed. Deadline: every block done and
the tables written by 2026-10-09 18:00 ET; the paper fold-in happens after. Deviations in `../README.md`, numbered
from 40. Orchestration: `scripts/step9_campaign.py` (Bill, 2026-10-05).

Rules unchanged from step 8: never overwrite anything under runs/; never commit prompts/speedbench*/; never touch
~/.config/lossy-token-eff/judge.env; no judge or API spend of any kind; no hand edits of paper/, Overleaf or
campaign/tables/*.csv (tables come from the scripts). No step-8 block is rerun.

## Phase 1 (required): 14 (pair, dataset) blocks, in this order

| block | pair (target + drafter) | dataset |
|---|---|---|
| 1 | GPT-OSS-20B + RedHatAI/gpt-oss-20b-speculator.eagle3 | AIME24 |
| 2 | Qwen3-8B + deepseek-ai/dspark_qwen3_8b_block7 | AIME24 |
| 3a-3e | GPT-OSS RH head, Qwen3 DSpark, Llama-3.1-8B-Instruct EAGLE-3, Llama-3.1-8B-Instruct EAGLE-1, R1-Distill-Llama-8B EAGLE-3 | LongBench-v2 |
| 4a-4e | the same five | HumanEval |
| 5a-5b | Llama-3.1-8B-Instruct EAGLE-3, EAGLE-1 | AIME24 |

R1-Distill already has AIME24; MT-Bench, GSM8K and LiveCodeBench are done for all five (step 8).

## Protocol per block (identical to the step-8 lanes, dataset swapped)

Lossless reference with the pair's own drafter (seed 0) on the full case set; the five rules at their 4-point
alpha grids on case_001-003; three shared l_bar targets at the 20th / 55th / 90th percentile of the span the five
rules reach together; each rule at the grid alpha nearest each target on the full case set, plus the grid extremes
`pick_alphas` adds when two targets share one alpha (the step-8 "extra" rows); paired bootstrap per cell, 10,000
resamples. Budgets and case sets as the paper: AIME24 30 cases / 32,768 tokens, HumanEval 150 / 9,000, LongBench-v2
150 / 8,192. Seed 0, N_draft 6, T 1.0, top-p 1.0 (Llama's bundled sampler overridden with `--generation-config
vllm`, as step 8), one persistent vLLM process per arm on Killarney H100s, `sampler_path` as step 8 (V1 full patches
for the GPT-OSS RH head; V2 accept-test-only for cactus and spec_casc_tok on DSpark, the Llama EAGLE heads and the R1
head). Same mirrors, the same 65,536-position head configs (needed for LongBench-v2). R1's head collapses beyond
~2,048 positions: LongBench-v2 runs anyway and its lossless l_bar is reported as is, like AIME24. Graders: the
campaign's own (HumanEval execution, LongBench-v2 multiple choice, AIME `grade_aime.py` unchanged); every AIME boxed
answer longer than 3 digits is logged (`aime_boxed_long.csv`) for a later re-grade.

Block 0 (before any block runs): prompt format, grader path and head config for the three new datasets on each
pair, and one 2-case smoke run per (pair, dataset) (`BLOCK0.md`). Then start without waiting.

If the projection misses 2026-10-09 18:00 ET: drop the HumanEval blocks (4a-4e) first, then the Llama AIME24 blocks
(5a-5b).

## Phase 2 (only if Phase 1 finishes before 2026-10-08 18:00 ET; skipped entirely rather than started late)

Loosest grid alpha only, 5 rules + lossless, like the existing rows: Qwen3-8B + Qwen3-1.7B, Qwen3-8B + Qwen3-0.6B,
Qwen3-8B + P-EAGLE, Llama-3.1-8B-Instruct + Llama-3.2-1B, R1-Distill-Llama-8B + Llama-3.2-1B, each on HumanEval,
LongBench-v2, MT-Bench, AIME24, in that order.

## Deliverables

- `campaign/addendum/tables/step9__<target>__<drafter>.csv`: exactly the step-8 column schema, one row per
  (dataset, rule, setting), lossless columns filled.
- `campaign/addendum/tables/pairs__<target>__<drafter>.csv`: step-8 rows + step-9 rows of the same pair, same schema
  (what the paper script reads).
- `campaign/addendum/RESULTS.md`: a "Step 9" section, one block per pair-dataset in the step-8 format (completion
  time, GPU-h, lossless l_bar and accuracy, the numbers that matter), deviations from 40, Step 9 totals.
- `step9/manifest.csv` with `gpu_hours_actual`; one report line per completed block; a final DONE report.

## Estimate (2026-10-05 ~19:30Z, before Block 0)

GPU-h per block from the addendum's and step 8's per-case times, scaled to step 8's actuals (the same formula gives
47.7 / 20.9 GPU-h for step-8 Blocks 1 / 4, which took 34.0 / 16.9: factor 0.74; `step9_campaign.py estimate`):

| block | pair | dataset | GPU-h |
|---|---|---|---|
| 1 | gpt-oss-20b + RH EAGLE-3 | AIME24 | 7.0 |
| 2 | qwen3-8b + DSpark | AIME24 | 9.8 |
| 3a | gpt-oss-20b + RH EAGLE-3 | LongBench-v2 | 6.6 |
| 3b | qwen3-8b + DSpark | LongBench-v2 | 11.5 |
| 3c | llama31-8b-instruct + EAGLE-3 | LongBench-v2 | 7.3 |
| 3d | llama31-8b-instruct + EAGLE-1 | LongBench-v2 | 7.3 |
| 3e | r1-distill-llama-8b + EAGLE-3 | LongBench-v2 | 19.4 |
| 4a | gpt-oss-20b + RH EAGLE-3 | HumanEval | 5.2 |
| 4b | qwen3-8b + DSpark | HumanEval | 8.7 |
| 4c | llama31-8b-instruct + EAGLE-3 | HumanEval | 5.9 |
| 4d | llama31-8b-instruct + EAGLE-1 | HumanEval | 5.9 |
| 4e | r1-distill-llama-8b + EAGLE-3 | HumanEval | 16.2 |
| 5a | llama31-8b-instruct + EAGLE-3 | AIME24 | 6.5 |
| 5b | llama31-8b-instruct + EAGLE-1 | AIME24 | 6.5 |

Phase 1 ~124 GPU-h. At 12 concurrent Killarney lanes and 85% duty (10.2 GPU-h/h) it ends about Tue 2026-10-06 04:00
ET; at step 8's 8 lanes about 10:00 ET. Both well before the deadline: no block is dropped.

## Status

See `../PROGRESS.md` (step-9 entries), `manifest.csv`, and `../RESULTS.md` (Step 9 sections).
