# Per-benchmark results: every rule's best clean point and loosest point, relative to lossless

Generated from `cascade/results/speed_ignoring_accuracy.csv` (rows with >= 30 paired runs). *Best clean* = the setting with the most
verifier-pass reduction whose runaway (budget-exhausted) rate is within +5 points of lossless's. *Loosest* = the largest alpha run.
`passes` = lossless passes / rule passes (end-to-end speedup); `len` = mean answer length / lossless; `runaways` = fraction of runs that hit
the token budget; `acc` = accuracy (lossless's in the header). Campaign rows: fresh server per measurement, seed 0. NEW rows: warm servers, 3 seeds
(accuracies graded per seed, 2026-09-16 fix).

## gsm8k — campaign  (lossless: 150 runs, accuracy 0.96)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_opt | -0.3 | 1.09 | 1.09 | 0.01 | 0.93 | 0.05 | 0.94 | 1.46 | 0.05 | 0.94 |
| spec_casc_tok | 0.8 | 1.21 | 0.96 | 0.01 | 0.97 | 0.8 | 1.21 | 0.96 | 0.01 | 0.97 |
| cactus | 0.03 | 1.02 | 1.28 | 0.03 | 0.96 | 0.35 | 1.01 | 1.61 | 0.05 | 0.91 |
| mentored_dec | 0.75 | 1.20 | 1.16 | 0.04 | 0.93 | 0.75 | 1.20 | 1.16 | 0.04 | 0.93 |
| r_fuzzy | 0.08 | 1.07 | 1.05 | 0.01 | 0.92 | 0.25 | 0.88 | 1.70 | 0.05 | 0.87 |

## aime24 — campaign  (lossless: 30 runs, accuracy 0.77)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_opt | -0.3 | 0.90 | 1.33 | 0.10 | 0.80 | 0.05 | 0.59 | 2.48 | 0.43 | 0.37 |
| spec_casc_tok | 0.15 | 1.09 | 1.00 | 0.03 | 0.83 | 0.8 | 0.82 | 1.48 | 0.20 | 0.70 |
| cactus | (none clean) | -- | -- | -- | -- | 0.18 | 0.93 | 1.78 | 0.23 | 0.60 |
| mentored_dec | 0.15 | 1.01 | 1.08 | 0.07 | 0.80 | 0.75 | 0.85 | 1.70 | 0.20 | 0.63 |
| r_fuzzy | 0.08 | 0.86 | 1.31 | 0.10 | 0.70 | 0.25 | 0.73 | 2.13 | 0.30 | 0.50 |

## humaneval — campaign  (lossless: 150 runs, accuracy 0.96)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_opt | -0.3 | 1.05 | 1.09 | 0.01 | 0.94 | 0.05 | 0.77 | 1.73 | 0.02 | 0.82 |
| spec_casc_tok | 0.8 | 1.08 | 1.04 | 0.00 | 0.94 | 0.8 | 1.08 | 1.04 | 0.00 | 0.94 |
| cactus | 0.03 | 1.02 | 1.24 | 0.00 | 0.93 | 0.35 | 0.90 | 1.79 | 0.01 | 0.87 |
| mentored_dec | 0.35 | 1.11 | 1.03 | 0.00 | 0.95 | 0.75 | 1.03 | 1.30 | 0.01 | 0.96 |
| r_fuzzy | 0.08 | 1.03 | 1.05 | 0.00 | 0.81 | 0.25 | 0.86 | 1.64 | 0.01 | 0.63 |

## livecodebench — campaign  (lossless: 90 runs, accuracy 0.89)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_opt | (none clean) | -- | -- | -- | -- | 0.05 | 0.86 | 1.64 | 0.19 | 0.49 |
| spec_casc_tok | 0.15 | 1.04 | 1.00 | 0.06 | 0.92 | 0.8 | 1.02 | 1.16 | 0.07 | 0.88 |
| cactus | 0.03 | 1.00 | 1.31 | 0.06 | 0.79 | 0.18 | 1.07 | 1.54 | 0.11 | 0.61 |
| mentored_dec | 0.15 | 0.98 | 1.08 | 0.07 | 0.87 | 0.75 | 1.12 | 1.25 | 0.09 | 0.84 |
| r_fuzzy | 0.03 | 1.01 | 1.01 | 0.06 | 0.70 | 0.25 | 0.90 | 1.65 | 0.16 | 0.34 |

## mtbench — campaign  (lossless: 80 runs, accuracy --)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_opt | 0.05 | 1.32 | 1.09 | 0.03 | -- | 0.05 | 1.32 | 1.09 | 0.03 | -- |
| spec_casc_tok | 0.8 | 1.14 | 0.96 | 0.01 | -- | 0.8 | 1.14 | 0.96 | 0.01 | -- |
| cactus | 0.18 | 1.68 | 1.07 | 0.04 | -- | 0.35 | 1.61 | 1.18 | 0.06 | -- |
| mentored_dec | 0.75 | 1.33 | 1.10 | 0.01 | -- | 0.75 | 1.33 | 1.10 | 0.01 | -- |
| r_fuzzy | 0.25 | 1.32 | 1.20 | 0.04 | -- | 0.25 | 1.32 | 1.20 | 0.04 | -- |

## longbench_v2 — campaign  (lossless: 150 runs, accuracy 0.56)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_opt | -0.3 | 0.95 | 1.21 | 0.03 | 0.53 | 0.05 | 0.76 | 1.79 | 0.14 | 0.47 |
| spec_casc_tok | 0.8 | 1.04 | 1.13 | 0.01 | 0.53 | 0.8 | 1.04 | 1.13 | 0.01 | 0.53 |
| cactus | 0.35 | 1.15 | 1.77 | 0.02 | 0.36 | 0.35 | 1.15 | 1.77 | 0.02 | 0.36 |
| mentored_dec | 0.55 | 1.12 | 1.11 | 0.01 | 0.57 | 0.75 | 0.90 | 1.59 | 0.03 | 0.51 |
| r_fuzzy | 0.25 | 0.91 | 1.69 | 0.05 | 0.40 | 0.25 | 0.91 | 1.69 | 0.05 | 0.40 |

## gsm8k_qwen3 — campaign  (lossless: 150 runs, accuracy 0.80)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_opt | -0.3 | 1.04 | 1.00 | 0.25 | 0.77 | 0.05 | 0.95 | 1.33 | 0.58 | 0.49 |
| spec_casc_tok | 0.8 | 1.05 | 0.99 | 0.23 | 0.79 | 0.8 | 1.05 | 0.99 | 0.23 | 0.79 |
| cactus | 0.35 | 1.12 | 1.04 | 0.27 | 0.77 | 0.35 | 1.12 | 1.04 | 0.27 | 0.77 |
| mentored_dec | 0.75 | 1.07 | 1.03 | 0.26 | 0.77 | 0.75 | 1.07 | 1.03 | 0.26 | 0.77 |
| r_fuzzy | (none clean) | -- | -- | -- | -- | 0.25 | 1.31 | 0.95 | 0.35 | 0.55 |

## aime24_qwen3 — campaign  (lossless: 30 runs, accuracy 0.70)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_opt | (none clean) | -- | -- | -- | -- | 0.05 | 0.94 | 1.42 | 0.63 | 0.30 |
| spec_casc_tok | 0.8 | 1.07 | 0.98 | 0.13 | 0.70 | 0.8 | 1.07 | 0.98 | 0.13 | 0.70 |
| cactus | 0.03 | 1.13 | 1.15 | 0.17 | 0.60 | 0.35 | 1.83 | 1.26 | 0.57 | 0.23 |
| mentored_dec | 0.15 | 1.13 | 0.91 | 0.13 | 0.73 | 0.75 | 1.07 | 1.01 | 0.23 | 0.73 |
| r_fuzzy | 0.03 | 0.95 | 1.04 | 0.17 | 0.67 | 0.25 | 0.86 | 1.29 | 0.37 | 0.40 |

## humaneval_qwen3 — campaign  (lossless: 150 runs, accuracy 0.83)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_opt | -0.3 | 1.00 | 1.04 | 0.11 | 0.86 | 0.05 | 0.74 | 1.72 | 0.40 | 0.49 |
| spec_casc_tok | 0.8 | 0.96 | 1.08 | 0.11 | 0.85 | 0.8 | 0.96 | 1.08 | 0.11 | 0.85 |
| cactus | 0.18 | 1.00 | 1.13 | 0.15 | 0.81 | 0.35 | 1.04 | 1.15 | 0.20 | 0.75 |
| mentored_dec | 0.75 | 1.01 | 1.08 | 0.13 | 0.85 | 0.75 | 1.01 | 1.08 | 0.13 | 0.85 |
| r_fuzzy | 0.03 | 0.86 | 1.16 | 0.13 | 0.61 | 0.25 | 0.75 | 1.65 | 0.38 | 0.16 |

## livecodebench_qwen3 — campaign  (lossless: 90 runs, accuracy 0.70)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_opt | -0.3 | 1.01 | 1.05 | 0.33 | 0.68 | 0.05 | 0.97 | 1.27 | 0.61 | 0.33 |
| spec_casc_tok | 0.8 | 1.06 | 1.00 | 0.30 | 0.71 | 0.8 | 1.06 | 1.00 | 0.30 | 0.71 |
| cactus | 0.03 | 1.05 | 1.06 | 0.37 | 0.63 | 0.35 | 1.39 | 1.15 | 0.54 | 0.44 |
| mentored_dec | 0.75 | 1.08 | 1.05 | 0.34 | 0.63 | 0.75 | 1.08 | 1.05 | 0.34 | 0.63 |
| r_fuzzy | 0.03 | 0.94 | 1.07 | 0.36 | 0.37 | 0.25 | 1.14 | 1.07 | 0.61 | 0.02 |

## mtbench_qwen3 — campaign  (lossless: 80 runs, accuracy --)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_opt | -0.3 | 1.06 | 1.02 | 0.15 | -- | 0.05 | 1.06 | 1.22 | 0.28 | -- |
| spec_casc_tok | 0.8 | 1.04 | 1.04 | 0.14 | -- | 0.8 | 1.04 | 1.04 | 0.14 | -- |
| cactus | 0.03 | 1.20 | 1.04 | 0.16 | -- | 0.35 | 1.57 | 1.16 | 0.33 | -- |
| mentored_dec | 0.15 | 1.02 | 1.02 | 0.16 | -- | 0.75 | 1.12 | 1.04 | 0.21 | -- |
| r_fuzzy | 0.03 | 1.02 | 1.00 | 0.16 | -- | 0.25 | 1.17 | 1.12 | 0.26 | -- |

## longbench_v2_qwen3 — campaign  (lossless: 150 runs, accuracy 0.53)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_opt | -0.3 | 1.00 | 1.09 | 0.07 | 0.47 | 0.05 | 1.20 | 1.16 | 0.17 | 0.37 |
| spec_casc_tok | 0.8 | 1.04 | 1.00 | 0.04 | 0.49 | 0.8 | 1.04 | 1.00 | 0.04 | 0.49 |
| cactus | (none clean) | -- | -- | -- | -- | 0.35 | 1.25 | 2.10 | 0.57 | 0.29 |
| mentored_dec | 0.15 | 1.03 | 0.99 | 0.03 | 0.50 | 0.75 | 1.02 | 1.06 | 0.05 | 0.51 |
| r_fuzzy | 0.03 | 0.97 | 1.05 | 0.06 | 0.48 | 0.25 | 1.04 | 1.08 | 0.11 | 0.44 |

## gsm8k — NEW proper (150 problems x 3 seeds)  (lossless: 450 runs, accuracy 0.96)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_tok | 0.55 | 1.24 | 0.86 | 0.00 | -- | 0.8 | 1.22 | 0.93 | 0.00 | -- |
| spec_casc_tok_lt | 0.8 | 1.27 | 0.92 | 0.00 | -- | 0.8 | 1.27 | 0.92 | 0.00 | -- |

## aime24 — NEW proper (30 x 3 seeds; fine alpha grid)  (lossless: 90 runs, accuracy 0.78)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_opt_head | -0.3 (beta0.35) | 1.06 | 1.03 | 0.03 | -- | 0.05 (beta0.15) | 0.91 | 1.19 | 0.03 | -- |
| spec_casc_tok | 0.25 | 1.05 | 1.02 | 0.11 | 0.78 | 0.8 | 0.85 | 1.39 | 0.13 | -- |
| spec_casc_tok_lt | 0.15 | 1.08 | 1.01 | 0.07 | 0.79 | 0.8 | 0.79 | 1.51 | 0.17 | -- |

## humaneval — NEW proper (150 x 3 seeds)  (lossless: 450 runs, accuracy 0.96)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_tok | 0.2 | 1.01 | 1.01 | 0.00 | 0.97 | 0.25 | 1.01 | 1.03 | 0.00 | 0.96 |
| spec_casc_tok_lt | 0.25 | 1.09 | 1.00 | 0.00 | 0.97 | 0.25 | 1.09 | 1.00 | 0.00 | 0.97 |

## livecodebench — NEW proper (90 x 3 seeds)  (lossless: 270 runs, accuracy 0.89)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_tok | 0.15 | 1.01 | 1.03 | 0.04 | 0.93 | 0.25 | 1.00 | 1.05 | 0.04 | 0.89 |
| spec_casc_tok_lt | 0.15 | 1.06 | 1.02 | 0.04 | 0.89 | 0.25 | 1.01 | 1.08 | 0.05 | 0.89 |

## mtbench — NEW proper (80 x 3 seeds; no grader)  (lossless: 240 runs, accuracy --)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_tok | 0.25 | 1.04 | 0.97 | 0.02 | -- | 0.25 | 1.04 | 0.97 | 0.02 | -- |
| spec_casc_tok_lt | 0.25 | 1.09 | 0.99 | 0.01 | -- | 0.25 | 1.09 | 0.99 | 0.01 | -- |

## longbench_v2 — NEW proper (30 x 3 seeds)  (lossless: 90 runs, accuracy 0.60)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_tok | 0.25 | 1.09 | 0.99 | 0.00 | 0.52 | 0.25 | 1.09 | 0.99 | 0.00 | 0.52 |
| spec_casc_tok_lt | 0.2 | 1.09 | 0.99 | 0.00 | 0.53 | 0.25 | 0.88 | 1.27 | 0.06 | 0.56 |

## aime24 — NEW E6 opt_head (30, 1 seed; tok/tok_lt rows are the fine sweep's)  (lossless: 90 runs, accuracy 0.78)

| rule | best clean: alpha | passes | len | runaways | acc | loosest: alpha | passes | len | runaways | acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_opt_head | -0.3 (beta0.35) | 1.06 | 1.03 | 0.03 | 0.80 | 0.05 (beta0.15) | 0.91 | 1.19 | 0.03 | 0.80 |
| spec_casc_tok | 0.25 | 1.05 | 1.02 | 0.11 | 0.78 | 0.8 | 0.85 | 1.39 | 0.13 | -- |
| spec_casc_tok_lt | 0.15 | 1.08 | 1.01 | 0.07 | 0.79 | 0.8 | 0.79 | 1.51 | 0.17 | -- |

