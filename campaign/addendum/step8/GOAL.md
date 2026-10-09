# Step 8 goal: more drafters, a third model family, the fix on Qwen3

Branch `addendum-step8` off main d35d52de7 (not the SPEED-Bench branch). Commit after
every block. Deadline: blocks 0-6 on the branch by 2026-10-08; later work goes to the rebuttal.
No SPEED-Bench, no judge calls, no API credit. Deviations in `../README.md`, numbered from 29.

Priority: (1) Llama-3.1-8B family (Instruct + DeepSeek-R1-Distill-Llama-8B) with published
drafters; (2) more drafters on GPT-OSS-20B and Qwen3-8B; (3) the fix (head-restricted
relaxation) on Qwen3-8B.

## Protocol (confirmed with Bill 2026-10-03)

Dedicated-drafter blocks (1-4) use the paper's main-grid protocol, as `scripts/campaign_run.py`
encodes it, per (target, drafter, dataset):

1. Calibration: the five rules at their 4-point grids (`ALPHA_GRIDS`) on case_001-003.
2. Three shared l_bar targets at the 20th / 55th / 90th percentile of the span the five rules reach together.
3. Each rule at the grid alpha nearest each target, on the full case set (GSM8K 150, LiveCodeBench 90,
   MT-Bench 80, AIME24 30), plus the drafter's own lossless reference on the same cases.
4. Calibration JSONs: `campaign/calibration/<dataset>_<family>_<drafter>.json`.

Servers: one persistent server per arm (rule + alpha; alpha is fixed at server start), for
calibration and full runs alike, as `persistent_arm_replay.py` ran the addendum (prefix caching off,
one request at a time). Request ordinal, node and server start time recorded per run. No server is
ever shared across arms. (Deviation 30; the paper's Limitations already describes the body's runs as
first cases after a fresh start, the rest on a reused process.)

Settings for every model: seed 0, N_draft 6, T 1.0, top-p 1.0 enforced with `--generation-config vllm`
(Llama-3.1-8B-Instruct ships 0.6/0.9, R1-Distill recommends 0.6: both overridden), max model length
65536, draft sampling probabilistic, parallel drafting off, YaRN 1.6 for Qwen3 only (Llama native 128k,
no rope override), the paper's token budgets (GSM8K 2048, LCB 12000, MT-Bench 4096, AIME24 32768),
`--no-trace-proposals`. Before any full run: grade 5 sample outputs per new model (R1-Distill think
block, Llama plain text). Standalone-drafter rows (blocks 2, 3, 5): loosest grid alpha only, GSM8K and
LiveCodebench, own lossless reference. Every arm of one block on one node type, hostname recorded.

Tables: `campaign/addendum/tables/step8__<target>__<drafter>.csv` through `addendum_tables.py`: one row
per (target, drafter, rule, setting, dataset) with l_bar lossless/arm, mean completion tokens, lambda,
round ratio, time ratio, cap-out rate, accuracy, paired bootstrap intervals over cases, node, and
`sampler_path` (V1 full patches / V2 accept-test-only).

Sampler path (vLLM 0.26.0, `config/vllm.py use_v2_model_runner`): dense targets with eagle / eagle3 /
dflash run the V2 runner, whose consolidated sampler is accept-test-only for cactus and spec_casc_tok;
medusa, draft_model, parallel drafting (P-EAGLE) and every GPT-OSS row (MoE) run V1 with full patches.

Llama weights: the gated `meta-llama/*` repos are replaced by NousResearch/Meta-Llama-3.1-8B-Instruct and
alpindale/Llama-3.2-1B-Instruct (hashes vs Meta's non-weight files and unsloth's independent weight copies
in deviation 29); tables cite Meta's ids with a note.

## Blocks

| block | what | est. GPU-h | cluster |
|---|---|---|---|
| 0 | load checks a-f, prompt sets g | ~2 | Killarney |
| 1 | R1-Distill-Llama-8B + EAGLE-3; GSM8K, LCB, MT-Bench, AIME24 | ~25 | Killarney |
| 2 | Llama-3.1-8B-Instruct: EAGLE-3, EAGLE-1, Medusa (GSM8K, LCB, MT-Bench); Llama-3.2-1B standalone | ~11 | Nibi |
| 3 | Qwen3-8B: the one second dedicated drafter that passed 0(d), full protocol on GSM8K, LCB, MT-Bench; Qwen3-1.7B standalone | ~30 | Killarney |
| 4 | GPT-OSS-20B + RedHatAI EAGLE-3: GSM8K, LCB, MT-Bench | ~6 | Nibi |
| 5 | R1-Distill-Llama-8B + Llama-3.2-1B standalone | ~7 | Killarney |
| 6 | fix on Qwen3-8B: tok_lt (0.15, 0.20), opt_head (beta 0.15, alpha 0.05), GSM8K + LCB; GPT-OSS fix re-export | ~5 | Killarney |
| 7 | (optional) Qwen3-8B P-EAGLE loosest, GSM8K + LCB | ~7 | Killarney |

Total for blocks 1-6 about 102 GPU-h (Bill, 2026-10-03). Actual hours reported per block.

Block 0(d) (Bill, 2026-10-03): Qwen3-8B's second dedicated drafter, checked in this order, stopping at the
first that passes: (i) deepseek-ai/dspark_qwen3_8b_block7 (method dspark); (ii) RedHatAI/Qwen3-8B-speculator.dflash
(dflash); (iii) RedHatAI/Qwen3-8B-Thinking-speculator.eagle3 (eagle3). A drafter passes only if vLLM 0.26.0 serves
it with the patched sampler AND per-position draft probabilities q reach the rejection sampler, confirmed on one
prompt by a log that the draft-prob tensor is present and not one-hot (the cascade and fuzzy rules need q).
The Block 0 report names the one that passed and its sampler path. Qwen3-1.7B stays the draft_model row.
The same q probe is logged for every other drafter (V2: the `[Q-PROBE V2]` line of the step-8 V2 file; V1:
a traced strict run, `patches/relaxation_trace.py` records q(x) and the draft entropy).

Fallbacks: (a) fails -> Qwen3-14B + RedHatAI EAGLE-3 with the Qwen3 prompts; Medusa fails -> drop;
(b) or the Llama-3.2-1B check fails -> drop that standalone row.

Every step-8 table row also carries `drafter_family` (eagle3, eagle1, medusa, dspark, dflash, draft_model)
next to `sampler_path`.

## Decisions after the Block 0 report (Bill, 2026-10-03)

- Block 1 runs as planned on all four datasets (option A). R1-Distill's EAGLE-3 head stops drafting past ~2048
  positions; that is reported as a property of the published drafter, not worked around. Estimated ~45-50 GPU-h
  (was 25), blocks 1-6 ~125 GPU-h.
- Block 5 runs: R1-Distill and Llama-3.2-1B share the vocabulary size and 128249 of 128256 token ids; the 7 others
  are special tokens R1 renamed or repurposed (README deviation 38).
- Medusa dropped (README deviation 36). Block 3's second drafter is DSpark (deviation 37).

## Status

See `../PROGRESS.md` (step-8 entries) and `../RESULTS.md` (Step 8 sections).
