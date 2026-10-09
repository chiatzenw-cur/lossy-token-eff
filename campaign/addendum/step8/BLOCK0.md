# Step 8 Block 0 report (2026-10-03)

All checks on Killarney H100 80GB HBM3 (kn169, kn173, kn175, kn176), vLLM 0.26.0, one prompt unless stated.
12 jobs, 6.15 GPU-h. Data: `block0/checks.csv` (every run), `block0/strict_limit.csv`, `block0/v2_ab.csv`,
`block0/server_log_lines.txt`; runs under `runs/addendum/step8_block0/` (not committed, like every addendum run).

## Load checks

| check | target + drafter (method) | result | sampler path | q at the sampler |
|---|---|---|---|---|
| a | R1-Distill-Llama-8B + yuhuili EAGLE-3 (eagle3) | **pass after two fixes** (dev. 31: head config 2048 -> 65536 positions; dev. 33: tokenizer class) | V2 accept-test-only | present, 0% one-hot, entropy 3.0-6.8 nats |
| b | R1-Distill-Llama-8B + Llama-3.2-1B (draft_model) | pass (strict, mentored_dec 0.75) | V1 full | present: 383/401 proposals, mean q(x) 0.66 |
| c | Llama-3.1-8B-Instruct + yuhuili EAGLE-3 (eagle3) | pass (65536-position copy, dev. 31) | V2 accept-test-only | present, 0-14% one-hot rows |
| c | Llama-3.1-8B-Instruct + yuhuili EAGLE-1 (eagle) | pass (65536-position copy) | V2 accept-test-only | present, 0-14% one-hot rows |
| c | Llama-3.1-8B-Instruct + nebius Medusa (medusa), **6 heads** | serves, but **fails q**: every q(x) = 1.0, no entropy -> **dropped** (dev. 36) | V1 | absent |
| c | Llama-3.1-8B-Instruct + Llama-3.2-1B (draft_model) | pass | V1 full | present: 176/190, mean q(x) 0.78 |
| d | Qwen3-8B + **DSpark** dspark_qwen3_8b_block7 (dspark) | **pass, first in order -> Block 3** (dev. 37) | V2 accept-test-only | present, 0% one-hot, entropy 0.28-0.80 |
| d | Qwen3-8B + DFlash / Thinking EAGLE-3 | both serve (strict, mentored_dec 0.75); not needed | V2 | not probed (DSpark passed first) |
| d | Qwen3-8B + Qwen3-1.7B (draft_model) | pass with its own compile cache (dev. 34) | V1 full | present: 657/715, mean q(x) 0.89 |
| e | GPT-OSS-20B + RedHatAI EAGLE-3 (eagle3) | pass (strict, mentored_dec 0.75) | V1 full (MoE) | present: 111/115, mean q(x) 0.53 |
| 7 | Qwen3-8B + RedHatAI P-EAGLE (parallel drafting) | serves (strict) | V1 | not probed |

Tokenizer check (b): R1-Distill and Llama-3.2-1B have the same vocabulary size (128256) and the same ids for
128249 tokens; the 7 others are special tokens R1 renamed or repurposed (128000/128001 BOS/EOS; 128011-128015
`<｜User｜>`, `<｜Assistant｜>`, `<think>`, `</think>`, pad, which are reserved/untrained in Llama-3.2-1B). Not
identical, compatible for vLLM; the 1B drafter sees untrained embeddings at those five ids.

## (f) Patches on the Llama sampler paths: strict limit

Each rule at its strict point (mentored_dec, cactus alpha 0; spec_casc_opt, r_fuzzy, spec_casc_tok -inf) must give
the lossless output token for token; at its loosest grid alpha it must differ.

- V1 (Llama-3.1-8B-Instruct + Llama-3.2-1B): 10/10. All five strict points byte-identical to lossless (280
  tokens); every loosest alpha differs (l_bar 4.1-5.1 vs 2.99).
- V2 (Llama-3.1-8B-Instruct + EAGLE-3): 10/10. All five strict points byte-identical to each other and to lossless
  on a warm compile cache (142 tokens, two reruns); the one lossless run on a cold cache gave 166 (dev. 35); every
  loosest alpha differs.
- Accept-test-only on V2 (as the paper's Qwen3 footnote): **cactus and spec_casc_tok** (residual on raw p) in
  every V2 row: Block 1 (R1 + EAGLE-3), Block 2 (Llama-3.1 + EAGLE-3, + EAGLE-1), Block 3 (Qwen3 + DSpark).
  Full patches (V1): every draft_model row (Blocks 2, 3, 5) and GPT-OSS (Block 4).

V2 port of the fix (Block 6, dev. 32): strict and all five rules bit-identical on the old (68d0a904) and new
(796e3c85) file; spec_casc_tok_lt and spec_casc_opt_head at -inf byte-identical to lossless; at 0.15 / 0.2 /
(0.05, beta 0.15) they change the output. Both are complete ports (switch rules: stock residual).

## (g) Prompt sets

`prompts/{gsm8k,livecodebench,mtbench,aime24}_{llama31,r1llama}` (150/90/80/30 cases), the _qwen3 cases
re-rendered through each model's own chat template (`scripts/build_prompts_qwen3.py --chat-format`; the qwen3
output reproduces byte for byte). Llama-3.1 renders Meta's current template (system header "Cutting Knowledge
Date: December 2023 / Today Date: 26 Jul 2024"); R1 ends the generation prompt with an opened `<think>`.
Families registered in `campaign_run.py` (`MODEL_FAMILIES`, `TOKEN_BUDGETS`, `base_dataset`).

Grading on new formats (5 samples per model, strict): GSM8K extraction works for both (R1 `\boxed{}`, Llama
`####`); wrong verdicts checked by hand are genuine errors. R1 LiveCodeBench outputs carry a clean code block after
the tokenizer fix; LiveCodeBench verdicts need the Linux grader (RLIMIT_AS), run with the campaign's grading.

## Findings that change the plan

1. **R1-Distill's yuhuili EAGLE-3 head does not draft past ~2048 positions.** Acceptance per position segment
   (lossless, tokenizer fixed, same case at four budgets):

   | segment | LCB case_002 l_bar | AIME24 case_001 l_bar |
   |---|---|---|
   | 0-1024 | 2.32 | 2.64 |
   | 1024-2048 | 2.16 | 3.36 |
   | 2048-4096 | 0.67 | 1.23 |
   | 4096-8192 | 0.23 | (answer ended at 3605) |

   GSM8K answers (250-670 tokens) keep l_bar 2.4-3.5; LiveCodeBench answers (3.8k-12k tokens) end at 0.39-1.2;
   AIME24 (up to 32k) would sit almost entirely in the collapsed range. It is the only published R1-Distill-Llama
   drafter of note (one 13-download "tree-eagle3" upload aside).
2. **R1-Distill's tokenizer class mis-encodes every prompt** under transformers 5.18 (dev. 33): fixed with a
   corrected copy; all R1 numbers come from the rerun.
3. Medusa dropped (no q); DSpark is Block 3's drafter.
