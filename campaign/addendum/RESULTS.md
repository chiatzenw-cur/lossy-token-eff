# NAACL-2027 addendum: results

Generated 2026-10-06 21:17 UTC by `scripts/addendum_results.py` from the CSVs it names; hand-written observations are in the last section (from `RESULTS_notes.md`). Settings and deviations: `campaign/addendum/README.md`.

## Status

Source: `campaign/addendum/manifest.csv` (292 rows). GPU-hours used so far (sum of `gpu_hours_actual`): 127.6; estimated remaining, runnable rows: 0.0; blocked rows: 5.2.

| step | done | running | queued | pending | blocked |
|---|---:|---:|---:|---:|---:|
| 0.5 | 12 | 0 | 0 | 0 | 0 |
| 2.1 | 96 | 0 | 0 | 0 | 0 |
| 2.2 | 26 | 0 | 0 | 0 | 0 |
| 3 | 20 | 0 | 0 | 0 | 0 |
| 4.1 | 8 | 0 | 0 | 0 | 0 |
| 4.2 | 12 | 0 | 0 | 0 | 0 |
| 4.3 | 8 | 0 | 0 | 0 | 0 |
| 5.1 | 41 | 0 | 0 | 0 | 0 |
| 5.2 | 25 | 0 | 0 | 0 | 0 |
| 6 | 30 | 0 | 0 | 0 | 0 |
| 7 | 0 | 0 | 0 | 0 | 14 |

## Step 1: zero-GPU analyses (seed 0, the paper's data)

**Eq. 4 vs measured** (`campaign/addendum/analysis/eq4_vs_measured_summary.csv`, row 1; per cell: `campaign/addendum/analysis/eq4_vs_measured.csv`), 60 loosest cells: Eq. 4 predicts a win in 33, rounds win in 38, time win in 27; 6 Eq. 4 wins and 11 rounds wins are time losses (paper: 33 / 38 / 27 / 6 / 11 -- reproduced exactly). New: 20 cells are time losses beyond the 95% paired bootstrap interval; of the Eq. 4-win time losses 1, and of the rounds-win time losses 2, lie beyond it.

| target | dataset | method | alpha | lambda | gain | gain/lambda | rounds ratio [95% CI] | time ratio [95% CI] |
|---|---|---|---:|---:|---:|---:|---|---|
| gpt-oss-20b | gsm8k | mentored_dec | 0.75 | 1.16 | 1.33 | 1.14 | 0.83 [0.73, 0.95] | 0.96 [0.86, 1.08] |
| gpt-oss-20b | gsm8k | cactus | 0.35 | 1.61 | 1.51 | 0.94 | 0.99 [0.86, 1.14] | 1.19 [1.06, 1.33] |
| gpt-oss-20b | gsm8k | spec_casc_opt | 0.05 | 1.46 | 1.31 | 0.90 | 1.07 [0.94, 1.22] | 1.18 [1.05, 1.31] |
| gpt-oss-20b | gsm8k | r_fuzzy | 0.25 | 1.70 | 1.41 | 0.83 | 1.14 [0.99, 1.31] | 1.29 [1.15, 1.46] |
| gpt-oss-20b | gsm8k | spec_casc_tok | 0.8 | 0.96 | 1.13 | 1.18 | 0.83 [0.76, 0.91] | 0.91 [0.85, 0.98] |
| gpt-oss-20b | aime24 | mentored_dec | 0.75 | 1.69 | 1.36 | 0.80 | 1.18 [0.93, 1.58] | 1.36 [1.07, 1.82] |
| gpt-oss-20b | aime24 | cactus | 0.18 | 1.78 | 1.54 | 0.87 | 1.07 [0.80, 1.51] | 1.33 [1.01, 1.85] |
| gpt-oss-20b | aime24 | spec_casc_opt | 0.05 | 2.48 | 1.37 | 0.55 | 1.70 [1.28, 2.43] | 2.01 [1.51, 2.85] |
| gpt-oss-20b | aime24 | r_fuzzy | 0.25 | 2.13 | 1.47 | 0.69 | 1.37 [1.04, 1.93] | 1.64 [1.26, 2.30] |
| gpt-oss-20b | aime24 | spec_casc_tok | 0.8 | 1.48 | 1.16 | 0.78 | 1.22 [0.88, 1.72] | 1.33 [0.96, 1.85] |
| gpt-oss-20b | humaneval | mentored_dec | 0.75 | 1.30 | 1.31 | 1.01 | 0.97 [0.85, 1.09] | 1.09 [0.97, 1.22] |
| gpt-oss-20b | humaneval | cactus | 0.35 | 1.79 | 1.52 | 0.85 | 1.12 [1.00, 1.25] | 1.35 [1.22, 1.49] |
| gpt-oss-20b | humaneval | spec_casc_opt | 0.05 | 1.73 | 1.29 | 0.74 | 1.29 [1.15, 1.46] | 1.43 [1.28, 1.60] |
| gpt-oss-20b | humaneval | r_fuzzy | 0.25 | 1.64 | 1.35 | 0.83 | 1.16 [1.03, 1.31] | 1.32 [1.19, 1.47] |
| gpt-oss-20b | humaneval | spec_casc_tok | 0.8 | 1.05 | 1.11 | 1.06 | 0.93 [0.84, 1.02] | 0.98 [0.91, 1.07] |
| gpt-oss-20b | livecodebench | mentored_dec | 0.75 | 1.25 | 1.35 | 1.08 | 0.89 [0.81, 0.99] | 1.01 [0.92, 1.10] |
| gpt-oss-20b | livecodebench | cactus | 0.18 | 1.54 | 1.53 | 1.00 | 0.94 [0.80, 1.09] | 1.14 [0.99, 1.32] |
| gpt-oss-20b | livecodebench | spec_casc_opt | 0.05 | 1.64 | 1.35 | 0.83 | 1.16 [1.03, 1.32] | 1.32 [1.17, 1.48] |
| gpt-oss-20b | livecodebench | r_fuzzy | 0.25 | 1.65 | 1.42 | 0.86 | 1.11 [0.97, 1.28] | 1.27 [1.11, 1.46] |
| gpt-oss-20b | livecodebench | spec_casc_tok | 0.8 | 1.16 | 1.16 | 1.00 | 0.98 [0.86, 1.11] | 1.04 [0.92, 1.17] |
| gpt-oss-20b | mtbench | mentored_dec | 0.75 | 1.10 | 1.38 | 1.26 | 0.75 [0.67, 0.84] | 0.87 [0.78, 0.97] |
| gpt-oss-20b | mtbench | cactus | 0.35 | 1.18 | 1.73 | 1.46 | 0.62 [0.53, 0.73] | 0.82 [0.72, 0.95] |
| gpt-oss-20b | mtbench | spec_casc_opt | 0.05 | 1.09 | 1.34 | 1.23 | 0.76 [0.68, 0.85] | 0.87 [0.78, 0.97] |
| gpt-oss-20b | mtbench | r_fuzzy | 0.25 | 1.20 | 1.46 | 1.22 | 0.76 [0.67, 0.86] | 0.92 [0.81, 1.04] |
| gpt-oss-20b | mtbench | spec_casc_tok | 0.8 | 0.96 | 1.09 | 1.13 | 0.88 [0.81, 0.95] | 0.90 [0.84, 0.99] |
| gpt-oss-20b | longbench_v2 | mentored_dec | 0.75 | 1.59 | 1.41 | 0.88 | 1.11 [0.98, 1.26] | 1.04 [1.02, 1.07] |
| gpt-oss-20b | longbench_v2 | cactus | 0.35 | 1.77 | 2.00 | 1.13 | 0.87 [0.76, 1.02] | 1.03 [1.00, 1.05] |
| gpt-oss-20b | longbench_v2 | spec_casc_opt | 0.05 | 1.79 | 1.33 | 0.74 | 1.31 [1.14, 1.52] | 1.07 [1.04, 1.10] |
| gpt-oss-20b | longbench_v2 | r_fuzzy | 0.25 | 1.69 | 1.52 | 0.90 | 1.10 [0.94, 1.28] | 1.05 [1.02, 1.07] |
| gpt-oss-20b | longbench_v2 | spec_casc_tok | 0.8 | 1.13 | 1.15 | 1.02 | 0.97 [0.85, 1.10] | 1.00 [0.98, 1.02] |
| qwen3-8b | gsm8k | mentored_dec | 0.75 | 1.03 | 1.09 | 1.07 | 0.93 [0.89, 0.97] | 0.95 [0.92, 1.00] |
| qwen3-8b | gsm8k | cactus | 0.35 | 1.04 | 1.14 | 1.10 | 0.90 [0.86, 0.93] | 0.94 [0.90, 0.97] |
| qwen3-8b | gsm8k | spec_casc_opt | 0.05 | 1.33 | 1.27 | 0.95 | 1.05 [0.99, 1.11] | 1.12 [1.07, 1.18] |
| qwen3-8b | gsm8k | r_fuzzy | 0.25 | 0.95 | 1.22 | 1.28 | 0.76 [0.69, 0.83] | 0.81 [0.74, 0.89] |
| qwen3-8b | gsm8k | spec_casc_tok | 0.8 | 0.99 | 1.04 | 1.05 | 0.95 [0.91, 0.99] | 0.96 [0.92, 1.00] |
| qwen3-8b | aime24 | mentored_dec | 0.75 | 1.01 | 1.09 | 1.08 | 0.94 [0.83, 1.07] | 0.95 [0.83, 1.10] |
| qwen3-8b | aime24 | cactus | 0.35 | 1.26 | 2.12 | 1.69 | 0.55 [0.47, 0.64] | 0.66 [0.56, 0.78] |
| qwen3-8b | aime24 | spec_casc_opt | 0.05 | 1.42 | 1.33 | 0.94 | 1.06 [0.89, 1.29] | 1.14 [0.94, 1.38] |
| qwen3-8b | aime24 | r_fuzzy | 0.25 | 1.29 | 1.13 | 0.87 | 1.16 [0.96, 1.40] | 1.18 [0.97, 1.45] |
| qwen3-8b | aime24 | spec_casc_tok | 0.8 | 0.98 | 1.07 | 1.08 | 0.93 [0.81, 1.07] | 0.93 [0.80, 1.06] |
| qwen3-8b | humaneval | mentored_dec | 0.75 | 1.08 | 1.07 | 0.99 | 0.99 [0.92, 1.06] | 1.02 [0.95, 1.09] |
| qwen3-8b | humaneval | cactus | 0.35 | 1.14 | 1.13 | 0.99 | 0.96 [0.89, 1.04] | 1.01 [0.94, 1.09] |
| qwen3-8b | humaneval | spec_casc_opt | 0.05 | 1.72 | 1.25 | 0.73 | 1.36 [1.24, 1.49] | 1.46 [1.34, 1.60] |
| qwen3-8b | humaneval | r_fuzzy | 0.25 | 1.65 | 1.26 | 0.76 | 1.33 [1.21, 1.46] | 1.41 [1.28, 1.55] |
| qwen3-8b | humaneval | spec_casc_tok | 0.8 | 1.08 | 1.03 | 0.96 | 1.04 [0.98, 1.10] | 1.05 [0.99, 1.11] |
| qwen3-8b | livecodebench | mentored_dec | 0.75 | 1.05 | 1.11 | 1.06 | 0.93 [0.90, 0.97] | 0.95 [0.92, 0.99] |
| qwen3-8b | livecodebench | cactus | 0.35 | 1.15 | 1.51 | 1.32 | 0.72 [0.66, 0.79] | 0.82 [0.76, 0.89] |
| qwen3-8b | livecodebench | spec_casc_opt | 0.05 | 1.27 | 1.22 | 0.96 | 1.03 [0.97, 1.10] | 1.09 [1.02, 1.16] |
| qwen3-8b | livecodebench | r_fuzzy | 0.25 | 1.07 | 1.25 | 1.17 | 0.87 [0.78, 0.97] | 0.92 [0.82, 1.03] |
| qwen3-8b | livecodebench | spec_casc_tok | 0.8 | 1.00 | 1.06 | 1.05 | 0.94 [0.91, 0.97] | 0.96 [0.92, 0.99] |
| qwen3-8b | mtbench | mentored_dec | 0.75 | 1.04 | 1.16 | 1.11 | 0.89 [0.84, 0.95] | 0.93 [0.87, 0.99] |
| qwen3-8b | mtbench | cactus | 0.35 | 1.16 | 1.79 | 1.55 | 0.64 [0.58, 0.70] | 0.75 [0.68, 0.84] |
| qwen3-8b | mtbench | spec_casc_opt | 0.05 | 1.22 | 1.28 | 1.05 | 0.94 [0.88, 1.01] | 1.01 [0.95, 1.09] |
| qwen3-8b | mtbench | r_fuzzy | 0.25 | 1.12 | 1.30 | 1.16 | 0.85 [0.79, 0.92] | 0.92 [0.85, 0.99] |
| qwen3-8b | mtbench | spec_casc_tok | 0.8 | 1.04 | 1.07 | 1.03 | 0.96 [0.91, 1.03] | 0.99 [0.93, 1.05] |
| qwen3-8b | longbench_v2 | mentored_dec | 0.75 | 1.06 | 1.07 | 1.01 | 0.98 [0.91, 1.05] | 0.99 [0.92, 1.06] |
| qwen3-8b | longbench_v2 | cactus | 0.35 | 2.10 | 2.62 | 1.25 | 0.80 [0.72, 0.89] | 1.05 [0.94, 1.16] |
| qwen3-8b | longbench_v2 | spec_casc_opt | 0.05 | 1.16 | 1.38 | 1.18 | 0.83 [0.76, 0.90] | 0.90 [0.83, 0.98] |
| qwen3-8b | longbench_v2 | r_fuzzy | 0.25 | 1.08 | 1.12 | 1.03 | 0.96 [0.88, 1.04] | 0.99 [0.90, 1.07] |
| qwen3-8b | longbench_v2 | spec_casc_tok | 0.8 | 1.00 | 1.03 | 1.04 | 0.96 [0.89, 1.03] | 0.97 [0.90, 1.04] |

**Where the extra length goes** (`campaign/addendum/analysis/split_inflation.csv`; thinking = GPT-OSS analysis channel / Qwen3 `<think>` blocks, characters):

| target | dataset | method | lambda (tokens) | lambda thinking | lambda answer | share of extra in thinking |
|---|---|---|---:|---:|---:|---:|
| gpt-oss-20b | gsm8k | mentored_dec | 1.16 | 1.16 | 1.36 | 96% |
| gpt-oss-20b | gsm8k | cactus | 1.61 | 1.62 | 3.35 | 93% |
| gpt-oss-20b | gsm8k | spec_casc_opt | 1.46 | 1.44 | 1.94 | 96% |
| gpt-oss-20b | gsm8k | r_fuzzy | 1.70 | 1.69 | 2.85 | 95% |
| gpt-oss-20b | gsm8k | spec_casc_tok | 0.96 | 0.94 | 0.89 | - |
| gpt-oss-20b | aime24 | mentored_dec | 1.69 | 1.80 | 0.83 | 102% |
| gpt-oss-20b | aime24 | cactus | 1.78 | 1.97 | 0.86 | 101% |
| gpt-oss-20b | aime24 | spec_casc_opt | 2.48 | 2.50 | 0.40 | 103% |
| gpt-oss-20b | aime24 | r_fuzzy | 2.13 | 2.30 | 0.77 | 101% |
| gpt-oss-20b | aime24 | spec_casc_tok | 1.48 | 1.47 | 0.86 | 102% |
| gpt-oss-20b | humaneval | mentored_dec | 1.30 | 1.38 | 1.02 | 98% |
| gpt-oss-20b | humaneval | cactus | 1.79 | 2.01 | 1.20 | 93% |
| gpt-oss-20b | humaneval | spec_casc_opt | 1.73 | 1.83 | 1.17 | 93% |
| gpt-oss-20b | humaneval | r_fuzzy | 1.64 | 1.74 | 1.27 | 88% |
| gpt-oss-20b | humaneval | spec_casc_tok | 1.05 | 1.02 | 0.99 | 128% |
| gpt-oss-20b | livecodebench | mentored_dec | 1.25 | 1.42 | 0.95 | 108% |
| gpt-oss-20b | livecodebench | cactus | 1.54 | 2.02 | 0.95 | 103% |
| gpt-oss-20b | livecodebench | spec_casc_opt | 1.64 | 1.98 | 0.90 | 108% |
| gpt-oss-20b | livecodebench | r_fuzzy | 1.65 | 2.07 | 1.03 | 98% |
| gpt-oss-20b | livecodebench | spec_casc_tok | 1.16 | 1.18 | 0.94 | 130% |
| gpt-oss-20b | mtbench | mentored_dec | 1.10 | 1.12 | 1.05 | 65% |
| gpt-oss-20b | mtbench | cactus | 1.18 | 1.48 | 0.89 | 139% |
| gpt-oss-20b | mtbench | spec_casc_opt | 1.09 | 1.15 | 0.97 | 131% |
| gpt-oss-20b | mtbench | r_fuzzy | 1.20 | 1.24 | 1.09 | 67% |
| gpt-oss-20b | mtbench | spec_casc_tok | 0.96 | 0.98 | 0.95 | - |
| gpt-oss-20b | longbench_v2 | mentored_dec | 1.59 | 1.61 | 0.91 | 100% |
| gpt-oss-20b | longbench_v2 | cactus | 1.77 | 1.76 | 1.21 | 100% |
| gpt-oss-20b | longbench_v2 | spec_casc_opt | 1.79 | 1.65 | 0.68 | 100% |
| gpt-oss-20b | longbench_v2 | r_fuzzy | 1.69 | 1.66 | 1.48 | 99% |
| gpt-oss-20b | longbench_v2 | spec_casc_tok | 1.13 | 1.12 | 0.84 | 101% |
| qwen3-8b | gsm8k | mentored_dec | 1.03 | 1.03 | 0.93 | 136% |
| qwen3-8b | gsm8k | cactus | 1.04 | 1.05 | 0.93 | 123% |
| qwen3-8b | gsm8k | spec_casc_opt | 1.33 | 1.23 | 0.60 | 128% |
| qwen3-8b | gsm8k | r_fuzzy | 0.95 | 0.89 | 0.97 | - |
| qwen3-8b | gsm8k | spec_casc_tok | 0.99 | 0.98 | 1.02 | - |
| qwen3-8b | aime24 | mentored_dec | 1.01 | 1.03 | 0.88 | 126% |
| qwen3-8b | aime24 | cactus | 1.26 | 1.06 | 9.38 | 13% |
| qwen3-8b | aime24 | spec_casc_opt | 1.42 | 1.12 | 1.22 | 91% |
| qwen3-8b | aime24 | r_fuzzy | 1.29 | 1.14 | 2.05 | 73% |
| qwen3-8b | aime24 | spec_casc_tok | 0.98 | 0.97 | 1.04 | - |
| qwen3-8b | humaneval | mentored_dec | 1.08 | 1.11 | 0.93 | 105% |
| qwen3-8b | humaneval | cactus | 1.14 | 1.15 | 1.34 | 87% |
| qwen3-8b | humaneval | spec_casc_opt | 1.72 | 1.53 | 1.50 | 94% |
| qwen3-8b | humaneval | r_fuzzy | 1.65 | 1.56 | 2.38 | 86% |
| qwen3-8b | humaneval | spec_casc_tok | 1.08 | 1.12 | 0.80 | 112% |
| qwen3-8b | livecodebench | mentored_dec | 1.05 | 1.06 | 0.95 | 106% |
| qwen3-8b | livecodebench | cactus | 1.15 | 1.10 | 2.89 | 42% |
| qwen3-8b | livecodebench | spec_casc_opt | 1.27 | 1.23 | 0.85 | 105% |
| qwen3-8b | livecodebench | r_fuzzy | 1.07 | 1.05 | 1.29 | 73% |
| qwen3-8b | livecodebench | spec_casc_tok | 1.00 | 1.00 | 0.98 | - |
| qwen3-8b | mtbench | mentored_dec | 1.04 | 1.04 | 1.01 | 93% |
| qwen3-8b | mtbench | cactus | 1.16 | 1.17 | 1.13 | 83% |
| qwen3-8b | mtbench | spec_casc_opt | 1.22 | 1.20 | 1.02 | 98% |
| qwen3-8b | mtbench | r_fuzzy | 1.12 | 1.15 | 0.94 | 112% |
| qwen3-8b | mtbench | spec_casc_tok | 1.04 | 1.04 | 1.02 | 91% |
| qwen3-8b | longbench_v2 | mentored_dec | 1.06 | 1.05 | 1.02 | 92% |
| qwen3-8b | longbench_v2 | cactus | 2.10 | 2.20 | 1.73 | 86% |
| qwen3-8b | longbench_v2 | spec_casc_opt | 1.16 | 0.96 | 1.08 | - |
| qwen3-8b | longbench_v2 | r_fuzzy | 1.08 | 1.07 | 0.98 | 111% |
| qwen3-8b | longbench_v2 | spec_casc_tok | 1.00 | 0.97 | 0.98 | - |

**Censoring** (`campaign/addendum/analysis/censoring.csv`): cap-out rates and lambda / accuracy restricted to pairs where both runs finished.

| target | dataset | method | cap-out relaxed | cap-out strict | lambda all | lambda both finished | acc relaxed / strict (all) | acc relaxed / strict (both finished) | n both finished |
|---|---|---|---:|---:|---:|---:|---|---|---:|
| gpt-oss-20b | gsm8k | mentored_dec | 4% | 2% | 1.16 | 1.09 | 93% / 96% | 97% / 98% | 144 |
| gpt-oss-20b | gsm8k | cactus | 5% | 2% | 1.61 | 1.60 | 91% / 96% | 96% / 99% | 142 |
| gpt-oss-20b | gsm8k | spec_casc_opt | 5% | 2% | 1.46 | 1.47 | 94% / 96% | 98% / 98% | 143 |
| gpt-oss-20b | gsm8k | r_fuzzy | 5% | 2% | 1.70 | 1.72 | 87% / 96% | 92% / 97% | 142 |
| gpt-oss-20b | gsm8k | spec_casc_tok | 1% | 2% | 0.96 | 0.95 | 97% / 96% | 99% / 97% | 147 |
| gpt-oss-20b | aime24 | mentored_dec | 20% | 7% | 1.69 | 1.76 | 63% / 77% | 78% / 83% | 23 |
| gpt-oss-20b | aime24 | cactus | 23% | 7% | 1.78 | 1.66 | 60% / 77% | 73% / 82% | 22 |
| gpt-oss-20b | aime24 | spec_casc_opt | 43% | 7% | 2.48 | 2.38 | 37% / 77% | 65% / 82% | 17 |
| gpt-oss-20b | aime24 | r_fuzzy | 30% | 7% | 2.13 | 2.27 | 50% / 77% | 67% / 81% | 21 |
| gpt-oss-20b | aime24 | spec_casc_tok | 20% | 7% | 1.48 | 1.28 | 70% / 77% | 88% / 88% | 24 |
| gpt-oss-20b | humaneval | mentored_dec | 1% | 0% | 1.30 | 1.26 | 96% / 96% | 97% / 96% | 149 |
| gpt-oss-20b | humaneval | cactus | 1% | 0% | 1.79 | 1.76 | 87% / 96% | 89% / 96% | 148 |
| gpt-oss-20b | humaneval | spec_casc_opt | 2% | 0% | 1.73 | 1.66 | 82% / 96% | 84% / 97% | 147 |
| gpt-oss-20b | humaneval | r_fuzzy | 1% | 0% | 1.64 | 1.61 | 63% / 96% | 63% / 96% | 149 |
| gpt-oss-20b | humaneval | spec_casc_tok | 0% | 0% | 1.05 | 1.05 | 94% / 96% | 94% / 96% | 150 |
| gpt-oss-20b | livecodebench | mentored_dec | 9% | 2% | 1.25 | 1.23 | 84% / 89% | 93% / 91% | 82 |
| gpt-oss-20b | livecodebench | cactus | 11% | 2% | 1.54 | 1.49 | 61% / 89% | 70% / 91% | 79 |
| gpt-oss-20b | livecodebench | spec_casc_opt | 19% | 2% | 1.64 | 1.62 | 49% / 89% | 60% / 90% | 73 |
| gpt-oss-20b | livecodebench | r_fuzzy | 16% | 2% | 1.65 | 1.62 | 34% / 89% | 41% / 92% | 75 |
| gpt-oss-20b | livecodebench | spec_casc_tok | 7% | 2% | 1.16 | 1.11 | 88% / 89% | 94% / 92% | 84 |
| gpt-oss-20b | mtbench | mentored_dec | 1% | 4% | 1.10 | 1.14 | - / - | - / - | 76 |
| gpt-oss-20b | mtbench | cactus | 6% | 4% | 1.18 | 1.22 | - / - | - / - | 72 |
| gpt-oss-20b | mtbench | spec_casc_opt | 2% | 4% | 1.09 | 1.14 | - / - | - / - | 75 |
| gpt-oss-20b | mtbench | r_fuzzy | 4% | 4% | 1.20 | 1.23 | - / - | - / - | 74 |
| gpt-oss-20b | mtbench | spec_casc_tok | 1% | 4% | 0.96 | 0.99 | - / - | - / - | 77 |
| gpt-oss-20b | longbench_v2 | mentored_dec | 3% | 1% | 1.59 | 1.57 | 51% / 56% | 51% / 55% | 145 |
| gpt-oss-20b | longbench_v2 | cactus | 2% | 1% | 1.77 | 1.87 | 36% / 56% | 36% / 57% | 145 |
| gpt-oss-20b | longbench_v2 | spec_casc_opt | 14% | 1% | 1.79 | 1.45 | 47% / 56% | 50% / 53% | 129 |
| gpt-oss-20b | longbench_v2 | r_fuzzy | 5% | 1% | 1.69 | 1.65 | 40% / 56% | 41% / 55% | 140 |
| gpt-oss-20b | longbench_v2 | spec_casc_tok | 1% | 1% | 1.13 | 1.15 | 53% / 56% | 53% / 56% | 147 |
| qwen3-8b | gsm8k | mentored_dec | 26% | 25% | 1.03 | 1.03 | 77% / 80% | 100% / 100% | 102 |
| qwen3-8b | gsm8k | cactus | 27% | 25% | 1.04 | 1.03 | 77% / 80% | 100% / 100% | 103 |
| qwen3-8b | gsm8k | spec_casc_opt | 58% | 25% | 1.33 | 1.47 | 49% / 80% | 95% / 100% | 63 |
| qwen3-8b | gsm8k | r_fuzzy | 35% | 25% | 0.95 | 0.87 | 55% / 80% | 82% / 100% | 83 |
| qwen3-8b | gsm8k | spec_casc_tok | 23% | 25% | 0.99 | 0.97 | 79% / 80% | 100% / 100% | 103 |
| qwen3-8b | aime24 | mentored_dec | 23% | 17% | 1.01 | 0.96 | 73% / 70% | 96% / 91% | 23 |
| qwen3-8b | aime24 | cactus | 57% | 17% | 1.26 | 1.17 | 23% / 70% | 50% / 100% | 12 |
| qwen3-8b | aime24 | spec_casc_opt | 63% | 17% | 1.42 | 1.41 | 30% / 70% | 90% / 100% | 10 |
| qwen3-8b | aime24 | r_fuzzy | 37% | 17% | 1.29 | 1.47 | 40% / 70% | 67% / 94% | 18 |
| qwen3-8b | aime24 | spec_casc_tok | 13% | 17% | 0.98 | 1.01 | 70% / 70% | 83% / 91% | 23 |
| qwen3-8b | humaneval | mentored_dec | 13% | 11% | 1.08 | 1.12 | 85% / 83% | 97% / 93% | 126 |
| qwen3-8b | humaneval | cactus | 20% | 11% | 1.14 | 1.13 | 75% / 83% | 96% / 93% | 117 |
| qwen3-8b | humaneval | spec_casc_opt | 40% | 11% | 1.72 | 1.84 | 49% / 83% | 80% / 92% | 85 |
| qwen3-8b | humaneval | r_fuzzy | 38% | 11% | 1.65 | 1.78 | 16% / 83% | 25% / 93% | 89 |
| qwen3-8b | humaneval | spec_casc_tok | 11% | 11% | 1.08 | 1.12 | 85% / 83% | 96% / 93% | 129 |
| qwen3-8b | livecodebench | mentored_dec | 34% | 32% | 1.05 | 1.11 | 63% / 70% | 96% / 98% | 53 |
| qwen3-8b | livecodebench | cactus | 54% | 32% | 1.15 | 1.23 | 44% / 70% | 97% / 97% | 38 |
| qwen3-8b | livecodebench | spec_casc_opt | 61% | 32% | 1.27 | 1.69 | 33% / 70% | 79% / 100% | 34 |
| qwen3-8b | livecodebench | r_fuzzy | 61% | 32% | 1.07 | 0.66 | 2% / 70% | 6% / 97% | 33 |
| qwen3-8b | livecodebench | spec_casc_tok | 30% | 32% | 1.00 | 1.01 | 71% / 70% | 100% / 98% | 56 |
| qwen3-8b | mtbench | mentored_dec | 21% | 14% | 1.04 | 1.00 | - / - | - / - | 62 |
| qwen3-8b | mtbench | cactus | 32% | 14% | 1.16 | 1.02 | - / - | - / - | 52 |
| qwen3-8b | mtbench | spec_casc_opt | 28% | 14% | 1.22 | 1.23 | - / - | - / - | 58 |
| qwen3-8b | mtbench | r_fuzzy | 26% | 14% | 1.12 | 1.07 | - / - | - / - | 58 |
| qwen3-8b | mtbench | spec_casc_tok | 14% | 14% | 1.04 | 1.03 | - / - | - / - | 64 |
| qwen3-8b | longbench_v2 | mentored_dec | 5% | 3% | 1.06 | 1.05 | 51% / 53% | 51% / 51% | 142 |
| qwen3-8b | longbench_v2 | cactus | 57% | 3% | 2.10 | 1.27 | 29% / 53% | 44% / 60% | 62 |
| qwen3-8b | longbench_v2 | spec_casc_opt | 17% | 3% | 1.16 | 0.94 | 37% / 53% | 42% / 48% | 125 |
| qwen3-8b | longbench_v2 | r_fuzzy | 11% | 3% | 1.08 | 1.00 | 44% / 53% | 45% / 48% | 132 |
| qwen3-8b | longbench_v2 | spec_casc_tok | 4% | 3% | 1.00 | 0.99 | 49% / 53% | 51% / 50% | 143 |

**Uniform shift or runaway completions?** (`campaign/addendum/analysis/distribution.csv`): per-case L_relaxed / L_strict.

| target | dataset | method | p10 | p50 | p90 | share > 2 | top-10% cases' share of net extra |
|---|---|---|---:|---:|---:|---:|---:|
| gpt-oss-20b | gsm8k | mentored_dec | 0.55 | 1.11 | 2.19 | 13% | 133% |
| gpt-oss-20b | gsm8k | cactus | 0.64 | 1.50 | 3.42 | 29% | 57% |
| gpt-oss-20b | gsm8k | spec_casc_opt | 0.55 | 1.22 | 2.85 | 23% | 68% |
| gpt-oss-20b | gsm8k | r_fuzzy | 0.76 | 1.54 | 3.65 | 35% | 52% |
| gpt-oss-20b | gsm8k | spec_casc_tok | 0.52 | 0.95 | 1.82 | 9% | - |
| gpt-oss-20b | aime24 | mentored_dec | 0.88 | 1.44 | 2.99 | 40% | 39% |
| gpt-oss-20b | aime24 | cactus | 0.84 | 1.71 | 4.90 | 43% | 39% |
| gpt-oss-20b | aime24 | spec_casc_opt | 1.12 | 2.60 | 7.16 | 70% | 23% |
| gpt-oss-20b | aime24 | r_fuzzy | 1.12 | 2.29 | 5.45 | 57% | 29% |
| gpt-oss-20b | aime24 | spec_casc_tok | 0.75 | 1.37 | 3.35 | 27% | 53% |
| gpt-oss-20b | humaneval | mentored_dec | 0.69 | 1.12 | 1.93 | 9% | 85% |
| gpt-oss-20b | humaneval | cactus | 0.85 | 1.43 | 3.34 | 29% | 52% |
| gpt-oss-20b | humaneval | spec_casc_opt | 0.78 | 1.33 | 2.86 | 23% | 61% |
| gpt-oss-20b | humaneval | r_fuzzy | 0.83 | 1.48 | 2.98 | 25% | 52% |
| gpt-oss-20b | humaneval | spec_casc_tok | 0.72 | 0.98 | 1.56 | 4% | 266% |
| gpt-oss-20b | livecodebench | mentored_dec | 0.82 | 1.21 | 1.96 | 9% | 55% |
| gpt-oss-20b | livecodebench | cactus | 0.83 | 1.52 | 2.65 | 31% | 43% |
| gpt-oss-20b | livecodebench | spec_casc_opt | 0.95 | 1.55 | 2.75 | 33% | 34% |
| gpt-oss-20b | livecodebench | r_fuzzy | 0.91 | 1.53 | 3.08 | 38% | 36% |
| gpt-oss-20b | livecodebench | spec_casc_tok | 0.72 | 1.11 | 1.83 | 9% | 92% |
| gpt-oss-20b | mtbench | mentored_dec | 0.70 | 1.09 | 1.92 | 8% | 107% |
| gpt-oss-20b | mtbench | cactus | 0.81 | 1.20 | 2.25 | 14% | 78% |
| gpt-oss-20b | mtbench | spec_casc_opt | 0.79 | 1.11 | 1.72 | 6% | 119% |
| gpt-oss-20b | mtbench | r_fuzzy | 0.71 | 1.30 | 2.15 | 12% | 64% |
| gpt-oss-20b | mtbench | spec_casc_tok | 0.66 | 0.99 | 1.47 | 2% | - |
| gpt-oss-20b | longbench_v2 | mentored_dec | 0.68 | 1.44 | 3.63 | 34% | 55% |
| gpt-oss-20b | longbench_v2 | cactus | 0.79 | 1.75 | 4.47 | 44% | 46% |
| gpt-oss-20b | longbench_v2 | spec_casc_opt | 0.70 | 1.53 | 3.90 | 35% | 55% |
| gpt-oss-20b | longbench_v2 | r_fuzzy | 0.53 | 1.65 | 4.41 | 39% | 52% |
| gpt-oss-20b | longbench_v2 | spec_casc_tok | 0.51 | 1.15 | 2.67 | 21% | 151% |
| qwen3-8b | gsm8k | mentored_dec | 0.72 | 1.00 | 1.41 | 2% | 206% |
| qwen3-8b | gsm8k | cactus | 0.73 | 1.00 | 1.48 | 2% | 147% |
| qwen3-8b | gsm8k | spec_casc_opt | 1.00 | 1.32 | 2.35 | 16% | 30% |
| qwen3-8b | gsm8k | r_fuzzy | 0.21 | 1.00 | 1.92 | 7% | - |
| qwen3-8b | gsm8k | spec_casc_tok | 0.74 | 1.00 | 1.32 | 1% | - |
| qwen3-8b | aime24 | mentored_dec | 0.64 | 1.00 | 1.43 | 3% | 545% |
| qwen3-8b | aime24 | cactus | 0.74 | 1.23 | 2.03 | 13% | 40% |
| qwen3-8b | aime24 | spec_casc_opt | 1.00 | 1.36 | 2.92 | 33% | 29% |
| qwen3-8b | aime24 | r_fuzzy | 0.88 | 1.42 | 2.50 | 23% | 36% |
| qwen3-8b | aime24 | spec_casc_tok | 0.54 | 1.02 | 1.36 | 3% | - |
| qwen3-8b | humaneval | mentored_dec | 0.72 | 1.05 | 1.71 | 5% | 123% |
| qwen3-8b | humaneval | cactus | 0.76 | 1.05 | 1.75 | 5% | 86% |
| qwen3-8b | humaneval | spec_casc_opt | 1.00 | 1.84 | 4.03 | 43% | 26% |
| qwen3-8b | humaneval | r_fuzzy | 0.86 | 1.88 | 3.50 | 47% | 27% |
| qwen3-8b | humaneval | spec_casc_tok | 0.79 | 1.05 | 1.52 | 5% | 106% |
| qwen3-8b | livecodebench | mentored_dec | 0.86 | 1.00 | 1.38 | 0% | 90% |
| qwen3-8b | livecodebench | cactus | 0.80 | 1.07 | 1.76 | 7% | 54% |
| qwen3-8b | livecodebench | spec_casc_opt | 1.00 | 1.22 | 2.20 | 19% | 32% |
| qwen3-8b | livecodebench | r_fuzzy | 0.18 | 1.02 | 2.48 | 17% | 121% |
| qwen3-8b | livecodebench | spec_casc_tok | 0.86 | 1.00 | 1.23 | 0% | 840% |
| qwen3-8b | mtbench | mentored_dec | 0.69 | 1.00 | 1.38 | 0% | 169% |
| qwen3-8b | mtbench | cactus | 0.63 | 1.07 | 2.02 | 11% | 77% |
| qwen3-8b | mtbench | spec_casc_opt | 0.85 | 1.18 | 1.96 | 10% | 46% |
| qwen3-8b | mtbench | r_fuzzy | 0.73 | 1.02 | 1.70 | 6% | 76% |
| qwen3-8b | mtbench | spec_casc_tok | 0.76 | 1.00 | 1.47 | 2% | 181% |
| qwen3-8b | longbench_v2 | mentored_dec | 0.59 | 1.02 | 1.78 | 6% | 166% |
| qwen3-8b | longbench_v2 | cactus | 0.71 | 2.08 | 6.21 | 51% | 23% |
| qwen3-8b | longbench_v2 | spec_casc_opt | 0.42 | 1.06 | 2.16 | 12% | 113% |
| qwen3-8b | longbench_v2 | r_fuzzy | 0.54 | 1.00 | 1.95 | 10% | 162% |
| qwen3-8b | longbench_v2 | spec_casc_tok | 0.58 | 0.96 | 1.65 | 5% | - |

**Exact repetition** (`campaign/addendum/analysis/repetition.csv`; per run: `campaign/addendum/analysis/repetition_runs.csv`): share of tokens inside a 50-gram that occurred earlier in the same output, and the longest repeated token run.

| target | dataset | method | rep-50 share relaxed | rep-50 share strict | longest repeat relaxed | longest repeat strict |
|---|---|---|---:|---:|---:|---:|
| gpt-oss-20b | gsm8k | mentored_dec | 0.06% | 0.00% | 11 | 10 |
| gpt-oss-20b | gsm8k | cactus | 0.09% | 0.00% | 13 | 10 |
| gpt-oss-20b | gsm8k | spec_casc_opt | 0.04% | 0.00% | 13 | 10 |
| gpt-oss-20b | gsm8k | r_fuzzy | 0.09% | 0.00% | 13 | 10 |
| gpt-oss-20b | gsm8k | spec_casc_tok | 0.05% | 0.00% | 11 | 10 |
| gpt-oss-20b | aime24 | mentored_dec | 0.02% | 0.00% | 29 | 25 |
| gpt-oss-20b | aime24 | cactus | 0.02% | 0.00% | 28 | 25 |
| gpt-oss-20b | aime24 | spec_casc_opt | 0.16% | 0.00% | 43 | 25 |
| gpt-oss-20b | aime24 | r_fuzzy | 0.01% | 0.00% | 27 | 25 |
| gpt-oss-20b | aime24 | spec_casc_tok | 0.11% | 0.00% | 37 | 25 |
| gpt-oss-20b | humaneval | mentored_dec | 1.15% | 1.85% | 28 | 27 |
| gpt-oss-20b | humaneval | cactus | 1.15% | 1.85% | 27 | 27 |
| gpt-oss-20b | humaneval | spec_casc_opt | 2.82% | 1.85% | 40 | 27 |
| gpt-oss-20b | humaneval | r_fuzzy | 0.35% | 1.85% | 22 | 27 |
| gpt-oss-20b | humaneval | spec_casc_tok | 1.47% | 1.85% | 28 | 27 |
| gpt-oss-20b | livecodebench | mentored_dec | 0.07% | 0.00% | 25 | 15 |
| gpt-oss-20b | livecodebench | cactus | 0.02% | 0.00% | 21 | 15 |
| gpt-oss-20b | livecodebench | spec_casc_opt | 0.18% | 0.00% | 27 | 15 |
| gpt-oss-20b | livecodebench | r_fuzzy | 0.12% | 0.00% | 23 | 15 |
| gpt-oss-20b | livecodebench | spec_casc_tok | 0.22% | 0.00% | 25 | 15 |
| gpt-oss-20b | mtbench | mentored_dec | 0.17% | 0.76% | 16 | 17 |
| gpt-oss-20b | mtbench | cactus | 0.57% | 0.76% | 19 | 17 |
| gpt-oss-20b | mtbench | spec_casc_opt | 0.47% | 0.76% | 18 | 17 |
| gpt-oss-20b | mtbench | r_fuzzy | 0.36% | 0.76% | 17 | 17 |
| gpt-oss-20b | mtbench | spec_casc_tok | 0.52% | 0.76% | 19 | 17 |
| gpt-oss-20b | longbench_v2 | mentored_dec | 1.20% | 0.75% | 36 | 29 |
| gpt-oss-20b | longbench_v2 | cactus | 0.53% | 0.75% | 27 | 29 |
| gpt-oss-20b | longbench_v2 | spec_casc_opt | 2.45% | 0.75% | 42 | 29 |
| gpt-oss-20b | longbench_v2 | r_fuzzy | 0.17% | 0.75% | 25 | 29 |
| gpt-oss-20b | longbench_v2 | spec_casc_tok | 2.86% | 0.75% | 43 | 29 |
| qwen3-8b | gsm8k | mentored_dec | 0.12% | 0.15% | 20 | 19 |
| qwen3-8b | gsm8k | cactus | 0.18% | 0.15% | 20 | 19 |
| qwen3-8b | gsm8k | spec_casc_opt | 0.93% | 0.15% | 34 | 19 |
| qwen3-8b | gsm8k | r_fuzzy | 0.04% | 0.15% | 16 | 19 |
| qwen3-8b | gsm8k | spec_casc_tok | 0.17% | 0.15% | 20 | 19 |
| qwen3-8b | aime24 | mentored_dec | 0.39% | 0.42% | 52 | 53 |
| qwen3-8b | aime24 | cactus | 1.39% | 0.42% | 56 | 53 |
| qwen3-8b | aime24 | spec_casc_opt | 15.11% | 0.42% | 2728 | 53 |
| qwen3-8b | aime24 | r_fuzzy | 0.00% | 0.42% | 30 | 53 |
| qwen3-8b | aime24 | spec_casc_tok | 0.62% | 0.42% | 62 | 53 |
| qwen3-8b | humaneval | mentored_dec | 8.38% | 8.17% | 159 | 206 |
| qwen3-8b | humaneval | cactus | 6.71% | 8.17% | 125 | 206 |
| qwen3-8b | humaneval | spec_casc_opt | 12.09% | 8.17% | 661 | 206 |
| qwen3-8b | humaneval | r_fuzzy | 1.84% | 8.17% | 58 | 206 |
| qwen3-8b | humaneval | spec_casc_tok | 8.53% | 8.17% | 159 | 206 |
| qwen3-8b | livecodebench | mentored_dec | 1.12% | 1.00% | 57 | 60 |
| qwen3-8b | livecodebench | cactus | 0.42% | 1.00% | 35 | 60 |
| qwen3-8b | livecodebench | spec_casc_opt | 4.05% | 1.00% | 327 | 60 |
| qwen3-8b | livecodebench | r_fuzzy | 0.01% | 1.00% | 26 | 60 |
| qwen3-8b | livecodebench | spec_casc_tok | 1.19% | 1.00% | 66 | 60 |
| qwen3-8b | mtbench | mentored_dec | 0.48% | 0.44% | 27 | 23 |
| qwen3-8b | mtbench | cactus | 0.75% | 0.44% | 38 | 23 |
| qwen3-8b | mtbench | spec_casc_opt | 0.84% | 0.44% | 30 | 23 |
| qwen3-8b | mtbench | r_fuzzy | 0.04% | 0.44% | 16 | 23 |
| qwen3-8b | mtbench | spec_casc_tok | 1.30% | 0.44% | 38 | 23 |
| qwen3-8b | longbench_v2 | mentored_dec | 1.89% | 1.30% | 35 | 33 |
| qwen3-8b | longbench_v2 | cactus | 2.69% | 1.30% | 70 | 33 |
| qwen3-8b | longbench_v2 | spec_casc_opt | 13.14% | 1.30% | 337 | 33 |
| qwen3-8b | longbench_v2 | r_fuzzy | 0.45% | 1.30% | 21 | 33 |
| qwen3-8b | longbench_v2 | spec_casc_tok | 1.92% | 1.30% | 34 | 33 |

**Time per round** (`campaign/addendum/analysis/time_per_round.csv`, `campaign/addendum/analysis/time_per_round_regression.csv`, `campaign/addendum/analysis/time_per_round_spearman.csv`): OLS of time per round on output tokens (dataset = all):

- gpt-oss-20b, strict runs (n=650): slope -4.57e-06 s/token, intercept 77.5 ms, R^2 0.015
- gpt-oss-20b, all runs (n=9373): slope -3.42e-06 s/token, intercept 82.8 ms, R^2 0.013
- qwen3-8b, strict runs (n=650): slope -6.54e-08 s/token, intercept 20.4 ms, R^2 0.017
- qwen3-8b, all runs (n=8716): slope -2.54e-08 s/token, intercept 20.9 ms, R^2 0.002
- Spearman(lambda, time-per-round ratio) over 60 cells: rho = 0.579, two-sided permutation p = 0 (20,000 shuffles)

**What the relaxed rules admit** (`campaign/addendum/analysis/admitted_tokens.csv`, GPT-OSS traced runs, loosest alpha): tokens accepted only because of the relaxation vs tokens both rules accept.

| method | class | tokens | target p median | target p mean | target rank mean | rank p90 | target entropy mean |
|---|---|---:|---:|---:|---:|---:|---:|
| mentored_dec | both | 188106 | 0.928 | 0.714 | 8.5 | 2 | 0.79 |
| mentored_dec | lossy_only | 35908 | 0.092 | 0.182 | 37.4 | 25 | 1.77 |
| cactus | both | 199770 | 0.785 | 0.629 | 17.8 | 5 | 1.14 |
| cactus | lossy_only | 63971 | 0.011 | 0.106 | 233.7 | 256 | 2.11 |
| spec_casc_opt | both | 297657 | 0.924 | 0.721 | 5.8 | 2 | 0.77 |
| spec_casc_opt | lossy_only | 55208 | 0.073 | 0.190 | 88.3 | 63 | 1.75 |
| r_fuzzy | both | 236305 | 0.832 | 0.655 | 11.0 | 3 | 1.00 |
| r_fuzzy | lossy_only | 62404 | 0.015 | 0.128 | 133.5 | 127 | 1.76 |
| spec_casc_tok | both | 160313 | 0.987 | 0.806 | 2.1 | 1 | 0.53 |
| spec_casc_tok | lossy_only | 13089 | 0.287 | 0.349 | 0.9 | 2 | 1.54 |

**MT-Bench judge (step 1.9)** (`campaign/addendum/analysis/mtbench_judge_summary.csv`, seed-0 rows at the loosest alpha; per run: `campaign/addendum/analysis/mtbench_judge.csv`): FastChat single-answer grading of turn 1 (`single-math-v1` with the GPT-4 reference answer for math/reasoning/coding, `single-v1` otherwise), judge claude-fable-5-1 at effort medium through the Message Batches API; a run whose output never reaches an answer scores 1 without a call. Mean score out of 10 with a 95% bootstrap interval; 'answered only' leaves the no-answer runs out.

| target | method | alpha | mean score [95% CI] | answered only | no answer | refusals |
|---|---|---:|---|---:|---:|---:|
| gpt-oss-20b | strict | strict | 7.29 [6.75, 7.80] | 7.29 | 0 | 0 |
| gpt-oss-20b | mentored_dec | 0.75 | 6.41 [5.72, 7.09] | 6.48 | 1 | 0 |
| gpt-oss-20b | cactus | 0.35 | 4.51 [3.70, 5.34] | 4.80 | 6 | 0 |
| gpt-oss-20b | spec_casc_opt | 0.05 | 5.74 [5.04, 6.45] | 5.86 | 2 | 0 |
| gpt-oss-20b | r_fuzzy | 0.25 | 4.58 [3.94, 5.22] | 4.71 | 3 | 0 |
| gpt-oss-20b | spec_casc_tok | 0.8 | 7.49 [6.96, 7.99] | 7.49 | 0 | 0 |
| qwen3-8b | strict | strict | 6.94 [6.31, 7.55] | 7.79 | 10 | 0 |
| qwen3-8b | mentored_dec | 0.75 | 6.40 [5.70, 7.06] | 7.45 | 13 | 0 |
| qwen3-8b | cactus | 0.35 | 2.99 [2.40, 3.64] | 3.74 | 22 | 0 |
| qwen3-8b | spec_casc_opt | 0.05 | 3.95 [3.42, 4.49] | 5.07 | 22 | 0 |
| qwen3-8b | r_fuzzy | 0.25 | 3.05 [2.61, 3.51] | 3.73 | 20 | 0 |
| qwen3-8b | spec_casc_tok | 0.8 | 7.21 [6.59, 7.80] | 8.00 | 9 | 0 |

## Step 2: seeds on the relaxed arms

Source: `campaign/addendum/seeds/summary.csv` (per-seed tables `campaign/addendum/seeds/<dataset>__seed<k>.csv`). Seed 0 is the campaign's run (old box, H100 PCIe); seeds 1-2 ran on Nibi (H100 SXM), except Qwen3 aime24's (Killarney H100, step 2.2; README deviation 12). Ratios pair each seed's relaxed arm with strict of the same seed; '-' = that seed is not complete yet.

| target | dataset | method | alpha | lambda s0 | lambda s1 | lambda s2 | lambda s3 | lambda s4 | lambda sd | lambda mean (sd) | time ratio s0 | time ratio s1 | time ratio s2 | time ratio s3 | time ratio s4 | time ratio sd | time mean (sd) | acc s0 | acc s1 | acc s2 | acc s3 | acc s4 | acc sd |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gpt-oss-20b | gsm8k | mentored_dec | 0.75 | 1.16 | 1.09 | 1.22 | - | - | 0.07 | 1.16 (0.07) | 0.96 | 0.78 | 0.88 | - | - | 0.09 | 0.87 (0.09) | 93% | 95% | 95% | - | - | 1% |
| gpt-oss-20b | gsm8k | cactus | 0.35 | 1.61 | 1.51 | 1.70 | - | - | 0.10 | 1.61 (0.10) | 1.19 | 0.94 | 1.07 | - | - | 0.12 | 1.06 (0.12) | 91% | 93% | 90% | - | - | 1% |
| gpt-oss-20b | gsm8k | spec_casc_opt | 0.05 | 1.46 | 1.26 | 1.44 | - | - | 0.11 | 1.39 (0.11) | 1.18 | 0.92 | 1.07 | - | - | 0.13 | 1.06 (0.13) | 94% | 93% | 93% | - | - | 1% |
| gpt-oss-20b | gsm8k | r_fuzzy | 0.25 | 1.70 | 1.57 | 1.74 | - | - | 0.09 | 1.67 (0.09) | 1.29 | 1.02 | 1.17 | - | - | 0.14 | 1.16 (0.14) | 87% | 89% | 89% | - | - | 1% |
| gpt-oss-20b | gsm8k | spec_casc_tok | 0.8 | 0.96 | 0.93 | 1.03 | - | - | 0.05 | 0.97 (0.05) | 0.91 | 0.81 | 0.91 | - | - | 0.06 | 0.87 (0.06) | 97% | 98% | 96% | - | - | 1% |
| gpt-oss-20b | aime24 | mentored_dec | 0.75 | 1.69 | 1.28 | 1.45 | 1.54 | 2.15 | 0.33 | 1.62 (0.33) | 1.36 | 0.93 | 1.02 | 1.09 | 1.51 | 0.25 | 1.18 (0.25) | 63% | 70% | 67% | 77% | 63% | 6% |
| gpt-oss-20b | aime24 | cactus | 0.18 | 1.78 | 1.54 | 1.62 | 1.86 | 1.85 | 0.15 | 1.73 (0.15) | 1.33 | 0.95 | 0.97 | 1.15 | 1.11 | 0.15 | 1.10 (0.15) | 60% | 50% | 43% | 50% | 53% | 6% |
| gpt-oss-20b | aime24 | spec_casc_opt | 0.05 | 2.48 | 2.03 | 2.31 | 2.43 | 2.53 | 0.20 | 2.36 (0.20) | 2.01 | 1.44 | 1.61 | 1.71 | 1.68 | 0.21 | 1.69 (0.21) | 37% | 33% | 43% | 43% | 40% | 4% |
| gpt-oss-20b | aime24 | r_fuzzy | 0.25 | 2.13 | 1.73 | 2.17 | 2.37 | 2.55 | 0.31 | 2.19 (0.31) | 1.64 | 1.16 | 1.41 | 1.58 | 1.65 | 0.21 | 1.49 (0.21) | 50% | 43% | 53% | 50% | 43% | 4% |
| gpt-oss-20b | aime24 | spec_casc_tok | 0.8 | 1.48 | 0.96 | 1.12 | 1.52 | 1.60 | 0.28 | 1.34 (0.28) | 1.33 | 0.81 | 0.93 | 1.31 | 1.34 | 0.25 | 1.14 (0.25) | 70% | 73% | 67% | 60% | 73% | 6% |
| gpt-oss-20b | humaneval | mentored_dec | 0.75 | 1.30 | 1.27 | 1.17 | - | - | 0.07 | 1.24 (0.07) | 1.09 | 0.95 | 0.84 | - | - | 0.12 | 0.96 (0.12) | 96% | 95% | 95% | - | - | 0% |
| gpt-oss-20b | humaneval | cactus | 0.35 | 1.79 | 1.62 | 1.62 | - | - | 0.10 | 1.68 (0.10) | 1.35 | 1.03 | 1.00 | - | - | 0.19 | 1.13 (0.19) | 87% | 93% | 90% | - | - | 3% |
| gpt-oss-20b | humaneval | spec_casc_opt | 0.05 | 1.73 | 1.91 | 1.58 | - | - | 0.16 | 1.74 (0.16) | 1.43 | 1.43 | 1.16 | - | - | 0.15 | 1.34 (0.15) | 82% | 83% | 78% | - | - | 3% |
| gpt-oss-20b | humaneval | r_fuzzy | 0.25 | 1.64 | 1.79 | 1.63 | - | - | 0.09 | 1.69 (0.09) | 1.32 | 1.27 | 1.14 | - | - | 0.09 | 1.24 (0.09) | 63% | 61% | 64% | - | - | 1% |
| gpt-oss-20b | humaneval | spec_casc_tok | 0.8 | 1.05 | 1.17 | 0.99 | - | - | 0.09 | 1.07 (0.09) | 0.98 | 1.06 | 0.88 | - | - | 0.09 | 0.97 (0.09) | 94% | 96% | 97% | - | - | 1% |
| gpt-oss-20b | livecodebench | mentored_dec | 0.75 | 1.25 | 1.33 | 1.37 | - | - | 0.06 | 1.31 (0.06) | 1.01 | 0.94 | 0.98 | - | - | 0.03 | 0.98 (0.03) | 84% | 80% | 88% | - | - | 4% |
| gpt-oss-20b | livecodebench | cactus | 0.18 | 1.54 | 1.76 | 1.67 | - | - | 0.11 | 1.66 (0.11) | 1.14 | 1.08 | 1.03 | - | - | 0.06 | 1.09 (0.06) | 61% | 66% | 63% | - | - | 2% |
| gpt-oss-20b | livecodebench | spec_casc_opt | 0.05 | 1.64 | 1.67 | 1.75 | - | - | 0.06 | 1.69 (0.06) | 1.32 | 1.20 | 1.25 | - | - | 0.06 | 1.26 (0.06) | 49% | 52% | 48% | - | - | 2% |
| gpt-oss-20b | livecodebench | r_fuzzy | 0.25 | 1.65 | 1.69 | 1.71 | - | - | 0.03 | 1.68 (0.03) | 1.27 | 1.15 | 1.14 | - | - | 0.08 | 1.19 (0.08) | 34% | 32% | 33% | - | - | 1% |
| gpt-oss-20b | livecodebench | spec_casc_tok | 0.8 | 1.16 | 1.20 | 1.19 | - | - | 0.02 | 1.18 (0.02) | 1.04 | 1.04 | 1.01 | - | - | 0.02 | 1.03 (0.02) | 88% | 90% | 89% | - | - | 1% |
| gpt-oss-20b | mtbench | mentored_dec | 0.75 | 1.10 | 1.14 | 1.19 | - | - | 0.05 | 1.14 (0.05) | 0.87 | 0.78 | 0.79 | - | - | 0.05 | 0.82 (0.05) | - | - | - | - | - | - |
| gpt-oss-20b | mtbench | cactus | 0.35 | 1.18 | 1.31 | 1.31 | - | - | 0.07 | 1.27 (0.07) | 0.82 | 0.69 | 0.67 | - | - | 0.08 | 0.73 (0.08) | - | - | - | - | - | - |
| gpt-oss-20b | mtbench | spec_casc_opt | 0.05 | 1.09 | 1.21 | 1.25 | - | - | 0.08 | 1.18 (0.08) | 0.87 | 0.85 | 0.87 | - | - | 0.01 | 0.86 (0.01) | - | - | - | - | - | - |
| gpt-oss-20b | mtbench | r_fuzzy | 0.25 | 1.20 | 1.28 | 1.26 | - | - | 0.04 | 1.25 (0.04) | 0.92 | 0.81 | 0.79 | - | - | 0.07 | 0.84 (0.07) | - | - | - | - | - | - |
| gpt-oss-20b | mtbench | spec_casc_tok | 0.8 | 0.96 | 1.02 | 1.06 | - | - | 0.05 | 1.01 (0.05) | 0.90 | 0.93 | 0.94 | - | - | 0.02 | 0.92 (0.02) | - | - | - | - | - | - |
| gpt-oss-20b | longbench_v2 | mentored_dec | 0.75 | 1.59 | 1.55 | 1.45 | - | - | 0.07 | 1.53 (0.07) | 1.04 | 1.05 | 1.02 | - | - | 0.02 | 1.04 (0.02) | 51% | 52% | 53% | - | - | 1% |
| gpt-oss-20b | longbench_v2 | spec_casc_opt | 0.05 | 1.79 | 1.85 | 1.72 | - | - | 0.06 | 1.79 (0.06) | 1.07 | 1.29 | 1.24 | - | - | 0.12 | 1.20 (0.12) | 47% | 45% | 51% | - | - | 3% |
| gpt-oss-20b | longbench_v2 | r_fuzzy | 0.25 | 1.69 | 1.62 | 1.62 | - | - | 0.04 | 1.65 (0.04) | 1.05 | 1.03 | 1.05 | - | - | 0.01 | 1.04 (0.01) | 40% | 42% | 51% | - | - | 6% |
| qwen3-8b | gsm8k | mentored_dec | 0.75 | 1.03 | 1.00 | 1.02 | - | - | 0.01 | 1.01 (0.01) | 0.95 | 0.91 | 0.93 | - | - | 0.02 | 0.93 (0.02) | 77% | 81% | 81% | - | - | 2% |
| qwen3-8b | gsm8k | cactus | 0.35 | 1.04 | 1.05 | 1.06 | - | - | 0.01 | 1.05 (0.01) | 0.94 | 0.93 | 0.91 | - | - | 0.01 | 0.92 (0.01) | 77% | 73% | 75% | - | - | 2% |
| qwen3-8b | gsm8k | spec_casc_opt | 0.05 | 1.33 | 1.29 | 1.32 | - | - | 0.02 | 1.31 (0.02) | 1.12 | 1.05 | 1.06 | - | - | 0.04 | 1.08 (0.04) | 49% | 49% | 49% | - | - | 0% |
| qwen3-8b | gsm8k | r_fuzzy | 0.25 | 0.95 | 1.01 | 1.06 | - | - | 0.05 | 1.01 (0.05) | 0.81 | 0.81 | 0.85 | - | - | 0.02 | 0.82 (0.02) | 55% | 57% | 62% | - | - | 3% |
| qwen3-8b | gsm8k | spec_casc_tok | 0.8 | 0.99 | 1.00 | 1.01 | - | - | 0.01 | 1.00 (0.01) | 0.96 | 0.97 | 0.97 | - | - | 0.01 | 0.97 (0.01) | 79% | 82% | 77% | - | - | 3% |
| qwen3-8b | aime24 | spec_casc_opt | 0.05 | 1.42 | 1.40 | 1.50 | 1.56 | 1.40 | 0.07 | 1.46 (0.07) | 1.14 | 1.08 | 1.22 | 1.35 | 0.97 | 0.15 | 1.15 (0.15) | 30% | 37% | 30% | 30% | 33% | 3% |
| qwen3-8b | aime24 | r_fuzzy | 0.25 | 1.29 | 1.36 | 1.23 | 1.44 | 1.17 | 0.11 | 1.30 (0.11) | 1.18 | 1.26 | 1.23 | 1.41 | 1.08 | 0.12 | 1.23 (0.12) | 40% | 33% | 40% | 37% | 27% | 6% |
| qwen3-8b | humaneval | mentored_dec | 0.75 | 1.08 | 1.05 | 1.08 | - | - | 0.02 | 1.07 (0.02) | 1.02 | 0.97 | 0.99 | - | - | 0.02 | 0.99 (0.02) | 85% | 79% | 81% | - | - | 3% |
| qwen3-8b | humaneval | cactus | 0.35 | 1.14 | 1.09 | 1.08 | - | - | 0.03 | 1.11 (0.03) | 1.01 | 0.90 | 0.90 | - | - | 0.06 | 0.94 (0.06) | 75% | 79% | 77% | - | - | 2% |
| qwen3-8b | humaneval | spec_casc_opt | 0.05 | 1.72 | 1.60 | 1.67 | - | - | 0.06 | 1.66 (0.06) | 1.46 | 1.30 | 1.33 | - | - | 0.08 | 1.36 (0.08) | 49% | 48% | 51% | - | - | 1% |
| qwen3-8b | humaneval | r_fuzzy | 0.25 | 1.65 | 1.52 | 1.46 | - | - | 0.10 | 1.54 (0.10) | 1.41 | 1.22 | 1.19 | - | - | 0.12 | 1.27 (0.12) | 16% | 13% | 12% | - | - | 2% |
| qwen3-8b | humaneval | spec_casc_tok | 0.8 | 1.08 | 1.03 | 1.01 | - | - | 0.03 | 1.04 (0.03) | 1.05 | 1.01 | 0.97 | - | - | 0.04 | 1.01 (0.04) | 85% | 83% | 88% | - | - | 3% |
| qwen3-8b | livecodebench | mentored_dec | 0.75 | 1.05 | 1.05 | 1.06 | - | - | 0.01 | 1.05 (0.01) | 0.95 | 0.95 | 0.96 | - | - | 0.01 | 0.95 (0.01) | 63% | 62% | 64% | - | - | 1% |
| qwen3-8b | livecodebench | cactus | 0.35 | 1.15 | 1.11 | 1.15 | - | - | 0.02 | 1.14 (0.02) | 0.82 | 0.68 | 0.69 | - | - | 0.08 | 0.73 (0.08) | 44% | 37% | 46% | - | - | 5% |
| qwen3-8b | livecodebench | spec_casc_opt | 0.05 | 1.27 | 1.22 | 1.25 | - | - | 0.03 | 1.24 (0.03) | 1.09 | 1.01 | 1.06 | - | - | 0.04 | 1.05 (0.04) | 33% | 30% | 32% | - | - | 2% |
| qwen3-8b | livecodebench | r_fuzzy | 0.25 | 1.07 | 0.97 | 0.96 | - | - | 0.06 | 1.00 (0.06) | 0.92 | 0.81 | 0.81 | - | - | 0.07 | 0.85 (0.07) | 2% | 0% | 2% | - | - | 1% |
| qwen3-8b | livecodebench | spec_casc_tok | 0.8 | 1.00 | 1.02 | 1.02 | - | - | 0.01 | 1.01 (0.01) | 0.96 | 0.97 | 0.98 | - | - | 0.01 | 0.97 (0.01) | 71% | 72% | 66% | - | - | 4% |
| qwen3-8b | mtbench | mentored_dec | 0.75 | 1.04 | 1.04 | 1.01 | - | - | 0.02 | 1.03 (0.02) | 0.93 | 0.86 | 0.87 | - | - | 0.04 | 0.89 (0.04) | - | - | - | - | - | - |
| qwen3-8b | mtbench | cactus | 0.35 | 1.16 | 1.16 | 1.19 | - | - | 0.02 | 1.17 (0.02) | 0.75 | 0.62 | 0.64 | - | - | 0.07 | 0.67 (0.07) | - | - | - | - | - | - |
| qwen3-8b | mtbench | spec_casc_opt | 0.05 | 1.22 | 1.16 | 1.14 | - | - | 0.04 | 1.18 (0.04) | 1.01 | 0.89 | 0.87 | - | - | 0.08 | 0.92 (0.08) | - | - | - | - | - | - |
| qwen3-8b | mtbench | r_fuzzy | 0.25 | 1.12 | 1.10 | 0.99 | - | - | 0.07 | 1.07 (0.07) | 0.92 | 0.83 | 0.76 | - | - | 0.08 | 0.83 (0.08) | - | - | - | - | - | - |
| qwen3-8b | mtbench | spec_casc_tok | 0.8 | 1.04 | 1.02 | 0.94 | - | - | 0.05 | 1.00 (0.05) | 0.99 | 0.96 | 0.87 | - | - | 0.06 | 0.94 (0.06) | - | - | - | - | - | - |

## Hardware dependence of the time ratios (found in step 2)

`campaign/addendum/analysis/seed_shift.csv`: GPT-OSS cells with seeds 0-2 complete. Seed 0 = the campaign's run on the old box (H100 PCIe); seeds 1-2 = Nibi (H100 SXM).

| metric | cells | mean seed 0 | mean seed 1 | mean seed 2 | mean s1-s0 | mean s2-s1 | cells s1 < s0 | win/loss flips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lambda | 28 | 1.493 | 1.438 | 1.477 | -0.055 | 0.039 | 14 | - |
| rounds_ratio | 28 | 1.044 | 1.008 | 1.033 | -0.036 | 0.025 | 14 | 8 |
| time_ratio | 28 | 1.168 | 1.012 | 1.031 | -0.156 | 0.018 | 23 | 8 |
| tpr_ratio | 28 | 1.118 | 1.005 | 1.002 | -0.113 | -0.003 | 27 | - |

`campaign/addendum/analysis/hardware_tpr_model.csv`: time per round = c0 + c1 x tokens per round (per-run OLS, strict + loosest arms):

| machine | dataset | runs | c0 (ms) | c1 (ms/token) | c1/c0 | R^2 |
|---|---|---:|---:|---:|---:|---:|
| old box (H100 PCIe), seed 0 | gsm8k | 900 | 24.45 | 1.74 | 0.071 | 0.04 |
| old box (H100 PCIe), seed 0 | humaneval | 900 | 14.11 | 3.04 | 0.215 | 0.45 |
| old box (H100 PCIe), seed 0 | mtbench | 480 | 11.87 | 3.24 | 0.273 | 0.39 |
| old box (H100 PCIe), seed 0 | livecodebench | 540 | 13.55 | 2.89 | 0.213 | 0.42 |
| old box (H100 PCIe), seed 0 | aime24 | 180 | 13.32 | 2.54 | 0.190 | 0.87 |
| old box (H100 PCIe), seed 0 | longbench_v2 | 900 | 276.52 | -12.49 | -0.045 | 0.00 |
| Nibi (H100 SXM), seeds 1-2 | gsm8k | 1800 | 7.57 | 0.07 | 0.009 | 0.00 |
| Nibi (H100 SXM), seeds 1-2 | humaneval | 1800 | 7.44 | 0.02 | 0.003 | 0.00 |
| Nibi (H100 SXM), seeds 1-2 | mtbench | 960 | 7.08 | 0.08 | 0.012 | 0.13 |
| Nibi (H100 SXM), seeds 1-2 | livecodebench | 1080 | 7.37 | 0.02 | 0.002 | 0.01 |
| Nibi (H100 SXM), seeds 1-2 | aime24 | 360 | 7.19 | 0.05 | 0.007 | 0.04 |
| Nibi (H100 SXM), seeds 1-2 | longbench_v2 | 1200 | 11.46 | -0.55 | -0.048 | 0.05 |

## Step 3: lossless draft-length sweep (strict, seed 0)

`campaign/addendum/tables/nspec__gsm8k.csv`:

| n_draft | source | n_cases | mean_l_bar | mean_l_bar_ci_lo | mean_l_bar_ci_hi | mean_completion_tokens | mean_completion_tokens_ci_lo | mean_completion_tokens_ci_hi | mean_verifier_rounds | mean_verifier_rounds_ci_lo | mean_verifier_rounds_ci_hi | mean_wall_time_s | mean_wall_time_s_ci_lo | mean_wall_time_s_ci_hi | accuracy | accuracy_ci_lo | accuracy_ci_hi | capout_rate | nodes | n_pairs_vs_nibiref | lambda_vs_nibiref | rounds_ratio_vs_nibiref | time_ratio_vs_nibiref | time_per_round_ratio_vs_nibiref | same_node_vs_nibiref | same_node_pairs_vs_nibiref | time_ratio_same_node_vs_nibiref | lambda_vs_nibiref_ci_lo | lambda_vs_nibiref_ci_hi | rounds_ratio_vs_nibiref_ci_lo | rounds_ratio_vs_nibiref_ci_hi | time_ratio_vs_nibiref_ci_lo | time_ratio_vs_nibiref_ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2.000 | nspec2 (Nibi) | 150.000 | 1.427 | 1.410 | 1.444 | 308.413 | 264.260 | 357.495 | 129.100 | 110.100 | 150.088 | 0.666 | 0.571 | 0.774 | 0.973 | 0.947 | 0.993 | 0.013 | g18.nibi.sharcnet | 150.000 | 0.959 | 1.387 | 0.928 | 0.669 | True | 150.000 | 0.928 | 0.852 | 1.075 | 1.233 | 1.555 | 0.828 | 1.036 |
| 3.000 | nspec3 (Nibi) | 150.000 | 1.876 | 1.846 | 1.906 | 323.420 | 265.127 | 389.107 | 115.133 | 94.059 | 138.894 | 0.662 | 0.546 | 0.793 | 0.960 | 0.927 | 0.987 | 0.033 | g18.nibi.sharcnet | 150.000 | 1.006 | 1.237 | 0.923 | 0.746 | True | 150.000 | 0.923 | 0.899 | 1.113 | 1.094 | 1.381 | 0.820 | 1.028 |
| 4.000 | nspec4 (Nibi) | 150.000 | 2.195 | 2.153 | 2.237 | 312.920 | 264.220 | 367.280 | 101.300 | 84.466 | 119.633 | 0.654 | 0.550 | 0.772 | 0.967 | 0.933 | 0.993 | 0.013 | g18.nibi.sharcnet | 150.000 | 0.973 | 1.088 | 0.911 | 0.837 | True | 150.000 | 0.911 | 0.852 | 1.109 | 0.951 | 1.248 | 0.804 | 1.040 |
| 6.000 | campaign seed 0 (old box, H100 PCIe) | 150.000 | 2.567 | 2.502 | 2.631 | 322.187 | 270.218 | 380.896 | 94.020 | 77.873 | 112.361 | 2.418 | 2.073 | 2.827 | 0.960 | 0.927 | 0.987 | 0.020 | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| 6.000 | nibiref (Nibi, campaign settings) | 150.000 | 2.582 | 2.518 | 2.647 | 321.627 | 267.113 | 383.728 | 93.087 | 76.847 | 111.714 | 0.718 | 0.598 | 0.854 | 0.967 | 0.933 | 0.993 | 0.013 | g18.nibi.sharcnet | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| 8.000 | nspec8 (Nibi) | 150.000 | 2.772 | 2.699 | 2.846 | 314.493 | 265.833 | 368.707 | 87.180 | 73.193 | 103.427 | 0.760 | 0.641 | 0.894 | 0.960 | 0.927 | 0.987 | 0.013 | g18.nibi.sharcnet | 150.000 | 0.978 | 0.937 | 1.059 | 1.131 | True | 150.000 | 1.059 | 0.848 | 1.127 | 0.809 | 1.089 | 0.921 | 1.227 |
| 10.000 | nspec10 (Nibi) | 150.000 | 2.878 | 2.801 | 2.957 | 333.907 | 277.693 | 397.048 | 90.020 | 74.246 | 108.460 | 0.873 | 0.721 | 1.049 | 0.953 | 0.920 | 0.987 | 0.027 | g18.nibi.sharcnet | 150.000 | 1.038 | 0.967 | 1.217 | 1.259 | True | 150.000 | 1.217 | 0.945 | 1.151 | 0.875 | 1.081 | 1.104 | 1.360 |

`campaign/addendum/tables/nspec__gsm8k_qwen3.csv`:

| n_draft | source | n_cases | mean_l_bar | mean_l_bar_ci_lo | mean_l_bar_ci_hi | mean_completion_tokens | mean_completion_tokens_ci_lo | mean_completion_tokens_ci_hi | mean_verifier_rounds | mean_verifier_rounds_ci_lo | mean_verifier_rounds_ci_hi | mean_wall_time_s | mean_wall_time_s_ci_lo | mean_wall_time_s_ci_hi | accuracy | accuracy_ci_lo | accuracy_ci_hi | capout_rate | nodes | n_pairs_vs_nibiref | lambda_vs_nibiref | rounds_ratio_vs_nibiref | time_ratio_vs_nibiref | time_per_round_ratio_vs_nibiref | same_node_vs_nibiref | same_node_pairs_vs_nibiref | time_ratio_same_node_vs_nibiref | lambda_vs_nibiref_ci_lo | lambda_vs_nibiref_ci_hi | rounds_ratio_vs_nibiref_ci_lo | rounds_ratio_vs_nibiref_ci_hi | time_ratio_vs_nibiref_ci_lo | time_ratio_vs_nibiref_ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2.000 | nspec2 (Nibi) | 150.000 | 1.107 | 1.094 | 1.119 | 1302.510 | 1212.010 | 1395.280 | 617.620 | 574.753 | 661.754 | 4.643 | 4.325 | 4.974 | 0.807 | 0.740 | 0.867 | 0.233 | kn176 | 150.000 | 1.018 | 1.212 | 1.005 | 0.829 | True | 150.000 | 1.005 | 0.983 | 1.055 | 1.168 | 1.256 | 0.969 | 1.042 |
| 3.000 | nspec3 (Nibi) | 150.000 | 1.315 | 1.297 | 1.332 | 1302.450 | 1211.890 | 1392.490 | 561.493 | 522.327 | 600.321 | 4.494 | 4.189 | 4.801 | 0.793 | 0.727 | 0.853 | 0.240 | kn176 | 150.000 | 1.018 | 1.102 | 0.973 | 0.883 | True | 150.000 | 0.973 | 0.984 | 1.054 | 1.064 | 1.141 | 0.939 | 1.008 |
| 4.000 | nspec4 (Nibi) | 150.000 | 1.421 | 1.398 | 1.443 | 1303.880 | 1208.090 | 1399.860 | 537.293 | 497.853 | 576.442 | 4.497 | 4.170 | 4.817 | 0.733 | 0.660 | 0.800 | 0.287 | kn176 | 150.000 | 1.019 | 1.054 | 0.973 | 0.923 | True | 150.000 | 0.973 | 0.989 | 1.051 | 1.021 | 1.087 | 0.943 | 1.004 |
| 6.000 | campaign seed 0 (old box, H100 PCIe) | 150.000 | 1.514 | 1.488 | 1.542 | 1291.930 | 1202.410 | 1382.250 | 510.080 | 475.492 | 545.520 | 10.299 | 9.568 | 11.019 | 0.800 | 0.733 | 0.860 | 0.247 | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| 6.000 | nibiref (Nibi, campaign settings) | 150.000 | 1.499 | 1.472 | 1.525 | 1279.450 | 1190.020 | 1371.280 | 509.680 | 474.633 | 544.294 | 4.620 | 4.298 | 4.937 | 0.800 | 0.733 | 0.860 | 0.227 | kn176 | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| 8.000 | nspec8 (Nibi) | 150.000 | 1.527 | 1.498 | 1.556 | 1305.920 | 1213.170 | 1398.570 | 514.360 | 478.960 | 549.720 | 4.995 | 4.647 | 5.341 | 0.793 | 0.727 | 0.853 | 0.233 | kn176 | 150.000 | 1.021 | 1.009 | 1.081 | 1.071 | True | 150.000 | 1.081 | 0.998 | 1.044 | 0.986 | 1.033 | 1.057 | 1.106 |
| 10.000 | nspec10 (Nibi) | 150.000 | 1.527 | 1.499 | 1.556 | 1314.410 | 1220.900 | 1405.490 | 517.507 | 481.393 | 553.047 | 5.347 | 4.980 | 5.712 | 0.767 | 0.700 | 0.833 | 0.267 | kn172 | 150.000 | 1.027 | 1.015 | 1.157 | 1.140 | False | 0.000 | - | 1.005 | 1.051 | 0.993 | 1.039 | 1.132 | 1.184 |

`campaign/addendum/tables/nspec__livecodebench.csv`:

| n_draft | source | n_cases | mean_l_bar | mean_l_bar_ci_lo | mean_l_bar_ci_hi | mean_completion_tokens | mean_completion_tokens_ci_lo | mean_completion_tokens_ci_hi | mean_verifier_rounds | mean_verifier_rounds_ci_lo | mean_verifier_rounds_ci_hi | mean_wall_time_s | mean_wall_time_s_ci_lo | mean_wall_time_s_ci_hi | accuracy | accuracy_ci_lo | accuracy_ci_hi | capout_rate | nodes | n_pairs_vs_nibiref | lambda_vs_nibiref | rounds_ratio_vs_nibiref | time_ratio_vs_nibiref | time_per_round_ratio_vs_nibiref | same_node_vs_nibiref | same_node_pairs_vs_nibiref | time_ratio_same_node_vs_nibiref | lambda_vs_nibiref_ci_lo | lambda_vs_nibiref_ci_hi | rounds_ratio_vs_nibiref_ci_lo | rounds_ratio_vs_nibiref_ci_hi | time_ratio_vs_nibiref_ci_lo | time_ratio_vs_nibiref_ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2.000 | nspec2 (Nibi) | 90.000 | 1.287 | 1.270 | 1.305 | 3406.870 | 2920.230 | 3946.010 | 1518.030 | 1284.390 | 1772.350 | 7.601 | 6.440 | 8.878 | 0.878 | 0.800 | 0.933 | 0.044 | g18.nibi.sharcnet | 90.000 | 1.004 | 1.355 | 0.912 | 0.673 | True | 90.000 | 0.912 | 0.917 | 1.092 | 1.221 | 1.493 | 0.822 | 1.005 |
| 3.000 | nspec3 (Nibi) | 90.000 | 1.660 | 1.631 | 1.689 | 3603.570 | 3065.950 | 4199.910 | 1395.490 | 1169.430 | 1645.070 | 7.811 | 6.564 | 9.223 | 0.922 | 0.867 | 0.967 | 0.044 | g18.nibi.sharcnet | 90.000 | 1.062 | 1.246 | 0.937 | 0.752 | True | 90.000 | 0.937 | 0.967 | 1.166 | 1.126 | 1.383 | 0.847 | 1.040 |
| 4.000 | nspec4 (Nibi) | 90.000 | 1.914 | 1.871 | 1.958 | 3540.600 | 2986.660 | 4146.470 | 1270.980 | 1054.640 | 1517.850 | 7.937 | 6.590 | 9.446 | 0.911 | 0.844 | 0.967 | 0.022 | g18.nibi.sharcnet | 90.000 | 1.043 | 1.135 | 0.952 | 0.839 | True | 90.000 | 0.952 | 0.937 | 1.160 | 1.013 | 1.273 | 0.849 | 1.067 |
| 6.000 | campaign seed 0 (old box, H100 PCIe) | 90.000 | 2.164 | 2.106 | 2.223 | 3456.240 | 2927.040 | 4051.130 | 1150.830 | 953.895 | 1361.050 | 25.190 | 21.146 | 29.554 | 0.889 | 0.822 | 0.944 | 0.022 | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| 6.000 | nibiref (Nibi, campaign settings) | 90.000 | 2.213 | 2.154 | 2.273 | 3394.530 | 2880.390 | 3975.960 | 1120.230 | 925.770 | 1335.800 | 8.333 | 6.901 | 9.964 | 0.911 | 0.844 | 0.967 | 0.044 | g18.nibi.sharcnet | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| 8.000 | nspec8 (Nibi) | 90.000 | 2.330 | 2.259 | 2.402 | 3460.600 | 2932.080 | 4053.070 | 1112.770 | 915.600 | 1332.150 | 9.381 | 7.766 | 11.216 | 0.867 | 0.789 | 0.933 | 0.033 | g18.nibi.sharcnet | 90.000 | 1.019 | 0.993 | 1.126 | 1.133 | True | 90.000 | 1.126 | 0.926 | 1.126 | 0.892 | 1.103 | 1.011 | 1.256 |
| 10.000 | nspec10 (Nibi) | 90.000 | 2.403 | 2.325 | 2.480 | 3462.240 | 2921.440 | 4062.780 | 1092.430 | 895.189 | 1314.410 | 10.314 | 8.434 | 12.460 | 0.889 | 0.822 | 0.944 | 0.067 | g18.nibi.sharcnet | 90.000 | 1.020 | 0.975 | 1.238 | 1.269 | True | 90.000 | 1.238 | 0.922 | 1.130 | 0.869 | 1.094 | 1.103 | 1.385 |

`campaign/addendum/tables/nspec__livecodebench_qwen3.csv`:

| n_draft | source | n_cases | mean_l_bar | mean_l_bar_ci_lo | mean_l_bar_ci_hi | mean_completion_tokens | mean_completion_tokens_ci_lo | mean_completion_tokens_ci_hi | mean_verifier_rounds | mean_verifier_rounds_ci_lo | mean_verifier_rounds_ci_hi | mean_wall_time_s | mean_wall_time_s_ci_lo | mean_wall_time_s_ci_hi | accuracy | accuracy_ci_lo | accuracy_ci_hi | capout_rate | nodes | n_pairs_vs_nibiref | lambda_vs_nibiref | rounds_ratio_vs_nibiref | time_ratio_vs_nibiref | time_per_round_ratio_vs_nibiref | same_node_vs_nibiref | same_node_pairs_vs_nibiref | time_ratio_same_node_vs_nibiref | lambda_vs_nibiref_ci_lo | lambda_vs_nibiref_ci_hi | rounds_ratio_vs_nibiref_ci_lo | rounds_ratio_vs_nibiref_ci_hi | time_ratio_vs_nibiref_ci_lo | time_ratio_vs_nibiref_ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2.000 | nspec2 (Nibi) | 90.000 | 0.937 | 0.922 | 0.952 | 8094.910 | 7332.760 | 8827.630 | 4232.990 | 3840.610 | 4638.300 | 32.610 | 29.451 | 35.724 | 0.711 | 0.611 | 0.800 | 0.311 | kn176 | 90.000 | 1.018 | 1.108 | 0.926 | 0.836 | True | 90.000 | 0.926 | 0.976 | 1.063 | 1.060 | 1.162 | 0.884 | 0.972 |
| 3.000 | nspec3 (Nibi) | 90.000 | 1.058 | 1.038 | 1.079 | 7986.440 | 7238.060 | 8715.170 | 3949.020 | 3560.110 | 4334.340 | 31.819 | 28.582 | 34.969 | 0.733 | 0.633 | 0.822 | 0.267 | kn176 | 90.000 | 1.004 | 1.034 | 0.904 | 0.874 | True | 90.000 | 0.904 | 0.968 | 1.042 | 0.994 | 1.075 | 0.869 | 0.941 |
| 4.000 | nspec4 (Nibi) | 90.000 | 1.106 | 1.081 | 1.130 | 7978.070 | 7219.170 | 8699.990 | 3873.670 | 3477.800 | 4264.190 | 32.766 | 29.416 | 36.083 | 0.744 | 0.656 | 0.833 | 0.244 | kn172:54+kn176:36 | 90.000 | 1.003 | 1.014 | 0.931 | 0.918 | False | 36.000 | 0.937 | 0.967 | 1.041 | 0.977 | 1.055 | 0.896 | 0.969 |
| 6.000 | campaign seed 0 (old box, H100 PCIe) | 90.000 | 1.205 | 1.181 | 1.230 | 8028.540 | 7265.280 | 8771.730 | 3703.370 | 3334.680 | 4077.910 | 71.423 | 64.079 | 78.641 | 0.700 | 0.600 | 0.789 | 0.322 | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| 6.000 | nibiref (Nibi, campaign settings) | 90.000 | 1.130 | 1.105 | 1.157 | 7954.860 | 7206.190 | 8712.070 | 3819.360 | 3428.310 | 4209.700 | 35.202 | 31.553 | 38.860 | 0.733 | 0.644 | 0.822 | 0.267 | kn176 | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| 8.000 | nspec8 (Nibi) | 90.000 | 1.132 | 1.103 | 1.161 | 7997.340 | 7244.430 | 8747.190 | 3851.330 | 3451.350 | 4241.880 | 37.987 | 33.993 | 41.841 | 0.700 | 0.600 | 0.789 | 0.311 | kn172 | 90.000 | 1.005 | 1.008 | 1.079 | 1.070 | False | 0.000 | - | 0.975 | 1.039 | 0.975 | 1.044 | 1.042 | 1.117 |
| 10.000 | nspec10 (Nibi) | 90.000 | 1.136 | 1.108 | 1.165 | 7908.100 | 7172.720 | 8654.550 | 3801.690 | 3415.670 | 4185.990 | 40.071 | 35.891 | 44.261 | 0.711 | 0.611 | 0.800 | 0.300 | kn172 | 90.000 | 0.994 | 0.995 | 1.138 | 1.144 | False | 0.000 | - | 0.961 | 1.026 | 0.960 | 1.029 | 1.097 | 1.177 |

## Step 4.1: temperature (strict, seed 0)

`campaign/addendum/tables/temp__gsm8k.csv`:

| temperature | source | n_cases | mean_l_bar | mean_l_bar_ci_lo | mean_l_bar_ci_hi | mean_completion_tokens | mean_completion_tokens_ci_lo | mean_completion_tokens_ci_hi | mean_verifier_rounds | mean_verifier_rounds_ci_lo | mean_verifier_rounds_ci_hi | mean_wall_time_s | mean_wall_time_s_ci_lo | mean_wall_time_s_ci_hi | accuracy | accuracy_ci_lo | accuracy_ci_hi | capout_rate | nodes | n_pairs_vs_nibiref | lambda_vs_nibiref | rounds_ratio_vs_nibiref | time_ratio_vs_nibiref | time_per_round_ratio_vs_nibiref | same_node_vs_nibiref | same_node_pairs_vs_nibiref | time_ratio_same_node_vs_nibiref | lambda_vs_nibiref_ci_lo | lambda_vs_nibiref_ci_hi | rounds_ratio_vs_nibiref_ci_lo | rounds_ratio_vs_nibiref_ci_hi | time_ratio_vs_nibiref_ci_lo | time_ratio_vs_nibiref_ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.000 | campaign seed 0 (old box, H100 PCIe) | 150.000 | 2.567 | 2.503 | 2.630 | 322.187 | 270.546 | 379.964 | 94.020 | 77.787 | 112.314 | 2.418 | 2.078 | 2.821 | 0.960 | 0.927 | 0.987 | 0.020 | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| 1.000 | nibiref (Nibi, campaign settings) | 150.000 | 2.582 | 2.516 | 2.646 | 321.627 | 266.393 | 382.822 | 93.087 | 76.793 | 111.081 | 0.718 | 0.600 | 0.855 | 0.967 | 0.933 | 0.993 | 0.013 | g18.nibi.sharcnet | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| 1.200 | temp1.2 (Nibi) | 150.000 | 2.359 | 2.299 | 2.421 | 408.113 | 342.573 | 480.314 | 127.633 | 106.047 | 152.460 | 0.966 | 0.803 | 1.140 | 0.960 | 0.927 | 0.987 | 0.033 | g18.nibi.sharcnet | 150.000 | 1.269 | 1.371 | 1.347 | 0.982 | True | 150.000 | 1.347 | 1.097 | 1.468 | 1.176 | 1.583 | 1.159 | 1.556 |
| 1.500 | temp1.5 (Nibi) | 150.000 | 1.791 | 1.751 | 1.833 | 1266.230 | 1139.000 | 1392.990 | 459.013 | 412.151 | 504.961 | 3.365 | 3.027 | 3.696 | 0.313 | 0.240 | 0.387 | 0.480 | g18.nibi.sharcnet | 150.000 | 3.937 | 4.931 | 4.690 | 0.951 | True | 150.000 | 4.690 | 3.290 | 4.711 | 4.105 | 5.930 | 3.942 | 5.623 |

`campaign/addendum/tables/temp__gsm8k_qwen3.csv`:

| temperature | source | n_cases | mean_l_bar | mean_l_bar_ci_lo | mean_l_bar_ci_hi | mean_completion_tokens | mean_completion_tokens_ci_lo | mean_completion_tokens_ci_hi | mean_verifier_rounds | mean_verifier_rounds_ci_lo | mean_verifier_rounds_ci_hi | mean_wall_time_s | mean_wall_time_s_ci_lo | mean_wall_time_s_ci_hi | accuracy | accuracy_ci_lo | accuracy_ci_hi | capout_rate | nodes | n_pairs_vs_nibiref | lambda_vs_nibiref | rounds_ratio_vs_nibiref | time_ratio_vs_nibiref | time_per_round_ratio_vs_nibiref | same_node_vs_nibiref | same_node_pairs_vs_nibiref | time_ratio_same_node_vs_nibiref | lambda_vs_nibiref_ci_lo | lambda_vs_nibiref_ci_hi | rounds_ratio_vs_nibiref_ci_lo | rounds_ratio_vs_nibiref_ci_hi | time_ratio_vs_nibiref_ci_lo | time_ratio_vs_nibiref_ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.000 | campaign seed 0 (old box, H100 PCIe) | 150.000 | 1.514 | 1.488 | 1.542 | 1291.930 | 1203.570 | 1380.760 | 510.080 | 475.179 | 544.467 | 10.299 | 9.569 | 11.027 | 0.800 | 0.733 | 0.860 | 0.247 | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| 1.000 | nibiref (Nibi, campaign settings) | 150.000 | 1.499 | 1.473 | 1.525 | 1279.450 | 1187.130 | 1371.730 | 509.680 | 474.260 | 544.848 | 4.620 | 4.308 | 4.938 | 0.800 | 0.733 | 0.860 | 0.227 | kn176 | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| 1.200 | temp1.2 (Nibi) | 150.000 | 1.277 | 1.252 | 1.301 | 1300.170 | 1205.770 | 1395.190 | 570.253 | 528.659 | 611.262 | 5.176 | 4.797 | 5.550 | 0.813 | 0.747 | 0.873 | 0.253 | kn176 | 150.000 | 1.016 | 1.119 | 1.120 | 1.001 | True | 150.000 | 1.120 | 0.977 | 1.059 | 1.072 | 1.167 | 1.074 | 1.167 |
| 1.500 | temp1.5 (Nibi) | 150.000 | 0.821 | 0.804 | 0.837 | 1320.270 | 1226.220 | 1412.620 | 725.833 | 673.492 | 777.434 | 6.563 | 6.097 | 7.038 | 0.773 | 0.707 | 0.840 | 0.273 | kn176 | 150.000 | 1.032 | 1.424 | 1.421 | 0.998 | True | 150.000 | 1.421 | 0.991 | 1.074 | 1.366 | 1.485 | 1.363 | 1.481 |

`campaign/addendum/tables/temp__livecodebench.csv`:

| temperature | source | n_cases | mean_l_bar | mean_l_bar_ci_lo | mean_l_bar_ci_hi | mean_completion_tokens | mean_completion_tokens_ci_lo | mean_completion_tokens_ci_hi | mean_verifier_rounds | mean_verifier_rounds_ci_lo | mean_verifier_rounds_ci_hi | mean_wall_time_s | mean_wall_time_s_ci_lo | mean_wall_time_s_ci_hi | accuracy | accuracy_ci_lo | accuracy_ci_hi | capout_rate | nodes | n_pairs_vs_nibiref | lambda_vs_nibiref | rounds_ratio_vs_nibiref | time_ratio_vs_nibiref | time_per_round_ratio_vs_nibiref | same_node_vs_nibiref | same_node_pairs_vs_nibiref | time_ratio_same_node_vs_nibiref | lambda_vs_nibiref_ci_lo | lambda_vs_nibiref_ci_hi | rounds_ratio_vs_nibiref_ci_lo | rounds_ratio_vs_nibiref_ci_hi | time_ratio_vs_nibiref_ci_lo | time_ratio_vs_nibiref_ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.000 | campaign seed 0 (old box, H100 PCIe) | 90.000 | 2.164 | 2.106 | 2.224 | 3456.240 | 2916.070 | 4036.960 | 1150.830 | 953.437 | 1367.740 | 25.190 | 21.212 | 29.607 | 0.889 | 0.822 | 0.944 | 0.022 | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| 1.000 | nibiref (Nibi, campaign settings) | 90.000 | 2.213 | 2.152 | 2.273 | 3394.530 | 2870.310 | 3973.440 | 1120.230 | 923.961 | 1338.890 | 8.333 | 6.880 | 9.949 | 0.911 | 0.844 | 0.967 | 0.044 | g18.nibi.sharcnet | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| 1.200 | temp1.2 (Nibi) | 90.000 | 2.004 | 1.946 | 2.064 | 3646.640 | 3094.240 | 4262.450 | 1296.980 | 1071.380 | 1538.380 | 9.625 | 7.946 | 11.467 | 0.867 | 0.789 | 0.933 | 0.056 | g18.nibi.sharcnet | 90.000 | 1.074 | 1.158 | 1.155 | 0.998 | True | 90.000 | 1.155 | 0.984 | 1.174 | 1.052 | 1.277 | 1.047 | 1.276 |
| 1.500 | temp1.5 (Nibi) | 90.000 | 1.254 | 1.194 | 1.316 | 6193.010 | 5417.230 | 6949.390 | 2932.840 | 2539.590 | 3320.870 | 20.889 | 18.121 | 23.606 | 0.078 | 0.033 | 0.133 | 0.022 | g18.nibi.sharcnet | 90.000 | 1.824 | 2.618 | 2.507 | 0.957 | True | 90.000 | 2.507 | 1.449 | 2.279 | 2.046 | 3.355 | 1.964 | 3.214 |

`campaign/addendum/tables/temp__livecodebench_qwen3.csv`:

| temperature | source | n_cases | mean_l_bar | mean_l_bar_ci_lo | mean_l_bar_ci_hi | mean_completion_tokens | mean_completion_tokens_ci_lo | mean_completion_tokens_ci_hi | mean_verifier_rounds | mean_verifier_rounds_ci_lo | mean_verifier_rounds_ci_hi | mean_wall_time_s | mean_wall_time_s_ci_lo | mean_wall_time_s_ci_hi | accuracy | accuracy_ci_lo | accuracy_ci_hi | capout_rate | nodes | n_pairs_vs_nibiref | lambda_vs_nibiref | rounds_ratio_vs_nibiref | time_ratio_vs_nibiref | time_per_round_ratio_vs_nibiref | same_node_vs_nibiref | same_node_pairs_vs_nibiref | time_ratio_same_node_vs_nibiref | lambda_vs_nibiref_ci_lo | lambda_vs_nibiref_ci_hi | rounds_ratio_vs_nibiref_ci_lo | rounds_ratio_vs_nibiref_ci_hi | time_ratio_vs_nibiref_ci_lo | time_ratio_vs_nibiref_ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.000 | campaign seed 0 (old box, H100 PCIe) | 90.000 | 1.205 | 1.180 | 1.229 | 8028.540 | 7273.240 | 8788.980 | 3703.370 | 3328.820 | 4067.680 | 71.423 | 64.093 | 78.719 | 0.700 | 0.600 | 0.789 | 0.322 | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| 1.000 | nibiref (Nibi, campaign settings) | 90.000 | 1.130 | 1.105 | 1.156 | 7954.860 | 7188.320 | 8706.620 | 3819.360 | 3423.990 | 4201.760 | 35.202 | 31.541 | 38.860 | 0.733 | 0.644 | 0.822 | 0.267 | kn176 | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| 1.200 | temp1.2 (Nibi) | 90.000 | 0.896 | 0.870 | 0.922 | 8095.680 | 7329.800 | 8829.000 | 4379.460 | 3943.680 | 4811.090 | 40.173 | 36.039 | 44.229 | 0.722 | 0.622 | 0.811 | 0.278 | kn172 | 90.000 | 1.018 | 1.147 | 1.141 | 0.995 | False | 0.000 | - | 0.983 | 1.054 | 1.107 | 1.189 | 1.099 | 1.184 |
| 1.500 | temp1.5 (Nibi) | 90.000 | 0.493 | 0.475 | 0.511 | 8311.140 | 7537.970 | 9054.840 | 5699.960 | 5135.370 | 6245.820 | 52.512 | 47.229 | 57.643 | 0.644 | 0.544 | 0.744 | 0.333 | kn172 | 90.000 | 1.045 | 1.492 | 1.492 | 1.000 | False | 0.000 | - | 1.001 | 1.092 | 1.428 | 1.564 | 1.427 | 1.566 |

## Step 4.2: Qwen3 at its recommended sampler

`campaign/addendum/tables/qwenT0.6__gsm8k_qwen3.csv`:

| condition | dataset | method | alpha | n_pairs | l_bar | l_bar_strict | mean_tokens | mean_tokens_strict | lambda | rounds_ratio | time_ratio | accuracy | accuracy_strict | capout_rate | capout_rate_strict | time_per_round_ratio | nodes | nodes_strict | same_node_pairs | same_node | time_ratio_same_node | lambda_ci_lo | lambda_ci_hi | rounds_ratio_ci_lo | rounds_ratio_ci_hi | time_ratio_ci_lo | time_ratio_ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwenT0.6 | gsm8k_qwen3 | mentored_dec | 0.750 | 150.000 | 1.853 | 1.684 | 1288.870 | 1279.090 | 1.008 | 0.942 | 0.942 | 0.813 | 0.793 | 0.233 | 0.247 | 1.000 | kn173 | kn173 | 150.000 | True | 0.942 | 0.975 | 1.043 | 0.910 | 0.976 | 0.911 | 0.977 |
| qwenT0.6 | gsm8k_qwen3 | cactus | 0.350 | 150.000 | 1.808 | 1.684 | 1289.150 | 1279.090 | 1.008 | 0.958 | 1.068 | 0.813 | 0.793 | 0.227 | 0.247 | 1.115 | kn176 | kn173 | 0.000 | False | - | 0.973 | 1.046 | 0.923 | 0.996 | 1.029 | 1.111 |
| qwenT0.6 | gsm8k_qwen3 | spec_casc_opt | 0.050 | 150.000 | 3.336 | 1.684 | 1940.130 | 1279.090 | 1.517 | 0.953 | 1.084 | 0.200 | 0.793 | 0.867 | 0.247 | 1.138 | kn176 | kn173 | 0.000 | False | - | 1.425 | 1.622 | 0.894 | 1.019 | 1.018 | 1.160 |
| qwenT0.6 | gsm8k_qwen3 | r_fuzzy | 0.250 | 150.000 | 2.051 | 1.684 | 1289.350 | 1279.090 | 1.008 | 0.885 | 0.887 | 0.640 | 0.793 | 0.387 | 0.247 | 1.001 | kn173 | kn173 | 150.000 | True | 0.887 | 0.921 | 1.092 | 0.810 | 0.961 | 0.812 | 0.963 |
| qwenT0.6 | gsm8k_qwen3 | spec_casc_tok | 0.800 | 150.000 | 1.804 | 1.684 | 1285.690 | 1279.090 | 1.005 | 0.957 | 1.071 | 0.780 | 0.793 | 0.260 | 0.247 | 1.119 | kn176 | kn173 | 0.000 | False | - | 0.970 | 1.042 | 0.923 | 0.995 | 1.032 | 1.113 |

`campaign/addendum/tables/qwenT0.6__livecodebench_qwen3.csv`:

| condition | dataset | method | alpha | n_pairs | l_bar | l_bar_strict | mean_tokens | mean_tokens_strict | lambda | rounds_ratio | time_ratio | accuracy | accuracy_strict | capout_rate | capout_rate_strict | time_per_round_ratio | nodes | nodes_strict | same_node_pairs | same_node | time_ratio_same_node | lambda_ci_lo | lambda_ci_hi | rounds_ratio_ci_lo | rounds_ratio_ci_hi | time_ratio_ci_lo | time_ratio_ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwenT0.6 | livecodebench_qwen3 | mentored_dec | 0.750 | 90.000 | 1.574 | 1.359 | 8364.690 | 8006.600 | 1.045 | 0.943 | 0.944 | 0.678 | 0.667 | 0.344 | 0.333 | 1.001 | kn173:62+kn169:28 | kn173 | 62.000 | False | 0.957 | 0.998 | 1.094 | 0.904 | 0.986 | 0.904 | 0.989 |
| qwenT0.6 | livecodebench_qwen3 | cactus | 0.350 | 90.000 | 1.529 | 1.359 | 8099.410 | 8006.600 | 1.012 | 0.932 | 1.033 | 0.722 | 0.667 | 0.289 | 0.333 | 1.109 | kn176 | kn173 | 0.000 | False | - | 0.979 | 1.045 | 0.900 | 0.966 | 0.996 | 1.072 |
| qwenT0.6 | livecodebench_qwen3 | spec_casc_opt | 0.050 | 90.000 | 3.731 | 1.359 | 11887.500 | 8006.600 | 1.485 | 0.746 | 0.833 | 0.000 | 0.667 | 0.989 | 0.333 | 1.116 | kn176 | kn173 | 0.000 | False | - | 1.359 | 1.633 | 0.675 | 0.831 | 0.753 | 0.930 |
| qwenT0.6 | livecodebench_qwen3 | r_fuzzy | 0.250 | 90.000 | 1.698 | 1.359 | 8681.840 | 8006.600 | 1.084 | 0.972 | 0.966 | 0.100 | 0.667 | 0.522 | 0.333 | 0.994 | kn169 | kn173 | 0.000 | False | - | 0.979 | 1.195 | 0.873 | 1.074 | 0.868 | 1.067 |
| qwenT0.6 | livecodebench_qwen3 | spec_casc_tok | 0.800 | 90.000 | 1.508 | 1.359 | 8150.600 | 8006.600 | 1.018 | 0.946 | 1.056 | 0.678 | 0.667 | 0.322 | 0.333 | 1.116 | kn176 | kn173 | 0.000 | False | - | 0.980 | 1.060 | 0.909 | 0.988 | 1.013 | 1.102 |

## Step 4.3: standalone LM drafter (Qwen3-0.6B)

`campaign/addendum/tables/lmdraft__gsm8k_qwen3.csv`:

| condition | dataset | method | alpha | n_pairs | l_bar | l_bar_strict | mean_tokens | mean_tokens_strict | lambda | rounds_ratio | time_ratio | accuracy | accuracy_strict | capout_rate | capout_rate_strict | time_per_round_ratio | nodes | nodes_strict | same_node_pairs | same_node | lambda_ci_lo | lambda_ci_hi | rounds_ratio_ci_lo | rounds_ratio_ci_hi | time_ratio_ci_lo | time_ratio_ci_hi | time_ratio_same_node |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lmdraft | gsm8k_qwen3 | mentored_dec | 0.750 | 150.000 | 3.822 | 3.161 | 1232.670 | 1309.720 | 0.941 | 0.800 | 0.707 | 0.827 | 0.767 | 0.200 | 0.273 | 0.884 | kn176 | kn169 | 0.000 | False | 0.900 | 0.985 | 0.762 | 0.839 | 0.674 | 0.743 | - |
| lmdraft | gsm8k_qwen3 | cactus | 0.350 | 150.000 | 4.072 | 3.161 | 1224.330 | 1309.720 | 0.935 | 0.749 | 0.693 | 0.827 | 0.767 | 0.187 | 0.273 | 0.925 | kn169 | kn169 | 150.000 | True | 0.893 | 0.975 | 0.716 | 0.783 | 0.662 | 0.726 | 0.693 |
| lmdraft | gsm8k_qwen3 | spec_casc_tok | 0.800 | 150.000 | 3.405 | 3.161 | 1247.030 | 1309.720 | 0.952 | 0.899 | 0.833 | 0.833 | 0.767 | 0.220 | 0.273 | 0.927 | kn176 | kn169 | 0.000 | False | 0.915 | 0.989 | 0.861 | 0.937 | 0.798 | 0.868 | - |
| lmdraft | gsm8k_qwen3 | spec_casc_opt | 0.050 | 150.000 | 3.656 | 3.161 | 1284.690 | 1309.720 | 0.981 | 0.869 | 0.780 | 0.787 | 0.767 | 0.233 | 0.273 | 0.897 | kn174 | kn169 | 0.000 | False | 0.941 | 1.024 | 0.831 | 0.911 | 0.745 | 0.818 | - |
| lmdraft | gsm8k_qwen3 | r_fuzzy | 0.250 | 150.000 | 4.681 | 3.161 | 1317.880 | 1309.720 | 1.006 | 0.719 | 0.644 | 0.760 | 0.767 | 0.253 | 0.273 | 0.896 | kn174 | kn169 | 0.000 | False | 0.965 | 1.051 | 0.687 | 0.754 | 0.616 | 0.675 | - |

`campaign/addendum/tables/lmdraft__livecodebench_qwen3.csv`:

| condition | dataset | method | alpha | n_pairs | l_bar | l_bar_strict | mean_tokens | mean_tokens_strict | lambda | rounds_ratio | time_ratio | accuracy | accuracy_strict | capout_rate | capout_rate_strict | time_per_round_ratio | nodes | nodes_strict | same_node_pairs | same_node | lambda_ci_lo | lambda_ci_hi | rounds_ratio_ci_lo | rounds_ratio_ci_hi | time_ratio_ci_lo | time_ratio_ci_hi | time_ratio_same_node |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lmdraft | livecodebench_qwen3 | mentored_dec | 0.750 | 90.000 | 3.899 | 3.014 | 7435.800 | 8076.410 | 0.921 | 0.735 | 0.713 | 0.722 | 0.722 | 0.267 | 0.289 | 0.970 | kn176 | kn169 | 0.000 | False | 0.883 | 0.959 | 0.709 | 0.764 | 0.687 | 0.741 | - |
| lmdraft | livecodebench_qwen3 | cactus | 0.350 | 90.000 | 4.312 | 3.014 | 7649.500 | 8076.410 | 0.947 | 0.695 | 0.683 | 0.756 | 0.722 | 0.244 | 0.289 | 0.983 | kn169 | kn169 | 90.000 | True | 0.908 | 0.988 | 0.668 | 0.725 | 0.656 | 0.713 | 0.683 |
| lmdraft | livecodebench_qwen3 | spec_casc_tok | 0.800 | 90.000 | 3.275 | 3.014 | 7551.780 | 8076.410 | 0.935 | 0.871 | 0.853 | 0.789 | 0.722 | 0.211 | 0.289 | 0.980 | kn176 | kn169 | 0.000 | False | 0.896 | 0.975 | 0.835 | 0.907 | 0.818 | 0.889 | - |
| lmdraft | livecodebench_qwen3 | spec_casc_opt | 0.050 | 90.000 | 3.526 | 3.014 | 7657.190 | 8076.410 | 0.948 | 0.825 | 0.833 | 0.700 | 0.722 | 0.300 | 0.289 | 1.010 | kn176 | kn169 | 0.000 | False | 0.906 | 0.990 | 0.790 | 0.860 | 0.798 | 0.870 | - |
| lmdraft | livecodebench_qwen3 | r_fuzzy | 0.250 | 90.000 | 4.989 | 3.014 | 8246.190 | 8076.410 | 1.021 | 0.677 | 0.681 | 0.611 | 0.722 | 0.344 | 0.289 | 1.005 | kn176 | kn169 | 0.000 | False | 0.976 | 1.069 | 0.648 | 0.709 | 0.650 | 0.713 | - |

## Step 5: alpha grid completion and best-setting validation

Source: `campaign/addendum/best_setting.csv`, one row per (target, dataset, method). Chosen alpha = the grid alpha with the lowest seed-0 time ratio among those whose accuracy is within 2 points of strict (mtbench, ungraded: rounds ratio < 1); `chosen_alpha_by_rounds_ratio` = the same choice made on the rounds ratio. Time ratios of the step-5.1 additions are taken against the step-0.5 strict reference on the same machine (Nibi for GPT-OSS, Killarney for Qwen3; `s0_time_ratio_basis`, `hardware_s0_*`). Seed 1 = the step-5.2 validation run, paired with strict seed 1 on the same machine (`s1_hardware`, `s1_strict_hardware`; '-' = not complete yet); validated = seed-1 time ratio < 1 and the same accuracy rule holds on seed 1. s1 same node = seed-1 pairs whose arm and strict ran on one node (`s1_same_node_pairs`; README deviations 13-17): a seed-1 time verdict on cross-node pairs carries the node effect, the rounds ratio does not.

| target | dataset | method | grid complete | chosen alpha (by rounds) | s0 lambda | s0 rounds ratio | s0 time ratio | s0 acc / strict | s1 lambda | s1 rounds ratio | s1 time ratio | s1 acc / strict | s1 same node | validated |
|---|---|---|---|---|---:|---:|---:|---|---:|---:|---:|---|---:|---|
| gpt-oss-20b | gsm8k | mentored_dec | True | 0.55 (0.55) | 1.10 | 0.86 | 0.84 | 95% / 96% | 0.98 | 0.76 | 0.75 | 97% / 96% | 150/150 | yes |
| gpt-oss-20b | gsm8k | spec_casc_tok | True | 0.55 (0.8) | 0.92 | 0.83 | 0.85 | 98% / 96% | 0.92 | 0.85 | 0.85 | 97% / 96% | 150/150 | yes |
| gpt-oss-20b | aime24 | mentored_dec | True | 0.55 (0.55) | 1.18 | 0.92 | 0.94 | 80% / 77% | 1.07 | 0.87 | 0.87 | 70% / 80% | 0/30 | no |
| gpt-oss-20b | aime24 | spec_casc_tok | True | 0.15 (0.15) | 1.00 | 0.91 | 0.95 | 83% / 77% | 1.15 | 1.12 | 1.12 | 77% / 80% | 0/30 | no |
| gpt-oss-20b | humaneval | mentored_dec | True | 0.55 (0.55) | 1.09 | 0.89 | 0.94 | 95% / 96% | 1.18 | 0.96 | 0.96 | 95% / 95% | 150/150 | yes |
| gpt-oss-20b | humaneval | spec_casc_tok | True | 0.35 (0.35) | 0.95 | 0.90 | 0.95 | 96% / 96% | 1.01 | 0.98 | 0.99 | 97% / 95% | 150/150 | yes |
| gpt-oss-20b | livecodebench | mentored_dec | True | 0.55 (0.55) | 1.20 | 0.96 | 0.95 | 88% / 89% | 1.15 | 0.93 | 0.92 | 87% / 90% | 90/90 | no |
| gpt-oss-20b | livecodebench | spec_casc_tok | True | 0.35 (0.35) | 1.01 | 0.94 | 0.96 | 91% / 89% | 1.02 | 0.96 | 0.94 | 93% / 90% | 90/90 | yes |
| gpt-oss-20b | mtbench | mentored_dec | True | 0.75 (0.75) | 1.10 | 0.75 | 0.87 | - / - | 1.14 | 0.76 | 0.78 | - / - | 80/80 | yes |
| gpt-oss-20b | mtbench | spec_casc_tok | True | 0.55 (0.8) | 0.97 | 0.93 | 0.89 | - / - | 1.00 | 0.95 | 0.95 | - / - | 80/80 | yes |
| gpt-oss-20b | longbench_v2 | mentored_dec | True | 0.55 (0.55) | 1.11 | 0.89 | 1.00 | 57% / 56% | 1.38 | 1.09 | 1.03 | 55% / 57% | 0/150 | no |
| gpt-oss-20b | longbench_v2 | spec_casc_tok | True | 0.55 (0.55) | 1.06 | 0.97 | 0.94 | 57% / 56% | 1.20 | 1.09 | 1.04 | 55% / 57% | 0/150 | no |
| qwen3-8b | gsm8k | mentored_dec | True | 0.35 (0.35) | 0.99 | 0.96 | 0.96 | 82% / 80% | 1.00 | 0.96 | 0.96 | 85% / 81% | 150/150 | yes |
| qwen3-8b | gsm8k | spec_casc_tok | True | 0.8 (0.8) | 0.99 | 0.95 | 0.96 | 79% / 80% | 1.00 | 0.95 | 0.97 | 82% / 81% | 150/150 | yes |
| qwen3-8b | aime24 | mentored_dec | True | 0.55 (0.15) | 0.99 | 1.01 | 0.88 | 77% / 70% | 1.03 | 0.98 | 1.00 | 80% / 77% | 0/30 | yes |
| qwen3-8b | aime24 | spec_casc_tok | True | 0.35 (0.8) | 0.95 | 0.99 | 0.83 | 77% / 70% | 0.94 | 0.92 | 0.93 | 70% / 77% | 0/30 | no |
| qwen3-8b | humaneval | mentored_dec | True | 0.55 (0.75) | 1.10 | 1.08 | 0.90 | 83% / 83% | 1.05 | 1.00 | 1.02 | 85% / 87% | 150/150 | no |
| qwen3-8b | humaneval | spec_casc_tok | True | 0.35 (0.8) | 1.04 | 1.07 | 0.90 | 85% / 83% | 1.03 | 1.03 | 1.03 | 84% / 87% | 150/150 | no |
| qwen3-8b | livecodebench | mentored_dec | True | 0.35 (0.15) | 1.03 | 1.02 | 0.98 | 70% / 70% | 1.01 | 0.97 | 0.99 | 73% / 76% | 90/90 | no |
| qwen3-8b | livecodebench | spec_casc_tok | True | 0.8 (0.8) | 1.00 | 0.94 | 0.96 | 71% / 70% | 1.02 | 0.96 | 0.97 | 72% / 69% | 0/90 | yes |
| qwen3-8b | mtbench | mentored_dec | True | 0.55 (0.75) | 1.00 | 0.93 | 0.83 | - / - | 1.02 | 0.92 | 0.90 | - / - | 80/80 | yes |
| qwen3-8b | mtbench | spec_casc_tok | True | 0.8 (0.8) | 1.04 | 0.96 | 0.99 | - / - | 1.02 | 0.96 | 0.96 | - / - | 0/80 | yes |
| qwen3-8b | longbench_v2 | mentored_dec | True | 0.75 (0.75) | 1.06 | 0.98 | 0.99 | 51% / 53% | 1.05 | 1.00 | 0.97 | 51% / 51% | 0/150 | yes |
| qwen3-8b | longbench_v2 | spec_casc_tok | True | 0.55 (0.15) | 0.99 | 1.12 | 0.95 | 53% / 53% | 1.03 | 1.01 | 0.99 | 55% / 51% | 150/150 | yes |

## Step 6: AIME24 accuracy repeats

Source: `campaign/addendum/aime24_repeats.csv`, one row per (target, method); seed 0 = the campaign (old box), seeds 1-4 = Nibi. Interval: two-level bootstrap (problems, then seeds within a problem), 10,000 resamples.

| target | method | alpha | acc s0 | acc s1 | acc s2 | acc s3 | acc s4 | mean over seeds [95% CI] | sd across seeds | seeds |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|
| gpt-oss-20b | strict | strict | 77% | 80% | 73% | 80% | 83% | 78.7% [65.3%, 90.7%] | 0.038 | 0 1 2 3 4 |
| gpt-oss-20b | mentored_dec | 0.75 | 63% | 70% | 67% | 77% | 63% | 68.0% [52.7%, 82.0%] | 0.056 | 0 1 2 3 4 |
| gpt-oss-20b | cactus | 0.18 | 60% | 50% | 43% | 50% | 53% | 51.3% [36.0%, 66.7%] | 0.061 | 0 1 2 3 4 |
| gpt-oss-20b | spec_casc_opt | 0.05 | 37% | 33% | 43% | 43% | 40% | 39.3% [25.3%, 53.3%] | 0.043 | 0 1 2 3 4 |
| gpt-oss-20b | r_fuzzy | 0.25 | 50% | 43% | 53% | 50% | 43% | 48.0% [33.3%, 62.7%] | 0.045 | 0 1 2 3 4 |
| gpt-oss-20b | spec_casc_tok | 0.8 | 70% | 73% | 67% | 60% | 73% | 68.7% [54.0%, 82.0%] | 0.056 | 0 1 2 3 4 |
| qwen3-8b | strict | strict | 70% | 77% | 80% | 63% | 70% | 72.0% [56.7%, 85.3%] | 0.065 | 0 1 2 3 4 |
| qwen3-8b | mentored_dec | 0.75 | 73% | 70% | 73% | 73% | 70% | 72.0% [56.0%, 86.7%] | 0.018 | 0 1 2 3 4 |
| qwen3-8b | cactus | 0.35 | 23% | 23% | 23% | 20% | 13% | 20.7% [8.7%, 34.7%] | 0.043 | 0 1 2 3 4 |
| qwen3-8b | spec_casc_opt | 0.05 | 30% | 37% | 30% | 30% | 33% | 32.0% [19.3%, 45.3%] | 0.030 | 0 1 2 3 4 |
| qwen3-8b | r_fuzzy | 0.25 | 40% | 33% | 40% | 37% | 27% | 35.3% [21.3%, 50.0%] | 0.056 | 0 1 2 3 4 |
| qwen3-8b | spec_casc_tok | 0.8 | 70% | 63% | 70% | 80% | 80% | 72.7% [58.0%, 86.0%] | 0.072 | 0 1 2 3 4 |

## Step 7: SPEED-Bench qualitative split (seed 0; GPT-OSS on Nibi, Qwen3's first 40 prompts per arm on Nibi and the rest on Killarney)

**Token-budget pilot, gpt-oss-20b** (`campaign/addendum/tables/speedbench_pilot__gpt-oss-20b.csv`; strict at 8192 on each category's first 20 cases, >10% cap-outs would raise the category to 16384): reasoning 0/20 cap-outs of 20 (mean 820, max 3269 tokens) -> budget 8192; math 0/4 cap-outs of 20 (mean 357, max 636 tokens) -> budget pending.

### gpt-oss-20b

Source: `campaign/addendum/tables/speedbench__gpt-oss-20b.csv`, one row per (method, category); Eq. 4 per (method, category): `campaign/addendum/tables/speedbench_eq4__gpt-oss-20b.csv`; per-method counts: `campaign/addendum/tables/speedbench_eq4_summary__gpt-oss-20b.csv`. Cell = lambda (completion tokens relaxed / strict) · R = verifier rounds ratio · T = wall-time ratio, all vs strict on the same cases; ↓/↑ = the 95% paired bootstrap interval lies entirely below/above 1. Strict column: mean completion tokens and cap-out rate. Where not every pair ran its arm and its strict case on one node (`same_node` False; README deviations 13-17), the cell adds T over the same-node pairs and their count (`time_ratio_same_node`, `same_node_pairs`), or 'cross-node' when fewer than 10 pairs share a node; R is hardware-independent.

| category | strict tokens (cap-out) | mentored_dec (0.75) | cactus (0.35) | spec_casc_opt (0.05) | r_fuzzy (0.25) | spec_casc_tok (0.8) |
|---|---:|---|---|---|---|---|
| all | 1266 (1%) | λ 1.15↑ · R 0.76↓ · T 0.75↓ (n=672) | λ 1.26↑ · R 0.63↓ · T 0.62↓ (n=672) · cross-node | λ 1.23↑ · R 0.82↓ · T 0.82↓ (n=672) | λ 1.20↑ · R 0.77↓ · T 0.75↓ (n=672) · cross-node | λ 1.09↑ · R 0.95↓ · T 0.92↓ (n=672) · cross-node |
| coding | 1686 (5%) | λ 1.17↑ · R 0.85↓ · T 0.84↓ (n=80) | λ 1.52↑ · R 0.87 · T 0.86 (n=80) · cross-node | λ 1.41↑ · R 1.01 · T 1.01 (n=80) | λ 1.28↑ · R 0.89 · T 0.88 (n=80) · cross-node | λ 1.05 · R 0.92 · T 0.90 (n=80) · cross-node |
| math | 370 (0%) | λ 1.11 · R 0.88 · T 0.88 (n=18) | λ 1.15 · R 0.84 · T 0.83 (n=18) · cross-node | λ 1.30↑ · R 1.02 · T 1.03 (n=18) | λ 1.71↑ · R 1.28↑ · T 1.26 (n=18) · cross-node | λ 1.00 · R 0.87↓ · T 0.86↓ (n=18) · cross-node |
| humanities | 2324 (0%) | λ 0.93 · R 0.59↓ · T 0.58↓ (n=8) | λ 1.11 · R 0.48↓ · T 0.47↓ (n=8) · cross-node | λ 1.16 · R 0.75↓ · T 0.75↓ (n=8) | λ 0.83 · R 0.49↓ · T 0.49↓ (n=8) · cross-node | λ 0.96 · R 0.86 · T 0.84 (n=8) · cross-node |
| stem | 1596 (0%) | λ 1.22↑ · R 0.83 · T 0.83↓ (n=6) | λ 1.35↑ · R 0.63↓ · T 0.62↓ (n=6) · cross-node | λ 1.35↑ · R 0.93 · T 0.93 (n=6) | λ 1.28↑ · R 0.84 · T 0.83 (n=6) · cross-node | λ 1.08 · R 0.99 · T 0.97 (n=6) · cross-node |
| writing | 3042 (0%) | λ 0.94 · R 0.56↓ · T 0.55↓ (n=80) | λ 0.85↓ · R 0.36↓ · T 0.36↓ (n=80) · cross-node | λ 1.01 · R 0.60↓ · T 0.60↓ (n=80) | λ 0.89↓ · R 0.55↓ · T 0.54↓ (n=80) · cross-node | λ 1.02 · R 0.89↓ · T 0.86↓ (n=80) · cross-node |
| summarization | 334 (0%) | λ 1.10 · R 0.86↓ · T 0.82↓ (n=80) | λ 1.38↑ · R 0.71↓ · T 0.67↓ (n=80) · cross-node | λ 1.10 · R 0.85↓ · T 0.81↓ (n=80) | λ 1.15↑ · R 0.90↓ · T 0.84↓ (n=80) · cross-node | λ 1.00 · R 0.91↓ · T 0.85↓ (n=80) · cross-node |
| roleplay | 656 (0%) | λ 1.20↑ · R 0.68↓ · T 0.66↓ (n=80) | λ 1.28↑ · R 0.53↓ · T 0.52↓ (n=80) · cross-node | λ 1.18↑ · R 0.74↓ · T 0.73↓ (n=80) | λ 1.19↑ · R 0.62↓ · T 0.60↓ (n=80) · cross-node | λ 1.25↑ · R 1.10 · T 1.04 (n=80) · cross-node |
| rag | 837 (0%) | λ 1.16 · R 0.78↓ · T 0.76↓ (n=80) | λ 1.37↑ · R 0.71↓ · T 0.68↓ (n=80) · cross-node | λ 1.03 · R 0.72↓ · T 0.71↓ (n=80) | λ 1.15 · R 0.74↓ · T 0.71↓ (n=80) · cross-node | λ 1.06 · R 0.88 · T 0.84↓ (n=80) · cross-node |
| multilingual | 968 (1%) | λ 1.43↑ · R 1.07 · T 1.07 (n=80) | λ 1.72↑ · R 0.96 · T 0.95 (n=80) · cross-node | λ 1.87↑ · R 1.31↑ · T 1.32↑ (n=80) | λ 1.86↑ · R 1.32↑ · T 1.30↑ (n=80) · cross-node | λ 1.03 · R 0.96 · T 0.94 (n=80) · cross-node |
| reasoning | 1104 (0%) | λ 1.21↑ · R 0.83↓ · T 0.83↓ (n=80) | λ 1.48↑ · R 0.80↓ · T 0.79↓ (n=80) · cross-node | λ 1.37↑ · R 0.97 · T 0.98 (n=80) | λ 1.37↑ · R 0.89 · T 0.88 (n=80) · cross-node | λ 1.05 · R 0.92 · T 0.90 (n=80) · cross-node |
| qa | 1575 (0%) | λ 1.34↑ · R 0.82↓ · T 0.82↓ (n=80) | λ 1.27↑ · R 0.61↓ · T 0.60↓ (n=80) · cross-node | λ 1.15 · R 0.75↓ · T 0.76↓ (n=80) | λ 1.25↑ · R 0.70↓ · T 0.69↓ (n=80) · cross-node | λ 1.32↑ · R 1.08 · T 1.07 (n=80) · cross-node |

- **spec_casc_opt** (alpha 0.05, `campaign/addendum/tables/speedbench_eq4_summary__gpt-oss-20b.csv` row `spec_casc_opt`): fewer verifier rounds in 8/11 categories (humanities, stem, writing, summarization, roleplay, rag, reasoning, qa); less wall time in 8/11 (humanities, stem, writing, summarization, roleplay, rag, reasoning, qa); Eq. 4 predicts a win in 8/11; completions longer by lambda 1.01 (writing) to 1.87 (multilingual); rounds and time disagree in: none.
- **mentored_dec** (alpha 0.75, `campaign/addendum/tables/speedbench_eq4_summary__gpt-oss-20b.csv` row `mentored_dec`): fewer verifier rounds in 10/11 categories (coding, math, humanities, stem, writing, summarization, roleplay, rag, reasoning, qa); less wall time in 10/11 (coding, math, humanities, stem, writing, summarization, roleplay, rag, reasoning, qa); Eq. 4 predicts a win in 10/11; completions longer by lambda 0.93 (humanities) to 1.43 (multilingual); rounds and time disagree in: none.
- **cactus** (alpha 0.35, `campaign/addendum/tables/speedbench_eq4_summary__gpt-oss-20b.csv` row `cactus`): fewer verifier rounds in 11/11 categories (coding, math, humanities, stem, writing, summarization, roleplay, rag, multilingual, reasoning, qa); less wall time in 11/11 (coding, math, humanities, stem, writing, summarization, roleplay, rag, multilingual, reasoning, qa); Eq. 4 predicts a win in 10/11; completions longer by lambda 0.85 (writing) to 1.72 (multilingual); rounds and time disagree in: none. Over all categories T 0.62 · cross-node (`campaign/addendum/tables/speedbench__gpt-oss-20b.csv` row `cactus`, category `all`).
- **r_fuzzy** (alpha 0.25, `campaign/addendum/tables/speedbench_eq4_summary__gpt-oss-20b.csv` row `r_fuzzy`): fewer verifier rounds in 9/11 categories (coding, humanities, stem, writing, summarization, roleplay, rag, reasoning, qa); less wall time in 9/11 (coding, humanities, stem, writing, summarization, roleplay, rag, reasoning, qa); Eq. 4 predicts a win in 9/11; completions longer by lambda 0.83 (humanities) to 1.86 (multilingual); rounds and time disagree in: none. Over all categories T 0.75 · cross-node (`campaign/addendum/tables/speedbench__gpt-oss-20b.csv` row `r_fuzzy`, category `all`).
- **spec_casc_tok** (alpha 0.8, `campaign/addendum/tables/speedbench_eq4_summary__gpt-oss-20b.csv` row `spec_casc_tok`): fewer verifier rounds in 9/11 categories (coding, math, humanities, stem, writing, summarization, rag, multilingual, reasoning); less wall time in 9/11 (coding, math, humanities, stem, writing, summarization, rag, multilingual, reasoning); Eq. 4 predicts a win in 9/11; completions longer by lambda 0.96 (humanities) to 1.32 (qa); rounds and time disagree in: none. Over all categories T 0.92 · cross-node (`campaign/addendum/tables/speedbench__gpt-oss-20b.csv` row `spec_casc_tok`, category `all`).

**Token-budget pilot, qwen3-8b** (`campaign/addendum/tables/speedbench_pilot__qwen3-8b.csv`; strict at 8192 on each category's first 20 cases, >10% cap-outs would raise the category to 16384): reasoning 2/20 cap-outs of 20 (mean 2352, max 8192 tokens) -> budget 8192; math 0/4 cap-outs of 20 (mean 2448, max 2946 tokens) -> budget pending.

### qwen3-8b

Source: `campaign/addendum/tables/speedbench__qwen3-8b.csv`, one row per (method, category); Eq. 4 per (method, category): `campaign/addendum/tables/speedbench_eq4__qwen3-8b.csv`; per-method counts: `campaign/addendum/tables/speedbench_eq4_summary__qwen3-8b.csv`. Cell = lambda (completion tokens relaxed / strict) · R = verifier rounds ratio · T = wall-time ratio, all vs strict on the same cases; ↓/↑ = the 95% paired bootstrap interval lies entirely below/above 1. Strict column: mean completion tokens and cap-out rate. Where not every pair ran its arm and its strict case on one node (`same_node` False; README deviations 13-17), the cell adds T over the same-node pairs and their count (`time_ratio_same_node`, `same_node_pairs`), or 'cross-node' when fewer than 10 pairs share a node; R is hardware-independent.

| category | strict tokens (cap-out) | mentored_dec (0.75) | cactus (0.35) | spec_casc_opt (0.05) | r_fuzzy (0.25) | spec_casc_tok (0.8) |
|---|---:|---|---|---|---|---|
| all | 2332 (5%) | λ 1.07↑ · R 0.93↓ · T 1.02 (n=672) · T same-node 0.91 (249 pairs) | λ 1.35↑ · R 0.67↓ · T 0.68↓ (n=672) · cross-node | λ 1.40↑ · R 1.02 · T 1.13↑ (n=672) · T same-node 1.06 (93 pairs) | λ 1.20↑ · R 0.95↓ · T 0.96↓ (n=672) | λ 1.01 · R 0.95↓ · T 0.95↓ (n=672) · T same-node 0.95 (632 pairs) |
| coding | 5495 (24%) | λ 1.13↑ · R 0.98 · T 1.07↑ (n=80) · T same-node 0.97 (30 pairs) | λ 1.32↑ · R 0.70↓ · T 0.71↓ (n=80) · cross-node | λ 1.35↑ · R 1.05 · T 1.16↑ (n=80) · T same-node 1.03 (11 pairs) | λ 1.35↑ · R 1.09 · T 1.10↑ (n=80) | λ 1.03 · R 0.97 · T 0.97 (n=80) · T same-node 0.97 (75 pairs) |
| math | 2356 (0%) | λ 1.00 · R 0.88 · T 0.98 (n=18) · cross-node | λ 1.17 · R 0.80↓ · T 0.81↓ (n=18) · cross-node | λ 2.04↑ · R 1.47↑ · T 1.64↑ (n=18) · cross-node | λ 1.39↑ · R 1.10 · T 1.11 (n=18) | λ 0.94 · R 0.91 · T 0.91 (n=18) |
| humanities | 2127 (0%) | λ 1.08 · R 0.91 · T 1.01 (n=8) · cross-node | λ 1.71 · R 0.72 · T 0.74 (n=8) · cross-node | λ 1.72↑ · R 1.09 · T 1.19 (n=8) · cross-node | λ 1.12 · R 0.85 · T 0.86 (n=8) | λ 0.91↓ · R 0.88↓ · T 0.87↓ (n=8) · cross-node |
| stem | 2259 (0%) | λ 0.88 · R 0.77 · T 0.86 (n=6) · cross-node | λ 1.49↑ · R 0.70↓ · T 0.72↓ (n=6) · cross-node | λ 1.07 · R 0.87↓ · T 0.98 (n=6) · cross-node | λ 0.96 · R 0.76↓ · T 0.77↓ (n=6) | λ 0.85 · R 0.80↓ · T 0.80↓ (n=6) |
| writing | 3203 (1%) | λ 1.04 · R 0.91↓ · T 0.99 (n=80) · T same-node 0.88 (30 pairs) | λ 1.50↑ · R 0.59↓ · T 0.60↓ (n=80) · cross-node | λ 1.37↑ · R 0.97 · T 1.09 (n=80) · T same-node 1.10 (11 pairs) | λ 1.01 · R 0.78↓ · T 0.79↓ (n=80) | λ 1.01 · R 0.96 · T 0.96 (n=80) · T same-node 0.96 (75 pairs) |
| summarization | 660 (0%) | λ 0.94 · R 0.85↓ · T 0.91↓ (n=80) · T same-node 0.88 (31 pairs) | λ 1.26↑ · R 0.71↓ · T 0.73↓ (n=80) · cross-node | λ 0.99 · R 0.86↓ · T 0.93 (n=80) · T same-node 0.95 (11 pairs) | λ 0.96 · R 0.77↓ · T 0.78↓ (n=80) | λ 0.89↓ · R 0.86↓ · T 0.86↓ (n=80) · T same-node 0.86 (75 pairs) |
| roleplay | 713 (0%) | λ 1.11↑ · R 0.98 · T 1.08 (n=80) · T same-node 1.00 (30 pairs) | λ 2.02↑ · R 0.82 · T 0.84 (n=80) · cross-node | λ 1.47↑ · R 0.95 · T 1.07 (n=80) · T same-node 1.24 (12 pairs) | λ 1.25↑ · R 0.94 · T 0.95 (n=80) | λ 1.06 · R 1.02 · T 1.02 (n=80) · T same-node 1.02 (76 pairs) |
| rag | 1181 (0%) | λ 1.02 · R 0.89↓ · T 0.98 (n=80) · T same-node 0.86 (30 pairs) | λ 1.43↑ · R 0.74↓ · T 0.76↓ (n=80) · cross-node | λ 1.41↑ · R 1.03 · T 1.15 (n=80) · T same-node 1.17 (11 pairs) | λ 1.13 · R 0.89 · T 0.90 (n=80) | λ 0.98 · R 0.94 · T 0.94 (n=80) · T same-node 0.94 (75 pairs) |
| multilingual | 3004 (10%) | λ 1.00 · R 0.90 · T 0.98 (n=80) · T same-node 0.89 (31 pairs) | λ 1.20↑ · R 0.61↓ · T 0.63↓ (n=80) · cross-node | λ 1.57↑ · R 1.11 · T 1.23↑ (n=80) · T same-node 1.03 (11 pairs) | λ 1.17↑ · R 0.98 · T 0.99 (n=80) | λ 1.01 · R 0.97 · T 0.97 (n=80) · T same-node 0.96 (75 pairs) |
| reasoning | 2829 (10%) | λ 1.16↑ · R 1.00 · T 1.09 (n=80) · T same-node 0.91 (30 pairs) | λ 1.30↑ · R 0.68↓ · T 0.70↓ (n=80) · cross-node | λ 1.34↑ · R 0.96 · T 1.07 (n=80) · T same-node 1.13 (11 pairs) | λ 1.31↑ · R 1.01 · T 1.02 (n=80) | λ 1.02 · R 0.95 · T 0.95 (n=80) · T same-node 0.96 (75 pairs) |
| qa | 1594 (0%) | λ 1.02 · R 0.82↓ · T 0.89↓ (n=80) · T same-node 0.92 (30 pairs) | λ 1.19 · R 0.57↓ · T 0.58↓ (n=80) · cross-node | λ 1.29↑ · R 0.86↓ · T 0.96 (n=80) · T same-node 0.77 (11 pairs) | λ 1.02 · R 0.75↓ · T 0.76↓ (n=80) | λ 1.00 · R 0.89↓ · T 0.89↓ (n=80) · T same-node 0.89 (75 pairs) |

- **spec_casc_opt** (alpha 0.05, `campaign/addendum/tables/speedbench_eq4_summary__qwen3-8b.csv` row `spec_casc_opt`): fewer verifier rounds in 6/11 categories (stem, writing, summarization, roleplay, reasoning, qa); less wall time in 3/11 (stem, summarization, qa); Eq. 4 predicts a win in 4/11; completions longer by lambda 0.99 (summarization) to 2.04 (math); rounds and time disagree in: writing roleplay reasoning. Over all categories T 1.13 · T same-node 1.06 (93 pairs) (`campaign/addendum/tables/speedbench__qwen3-8b.csv` row `spec_casc_opt`, category `all`).
- **mentored_dec** (alpha 0.75, `campaign/addendum/tables/speedbench_eq4_summary__qwen3-8b.csv` row `mentored_dec`): fewer verifier rounds in 11/11 categories (coding, math, humanities, stem, writing, summarization, roleplay, rag, multilingual, reasoning, qa); less wall time in 7/11 (math, stem, writing, summarization, rag, multilingual, qa); Eq. 4 predicts a win in 10/11; completions longer by lambda 0.88 (stem) to 1.16 (reasoning); rounds and time disagree in: coding humanities roleplay reasoning. Over all categories T 1.02 · T same-node 0.91 (249 pairs) (`campaign/addendum/tables/speedbench__qwen3-8b.csv` row `mentored_dec`, category `all`).
- **cactus** (alpha 0.35, `campaign/addendum/tables/speedbench_eq4_summary__qwen3-8b.csv` row `cactus`): fewer verifier rounds in 11/11 categories (coding, math, humanities, stem, writing, summarization, roleplay, rag, multilingual, reasoning, qa); less wall time in 11/11 (coding, math, humanities, stem, writing, summarization, roleplay, rag, multilingual, reasoning, qa); Eq. 4 predicts a win in 11/11; completions longer by lambda 1.17 (math) to 2.02 (roleplay); rounds and time disagree in: none. Over all categories T 0.68 · cross-node (`campaign/addendum/tables/speedbench__qwen3-8b.csv` row `cactus`, category `all`).
- **r_fuzzy** (alpha 0.25, `campaign/addendum/tables/speedbench_eq4_summary__qwen3-8b.csv` row `r_fuzzy`): fewer verifier rounds in 8/11 categories (humanities, stem, writing, summarization, roleplay, rag, multilingual, qa); less wall time in 8/11 (humanities, stem, writing, summarization, roleplay, rag, multilingual, qa); Eq. 4 predicts a win in 7/11; completions longer by lambda 0.96 (summarization) to 1.39 (math); rounds and time disagree in: none.
- **spec_casc_tok** (alpha 0.8, `campaign/addendum/tables/speedbench_eq4_summary__qwen3-8b.csv` row `spec_casc_tok`): fewer verifier rounds in 10/11 categories (coding, math, humanities, stem, writing, summarization, rag, multilingual, reasoning, qa); less wall time in 10/11 (coding, math, humanities, stem, writing, summarization, rag, multilingual, reasoning, qa); Eq. 4 predicts a win in 10/11; completions longer by lambda 0.85 (stem) to 1.06 (roleplay); rounds and time disagree in: none. Over all categories T 0.95 · T same-node 0.95 (632 pairs) (`campaign/addendum/tables/speedbench__qwen3-8b.csv` row `spec_casc_tok`, category `all`).

## Step 8: more drafters, the Llama-3.1-8B family, the fix on Qwen3-8B

Seed 0, N_draft 6, T 1.0, top-p 1.0, the paper's budgets; one persistent server per arm (README deviation 30); every arm paired case by case with its own pair's lossless run. Ratios: lambda (completion tokens), R (draft rounds), T (wall time), relaxed / lossless, with 95% bootstrap intervals over cases (arrows: interval excludes 1). Accuracy: the campaign's graders (MT-Bench: none). `sampler_path`: V2 = vLLM's V2 runner, whose sampler is accept-test-only for cactus and spec_casc_tok; V1 = full patches. Block 0: `step8/BLOCK0.md`.

### Block 1: DeepSeek-R1-Distill-Llama-8B + EAGLE-3 (yuhuili), matched-l_bar protocol

GPU-h actual (lane journals): 34.0.

`campaign/addendum/tables/step8__r1-distill-llama-8b__eagle3.csv` -- deepseek-ai/DeepSeek-R1-Distill-Llama-8B + yuhuili/EAGLE3-DeepSeek-R1-Distill-LLaMA-8B (eagle3, V2 accept-test-only):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gsm8k_r1llama | mentored_dec | low | 0.15 | 150 | 3.27 (3.07) | 623 (623) | 1.00 [0.95, 1.06] | 0.94 [0.89, 1.00] | 0.93 · cross-node | 6% (7%) | 78% (77%) | kn173:147+kn175:3 |
| gsm8k_r1llama | mentored_dec | mid+high | 0.75 | 150 | 3.95 (3.07) | 691 (623) | 1.11 [1.05, 1.18]↑ | 0.87 [0.82, 0.93]↓ | 0.87 · cross-node | 12% (7%) | 69% (77%) | kn173:147+kn175:3 |
| gsm8k_r1llama | cactus | low | 0.03 | 150 | 3.62 (3.07) | 825 (623) | 1.32 [1.21, 1.46]↑ | 1.12 [1.01, 1.25]↑ | 1.09 | 17% (7%) | 62% (77%) | kn175 |
| gsm8k_r1llama | cactus | mid | 0.08 | 150 | 3.92 (3.07) | 889 (623) | 1.43 [1.30, 1.57]↑ | 1.11 [1.01, 1.24]↑ | 1.08 · cross-node | 21% (7%) | 60% (77%) | kn174:147+kn175:3 |
| gsm8k_r1llama | cactus | high | 0.35 | 150 | 4.52 (3.07) | 910 (623) | 1.46 [1.33, 1.61]↑ | 1.00 [0.90, 1.11] | 0.99 · cross-node | 21% (7%) | 55% (77%) | kn173:147+kn175:3 |
| gsm8k_r1llama | spec_casc_opt | low | -0.3 | 150 | 3.53 (3.07) | 667 (623) | 1.07 [1.00, 1.15]↑ | 0.94 [0.87, 1.01] | 0.94 · cross-node | 9% (7%) | 68% (77%) | kn173:147+kn175:3 |
| gsm8k_r1llama | spec_casc_opt | mid | -0.02 | 150 | 3.71 (3.07) | 704 (623) | 1.13 [1.04, 1.23]↑ | 0.94 [0.87, 1.02] | 0.92 | 13% (7%) | 66% (77%) | kn175 |
| gsm8k_r1llama | spec_casc_opt | high | 0.05 | 150 | 3.81 (3.07) | 693 (623) | 1.11 [1.04, 1.20]↑ | 0.89 [0.83, 0.97]↓ | 0.88 · cross-node | 13% (7%) | 68% (77%) | kn174:147+kn175:3 |
| gsm8k_r1llama | r_fuzzy | low | 0.08 | 150 | 3.32 (3.07) | 726 (623) | 1.17 [1.08, 1.26]↑ | 1.08 [0.99, 1.18] | 1.07 · cross-node | 12% (7%) | 62% (77%) | kn174:147+kn175:3 |
| gsm8k_r1llama | r_fuzzy | mid | 0.15 | 150 | 3.66 (3.07) | 822 (623) | 1.32 [1.21, 1.44]↑ | 1.09 [1.00, 1.20]↑ | 1.10 · cross-node | 17% (7%) | 58% (77%) | kn174:147+kn175:3 |
| gsm8k_r1llama | r_fuzzy | high | 0.25 | 150 | 4.16 (3.07) | 942 (623) | 1.51 [1.36, 1.69]↑ | 1.11 [1.00, 1.25] | 1.11 · cross-node | 27% (7%) | 47% (77%) | kn173:147+kn175:3 |
| gsm8k_r1llama | spec_casc_tok | low+mid+high | 0.8 | 150 | 3.50 (3.07) | 629 (623) | 1.01 [0.95, 1.07] | 0.90 [0.85, 0.96]↓ | 0.91 · cross-node | 7% (7%) | 75% (77%) | kn173:147+kn175:3 |
| gsm8k_r1llama | spec_casc_tok | extra | 0.15 | 150 | 3.11 (3.07) | 608 (623) | 0.98 [0.90, 1.06] | 0.97 [0.89, 1.07] | 0.95 | 5% (7%) | 77% (77%) | kn175 |
| livecodebench_r1llama | mentored_dec | low+mid+high | 0.75 | 90 | 0.87 (0.77) | 9499 (8882) | 1.07 [1.02, 1.13]↑ | 0.96 [0.90, 1.02] | 0.96 · cross-node | 39% (42%) | 43% (58%) | kn174:87+kn175:3 |
| livecodebench_r1llama | mentored_dec | extra | 0.15 | 90 | 0.78 (0.77) | 8795 (8882) | 0.99 [0.94, 1.04] | 0.97 [0.91, 1.03] | 0.97 · T same-node 0.92 (39 pairs) | 41% (42%) | 53% (58%) | kn173:87+kn175:3 |
| livecodebench_r1llama | cactus | low+mid | 0.03 | 90 | 2.28 (0.77) | 11200 (8882) | 1.26 [1.17, 1.37]↑ | 0.59 [0.53, 0.66]↓ | 0.59 · T same-node 0.57 (36 pairs) | 90% (42%) | 2% (58%) | kn175:72+kn174:18 |
| livecodebench_r1llama | cactus | high | 0.18 | 90 | 3.54 (0.77) | 11804 (8882) | 1.33 [1.23, 1.45]↑ | 0.44 [0.40, 0.49]↓ | 0.45 · T same-node 0.45 (54 pairs) | 98% (42%) | 2% (58%) | kn175 |
| livecodebench_r1llama | cactus | extra | 0.35 | 90 | 4.09 (0.77) | 11805 (8882) | 1.33 [1.23, 1.45]↑ | 0.39 [0.35, 0.44]↓ | 0.39 · T same-node 0.39 (42 pairs) | 98% (42%) | 0% (58%) | kn175:78+kn174:12 |
| livecodebench_r1llama | spec_casc_opt | low+mid+high | 0.05 | 90 | 1.33 (0.77) | 9160 (8882) | 1.03 [0.97, 1.10] | 0.72 [0.67, 0.78]↓ | 0.72 · T same-node 0.72 (18 pairs) | 30% (42%) | 38% (58%) | kn173:66+kn175:24 |
| livecodebench_r1llama | spec_casc_opt | extra | -0.3 | 90 | 0.85 (0.77) | 8861 (8882) | 1.00 [0.96, 1.04] | 0.94 [0.89, 0.99]↓ | 0.93 · T same-node 0.93 (39 pairs) | 37% (42%) | 58% (58%) | kn173:87+kn175:3 |
| livecodebench_r1llama | r_fuzzy | low+mid+high | 0.25 | 90 | 0.78 (0.77) | 9920 (8882) | 1.12 [1.07, 1.18]↑ | 1.00 [0.94, 1.07] | 1.00 · T same-node 0.94 (31 pairs) | 38% (42%) | 17% (58%) | kn175:67+kn174:23 |
| livecodebench_r1llama | r_fuzzy | extra | 0.03 | 90 | 0.71 (0.77) | 9194 (8882) | 1.04 [0.99, 1.09] | 1.03 [0.98, 1.10] | 1.02 · cross-node | 44% (42%) | 40% (58%) | kn174:87+kn175:3 |
| livecodebench_r1llama | spec_casc_tok | low+mid+high | 0.55 | 90 | 0.85 (0.77) | 8402 (8882) | 0.95 [0.90, 0.99]↓ | 0.92 [0.87, 0.98]↓ | 0.92 · T same-node 0.92 (25 pairs) | 38% (42%) | 59% (58%) | kn173:73+kn176:14+kn175:3 |
| livecodebench_r1llama | spec_casc_tok | extra | 0.15 | 90 | 0.83 (0.77) | 8517 (8882) | 0.96 [0.91, 1.01] | 0.95 [0.89, 1.01] | 0.95 · T same-node 0.97 (54 pairs) | 37% (42%) | 58% (58%) | kn175 |
| livecodebench_r1llama | spec_casc_tok | extra | 0.8 | 90 | 0.85 (0.77) | 8978 (8882) | 1.01 [0.97, 1.05] | 0.99 [0.94, 1.04] | 0.98 · T same-node 0.99 (54 pairs) | 47% (42%) | 49% (58%) | kn175 |
| mtbench_r1llama | mentored_dec | low | 0.35 | 80 | 2.51 (2.13) | 1534 (1384) | 1.11 [1.03, 1.20]↑ | 0.98 [0.89, 1.09] | 1.01 · cross-node | 14% (11%) | - (-) | kn175 |
| mtbench_r1llama | mentored_dec | mid+high | 0.75 | 80 | 3.02 (2.13) | 1504 (1384) | 1.09 [1.00, 1.19]↑ | 0.85 [0.75, 0.96]↓ | 0.87 · cross-node | 15% (11%) | - (-) | kn175 |
| mtbench_r1llama | mentored_dec | extra | 0.15 | 80 | 2.35 (2.13) | 1383 (1384) | 1.00 [0.90, 1.13] | 0.92 [0.80, 1.07] | 0.94 · cross-node | 10% (11%) | - (-) | kn173:77+kn175:3 |
| mtbench_r1llama | cactus | low | 0.03 | 80 | 3.09 (2.13) | 1756 (1384) | 1.27 [1.15, 1.43]↑ | 0.88 [0.78, 1.02] | 0.90 · cross-node | 22% (11%) | - (-) | kn175 |
| mtbench_r1llama | cactus | mid | 0.08 | 80 | 3.54 (2.13) | 1714 (1384) | 1.24 [1.12, 1.39]↑ | 0.76 [0.67, 0.88]↓ | 0.77 · cross-node | 22% (11%) | - (-) | kn175 |
| mtbench_r1llama | cactus | high | 0.35 | 80 | 4.37 (2.13) | 1820 (1384) | 1.31 [1.18, 1.48]↑ | 0.67 [0.58, 0.78]↓ | 0.68 · cross-node | 24% (11%) | - (-) | kn175 |
| mtbench_r1llama | spec_casc_opt | low | -0.1 | 80 | 2.64 (2.13) | 1496 (1384) | 1.08 [1.00, 1.18] | 0.90 [0.81, 1.01] | 0.93 · cross-node | 12% (11%) | - (-) | kn173:77+kn175:3 |
| mtbench_r1llama | spec_casc_opt | mid+high | 0.05 | 80 | 2.93 (2.13) | 1574 (1384) | 1.14 [1.02, 1.28]↑ | 0.89 [0.76, 1.05] | 0.90 · cross-node | 14% (11%) | - (-) | kn175 |
| mtbench_r1llama | spec_casc_opt | extra | -0.3 | 80 | 2.47 (2.13) | 1413 (1384) | 1.02 [0.93, 1.11] | 0.91 [0.81, 1.01] | 0.93 · cross-node | 11% (11%) | - (-) | kn175 |
| mtbench_r1llama | r_fuzzy | low+mid+high | 0.25 | 80 | 2.98 (2.13) | 2095 (1384) | 1.51 [1.33, 1.75]↑ | 1.18 [0.99, 1.42] | 1.22 · cross-node | 28% (11%) | - (-) | kn175 |
| mtbench_r1llama | r_fuzzy | extra | 0.03 | 80 | 2.13 (2.13) | 1526 (1384) | 1.10 [1.01, 1.22]↑ | 1.12 [1.00, 1.28] | 1.14 · cross-node | 14% (11%) | - (-) | kn173:77+kn175:3 |
| mtbench_r1llama | spec_casc_tok | low+mid+high | 0.8 | 80 | 2.51 (2.13) | 1297 (1384) | 0.94 [0.85, 1.02] | 0.82 [0.73, 0.90]↓ | 0.82 · cross-node | 8% (11%) | - (-) | kn175 |
| mtbench_r1llama | spec_casc_tok | extra | 0.15 | 80 | 2.10 (2.13) | 1480 (1384) | 1.07 [0.97, 1.19] | 1.05 [0.93, 1.20] | 1.07 · cross-node | 12% (11%) | - (-) | kn175 |
| aime24_r1llama | mentored_dec | low+mid+high | 0.35 | 30 | 0.88 (0.60) | 10869 (12527) | 0.87 [0.76, 0.99]↓ | 0.80 [0.67, 0.93]↓ | 0.79 · cross-node | 0% (0%) | 33% (27%) | kn175 |
| aime24_r1llama | mentored_dec | extra | 0.15 | 30 | 0.76 (0.60) | 11253 (12527) | 0.90 [0.80, 1.00] | 0.85 [0.73, 0.98]↓ | 0.85 · cross-node | 0% (0%) | 33% (27%) | kn175 |
| aime24_r1llama | mentored_dec | extra | 0.75 | 30 | 0.93 (0.60) | 9407 (12527) | 0.75 [0.68, 0.84]↓ | 0.58 [0.50, 0.66]↓ | 0.57 · T same-node 0.55 (27 pairs) | 0% (0%) | 30% (27%) | kn176:27+kn175:3 |
| aime24_r1llama | cactus | low+mid | 0.03 | 30 | 3.04 (0.60) | 30069 (12527) | 2.40 [2.08, 2.82]↑ | 0.85 [0.71, 1.04] | 0.89 · cross-node | 83% (0%) | 3% (27%) | kn173:27+kn175:3 |
| aime24_r1llama | cactus | high | 0.18 | 30 | 3.92 (0.60) | 32516 (12527) | 2.60 [2.29, 3.01]↑ | 0.75 [0.64, 0.92]↓ | 0.80 · cross-node | 97% (0%) | 0% (27%) | kn174:27+kn175:3 |
| aime24_r1llama | cactus | extra | 0.35 | 30 | 4.21 (0.60) | 32624 (12527) | 2.60 [2.29, 3.03]↑ | 0.71 [0.60, 0.87]↓ | 0.75 · cross-node | 97% (0%) | 3% (27%) | kn175 |
| aime24_r1llama | spec_casc_opt | low | -0.1 | 30 | 0.87 (0.60) | 11612 (12527) | 0.93 [0.80, 1.07] | 0.76 [0.63, 0.91]↓ | 0.76 · cross-node | 0% (0%) | 30% (27%) | kn175 |
| aime24_r1llama | spec_casc_opt | mid+high | 0.05 | 30 | 1.54 (0.60) | 16597 (12527) | 1.32 [1.05, 1.64]↑ | 0.72 [0.59, 0.88]↓ | 0.74 · cross-node | 17% (0%) | 13% (27%) | kn175 |
| aime24_r1llama | spec_casc_opt | extra | -0.3 | 30 | 0.75 (0.60) | 11780 (12527) | 0.94 [0.83, 1.08] | 0.87 [0.74, 1.04] | 0.87 · cross-node | 0% (0%) | 40% (27%) | kn175 |
| aime24_r1llama | r_fuzzy | low+mid+high | 0.03 | 30 | 0.83 (0.60) | 10551 (12527) | 0.84 [0.74, 0.95]↓ | 0.79 [0.66, 0.94]↓ | 0.79 · cross-node | 0% (0%) | 37% (27%) | kn175 |
| aime24_r1llama | r_fuzzy | extra | 0.25 | 30 | 0.75 (0.60) | 11792 (12527) | 0.94 [0.83, 1.07] | 0.82 [0.69, 0.98]↓ | 0.82 · T same-node 0.80 (27 pairs) | 0% (0%) | 27% (27%) | kn176:27+kn175:3 |
| aime24_r1llama | spec_casc_tok | low+mid+high | 0.55 | 30 | 0.73 (0.60) | 12009 (12527) | 0.96 [0.85, 1.07] | 0.94 [0.80, 1.09] | 0.96 · cross-node | 0% (0%) | 27% (27%) | kn173:27+kn175:3 |
| aime24_r1llama | spec_casc_tok | extra | 0.15 | 30 | 0.76 (0.60) | 11572 (12527) | 0.92 [0.78, 1.08] | 0.90 [0.72, 1.11] | 0.92 · cross-node | 0% (0%) | 33% (27%) | kn174:27+kn175:3 |
| aime24_r1llama | spec_casc_tok | extra | 0.8 | 30 | 0.96 (0.60) | 10770 (12527) | 0.86 [0.73, 0.99]↓ | 0.81 [0.65, 0.97]↓ | 0.80 · cross-node | 0% (0%) | 53% (27%) | kn175 |

### Block 2: Llama-3.1-8B-Instruct: EAGLE-3, EAGLE-1 (matched l_bar) and Llama-3.2-1B standalone (loosest)

GPU-h actual (lane journals): 32.9.

`campaign/addendum/tables/step8__llama31-8b-instruct__eagle3.csv` -- meta-llama/Llama-3.1-8B-Instruct + yuhuili/EAGLE3-LLaMA3.1-Instruct-8B (eagle3, V2 accept-test-only):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gsm8k_llama31 | mentored_dec | low | 0.35 | 150 | 2.56 (2.34) | 353 (290) | 1.22 [0.95, 1.55] | 1.17 [0.79, 1.72] | 1.15 · cross-node | 7% (3%) | 77% (81%) | kn176:147+kn175:3 |
| gsm8k_llama31 | mentored_dec | mid | 0.55 | 150 | 2.74 (2.34) | 300 (290) | 1.04 [0.82, 1.30] | 0.86 [0.61, 1.23] | 0.86 · cross-node | 4% (3%) | 81% (81%) | kn174:147+kn175:3 |
| gsm8k_llama31 | mentored_dec | high | 0.75 | 150 | 2.86 (2.34) | 461 (290) | 1.59 [1.22, 2.03]↑ | 1.25 [0.89, 1.80] | 1.21 | 12% (3%) | 69% (81%) | kn175 |
| gsm8k_llama31 | cactus | low+mid | 0.03 | 150 | 3.29 (2.34) | 1426 (290) | 4.92 [3.99, 6.09]↑ | 2.92 [2.15, 4.12]↑ | 2.81 | 66% (3%) | 30% (81%) | kn175 |
| gsm8k_llama31 | cactus | high | 0.18 | 150 | 4.21 (2.34) | 1588 (290) | 5.48 [4.47, 6.79]↑ | 2.67 [1.97, 3.78]↑ | 2.57 · cross-node | 75% (3%) | 16% (81%) | kn176:147+kn175:3 |
| gsm8k_llama31 | cactus | extra | 0.35 | 150 | 4.60 (2.34) | 1697 (290) | 5.86 [4.76, 7.21]↑ | 2.68 [1.97, 3.81]↑ | 2.78 · cross-node | 80% (3%) | 7% (81%) | kn176:147+kn175:3 |
| gsm8k_llama31 | spec_casc_opt | low | -0.1 | 150 | 2.62 (2.34) | 367 (290) | 1.27 [0.96, 1.63] | 1.19 [0.79, 1.78] | 1.18 · cross-node | 7% (3%) | 71% (81%) | kn174:147+kn175:3 |
| gsm8k_llama31 | spec_casc_opt | mid | -0.02 | 150 | 3.11 (2.34) | 392 (290) | 1.35 [1.07, 1.71]↑ | 0.77 [0.57, 1.07] | 0.77 | 6% (3%) | 57% (81%) | kn175 |
| gsm8k_llama31 | spec_casc_opt | high | 0.05 | 150 | 3.42 (2.34) | 458 (290) | 1.58 [1.25, 2.00]↑ | 0.82 [0.61, 1.15] | 0.82 | 9% (3%) | 48% (81%) | kn175 |
| gsm8k_llama31 | r_fuzzy | low | 0.15 | 150 | 1.77 (2.34) | 903 (290) | 3.12 [2.42, 3.91]↑ | 4.43 [3.15, 6.45]↑ | 4.26 | 35% (3%) | 37% (81%) | kn175 |
| gsm8k_llama31 | r_fuzzy | mid+high | 0.03 | 150 | 2.23 (2.34) | 350 (290) | 1.21 [0.93, 1.55] | 1.32 [0.88, 1.95] | 1.28 | 6% (3%) | 69% (81%) | kn175 |
| gsm8k_llama31 | r_fuzzy | extra | 0.25 | 150 | 1.38 (2.34) | 1509 (290) | 5.21 [4.27, 6.40]↑ | 7.58 [5.62, 10.72]↑ | 7.37 | 67% (3%) | 13% (81%) | kn175 |
| gsm8k_llama31 | spec_casc_tok | low | 0.15 | 150 | 2.41 (2.34) | 238 (290) | 0.82 [0.67, 1.02] | 0.67 [0.48, 0.99]↓ | 0.68 · cross-node | 1% (3%) | 81% (81%) | kn176:147+kn175:3 |
| gsm8k_llama31 | spec_casc_tok | mid+high | 0.8 | 150 | 2.69 (2.34) | 240 (290) | 0.83 [0.68, 1.01] | 0.63 [0.46, 0.89]↓ | 0.62 · cross-node | 1% (3%) | 83% (81%) | kn176:147+kn175:3 |
| livecodebench_llama31 | mentored_dec | low | 0.75 | 90 | 2.33 (2.05) | 1655 (770) | 2.15 [1.67, 2.69]↑ | 2.20 [1.51, 3.10]↑ | 2.12 · cross-node | 0% (0%) | 7% (14%) | kn175 |
| livecodebench_llama31 | mentored_dec | mid+high | 0.35 | 90 | 2.36 (2.05) | 794 (770) | 1.03 [0.83, 1.28] | 0.94 [0.63, 1.38] | 0.91 · cross-node | 0% (0%) | 14% (14%) | kn175 |
| livecodebench_llama31 | mentored_dec | extra | 0.15 | 90 | 2.15 (2.05) | 844 (770) | 1.10 [0.86, 1.38] | 1.14 [0.76, 1.69] | 1.09 · cross-node | 0% (0%) | 10% (14%) | kn175 |
| livecodebench_llama31 | cactus | low+mid | 0.03 | 90 | 3.89 (2.05) | 11001 (770) | 14.28 [12.09, 16.72]↑ | 7.54 [5.75, 10.02]↑ | 7.34 · cross-node | 82% (0%) | 2% (14%) | kn175 |
| livecodebench_llama31 | cactus | high | 0.08 | 90 | 4.30 (2.05) | 9835 (770) | 12.77 [10.85, 14.92]↑ | 6.21 [4.72, 8.24]↑ | 6.01 · T same-node 5.98 (87 pairs) | 57% (0%) | 0% (14%) | kn176:87+kn175:3 |
| livecodebench_llama31 | cactus | extra | 0.35 | 90 | 4.86 (2.05) | 9787 (770) | 12.71 [10.49, 15.10]↑ | 5.59 [4.11, 7.52]↑ | 5.46 · cross-node | 56% (0%) | 1% (14%) | kn175 |
| livecodebench_llama31 | spec_casc_opt | low | -0.3 | 90 | 2.05 (2.05) | 1178 (770) | 1.53 [1.17, 1.96]↑ | 1.88 [1.24, 2.78]↑ | 1.81 · cross-node | 0% (0%) | 12% (14%) | kn175 |
| livecodebench_llama31 | spec_casc_opt | mid | -0.02 | 90 | 3.40 (2.05) | 1795 (770) | 2.33 [1.80, 2.95]↑ | 1.29 [0.91, 1.80] | 1.24 · cross-node | 0% (0%) | 6% (14%) | kn175 |
| livecodebench_llama31 | spec_casc_opt | high | 0.05 | 90 | 3.75 (2.05) | 1991 (770) | 2.58 [1.95, 3.35]↑ | 1.55 [0.96, 2.51] | 1.63 · T same-node 1.65 (87 pairs) | 1% (0%) | 2% (14%) | kn176:87+kn175:3 |
| livecodebench_llama31 | r_fuzzy | low | 0.08 | 90 | 1.16 (2.05) | 2211 (770) | 2.87 [2.35, 3.49]↑ | 4.50 [3.30, 6.13]↑ | 4.37 · cross-node | 0% (0%) | 6% (14%) | kn174:87+kn175:3 |
| livecodebench_llama31 | r_fuzzy | mid+high | 0.03 | 90 | 1.65 (2.05) | 1292 (770) | 1.68 [1.36, 2.04]↑ | 2.24 [1.63, 3.09]↑ | 2.13 · cross-node | 0% (0%) | 10% (14%) | kn173:87+kn175:3 |
| livecodebench_llama31 | r_fuzzy | extra | 0.25 | 90 | 0.74 (2.05) | 3803 (770) | 4.94 [4.20, 5.77]↑ | 8.19 [6.19, 10.76]↑ | 8.39 · T same-node 8.30 (87 pairs) | 0% (0%) | 4% (14%) | kn176:87+kn175:3 |
| livecodebench_llama31 | spec_casc_tok | low | 0.35 | 90 | 2.25 (2.05) | 681 (770) | 0.88 [0.72, 1.09] | 0.77 [0.54, 1.10] | 0.73 · cross-node | 0% (0%) | 13% (14%) | kn175 |
| livecodebench_llama31 | spec_casc_tok | mid+high | 0.8 | 90 | 2.49 (2.05) | 666 (770) | 0.87 [0.73, 1.01] | 0.65 [0.49, 0.86]↓ | 0.64 · cross-node | 0% (0%) | 17% (14%) | kn175 |
| livecodebench_llama31 | spec_casc_tok | extra | 0.15 | 90 | 2.26 (2.05) | 656 (770) | 0.85 [0.73, 0.99]↓ | 0.69 [0.53, 0.91]↓ | 0.67 · cross-node | 0% (0%) | 18% (14%) | kn175 |
| mtbench_llama31 | mentored_dec | low | 0.15 | 80 | 2.16 (2.08) | 520 (472) | 1.10 [0.83, 1.42] | 1.08 [0.68, 1.61] | 1.09 · cross-node | 1% (1%) | - (-) | kn176:77+kn175:3 |
| mtbench_llama31 | mentored_dec | mid+high | 0.75 | 80 | 2.61 (2.08) | 805 (472) | 1.71 [1.26, 2.27]↑ | 1.59 [1.04, 2.40]↑ | 1.57 · cross-node | 9% (1%) | - (-) | kn174:77+kn175:3 |
| mtbench_llama31 | cactus | low+mid | 0.03 | 80 | 3.42 (2.08) | 2486 (472) | 5.27 [4.13, 6.60]↑ | 3.02 [2.07, 4.23]↑ | 2.94 | 56% (1%) | - (-) | kn175 |
| mtbench_llama31 | cactus | high | 0.18 | 80 | 4.15 (2.08) | 2027 (472) | 4.29 [3.25, 5.60]↑ | 2.12 [1.44, 3.07]↑ | 2.11 | 42% (1%) | - (-) | kn175 |
| mtbench_llama31 | cactus | extra | 0.35 | 80 | 4.49 (2.08) | 2079 (472) | 4.40 [3.44, 5.53]↑ | 2.04 [1.41, 2.90]↑ | 2.00 | 41% (1%) | - (-) | kn175 |
| mtbench_llama31 | spec_casc_opt | low | -0.3 | 80 | 2.29 (2.08) | 532 (472) | 1.13 [0.80, 1.56] | 1.14 [0.63, 1.92] | 1.12 | 2% (1%) | - (-) | kn175 |
| mtbench_llama31 | spec_casc_opt | mid+high | 0.05 | 80 | 3.40 (2.08) | 512 (472) | 1.08 [0.79, 1.49] | 0.61 [0.41, 0.88]↓ | 0.61 · cross-node | 2% (1%) | - (-) | kn173:77+kn175:3 |
| mtbench_llama31 | r_fuzzy | low+mid+high | 0.15 | 80 | 1.49 (2.08) | 1760 (472) | 3.73 [2.87, 4.75]↑ | 6.01 [4.14, 8.62]↑ | 6.44 · cross-node | 22% (1%) | - (-) | kn176:77+kn175:3 |
| mtbench_llama31 | r_fuzzy | extra | 0.03 | 80 | 1.87 (2.08) | 715 (472) | 1.51 [1.07, 2.05]↑ | 1.95 [1.15, 3.06]↑ | 1.97 · cross-node | 5% (1%) | - (-) | kn176:77+kn175:3 |
| mtbench_llama31 | r_fuzzy | extra | 0.25 | 80 | 1.37 (2.08) | 2371 (472) | 5.02 [3.97, 6.26]↑ | 7.89 [5.44, 11.10]↑ | 7.81 · cross-node | 31% (1%) | - (-) | kn174:77+kn175:3 |
| mtbench_llama31 | spec_casc_tok | low | 0.55 | 80 | 2.20 (2.08) | 410 (472) | 0.87 [0.69, 1.04] | 0.74 [0.51, 1.01] | 0.74 · T same-node 0.72 (77 pairs) | 0% (1%) | - (-) | kn175:77+kn174:3 |
| mtbench_llama31 | spec_casc_tok | mid+high | 0.8 | 80 | 2.43 (2.08) | 397 (472) | 0.84 [0.68, 1.00] | 0.67 [0.46, 0.89]↓ | 0.67 | 0% (1%) | - (-) | kn175 |
| mtbench_llama31 | spec_casc_tok | extra | 0.15 | 80 | 2.07 (2.08) | 422 (472) | 0.89 [0.72, 1.06] | 0.83 [0.57, 1.10] | 0.82 | 0% (1%) | - (-) | kn175 |

`campaign/addendum/tables/step8__llama31-8b-instruct__eagle1.csv` -- meta-llama/Llama-3.1-8B-Instruct + yuhuili/EAGLE-LLaMA3.1-Instruct-8B (eagle1, V2 accept-test-only):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gsm8k_llama31 | mentored_dec | low | 0.55 | 150 | 1.81 (1.57) | 348 (279) | 1.25 [0.99, 1.55] | 1.14 [0.85, 1.51] | 1.15 · cross-node | 3% (3%) | 78% (79%) | kn174:147+kn175:3 |
| gsm8k_llama31 | mentored_dec | mid+high | 0.75 | 150 | 1.92 (1.57) | 455 (279) | 1.63 [1.27, 2.06]↑ | 1.39 [1.03, 1.85]↑ | 1.40 · T same-node 1.15 (17 pairs) | 7% (3%) | 72% (79%) | kn176:147+kn175:3 |
| gsm8k_llama31 | mentored_dec | extra | 0.15 | 150 | 1.66 (1.57) | 304 (279) | 1.09 [0.87, 1.34] | 1.07 [0.79, 1.42] | 1.07 · T same-node 1.09 (136 pairs) | 4% (3%) | 81% (79%) | kn175 |
| gsm8k_llama31 | cactus | low | 0.03 | 150 | 2.37 (1.57) | 1255 (279) | 4.50 [3.62, 5.50]↑ | 2.88 [2.24, 3.71]↑ | 2.85 · T same-node 2.83 (136 pairs) | 54% (3%) | 29% (79%) | kn175 |
| gsm8k_llama31 | cactus | mid | 0.08 | 150 | 2.66 (1.57) | 1448 (279) | 5.19 [4.27, 6.24]↑ | 3.11 [2.44, 3.95]↑ | 3.07 · T same-node 2.98 (133 pairs) | 65% (3%) | 19% (79%) | kn175:147+kn174:3 |
| gsm8k_llama31 | cactus | high | 0.35 | 150 | 3.29 (1.57) | 1632 (279) | 5.84 [4.86, 7.00]↑ | 3.08 [2.46, 3.92]↑ | 3.07 · cross-node | 74% (3%) | 6% (79%) | kn173:147+kn175:3 |
| gsm8k_llama31 | spec_casc_opt | low | -0.3 | 150 | 1.81 (1.57) | 298 (279) | 1.07 [0.84, 1.35] | 0.96 [0.70, 1.30] | 1.01 · T same-node 0.97 (17 pairs) | 3% (3%) | 75% (79%) | kn176:147+kn175:3 |
| gsm8k_llama31 | spec_casc_opt | mid | 0.05 | 150 | 3.09 (1.57) | 801 (279) | 2.87 [2.27, 3.59]↑ | 1.35 [1.03, 1.76]↑ | 1.43 · T same-node 2.13 (17 pairs) | 29% (3%) | 35% (79%) | kn176:147+kn175:3 |
| gsm8k_llama31 | spec_casc_opt | high | -0.02 | 150 | 2.55 (1.57) | 571 (279) | 2.05 [1.56, 2.63]↑ | 1.11 [0.85, 1.45] | 1.12 · cross-node | 17% (3%) | 53% (79%) | kn174:147+kn175:3 |
| gsm8k_llama31 | r_fuzzy | low | 0.15 | 150 | 1.41 (1.57) | 674 (279) | 2.41 [1.89, 3.04]↑ | 2.88 [2.12, 3.84]↑ | 2.85 · T same-node 2.86 (17 pairs) | 21% (3%) | 51% (79%) | kn176:147+kn175:3 |
| gsm8k_llama31 | r_fuzzy | mid+high | 0.25 | 150 | 1.79 (1.57) | 1003 (279) | 3.59 [2.90, 4.46]↑ | 3.18 [2.46, 4.17]↑ | 3.14 · T same-node 2.95 (136 pairs) | 27% (3%) | 26% (79%) | kn175 |
| gsm8k_llama31 | r_fuzzy | extra | 0.03 | 150 | 1.54 (1.57) | 304 (279) | 1.09 [0.85, 1.39] | 1.13 [0.81, 1.56] | 1.13 · T same-node 1.07 (136 pairs) | 3% (3%) | 82% (79%) | kn175 |
| gsm8k_llama31 | spec_casc_tok | low | 0.55 | 150 | 1.76 (1.57) | 239 (279) | 0.86 [0.70, 1.05] | 0.76 [0.58, 1.01] | 0.77 · T same-node 0.75 (133 pairs) | 1% (3%) | 85% (79%) | kn175:147+kn174:3 |
| gsm8k_llama31 | spec_casc_tok | mid+high | 0.8 | 150 | 1.81 (1.57) | 240 (279) | 0.86 [0.70, 1.05] | 0.73 [0.57, 0.96]↓ | 0.74 · cross-node | 1% (3%) | 79% (79%) | kn173:147+kn175:3 |
| gsm8k_llama31 | spec_casc_tok | extra | 0.15 | 150 | 1.65 (1.57) | 272 (279) | 0.97 [0.76, 1.24] | 0.94 [0.67, 1.30] | 0.99 · T same-node 1.68 (17 pairs) | 3% (3%) | 81% (79%) | kn176:147+kn175:3 |
| livecodebench_llama31 | mentored_dec | low | 0.35 | 90 | 1.55 (1.42) | 837 (830) | 1.01 [0.81, 1.24] | 0.93 [0.71, 1.22] | 0.93 · T same-node 1.02 (87 pairs) | 0% (0%) | 18% (19%) | kn176:87+kn175:3 |
| livecodebench_llama31 | mentored_dec | mid+high | 0.75 | 90 | 1.96 (1.42) | 2850 (830) | 3.43 [2.51, 4.57]↑ | 2.59 [1.83, 3.62]↑ | 2.89 · T same-node 3.22 (87 pairs) | 4% (0%) | 10% (19%) | kn176:87+kn175:3 |
| livecodebench_llama31 | mentored_dec | extra | 0.15 | 90 | 1.47 (1.42) | 880 (830) | 1.06 [0.83, 1.36] | 1.03 [0.75, 1.42] | 1.04 · cross-node | 0% (0%) | 19% (19%) | kn175:87+kn173:3 |
| livecodebench_llama31 | cactus | low | 0.08 | 90 | 2.85 (1.42) | 5573 (830) | 6.71 [5.30, 8.48]↑ | 3.96 [2.96, 5.38]↑ | 4.04 · cross-node | 20% (0%) | 0% (19%) | kn174:87+kn175:3 |
| livecodebench_llama31 | cactus | mid | 0.03 | 90 | 2.59 (1.42) | 7219 (830) | 8.69 [6.86, 11.05]↑ | 5.43 [4.08, 7.24]↑ | 5.49 · cross-node | 37% (0%) | 0% (19%) | kn175 |
| livecodebench_llama31 | cactus | high | 0.35 | 90 | 3.98 (1.42) | 3360 (830) | 4.05 [2.95, 5.49]↑ | 1.80 [1.26, 2.58]↑ | 2.05 · T same-node 2.27 (87 pairs) | 10% (0%) | 0% (19%) | kn176:87+kn175:3 |
| livecodebench_llama31 | spec_casc_opt | low | -0.3 | 90 | 1.62 (1.42) | 937 (830) | 1.13 [0.82, 1.62] | 0.89 [0.66, 1.22] | 0.89 · cross-node | 1% (0%) | 10% (19%) | kn173 |
| livecodebench_llama31 | spec_casc_opt | mid+high | 0.05 | 90 | 2.94 (1.42) | 2925 (830) | 3.52 [2.55, 4.77]↑ | 1.68 [1.22, 2.33]↑ | 1.70 · T same-node 1.88 (87 pairs) | 10% (0%) | 2% (19%) | kn176:87+kn175:3 |
| livecodebench_llama31 | r_fuzzy | low+mid+high | 0.15 | 90 | 0.95 (1.42) | 3205 (830) | 3.86 [2.96, 4.97]↑ | 4.81 [3.53, 6.58]↑ | 5.39 · T same-node 5.94 (87 pairs) | 2% (0%) | 1% (19%) | kn176:87+kn174:3 |
| livecodebench_llama31 | r_fuzzy | extra | 0.03 | 90 | 1.36 (1.42) | 979 (830) | 1.18 [0.94, 1.48] | 1.22 [0.91, 1.63] | 1.22 · cross-node | 0% (0%) | 11% (19%) | kn175 |
| livecodebench_llama31 | r_fuzzy | extra | 0.25 | 90 | 1.43 (1.42) | 5300 (830) | 6.38 [4.90, 8.21]↑ | 5.72 [4.24, 7.80]↑ | 5.75 · cross-node | 12% (0%) | 2% (19%) | kn175 |
| livecodebench_llama31 | spec_casc_tok | low | 0.35 | 90 | 1.57 (1.42) | 666 (830) | 0.80 [0.65, 1.00]↓ | 0.69 [0.54, 0.91]↓ | 0.70 · cross-node | 0% (0%) | 11% (19%) | kn174:87+kn175:3 |
| livecodebench_llama31 | spec_casc_tok | mid+high | 0.15 | 90 | 1.54 (1.42) | 652 (830) | 0.78 [0.65, 0.95]↓ | 0.69 [0.54, 0.89]↓ | 0.70 · cross-node | 0% (0%) | 17% (19%) | kn175:87+kn173:3 |
| livecodebench_llama31 | spec_casc_tok | extra | 0.8 | 90 | 1.67 (1.42) | 638 (830) | 0.77 [0.62, 0.95]↓ | 0.64 [0.49, 0.83]↓ | 0.70 · T same-node 0.77 (87 pairs) | 0% (0%) | 14% (19%) | kn176:87+kn174:3 |
| mtbench_llama31 | mentored_dec | low+mid+high | 0.75 | 80 | 1.77 (1.32) | 996 (468) | 2.13 [1.63, 2.71]↑ | 1.79 [1.33, 2.35]↑ | 1.81 · cross-node | 10% (1%) | - (-) | kn174:77+kn175:3 |
| mtbench_llama31 | mentored_dec | extra | 0.15 | 80 | 1.35 (1.32) | 542 (468) | 1.16 [0.97, 1.40] | 1.19 [0.96, 1.51] | 1.21 · cross-node | 0% (1%) | - (-) | kn175 |
| mtbench_llama31 | cactus | low+mid | 0.03 | 80 | 2.63 (1.32) | 2692 (468) | 5.75 [4.58, 7.10]↑ | 3.35 [2.55, 4.27]↑ | 3.78 · T same-node 3.96 (77 pairs) | 57% (1%) | - (-) | kn176:77+kn173:3 |
| mtbench_llama31 | cactus | high | 0.08 | 80 | 2.78 (1.32) | 2620 (468) | 5.60 [4.43, 6.96]↑ | 3.22 [2.44, 4.13]↑ | 3.20 · cross-node | 55% (1%) | - (-) | kn173:77+kn175:3 |
| mtbench_llama31 | cactus | extra | 0.35 | 80 | 3.45 (1.32) | 2312 (468) | 4.94 [3.76, 6.31]↑ | 2.46 [1.79, 3.27]↑ | 2.46 · T same-node 2.55 (77 pairs) | 40% (1%) | - (-) | kn176:77+kn174:3 |
| mtbench_llama31 | spec_casc_opt | low | -0.3 | 80 | 1.49 (1.32) | 558 (468) | 1.19 [0.95, 1.53] | 1.09 [0.88, 1.39] | 1.10 · cross-node | 1% (1%) | - (-) | kn174:77+kn175:3 |
| mtbench_llama31 | spec_casc_opt | mid | -0.1 | 80 | 1.95 (1.32) | 600 (468) | 1.28 [1.02, 1.64]↑ | 0.87 [0.73, 1.06] | 0.91 · T same-node 0.93 (77 pairs) | 4% (1%) | - (-) | kn176:77+kn175:3 |
| mtbench_llama31 | spec_casc_opt | high | 0.05 | 80 | 2.81 (1.32) | 881 (468) | 1.88 [1.28, 2.61]↑ | 0.93 [0.64, 1.29] | 0.93 · cross-node | 8% (1%) | - (-) | kn175 |
| mtbench_llama31 | r_fuzzy | low+mid+high | 0.25 | 80 | 1.57 (1.32) | 2033 (468) | 4.35 [3.27, 5.43]↑ | 4.01 [2.91, 5.15]↑ | 4.06 · cross-node | 36% (1%) | - (-) | kn175:77+kn174:3 |
| mtbench_llama31 | r_fuzzy | extra | 0.03 | 80 | 1.29 (1.32) | 436 (468) | 0.93 [0.72, 1.15] | 0.94 [0.69, 1.22] | 1.00 · T same-node 1.01 (77 pairs) | 0% (1%) | - (-) | kn176:77+kn173:3 |
| mtbench_llama31 | spec_casc_tok | low+mid+high | 0.35 | 80 | 1.39 (1.32) | 386 (468) | 0.83 [0.67, 0.96]↓ | 0.78 [0.61, 0.94]↓ | 0.79 · cross-node | 0% (1%) | - (-) | kn175 |
| mtbench_llama31 | spec_casc_tok | extra | 0.15 | 80 | 1.34 (1.32) | 402 (468) | 0.86 [0.70, 1.00]↓ | 0.84 [0.65, 1.00]↓ | 0.84 · cross-node | 0% (1%) | - (-) | kn173:77+kn175:3 |
| mtbench_llama31 | spec_casc_tok | extra | 0.8 | 80 | 1.49 (1.32) | 410 (468) | 0.88 [0.71, 1.03] | 0.79 [0.61, 0.96]↓ | 0.80 · T same-node 0.79 (77 pairs) | 0% (1%) | - (-) | kn176:77+kn175:3 |

`campaign/addendum/tables/step8__llama31-8b-instruct__llama32-1b.csv` -- meta-llama/Llama-3.1-8B-Instruct + meta-llama/Llama-3.2-1B-Instruct (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gsm8k_llama31 | mentored_dec | loosest | 0.75 | 150 | 5.17 (4.04) | 230 (269) | 0.86 [0.72, 1.03] | 0.68 [0.57, 0.81]↓ | 0.66 · cross-node | 0% (1%) | 75% (78%) | kn174 |
| gsm8k_llama31 | cactus | loosest | 0.35 | 150 | 5.46 (4.04) | 388 (269) | 1.44 [1.13, 1.82]↑ | 1.06 [0.83, 1.32] | 1.03 · cross-node | 7% (1%) | 60% (78%) | kn175 |
| gsm8k_llama31 | spec_casc_opt | loosest | 0.05 | 150 | 4.86 (4.04) | 218 (269) | 0.81 [0.69, 0.93]↓ | 0.68 [0.58, 0.79]↓ | 0.67 · cross-node | 0% (1%) | 72% (78%) | kn175 |
| gsm8k_llama31 | r_fuzzy | loosest | 0.25 | 150 | 5.46 (4.04) | 313 (269) | 1.17 [0.92, 1.47] | 0.86 [0.68, 1.08] | 0.84 · cross-node | 3% (1%) | 61% (78%) | kn176 |
| gsm8k_llama31 | spec_casc_tok | loosest | 0.8 | 150 | 4.51 (4.04) | 222 (269) | 0.83 [0.74, 0.93]↓ | 0.74 [0.66, 0.84]↓ | 0.73 · cross-node | 0% (1%) | 86% (78%) | kn176 |
| livecodebench_llama31 | mentored_dec | loosest | 0.75 | 90 | 5.05 (3.48) | 769 (764) | 1.01 [0.77, 1.28] | 0.74 [0.58, 0.92]↓ | 0.73 · cross-node | 0% (0%) | 7% (16%) | kn174 |
| livecodebench_llama31 | cactus | loosest | 0.35 | 90 | 5.48 (3.48) | 1135 (764) | 1.49 [1.06, 2.04]↑ | 1.01 [0.74, 1.35] | 1.00 · cross-node | 0% (0%) | 1% (16%) | kn175 |
| livecodebench_llama31 | spec_casc_opt | loosest | 0.05 | 90 | 4.72 (3.48) | 692 (764) | 0.91 [0.71, 1.12] | 0.71 [0.56, 0.86]↓ | 0.71 · cross-node | 0% (0%) | 13% (16%) | kn175 |
| livecodebench_llama31 | r_fuzzy | loosest | 0.25 | 90 | 5.48 (3.48) | 1043 (764) | 1.37 [1.05, 1.74]↑ | 0.93 [0.73, 1.16] | 0.92 · cross-node | 0% (0%) | 1% (16%) | kn176 |
| livecodebench_llama31 | spec_casc_tok | loosest | 0.8 | 90 | 4.13 (3.48) | 601 (764) | 0.79 [0.62, 0.94]↓ | 0.69 [0.56, 0.82]↓ | 0.69 · cross-node | 0% (0%) | 22% (16%) | kn176 |

### Block 3: Qwen3-8B: DSpark (matched l_bar) and Qwen3-1.7B standalone (loosest)

GPU-h actual (lane journals): 25.2.

`campaign/addendum/tables/step8__qwen3-8b__dspark.csv` -- Qwen/Qwen3-8B + deepseek-ai/dspark_qwen3_8b_block7 (dspark, V2 accept-test-only):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gsm8k_qwen3 | mentored_dec | low | 0.35 | 150 | 3.05 (2.77) | 1247 (1335) | 0.93 [0.90, 0.97]↓ | 0.86 [0.83, 0.90]↓ | 0.85 · T same-node 0.85 (147 pairs) | 26% (30%) | 79% (75%) | kn173:147+kn174:3 |
| gsm8k_qwen3 | mentored_dec | mid+high | 0.75 | 150 | 3.37 (2.77) | 1259 (1335) | 0.94 [0.90, 0.98]↓ | 0.80 [0.76, 0.83]↓ | 0.79 · cross-node | 22% (30%) | 81% (75%) | kn176:147+kn175:3 |
| gsm8k_qwen3 | mentored_dec | extra | 0.15 | 150 | 2.92 (2.77) | 1247 (1335) | 0.93 [0.90, 0.97]↓ | 0.89 [0.86, 0.93]↓ | 0.94 · cross-node | 21% (30%) | 83% (75%) | kn176:147+kn175:3 |
| gsm8k_qwen3 | cactus | low | 0.03 | 150 | 3.01 (2.77) | 1302 (1335) | 0.98 [0.94, 1.01] | 0.91 [0.87, 0.94]↓ | 0.89 · cross-node | 24% (30%) | 82% (75%) | kn175:147+kn173:3 |
| gsm8k_qwen3 | cactus | mid+high | 0.35 | 150 | 3.40 (2.77) | 1248 (1335) | 0.93 [0.90, 0.97]↓ | 0.78 [0.75, 0.81]↓ | 0.76 · cross-node | 25% (30%) | 79% (75%) | kn175:147+kn174:3 |
| gsm8k_qwen3 | spec_casc_opt | low | -0.3 | 150 | 3.17 (2.77) | 1296 (1335) | 0.97 [0.93, 1.01] | 0.87 [0.83, 0.91]↓ | 0.87 · cross-node | 26% (30%) | 80% (75%) | kn174:147+kn173:3 |
| gsm8k_qwen3 | spec_casc_opt | mid | -0.1 | 150 | 3.41 (2.77) | 1280 (1335) | 0.96 [0.92, 1.00]↓ | 0.80 [0.77, 0.84]↓ | 0.81 · cross-node | 25% (30%) | 78% (75%) | kn175:147+kn174:3 |
| gsm8k_qwen3 | spec_casc_opt | high | 0.05 | 150 | 3.92 (2.77) | 1473 (1335) | 1.10 [1.06, 1.16]↑ | 0.83 [0.79, 0.87]↓ | 0.89 · cross-node | 41% (30%) | 64% (75%) | kn176:147+kn175:3 |
| gsm8k_qwen3 | r_fuzzy | low | 0.08 | 150 | 3.00 (2.77) | 1302 (1335) | 0.98 [0.93, 1.01] | 0.92 [0.88, 0.96]↓ | 0.90 · T same-node 0.90 (147 pairs) | 26% (30%) | 77% (75%) | kn173:147+kn175:3 |
| gsm8k_qwen3 | r_fuzzy | mid+high | 0.25 | 150 | 3.54 (2.77) | 1394 (1335) | 1.04 [1.00, 1.09] | 0.86 [0.82, 0.90]↓ | 0.83 · cross-node | 37% (30%) | 69% (75%) | kn176:147+kn174:3 |
| gsm8k_qwen3 | r_fuzzy | extra | 0.03 | 150 | 2.87 (2.77) | 1289 (1335) | 0.97 [0.93, 1.00]↓ | 0.95 [0.91, 0.98]↓ | 1.00 · cross-node | 25% (30%) | 81% (75%) | kn176:147+kn173:3 |
| gsm8k_qwen3 | spec_casc_tok | low+mid+high | 0.8 | 150 | 3.15 (2.77) | 1216 (1335) | 0.91 [0.87, 0.95]↓ | 0.82 [0.78, 0.86]↓ | 0.80 · cross-node | 23% (30%) | 83% (75%) | kn175 |
| gsm8k_qwen3 | spec_casc_tok | extra | 0.15 | 150 | 2.88 (2.77) | 1244 (1335) | 0.93 [0.89, 0.97]↓ | 0.90 [0.86, 0.94]↓ | 0.88 · cross-node | 21% (30%) | 82% (75%) | kn175:147+kn173:3 |
| livecodebench_qwen3 | mentored_dec | low | 0.35 | 90 | 2.65 (2.31) | 8079 (8063) | 1.00 [0.96, 1.04] | 0.89 [0.86, 0.93]↓ | 0.92 · cross-node | 28% (27%) | 72% (74%) | kn174 |
| livecodebench_qwen3 | mentored_dec | mid+high | 0.55 | 90 | 2.86 (2.31) | 8222 (8063) | 1.02 [0.98, 1.06] | 0.86 [0.83, 0.89]↓ | 0.88 · cross-node | 34% (27%) | 66% (74%) | kn173 |
| livecodebench_qwen3 | mentored_dec | extra | 0.15 | 90 | 2.47 (2.31) | 8012 (8063) | 0.99 [0.96, 1.03] | 0.94 [0.91, 0.98]↓ | 1.06 · cross-node | 28% (27%) | 73% (74%) | kn176:87+kn175:3 |
| livecodebench_qwen3 | cactus | low+mid+high | 0.08 | 90 | 2.77 (2.31) | 8238 (8063) | 1.02 [0.98, 1.07] | 0.88 [0.84, 0.92]↓ | 0.93 · cross-node | 34% (27%) | 68% (74%) | kn176:87+kn173:3 |
| livecodebench_qwen3 | cactus | extra | 0.03 | 90 | 2.61 (2.31) | 8395 (8063) | 1.04 [1.00, 1.08]↑ | 0.94 [0.91, 0.98]↓ | 0.95 · T same-node 0.95 (87 pairs) | 38% (27%) | 64% (74%) | kn175:87+kn174:3 |
| livecodebench_qwen3 | cactus | extra | 0.35 | 90 | 3.17 (2.31) | 8612 (8063) | 1.07 [1.02, 1.12]↑ | 0.82 [0.79, 0.86]↓ | 0.83 | 43% (27%) | 54% (74%) | kn175 |
| livecodebench_qwen3 | spec_casc_opt | low+mid+high | -0.3 | 90 | 2.80 (2.31) | 8406 (8063) | 1.04 [1.00, 1.08]↑ | 0.89 [0.86, 0.93]↓ | 0.90 · T same-node 0.90 (87 pairs) | 40% (27%) | 62% (74%) | kn175:87+kn174:3 |
| livecodebench_qwen3 | spec_casc_opt | extra | 0.05 | 90 | 3.62 (2.31) | 10054 (8063) | 1.25 [1.18, 1.32]↑ | 0.88 [0.83, 0.93]↓ | 0.89 · cross-node | 64% (27%) | 30% (74%) | kn176:87+kn174:3 |
| livecodebench_qwen3 | r_fuzzy | low+mid+high | 0.15 | 90 | 2.82 (2.31) | 8610 (8063) | 1.07 [1.01, 1.13]↑ | 0.93 [0.87, 0.98]↓ | 0.94 · T same-node 0.93 (77 pairs) | 43% (27%) | 41% (74%) | kn175:77+kn174:13 |
| livecodebench_qwen3 | r_fuzzy | extra | 0.03 | 90 | 2.43 (2.31) | 7846 (8063) | 0.97 [0.92, 1.02] | 0.96 [0.90, 1.00] | 0.98 · cross-node | 27% (27%) | 61% (74%) | kn173:87+kn174:3 |
| livecodebench_qwen3 | r_fuzzy | extra | 0.25 | 90 | 3.24 (2.31) | 8957 (8063) | 1.11 [1.04, 1.18]↑ | 0.87 [0.81, 0.92]↓ | 0.98 · cross-node | 50% (27%) | 32% (74%) | kn176:87+kn175:3 |
| livecodebench_qwen3 | spec_casc_tok | low+mid+high | 0.8 | 90 | 2.79 (2.31) | 8156 (8063) | 1.01 [0.97, 1.06] | 0.87 [0.83, 0.91]↓ | 0.87 · cross-node | 32% (27%) | 68% (74%) | kn176:87+kn174:3 |
| livecodebench_qwen3 | spec_casc_tok | extra | 0.15 | 90 | 2.43 (2.31) | 8164 (8063) | 1.01 [0.97, 1.06] | 0.97 [0.93, 1.02] | 0.98 · T same-node 0.98 (87 pairs) | 34% (27%) | 68% (74%) | kn175:87+kn174:3 |
| mtbench_qwen3 | mentored_dec | low | 0.55 | 80 | 2.66 (2.12) | 2115 (2133) | 0.99 [0.93, 1.05] | 0.84 [0.79, 0.89]↓ | 0.86 · cross-node | 21% (20%) | - (-) | kn175:77+kn174:3 |
| mtbench_qwen3 | mentored_dec | mid+high | 0.75 | 80 | 2.99 (2.12) | 2159 (2133) | 1.01 [0.95, 1.07] | 0.79 [0.75, 0.84]↓ | 0.81 · cross-node | 16% (20%) | - (-) | kn175 |
| mtbench_qwen3 | mentored_dec | extra | 0.15 | 80 | 2.28 (2.12) | 2015 (2133) | 0.94 [0.90, 0.99]↓ | 0.90 [0.86, 0.95]↓ | 0.92 · T same-node 0.92 (77 pairs) | 14% (20%) | - (-) | kn176:77+kn173:3 |
| mtbench_qwen3 | cactus | low | 0.08 | 80 | 2.69 (2.12) | 2168 (2133) | 1.02 [0.94, 1.09] | 0.86 [0.80, 0.91]↓ | 0.87 · cross-node | 21% (20%) | - (-) | kn175 |
| mtbench_qwen3 | cactus | mid+high | 0.35 | 80 | 3.16 (2.12) | 2257 (2133) | 1.06 [0.98, 1.14] | 0.79 [0.73, 0.84]↓ | 0.79 · cross-node | 21% (20%) | - (-) | kn175:77+kn174:3 |
| mtbench_qwen3 | cactus | extra | 0.03 | 80 | 2.49 (2.12) | 2135 (2133) | 1.00 [0.92, 1.07] | 0.90 [0.83, 0.96]↓ | 0.92 · T same-node 0.92 (77 pairs) | 20% (20%) | - (-) | kn176:77+kn173:3 |
| mtbench_qwen3 | spec_casc_opt | low | -0.3 | 80 | 2.72 (2.12) | 2172 (2133) | 1.02 [0.95, 1.09] | 0.86 [0.80, 0.91]↓ | 0.86 · cross-node | 20% (20%) | - (-) | kn175:77+kn173:3 |
| mtbench_qwen3 | spec_casc_opt | mid | -0.1 | 80 | 3.10 (2.12) | 2205 (2133) | 1.03 [0.98, 1.09] | 0.78 [0.74, 0.82]↓ | 0.78 · cross-node | 22% (20%) | - (-) | kn175:77+kn174:3 |
| mtbench_qwen3 | spec_casc_opt | high | 0.05 | 80 | 3.67 (2.12) | 2464 (2133) | 1.16 [1.07, 1.25]↑ | 0.77 [0.72, 0.82]↓ | 0.78 · T same-node 0.77 (77 pairs) | 30% (20%) | - (-) | kn176:77+kn175:3 |
| mtbench_qwen3 | r_fuzzy | low | 0.15 | 80 | 2.59 (2.12) | 2187 (2133) | 1.03 [0.97, 1.09] | 0.89 [0.84, 0.94]↓ | 0.89 · cross-node | 18% (20%) | - (-) | kn175:77+kn174:3 |
| mtbench_qwen3 | r_fuzzy | mid+high | 0.25 | 80 | 3.05 (2.12) | 2269 (2133) | 1.06 [0.99, 1.15] | 0.82 [0.77, 0.87]↓ | 0.84 · cross-node | 25% (20%) | - (-) | kn175:77+kn174:3 |
| mtbench_qwen3 | r_fuzzy | extra | 0.03 | 80 | 2.20 (2.12) | 2064 (2133) | 0.97 [0.92, 1.02] | 0.95 [0.90, 1.00] | 0.95 · cross-node | 15% (20%) | - (-) | kn175:77+kn173:3 |
| mtbench_qwen3 | spec_casc_tok | low+mid+high | 0.8 | 80 | 2.61 (2.12) | 2057 (2133) | 0.96 [0.90, 1.03] | 0.84 [0.78, 0.89]↓ | 0.86 · cross-node | 16% (20%) | - (-) | kn174:77+kn175:3 |
| mtbench_qwen3 | spec_casc_tok | extra | 0.15 | 80 | 2.28 (2.12) | 2065 (2133) | 0.97 [0.90, 1.03] | 0.93 [0.86, 0.99]↓ | 1.03 · T same-node 1.03 (77 pairs) | 15% (20%) | - (-) | kn176:77+kn173:3 |

`campaign/addendum/tables/step8__qwen3-8b__qwen3-1.7b.csv` -- Qwen/Qwen3-8B + Qwen/Qwen3-1.7B (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gsm8k_qwen3 | mentored_dec | loosest | 0.75 | 150 | 4.77 (3.82) | 1227 (1316) | 0.93 [0.90, 0.97]↓ | 0.76 [0.73, 0.79]↓ | 0.74 | 20% (25%) | 83% (79%) | kn175 |
| gsm8k_qwen3 | cactus | loosest | 0.35 | 150 | 4.81 (3.82) | 1228 (1316) | 0.93 [0.89, 0.98]↓ | 0.76 [0.73, 0.80]↓ | 0.75 | 20% (25%) | 83% (79%) | kn175 |
| gsm8k_qwen3 | spec_casc_opt | loosest | 0.05 | 150 | 5.04 (3.82) | 1261 (1316) | 0.96 [0.92, 1.00]↓ | 0.76 [0.72, 0.79]↓ | 0.74 | 23% (25%) | 82% (79%) | kn175 |
| gsm8k_qwen3 | r_fuzzy | loosest | 0.25 | 150 | 4.85 (3.82) | 1216 (1316) | 0.92 [0.89, 0.96]↓ | 0.75 [0.72, 0.78]↓ | 0.72 · cross-node | 18% (25%) | 85% (79%) | kn174 |
| gsm8k_qwen3 | spec_casc_tok | loosest | 0.8 | 150 | 4.41 (3.82) | 1231 (1316) | 0.94 [0.89, 0.98]↓ | 0.83 [0.79, 0.87]↓ | 0.81 | 22% (25%) | 81% (79%) | kn175 |
| livecodebench_qwen3 | mentored_dec | loosest | 0.75 | 90 | 5.08 (3.80) | 7364 (8098) | 0.91 [0.86, 0.95]↓ | 0.70 [0.66, 0.73]↓ | 0.75 · cross-node | 24% (31%) | 73% (69%) | kn176 |
| livecodebench_qwen3 | cactus | loosest | 0.35 | 90 | 5.11 (3.80) | 7346 (8098) | 0.91 [0.87, 0.94]↓ | 0.69 [0.67, 0.72]↓ | 0.69 · cross-node | 24% (31%) | 77% (69%) | kn176 |
| livecodebench_qwen3 | spec_casc_opt | loosest | 0.05 | 90 | 4.98 (3.80) | 7414 (8098) | 0.92 [0.87, 0.96]↓ | 0.72 [0.69, 0.76]↓ | 0.72 · cross-node | 22% (31%) | 80% (69%) | kn176 |
| livecodebench_qwen3 | r_fuzzy | loosest | 0.25 | 90 | 5.24 (3.80) | 7485 (8098) | 0.92 [0.88, 0.97]↓ | 0.69 [0.66, 0.73]↓ | 0.69 · cross-node | 24% (31%) | 76% (69%) | kn174 |
| livecodebench_qwen3 | spec_casc_tok | loosest | 0.8 | 90 | 4.48 (3.80) | 7560 (8098) | 0.93 [0.89, 0.98]↓ | 0.80 [0.77, 0.84]↓ | 0.80 | 27% (31%) | 71% (69%) | kn175 |

### Block 4: GPT-OSS-20B + RedHatAI EAGLE-3, matched-l_bar protocol

GPU-h actual (lane journals): 16.9.

`campaign/addendum/tables/step8__gpt-oss-20b__rh-eagle3.csv` -- openai/gpt-oss-20b + RedHatAI/gpt-oss-20b-speculator.eagle3 (eagle3, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gsm8k | mentored_dec | low | 0.35 | 150 | 2.46 (2.13) | 339 (353) | 0.96 [0.87, 1.06] | 0.86 [0.76, 0.96]↓ | 0.86 · cross-node | 1% (3%) | 97% (97%) | kn176:147+kn174:3 |
| gsm8k | mentored_dec | mid+high | 0.75 | 150 | 2.97 (2.13) | 462 (353) | 1.31 [1.16, 1.49]↑ | 0.98 [0.87, 1.11] | 0.97 · cross-node | 4% (3%) | 95% (97%) | kn176:147+kn173:3 |
| gsm8k | mentored_dec | extra | 0.15 | 150 | 2.29 (2.13) | 353 (353) | 1.00 [0.89, 1.13] | 0.95 [0.84, 1.08] | 0.94 · cross-node | 3% (3%) | 96% (97%) | kn176:147+kn173:3 |
| gsm8k | cactus | low+mid | 0.03 | 150 | 3.05 (2.13) | 599 (353) | 1.70 [1.50, 1.93]↑ | 1.24 [1.09, 1.42]↑ | 1.24 · T same-node 1.23 (147 pairs) | 5% (3%) | 92% (97%) | kn175:147+kn174:3 |
| gsm8k | cactus | high | 0.35 | 150 | 4.31 (2.13) | 880 (353) | 2.49 [2.16, 2.91]↑ | 1.38 [1.18, 1.61]↑ | 1.34 · T same-node 1.33 (147 pairs) | 13% (3%) | 83% (97%) | kn175:147+kn174:3 |
| gsm8k | spec_casc_opt | low | -0.1 | 150 | 2.56 (2.13) | 420 (353) | 1.19 [1.05, 1.34]↑ | 1.02 [0.89, 1.16] | 1.03 · cross-node | 2% (3%) | 97% (97%) | kn176:147+kn174:3 |
| gsm8k | spec_casc_opt | mid+high | 0.05 | 150 | 2.81 (2.13) | 475 (353) | 1.35 [1.20, 1.51]↑ | 1.08 [0.95, 1.22] | 1.08 · cross-node | 3% (3%) | 93% (97%) | kn176:147+kn173:3 |
| gsm8k | spec_casc_opt | extra | -0.3 | 150 | 2.42 (2.13) | 390 (353) | 1.10 [0.99, 1.24] | 1.00 [0.89, 1.13] | 1.01 · cross-node | 1% (3%) | 97% (97%) | kn174:147+kn173:3 |
| gsm8k | r_fuzzy | low | 0.15 | 150 | 2.71 (2.13) | 581 (353) | 1.65 [1.46, 1.87]↑ | 1.36 [1.19, 1.54]↑ | 1.36 · T same-node 1.34 (147 pairs) | 4% (3%) | 91% (97%) | kn175:147+kn174:3 |
| gsm8k | r_fuzzy | mid+high | 0.25 | 150 | 3.52 (2.13) | 848 (353) | 2.40 [2.08, 2.79]↑ | 1.59 [1.36, 1.85]↑ | 1.57 · T same-node 1.56 (147 pairs) | 10% (3%) | 78% (97%) | kn175:147+kn174:3 |
| gsm8k | r_fuzzy | extra | 0.03 | 150 | 2.19 (2.13) | 345 (353) | 0.98 [0.89, 1.08] | 0.95 [0.86, 1.05] | 0.96 · T same-node 0.95 (147 pairs) | 1% (3%) | 94% (97%) | kn175:147+kn174:3 |
| gsm8k | spec_casc_tok | low+mid+high | 0.55 | 150 | 2.25 (2.13) | 306 (353) | 0.87 [0.79, 0.95]↓ | 0.83 [0.75, 0.91]↓ | 0.84 · cross-node | 1% (3%) | 97% (97%) | kn176:147+kn175:3 |
| gsm8k | spec_casc_tok | extra | 0.15 | 150 | 2.16 (2.13) | 320 (353) | 0.91 [0.81, 1.01] | 0.89 [0.79, 1.00] | 0.89 · T same-node 0.88 (147 pairs) | 1% (3%) | 97% (97%) | kn175:147+kn173:3 |
| gsm8k | spec_casc_tok | extra | 0.8 | 150 | 2.37 (2.13) | 364 (353) | 1.03 [0.92, 1.16] | 0.94 [0.84, 1.06] | 0.95 · cross-node | 1% (3%) | 97% (97%) | kn176:147+kn173:3 |
| livecodebench | mentored_dec | low | 0.55 | 90 | 1.81 (1.57) | 4358 (3445) | 1.26 [1.13, 1.42]↑ | 1.23 [1.02, 1.49]↑ | 1.23 · T same-node 1.24 (87 pairs) | 8% (6%) | 84% (83%) | kn174:87+kn175:3 |
| livecodebench | mentored_dec | mid+high | 0.75 | 90 | 1.95 (1.57) | 4930 (3445) | 1.43 [1.30, 1.59]↑ | 1.34 [1.16, 1.57]↑ | 1.31 · cross-node | 10% (6%) | 81% (83%) | kn176:87+kn173:3 |
| livecodebench | mentored_dec | extra | 0.15 | 90 | 1.66 (1.57) | 3598 (3445) | 1.04 [0.96, 1.15] | 1.01 [0.89, 1.17] | 0.99 · cross-node | 6% (6%) | 89% (83%) | kn175:87+kn174:3 |
| livecodebench | cactus | low | 0.03 | 90 | 2.36 (1.57) | 6722 (3445) | 1.95 [1.66, 2.30]↑ | 1.32 [1.05, 1.69]↑ | 1.30 · cross-node | 29% (6%) | 41% (83%) | kn175:87+kn174:3 |
| livecodebench | cactus | mid | 0.08 | 90 | 3.18 (1.57) | 8081 (3445) | 2.35 [1.96, 2.82]↑ | 1.21 [0.94, 1.58] | 1.18 · cross-node | 51% (6%) | 24% (83%) | kn176:87+kn174:3 |
| livecodebench | cactus | high | 0.18 | 90 | 3.99 (1.57) | 8800 (3445) | 2.55 [2.16, 3.03]↑ | 1.08 [0.86, 1.39] | 1.06 · cross-node | 62% (6%) | 16% (83%) | kn175 |
| livecodebench | spec_casc_opt | low+mid+high | -0.02 | 90 | 1.75 (1.57) | 5023 (3445) | 1.46 [1.31, 1.63]↑ | 1.38 [1.17, 1.65]↑ | 1.54 · cross-node | 9% (6%) | 73% (83%) | kn176:87+kn174:3 |
| livecodebench | spec_casc_opt | extra | -0.3 | 90 | 1.69 (1.57) | 3898 (3445) | 1.13 [1.05, 1.23]↑ | 1.10 [0.98, 1.23] | 1.08 · cross-node | 7% (6%) | 82% (83%) | kn175:87+kn173:3 |
| livecodebench | spec_casc_opt | extra | 0.05 | 90 | 1.85 (1.57) | 5286 (3445) | 1.53 [1.36, 1.75]↑ | 1.37 [1.14, 1.67]↑ | 1.38 | 8% (6%) | 49% (83%) | kn174 |
| livecodebench | r_fuzzy | low+mid+high | 0.08 | 90 | 1.56 (1.57) | 4399 (3445) | 1.28 [1.15, 1.42]↑ | 1.28 [1.10, 1.50]↑ | 1.26 · cross-node | 7% (6%) | 39% (83%) | kn176:87+kn175:3 |
| livecodebench | r_fuzzy | extra | 0.03 | 90 | 1.58 (1.57) | 3689 (3445) | 1.07 [0.98, 1.17] | 1.04 [0.92, 1.18] | 1.02 · cross-node | 3% (6%) | 67% (83%) | kn175 |
| livecodebench | r_fuzzy | extra | 0.25 | 90 | 1.60 (1.57) | 7561 (3445) | 2.19 [1.92, 2.54]↑ | 2.28 [1.85, 2.85]↑ | 2.26 · cross-node | 24% (6%) | 11% (83%) | kn175:87+kn174:3 |
| livecodebench | spec_casc_tok | low+mid+high | 0.55 | 90 | 1.65 (1.57) | 3768 (3445) | 1.09 [0.97, 1.22] | 1.06 [0.89, 1.26] | 1.05 · cross-node | 6% (6%) | 91% (83%) | kn176:87+kn174:3 |
| livecodebench | spec_casc_tok | extra | 0.15 | 90 | 1.56 (1.57) | 3769 (3445) | 1.09 [0.98, 1.23] | 1.10 [0.93, 1.32] | 1.09 · cross-node | 6% (6%) | 93% (83%) | kn175:87+kn174:3 |
| livecodebench | spec_casc_tok | extra | 0.8 | 90 | 1.71 (1.57) | 3873 (3445) | 1.12 [1.01, 1.24]↑ | 1.10 [0.95, 1.26] | 1.23 · cross-node | 7% (6%) | 87% (83%) | kn176:87+kn175:3 |
| mtbench | mentored_dec | low | 0.35 | 80 | 2.13 (1.82) | 1355 (1157) | 1.17 [1.06, 1.30]↑ | 1.04 [0.94, 1.15] | 1.05 · T same-node 1.09 (77 pairs) | 2% (1%) | - (-) | kn175:77+kn173:3 |
| mtbench | mentored_dec | mid+high | 0.75 | 80 | 2.83 (1.82) | 1570 (1157) | 1.36 [1.23, 1.51]↑ | 0.95 [0.85, 1.06] | 0.97 · cross-node | 5% (1%) | - (-) | kn174 |
| mtbench | mentored_dec | extra | 0.15 | 80 | 1.92 (1.82) | 1292 (1157) | 1.12 [1.02, 1.23]↑ | 1.06 [0.97, 1.17] | 1.08 · cross-node | 2% (1%) | - (-) | kn176:77+kn175:3 |
| mtbench | cactus | low+mid | 0.03 | 80 | 3.40 (1.82) | 1594 (1157) | 1.38 [1.22, 1.56]↑ | 0.81 [0.70, 0.94]↓ | 0.83 · T same-node 0.85 (77 pairs) | 6% (1%) | - (-) | kn175:77+kn173:3 |
| mtbench | cactus | high | 0.18 | 80 | 4.41 (1.82) | 1809 (1157) | 1.56 [1.40, 1.75]↑ | 0.74 [0.65, 0.84]↓ | 0.75 | 14% (1%) | - (-) | kn175 |
| mtbench | cactus | extra | 0.35 | 80 | 4.78 (1.82) | 1905 (1157) | 1.65 [1.42, 1.91]↑ | 0.74 [0.62, 0.88]↓ | 0.75 · T same-node 0.77 (77 pairs) | 14% (1%) | - (-) | kn175:77+kn173:3 |
| mtbench | spec_casc_opt | low | -0.02 | 80 | 2.39 (1.82) | 1374 (1157) | 1.19 [1.08, 1.31]↑ | 0.95 [0.86, 1.06] | 0.98 · cross-node | 4% (1%) | - (-) | kn176:77+kn174:3 |
| mtbench | spec_casc_opt | mid+high | 0.05 | 80 | 2.54 (1.82) | 1520 (1157) | 1.31 [1.19, 1.45]↑ | 0.99 [0.89, 1.10] | 1.02 · cross-node | 6% (1%) | - (-) | kn174 |
| mtbench | spec_casc_opt | extra | -0.3 | 80 | 2.09 (1.82) | 1360 (1157) | 1.18 [1.07, 1.30]↑ | 1.05 [0.95, 1.18] | 1.06 · T same-node 1.09 (77 pairs) | 2% (1%) | - (-) | kn175:77+kn174:3 |
| mtbench | r_fuzzy | low | 0.08 | 80 | 1.99 (1.82) | 1410 (1157) | 1.22 [1.11, 1.34]↑ | 1.13 [1.02, 1.25]↑ | 1.20 · cross-node | 2% (1%) | - (-) | kn176:77+kn174:3 |
| mtbench | r_fuzzy | mid+high | 0.25 | 80 | 3.42 (1.82) | 1824 (1157) | 1.58 [1.40, 1.78]↑ | 0.93 [0.82, 1.08] | 0.94 · cross-node | 10% (1%) | - (-) | kn176:77+kn173:3 |
| mtbench | r_fuzzy | extra | 0.03 | 80 | 1.85 (1.82) | 1212 (1157) | 1.05 [0.95, 1.17] | 1.02 [0.93, 1.13] | 1.04 · T same-node 1.05 (77 pairs) | 1% (1%) | - (-) | kn175:77+kn173:3 |
| mtbench | spec_casc_tok | low+mid+high | 0.8 | 80 | 2.03 (1.82) | 1284 (1157) | 1.11 [1.00, 1.23] | 1.03 [0.93, 1.14] | 1.03 · T same-node 1.05 (77 pairs) | 4% (1%) | - (-) | kn175:77+kn174:3 |
| mtbench | spec_casc_tok | extra | 0.15 | 80 | 1.83 (1.82) | 1203 (1157) | 1.04 [0.92, 1.17] | 1.02 [0.91, 1.15] | 1.05 · T same-node 1.04 (77 pairs) | 4% (1%) | - (-) | kn175:77+kn174:3 |

### Block 5: DeepSeek-R1-Distill-Llama-8B + Llama-3.2-1B standalone (loosest)

GPU-h actual (lane journals): 7.5.

`campaign/addendum/tables/step8__r1-distill-llama-8b__llama32-1b.csv` -- deepseek-ai/DeepSeek-R1-Distill-Llama-8B + meta-llama/Llama-3.2-1B-Instruct (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gsm8k_r1llama | mentored_dec | loosest | 0.75 | 150 | 3.32 (2.71) | 450 (440) | 1.02 [0.96, 1.09] | 0.87 [0.81, 0.94]↓ | 0.84 · cross-node | 1% (1%) | 73% (71%) | kn175 |
| gsm8k_r1llama | cactus | loosest | 0.35 | 150 | 4.26 (2.71) | 971 (440) | 2.21 [1.92, 2.51]↑ | 1.37 [1.20, 1.55]↑ | 1.31 | 35% (1%) | 44% (71%) | kn176 |
| gsm8k_r1llama | spec_casc_opt | loosest | 0.05 | 150 | 3.98 (2.71) | 1395 (440) | 3.17 [2.81, 3.55]↑ | 2.30 [2.00, 2.60]↑ | 2.21 · cross-node | 52% (1%) | 51% (71%) | kn174 |
| gsm8k_r1llama | r_fuzzy | loosest | 0.25 | 150 | 3.13 (2.71) | 892 (440) | 2.03 [1.79, 2.27]↑ | 1.99 [1.71, 2.31]↑ | 1.93 · cross-node | 19% (1%) | 49% (71%) | kn175 |
| gsm8k_r1llama | spec_casc_tok | loosest | 0.8 | 150 | 2.96 (2.71) | 426 (440) | 0.97 [0.91, 1.03] | 0.89 [0.82, 0.95]↓ | 0.86 · cross-node | 1% (1%) | 77% (71%) | kn175 |
| livecodebench_r1llama | mentored_dec | loosest | 0.75 | 90 | 2.59 (1.56) | 10337 (8742) | 1.18 [1.12, 1.26]↑ | 0.84 [0.79, 0.89]↓ | 0.83 | 63% (39%) | 32% (56%) | kn176 |
| livecodebench_r1llama | cactus | loosest | 0.35 | 90 | 5.50 (1.56) | 11179 (8742) | 1.28 [1.18, 1.40]↑ | 0.50 [0.46, 0.55]↓ | 0.50 · cross-node | 83% (39%) | 4% (56%) | kn174 |
| livecodebench_r1llama | spec_casc_opt | loosest | 0.05 | 90 | 2.62 (1.56) | 9539 (8742) | 1.09 [1.02, 1.17]↑ | 0.78 [0.72, 0.84]↓ | 0.79 · cross-node | 44% (39%) | 30% (56%) | kn175 |
| livecodebench_r1llama | r_fuzzy | loosest | 0.25 | 90 | 2.07 (1.56) | 7688 (8742) | 0.88 [0.81, 0.96]↓ | 0.74 [0.67, 0.80]↓ | 0.73 · cross-node | 2% (39%) | 14% (56%) | kn175 |
| livecodebench_r1llama | spec_casc_tok | loosest | 0.8 | 90 | 2.34 (1.56) | 9067 (8742) | 1.04 [0.99, 1.09] | 0.78 [0.75, 0.82]↓ | 0.78 · cross-node | 46% (39%) | 42% (56%) | kn175 |

### Block 6: the fix (head-restricted relaxation) on Qwen3-8B; GPT-OSS-20B re-export

GPU-h actual (lane journals): 2.5.

`campaign/addendum/tables/step8__qwen3-8b__eagle3-fix.csv` -- Qwen/Qwen3-8B + RedHatAI/Qwen3-8B-speculator.eagle3 (eagle3, V2 accept-test-only):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gsm8k_qwen3 | spec_casc_tok_lt | fix | 0.15 | 150 | 1.54 (1.50) | 1296 (1279) | 1.01 [0.98, 1.05] | 0.99 [0.96, 1.03] | 0.97 · cross-node | 23% (23%) | 79% (80%) | kn175 |
| gsm8k_qwen3 | spec_casc_tok_lt | fix | 0.2 | 150 | 1.54 (1.50) | 1296 (1279) | 1.01 [0.98, 1.05] | 0.99 [0.96, 1.03] | 0.97 · cross-node | 23% (23%) | 79% (80%) | kn175 |
| gsm8k_qwen3 | spec_casc_opt_head | fix | 0.05, beta 0.15 | 150 | 1.54 (1.50) | 1296 (1279) | 1.01 [0.98, 1.05] | 0.99 [0.96, 1.03] | 0.98 | 23% (23%) | 79% (80%) | kn176 |
| livecodebench_qwen3 | spec_casc_tok_lt | fix | 0.15 | 90 | 1.17 (1.13) | 8009 (7955) | 1.01 [0.97, 1.05] | 0.99 [0.95, 1.04] | 0.98 · cross-node | 26% (27%) | 74% (73%) | kn175 |
| livecodebench_qwen3 | spec_casc_tok_lt | fix | 0.2 | 90 | 1.17 (1.13) | 8009 (7955) | 1.01 [0.97, 1.05] | 0.99 [0.95, 1.04] | 0.97 · cross-node | 26% (27%) | 74% (73%) | kn175 |
| livecodebench_qwen3 | spec_casc_opt_head | fix | 0.05, beta 0.15 | 90 | 1.17 (1.13) | 8004 (7955) | 1.01 [0.97, 1.05] | 0.99 [0.95, 1.03] | 0.97 · cross-node | 26% (27%) | 74% (73%) | kn175 |

`campaign/addendum/tables/fix__gpt-oss-20b.csv`:

| condition | dataset | method | alpha | n_pairs | l_bar | l_bar_strict | mean_tokens | mean_tokens_strict | lambda | rounds_ratio | time_ratio | accuracy | accuracy_strict | capout_rate | capout_rate_strict | time_per_round_ratio | nodes | nodes_strict | same_node_pairs | same_node | lambda_ci_lo | lambda_ci_hi | rounds_ratio_ci_lo | rounds_ratio_ci_hi | time_ratio_ci_lo | time_ratio_ci_hi | time_ratio_same_node | target | drafter | beta | seeds | n_seeds | server | experiment | source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fix | aime24 | spec_casc_tok_lt | 0.050 | 90.000 | 2.448 | 2.201 | 10006.800 | 9703.380 | 1.031 | 0.939 | 0.941 | 0.756 | 0.778 | 0.100 | 0.067 | 1.002 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21804913 (strict and relaxed arms in this one job) | E1F | campaign/tables/aime24_fine.csv (method=spec_casc_tok_lt, params=alpha0.05, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/aime24_fine.csv (method=spec_casc_tok_lt, alpha=0.05); accuracy_strict: campaign/results/aime24_fine.csv (strict); reported in cascade/RESULTS.md 2.3 |
| fix | aime24 | spec_casc_tok_lt | 0.100 | 90.000 | 2.444 | 2.201 | 10520.100 | 9703.380 | 1.084 | 0.994 | 0.994 | 0.756 | 0.778 | 0.089 | 0.067 | 1.000 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21804913 (strict and relaxed arms in this one job) | E1F | campaign/tables/aime24_fine.csv (method=spec_casc_tok_lt, params=alpha0.1, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/aime24_fine.csv (method=spec_casc_tok_lt, alpha=0.1); accuracy_strict: campaign/results/aime24_fine.csv (strict); reported in cascade/RESULTS.md 2.3 |
| fix | aime24 | spec_casc_tok_lt | 0.150 | 90.000 | 2.480 | 2.201 | 9794.190 | 9703.380 | 1.009 | 0.929 | 0.938 | 0.789 | 0.778 | 0.067 | 0.067 | 1.009 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21804913 (strict and relaxed arms in this one job) | E1F | campaign/tables/aime24_fine.csv (method=spec_casc_tok_lt, params=alpha0.15, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/aime24_fine.csv (method=spec_casc_tok_lt, alpha=0.15); accuracy_strict: campaign/results/aime24_fine.csv (strict); reported in cascade/RESULTS.md 2.3 |
| fix | aime24 | spec_casc_tok_lt | 0.200 | 90.000 | 2.489 | 2.201 | 10073.900 | 9703.380 | 1.038 | 0.945 | 0.944 | 0.778 | 0.778 | 0.067 | 0.067 | 0.999 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21804913 (strict and relaxed arms in this one job) | E1F | campaign/tables/aime24_fine.csv (method=spec_casc_tok_lt, params=alpha0.2, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/aime24_fine.csv (method=spec_casc_tok_lt, alpha=0.2); accuracy_strict: campaign/results/aime24_fine.csv (strict); reported in cascade/RESULTS.md 2.3 |
| fix | aime24 | spec_casc_tok_lt | 0.250 | 90.000 | 2.497 | 2.201 | 10427.300 | 9703.380 | 1.075 | 0.986 | 0.981 | 0.656 | 0.778 | 0.122 | 0.067 | 0.995 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21804913 (strict and relaxed arms in this one job) | E1F | campaign/tables/aime24_fine.csv (method=spec_casc_tok_lt, params=alpha0.25, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/aime24_fine.csv (method=spec_casc_tok_lt, alpha=0.25); accuracy_strict: campaign/results/aime24_fine.csv (strict); reported in cascade/RESULTS.md 2.3 |
| fix | gsm8k | spec_casc_tok_lt | 0.150 | 450.000 | 2.915 | 2.593 | 331.504 | 325.511 | 1.018 | 0.935 | 0.943 | 0.956 | 0.962 | 0.018 | 0.016 | 1.009 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21986969, may reuse runs from failed 21910960 (lane 1, nodes g1-g14) | E1P | campaign/tables/gsm8k_proper.csv (method=spec_casc_tok_lt, params=alpha0.15, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/gsm8k_proper.csv (method=spec_casc_tok_lt, alpha=0.15); accuracy_strict: campaign/results/gsm8k_proper.csv (strict); reported in cascade/RESULTS.md 2.3b |
| fix | gsm8k | spec_casc_tok_lt | 0.200 | 450.000 | 2.908 | 2.593 | 339.593 | 325.511 | 1.043 | 0.958 | 0.954 | 0.958 | 0.962 | 0.022 | 0.016 | 0.996 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21986969, may reuse runs from failed 21910960 (lane 1, nodes g1-g14) | E1P | campaign/tables/gsm8k_proper.csv (method=spec_casc_tok_lt, params=alpha0.2, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/gsm8k_proper.csv (method=spec_casc_tok_lt, alpha=0.2); accuracy_strict: campaign/results/gsm8k_proper.csv (strict); reported in cascade/RESULTS.md 2.3b |
| fix | gsm8k | spec_casc_tok_lt | 0.250 | 450.000 | 2.925 | 2.593 | 334.240 | 325.511 | 1.027 | 0.935 | 0.928 | 0.958 | 0.962 | 0.024 | 0.016 | 0.993 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21986969, may reuse runs from failed 21910960 (lane 1, nodes g1-g14) | E1P | campaign/tables/gsm8k_proper.csv (method=spec_casc_tok_lt, params=alpha0.25, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/gsm8k_proper.csv (method=spec_casc_tok_lt, alpha=0.25); accuracy_strict: campaign/results/gsm8k_proper.csv (strict); reported in cascade/RESULTS.md 2.3b |
| fix | humaneval | spec_casc_tok_lt | 0.150 | 450.000 | 2.764 | 2.514 | 892.393 | 889.336 | 1.003 | 0.927 | 0.931 | 0.949 | 0.960 | 0.000 | 0.002 | 1.004 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21986970 + gap-fill 22068663 (tok_lt alpha 0.15), may reuse runs from failed 21910961 (lane 1, nodes g1-g14) | E1P | campaign/tables/humaneval_proper.csv (method=spec_casc_tok_lt, params=alpha0.15, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/humaneval_proper.csv (method=spec_casc_tok_lt, alpha=0.15); accuracy_strict: campaign/results/humaneval_proper.csv (strict); reported in cascade/RESULTS.md 2.3b |
| fix | humaneval | spec_casc_tok_lt | 0.200 | 450.000 | 2.743 | 2.514 | 940.173 | 889.336 | 1.057 | 0.991 | 0.980 | 0.962 | 0.960 | 0.004 | 0.002 | 0.989 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21986970 + gap-fill 22068663 (tok_lt alpha 0.15), may reuse runs from failed 21910961 (lane 1, nodes g1-g14) | E1P | campaign/tables/humaneval_proper.csv (method=spec_casc_tok_lt, params=alpha0.2, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/humaneval_proper.csv (method=spec_casc_tok_lt, alpha=0.2); accuracy_strict: campaign/results/humaneval_proper.csv (strict); reported in cascade/RESULTS.md 2.3b |
| fix | humaneval | spec_casc_tok_lt | 0.250 | 450.000 | 2.797 | 2.514 | 891.416 | 889.336 | 1.002 | 0.921 | 0.917 | 0.967 | 0.960 | 0.000 | 0.002 | 0.996 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21986970 + gap-fill 22068663 (tok_lt alpha 0.15), may reuse runs from failed 21910961 (lane 1, nodes g1-g14) | E1P | campaign/tables/humaneval_proper.csv (method=spec_casc_tok_lt, params=alpha0.25, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/humaneval_proper.csv (method=spec_casc_tok_lt, alpha=0.25); accuracy_strict: campaign/results/humaneval_proper.csv (strict); reported in cascade/RESULTS.md 2.3b |
| fix | livecodebench | spec_casc_tok_lt | 0.150 | 270.000 | 2.443 | 2.202 | 3421.550 | 3338.690 | 1.025 | 0.942 | 0.939 | 0.893 | 0.889 | 0.037 | 0.033 | 0.997 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21986971, may reuse runs from failed 21910964 (lane 1, nodes g1-g14) | E1P | campaign/tables/livecodebench_proper.csv (method=spec_casc_tok_lt, params=alpha0.15, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/livecodebench_proper.csv (method=spec_casc_tok_lt, alpha=0.15); accuracy_strict: campaign/results/livecodebench_proper.csv (strict); reported in cascade/RESULTS.md 2.3b |
| fix | livecodebench | spec_casc_tok_lt | 0.200 | 270.000 | 2.452 | 2.202 | 3441.730 | 3338.690 | 1.031 | 0.947 | 0.946 | 0.896 | 0.889 | 0.037 | 0.033 | 0.999 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21986971, may reuse runs from failed 21910964 (lane 1, nodes g1-g14) | E1P | campaign/tables/livecodebench_proper.csv (method=spec_casc_tok_lt, params=alpha0.2, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/livecodebench_proper.csv (method=spec_casc_tok_lt, alpha=0.2); accuracy_strict: campaign/results/livecodebench_proper.csv (strict); reported in cascade/RESULTS.md 2.3b |
| fix | livecodebench | spec_casc_tok_lt | 0.250 | 270.000 | 2.470 | 2.202 | 3609.570 | 3338.690 | 1.081 | 0.994 | 0.982 | 0.889 | 0.889 | 0.052 | 0.033 | 0.987 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21986971, may reuse runs from failed 21910964 (lane 1, nodes g1-g14) | E1P | campaign/tables/livecodebench_proper.csv (method=spec_casc_tok_lt, params=alpha0.25, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/livecodebench_proper.csv (method=spec_casc_tok_lt, alpha=0.25); accuracy_strict: campaign/results/livecodebench_proper.csv (strict); reported in cascade/RESULTS.md 2.3b |
| fix | mtbench | spec_casc_tok_lt | 0.150 | 240.000 | 2.551 | 2.291 | 1235.160 | 1234.180 | 1.001 | 0.927 | 0.928 | - | - | 0.021 | 0.017 | 1.001 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21988492, may reuse runs from failed 21910962 (lane 2, nodes g15-g28) | E1P | campaign/tables/mtbench_proper.csv (method=spec_casc_tok_lt, params=alpha0.15, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/mtbench_proper.csv (method=spec_casc_tok_lt, alpha=0.15); accuracy_strict: campaign/results/mtbench_proper.csv (strict); reported in cascade/RESULTS.md 2.3b |
| fix | mtbench | spec_casc_tok_lt | 0.200 | 240.000 | 2.538 | 2.291 | 1232.000 | 1234.180 | 0.998 | 0.920 | 0.921 | - | - | 0.021 | 0.017 | 1.001 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21988492, may reuse runs from failed 21910962 (lane 2, nodes g15-g28) | E1P | campaign/tables/mtbench_proper.csv (method=spec_casc_tok_lt, params=alpha0.2, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/mtbench_proper.csv (method=spec_casc_tok_lt, alpha=0.2); accuracy_strict: campaign/results/mtbench_proper.csv (strict); reported in cascade/RESULTS.md 2.3b |
| fix | mtbench | spec_casc_tok_lt | 0.250 | 240.000 | 2.538 | 2.291 | 1224.790 | 1234.180 | 0.992 | 0.913 | 0.906 | - | - | 0.008 | 0.017 | 0.992 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21988492, may reuse runs from failed 21910962 (lane 2, nodes g15-g28) | E1P | campaign/tables/mtbench_proper.csv (method=spec_casc_tok_lt, params=alpha0.25, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/mtbench_proper.csv (method=spec_casc_tok_lt, alpha=0.25); accuracy_strict: campaign/results/mtbench_proper.csv (strict); reported in cascade/RESULTS.md 2.3b |
| fix | longbench_v2 | spec_casc_tok_lt | 0.150 | 90.000 | 2.184 | 1.966 | 1500.110 | 1381.570 | 1.086 | 1.001 | 1.013 | 0.556 | 0.600 | 0.011 | 0.000 | 1.011 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); jobs 21988496 + refill 22068664, may reuse runs from failed 21910965 (lane 2, nodes g15-g28) | E1P | campaign/tables/longbench_v2_proper.csv (method=spec_casc_tok_lt, params=alpha0.15, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/longbench_v2_proper.csv (method=spec_casc_tok_lt, alpha=0.15); accuracy_strict: campaign/results/longbench_v2_proper.csv (strict); reported in cascade/RESULTS.md 2.3b |
| fix | longbench_v2 | spec_casc_tok_lt | 0.200 | 90.000 | 2.187 | 1.966 | 1373.330 | 1381.570 | 0.994 | 0.921 | 0.941 | 0.533 | 0.600 | 0.000 | 0.000 | 1.021 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); jobs 21988496 + refill 22068664, may reuse runs from failed 21910965 (lane 2, nodes g15-g28) | E1P | campaign/tables/longbench_v2_proper.csv (method=spec_casc_tok_lt, params=alpha0.2, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/longbench_v2_proper.csv (method=spec_casc_tok_lt, alpha=0.2); accuracy_strict: campaign/results/longbench_v2_proper.csv (strict); reported in cascade/RESULTS.md 2.3b |
| fix | longbench_v2 | spec_casc_tok_lt | 0.250 | 90.000 | 2.220 | 1.966 | 1756.240 | 1381.570 | 1.271 | 1.140 | 1.123 | 0.556 | 0.600 | 0.056 | 0.000 | 0.984 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | - | 0,1,2 | 3.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); jobs 21988496 + refill 22068664, may reuse runs from failed 21910965 (lane 2, nodes g15-g28) | E1P | campaign/tables/longbench_v2_proper.csv (method=spec_casc_tok_lt, params=alpha0.25, seeds 0,1,2; strict same case+seed); accuracy: campaign/results/longbench_v2_proper.csv (method=spec_casc_tok_lt, alpha=0.25); accuracy_strict: campaign/results/longbench_v2_proper.csv (strict); reported in cascade/RESULTS.md 2.3b |
| fix | aime24 | spec_casc_opt_head | -0.300 | 30.000 | 2.455 | 2.224 | 9278.630 | 8481.430 | 1.094 | 0.990 | 0.982 | 0.733 | 0.800 | 0.033 | 0.067 | 0.993 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | 0.150 | 0.000 | 1.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21848564 (opt_head arms; strict seed 0 is E1F job 21804913's, identical rows) | E6 | campaign/tables/aime24_e6.csv (method=spec_casc_opt_head, params=alphaneg0.3_beta0.15, seeds 0; strict same case+seed); accuracy: campaign/results/aime24_e6.csv (method=spec_casc_opt_head_beta0.15, alpha=-0.3); accuracy_strict: cascade/RESULTS.md 2.4 'Lossless (seed 0): ... 80%'; reported in cascade/RESULTS.md 2.4 |
| fix | aime24 | spec_casc_opt_head | -0.100 | 30.000 | 2.468 | 2.224 | 9586.830 | 8481.430 | 1.130 | 1.049 | 1.075 | 0.733 | 0.800 | 0.100 | 0.067 | 1.025 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | 0.150 | 0.000 | 1.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21848564 (opt_head arms; strict seed 0 is E1F job 21804913's, identical rows) | E6 | campaign/tables/aime24_e6.csv (method=spec_casc_opt_head, params=alphaneg0.1_beta0.15, seeds 0; strict same case+seed); accuracy: campaign/results/aime24_e6.csv (method=spec_casc_opt_head_beta0.15, alpha=-0.1); accuracy_strict: cascade/RESULTS.md 2.4 'Lossless (seed 0): ... 80%'; reported in cascade/RESULTS.md 2.4 |
| fix | aime24 | spec_casc_opt_head | -0.020 | 30.000 | 2.484 | 2.224 | 11022.100 | 8481.430 | 1.300 | 1.194 | 1.199 | 0.833 | 0.800 | 0.067 | 0.067 | 1.004 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | 0.150 | 0.000 | 1.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21848564 (opt_head arms; strict seed 0 is E1F job 21804913's, identical rows) | E6 | campaign/tables/aime24_e6.csv (method=spec_casc_opt_head, params=alphaneg0.02_beta0.15, seeds 0; strict same case+seed); accuracy: campaign/results/aime24_e6.csv (method=spec_casc_opt_head_beta0.15, alpha=-0.02); accuracy_strict: cascade/RESULTS.md 2.4 'Lossless (seed 0): ... 80%'; reported in cascade/RESULTS.md 2.4 |
| fix | aime24 | spec_casc_opt_head | 0.050 | 30.000 | 2.455 | 2.224 | 10106.100 | 8481.430 | 1.192 | 1.095 | 1.125 | 0.800 | 0.800 | 0.033 | 0.067 | 1.027 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | 0.150 | 0.000 | 1.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21848564 (opt_head arms; strict seed 0 is E1F job 21804913's, identical rows) | E6 | campaign/tables/aime24_e6.csv (method=spec_casc_opt_head, params=alpha0.05_beta0.15, seeds 0; strict same case+seed); accuracy: campaign/results/aime24_e6.csv (method=spec_casc_opt_head_beta0.15, alpha=0.05); accuracy_strict: cascade/RESULTS.md 2.4 'Lossless (seed 0): ... 80%'; reported in cascade/RESULTS.md 2.4 |
| fix | aime24 | spec_casc_opt_head | -0.300 | 30.000 | 2.490 | 2.224 | 8738.970 | 8481.430 | 1.030 | 0.939 | 0.949 | 0.800 | 0.800 | 0.033 | 0.067 | 1.011 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | 0.350 | 0.000 | 1.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21848564 (opt_head arms; strict seed 0 is E1F job 21804913's, identical rows) | E6 | campaign/tables/aime24_e6.csv (method=spec_casc_opt_head, params=alphaneg0.3_beta0.35, seeds 0; strict same case+seed); accuracy: campaign/results/aime24_e6.csv (method=spec_casc_opt_head_beta0.35, alpha=-0.3); accuracy_strict: cascade/RESULTS.md 2.4 'Lossless (seed 0): ... 80%'; reported in cascade/RESULTS.md 2.4 |
| fix | aime24 | spec_casc_opt_head | -0.100 | 30.000 | 2.470 | 2.224 | 10698.200 | 8481.430 | 1.261 | 1.159 | 1.187 | 0.633 | 0.800 | 0.167 | 0.067 | 1.024 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | 0.350 | 0.000 | 1.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21848564 (opt_head arms; strict seed 0 is E1F job 21804913's, identical rows) | E6 | campaign/tables/aime24_e6.csv (method=spec_casc_opt_head, params=alphaneg0.1_beta0.35, seeds 0; strict same case+seed); accuracy: campaign/results/aime24_e6.csv (method=spec_casc_opt_head_beta0.35, alpha=-0.1); accuracy_strict: cascade/RESULTS.md 2.4 'Lossless (seed 0): ... 80%'; reported in cascade/RESULTS.md 2.4 |
| fix | aime24 | spec_casc_opt_head | -0.020 | 30.000 | 2.533 | 2.224 | 9481.370 | 8481.430 | 1.118 | 1.001 | 1.028 | 0.800 | 0.800 | 0.067 | 0.067 | 1.026 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | 0.350 | 0.000 | 1.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21848564 (opt_head arms; strict seed 0 is E1F job 21804913's, identical rows) | E6 | campaign/tables/aime24_e6.csv (method=spec_casc_opt_head, params=alphaneg0.02_beta0.35, seeds 0; strict same case+seed); accuracy: campaign/results/aime24_e6.csv (method=spec_casc_opt_head_beta0.35, alpha=-0.02); accuracy_strict: cascade/RESULTS.md 2.4 'Lossless (seed 0): ... 80%'; reported in cascade/RESULTS.md 2.4 |
| fix | aime24 | spec_casc_opt_head | 0.050 | 30.000 | 2.528 | 2.224 | 10772.200 | 8481.430 | 1.270 | 1.151 | 1.164 | 0.667 | 0.800 | 0.167 | 0.067 | 1.011 | - | - | - | - | - | - | - | - | - | - | - | gpt-oss-20b | nebius/EAGLE3-gpt-oss-20b | 0.350 | 0.000 | 1.000 | Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed (scripts/persistent_arm_replay.py); job 21848564 (opt_head arms; strict seed 0 is E1F job 21804913's, identical rows) | E6 | campaign/tables/aime24_e6.csv (method=spec_casc_opt_head, params=alpha0.05_beta0.35, seeds 0; strict same case+seed); accuracy: campaign/results/aime24_e6.csv (method=spec_casc_opt_head_beta0.35, alpha=0.05); accuracy_strict: cascade/RESULTS.md 2.4 'Lossless (seed 0): ... 80%'; reported in cascade/RESULTS.md 2.4 |

### Block 7 (optional): Qwen3-8B + RedHatAI P-EAGLE (parallel drafting), loosest

GPU-h actual (lane journals): 5.2.

`campaign/addendum/tables/step8__qwen3-8b__peagle.csv` -- Qwen/Qwen3-8B + RedHatAI/Qwen3-8B-speculator.peagle (eagle3, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gsm8k_qwen3 | mentored_dec | loosest | 0.75 | 150 | 2.37 (2.16) | 1331 (1303) | 1.02 [0.99, 1.06] | 0.95 [0.92, 0.99]↓ | 0.95 · cross-node | 25% (23%) | 79% (81%) | kn174 |
| gsm8k_qwen3 | cactus | loosest | 0.35 | 150 | 2.47 (2.16) | 1358 (1303) | 1.04 [1.00, 1.08]↑ | 0.94 [0.91, 0.98]↓ | 0.95 | 27% (23%) | 77% (81%) | kn175 |
| gsm8k_qwen3 | spec_casc_opt | loosest | 0.05 | 150 | 2.36 (2.16) | 1334 (1303) | 1.02 [0.98, 1.07] | 0.96 [0.92, 1.00]↓ | 0.94 · cross-node | 27% (23%) | 77% (81%) | kn174 |
| gsm8k_qwen3 | r_fuzzy | loosest | 0.25 | 150 | 2.75 (2.16) | 1672 (1303) | 1.28 [1.22, 1.36]↑ | 1.08 [1.02, 1.14]↑ | 1.08 | 56% (23%) | 51% (81%) | kn175 |
| gsm8k_qwen3 | spec_casc_tok | loosest | 0.8 | 150 | 2.23 (2.16) | 1304 (1303) | 1.00 [0.96, 1.04] | 0.98 [0.94, 1.02] | 0.98 · cross-node | 28% (23%) | 73% (81%) | kn174 |
| livecodebench_qwen3 | mentored_dec | loosest | 0.75 | 90 | 2.10 (1.84) | 8173 (8072) | 1.01 [0.97, 1.05] | 0.92 [0.88, 0.96]↓ | 0.92 | 33% (29%) | 67% (73%) | kn175 |
| livecodebench_qwen3 | cactus | loosest | 0.35 | 90 | 2.24 (1.84) | 8847 (8072) | 1.10 [1.05, 1.14]↑ | 0.94 [0.91, 0.99]↓ | 0.95 · cross-node | 46% (29%) | 56% (73%) | kn176 |
| livecodebench_qwen3 | spec_casc_opt | loosest | 0.05 | 90 | 2.08 (1.84) | 8413 (8072) | 1.04 [1.00, 1.09] | 0.95 [0.91, 0.99]↓ | 0.95 · cross-node | 34% (29%) | 51% (73%) | kn176 |
| livecodebench_qwen3 | r_fuzzy | loosest | 0.25 | 90 | 2.38 (1.84) | 10562 (8072) | 1.31 [1.23, 1.40]↑ | 1.10 [1.04, 1.17]↑ | 1.13 · cross-node | 70% (29%) | 3% (73%) | kn172 |
| livecodebench_qwen3 | spec_casc_tok | loosest | 0.8 | 90 | 1.99 (1.84) | 8363 (8072) | 1.04 [0.99, 1.09] | 0.98 [0.93, 1.03] | 0.98 · cross-node | 33% (29%) | 64% (73%) | kn176 |

## Step 9: the five rules on every dataset for the five dedicated step-8 pairs

The step-8 protocol on AIME24, LongBench-v2 and HumanEval (the paper's budgets and case sets): seed 0, N_draft 6, T 1.0, top-p 1.0, one persistent server per arm, every arm paired case by case with its own pair's lossless run; three matched-l_bar settings per rule plus the grid extremes when two targets share an alpha ("extra"). Ratios relaxed / lossless with 95% bootstrap intervals over cases (arrows: interval excludes 1). Each block ran whole on one cluster (H100 80GB HBM3 on both; README deviation 42). Block 0: `step9/BLOCK0.md`. Step 8 + step 9 per pair: `tables/pairs__<target>__<drafter>.csv`.

### Block 1: openai/gpt-oss-20b + RedHatAI/gpt-oss-20b-speculator.eagle3, aime24 (killarney)

GPU-h actual (lane journals): 10.6.

`campaign/addendum/tables/step9__gpt-oss-20b__rh-eagle3.csv` (eagle3, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aime24 | mentored_dec | low+mid+high | 0.55 | 30 | 1.39 (1.34) | 11936 (9650) | 1.24 [0.99, 1.55] | 1.23 [0.90, 1.70] | 1.20 · cross-node | 10% (7%) | 80% (77%) | kn171 |
| aime24 | mentored_dec | extra | 0.15 | 30 | 1.41 (1.34) | 8992 (9650) | 0.93 [0.70, 1.28] | 0.88 [0.58, 1.38] | 0.85 · cross-node | 3% (7%) | 80% (77%) | kn176:27+kn174:3 |
| aime24 | mentored_dec | extra | 0.75 | 30 | 1.58 (1.34) | 12766 (9650) | 1.32 [1.04, 1.69]↑ | 1.28 [0.93, 1.84] | 1.35 · cross-node | 10% (7%) | 77% (77%) | kn173:27+kn174:3 |
| aime24 | cactus | low | 0.03 | 30 | 2.09 (1.34) | 8814 (9650) | 0.91 [0.62, 1.39] | 0.56 [0.33, 1.04] | 0.56 · cross-node | 0% (7%) | 50% (77%) | kn173 |
| aime24 | cactus | mid | 0.08 | 30 | 2.78 (1.34) | 10762 (9650) | 1.12 [0.72, 1.79] | 0.49 [0.29, 0.92]↓ | 0.53 · cross-node | 3% (7%) | 27% (77%) | kn173 |
| aime24 | cactus | high | 0.18 | 30 | 3.58 (1.34) | 12984 (9650) | 1.35 [0.89, 2.04] | 0.46 [0.29, 0.79]↓ | 0.45 · cross-node | 20% (7%) | 20% (77%) | kn171 |
| aime24 | spec_casc_opt | low+mid+high | 0.05 | 30 | 1.54 (1.34) | 13859 (9650) | 1.44 [1.11, 1.93]↑ | 1.18 [0.82, 1.82] | 1.16 · cross-node | 7% (7%) | 63% (77%) | kn171:27+kn173:3 |
| aime24 | spec_casc_opt | extra | -0.3 | 30 | 1.36 (1.34) | 12124 (9650) | 1.26 [1.00, 1.61]↑ | 1.26 [0.94, 1.81] | 1.23 · cross-node | 10% (7%) | 73% (77%) | kn175:27+kn174:3 |
| aime24 | r_fuzzy | low+mid+high | 0.25 | 30 | 1.05 (1.34) | 16251 (9650) | 1.68 [1.28, 2.32]↑ | 1.67 [1.15, 2.69]↑ | 1.64 · cross-node | 10% (7%) | 60% (77%) | kn175:27+kn173:3 |
| aime24 | r_fuzzy | extra | 0.03 | 30 | 1.37 (1.34) | 10534 (9650) | 1.09 [0.84, 1.43] | 1.13 [0.78, 1.66] | 1.11 · cross-node | 7% (7%) | 73% (77%) | kn176:27+kn171:3 |
| aime24 | spec_casc_tok | low+mid+high | 0.8 | 30 | 1.33 (1.34) | 12316 (9650) | 1.28 [1.04, 1.62]↑ | 1.33 [1.01, 1.86]↑ | 1.30 · cross-node | 13% (7%) | 77% (77%) | kn175:27+kn171:3 |
| aime24 | spec_casc_tok | extra | 0.15 | 30 | 1.34 (1.34) | 9740 (9650) | 1.01 [0.78, 1.31] | 0.99 [0.68, 1.44] | 0.96 · cross-node | 7% (7%) | 63% (77%) | kn175:27+kn173:3 |

### Block 2: Qwen/Qwen3-8B + deepseek-ai/dspark_qwen3_8b_block7, aime24 (killarney)

GPU-h actual (lane journals): 12.6.

`campaign/addendum/tables/step9__qwen3-8b__dspark.csv` (dspark, V2 accept-test-only):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aime24_qwen3 | mentored_dec | low | 0.35 | 30 | 2.97 (2.51) | 18927 (19550) | 0.97 [0.86, 1.09] | 0.85 [0.75, 0.96]↓ | 0.84 · T same-node 0.83 (27 pairs) | 20% (20%) | 73% (70%) | kn176:27+kn173:3 |
| aime24_qwen3 | mentored_dec | mid+high | 0.75 | 30 | 3.38 (2.51) | 22087 (19550) | 1.13 [1.01, 1.27]↑ | 0.90 [0.80, 1.02] | 0.90 · cross-node | 33% (20%) | 63% (70%) | kn175:27+kn171:3 |
| aime24_qwen3 | mentored_dec | extra | 0.15 | 30 | 2.74 (2.51) | 18650 (19550) | 0.95 [0.85, 1.05] | 0.90 [0.80, 0.99]↓ | 0.90 · cross-node | 17% (20%) | 70% (70%) | kn173:29+kn172:1 |
| aime24_qwen3 | cactus | low | 0.03 | 30 | 2.89 (2.51) | 19311 (19550) | 0.99 [0.91, 1.07] | 0.89 [0.82, 0.96]↓ | 0.89 · cross-node | 20% (20%) | 70% (70%) | kn171:27+kn173:3 |
| aime24_qwen3 | cactus | mid+high | 0.35 | 30 | 3.47 (2.51) | 21271 (19550) | 1.09 [0.94, 1.26] | 0.84 [0.72, 1.00] | 0.84 · cross-node | 20% (20%) | 70% (70%) | kn171:27+kn175:3 |
| aime24_qwen3 | spec_casc_opt | low | -0.3 | 30 | 3.20 (2.51) | 20507 (19550) | 1.05 [0.93, 1.19] | 0.87 [0.77, 1.00]↓ | 0.88 · cross-node | 23% (20%) | 67% (70%) | kn169:27+kn171:3 |
| aime24_qwen3 | spec_casc_opt | mid | -0.1 | 30 | 3.49 (2.51) | 23967 (19550) | 1.23 [1.08, 1.41]↑ | 0.94 [0.82, 1.10] | 0.95 · cross-node | 40% (20%) | 57% (70%) | kn171:27+kn172:3 |
| aime24_qwen3 | spec_casc_opt | high | 0.05 | 30 | 4.22 (2.51) | 29687 (19550) | 1.52 [1.32, 1.78]↑ | 0.99 [0.85, 1.19] | 1.01 · cross-node | 70% (20%) | 37% (70%) | kn173:27+kn176:3 |
| aime24_qwen3 | r_fuzzy | low | 0.15 | 30 | 2.88 (2.51) | 22644 (19550) | 1.16 [1.03, 1.32]↑ | 1.04 [0.91, 1.20] | 1.05 · cross-node | 33% (20%) | 63% (70%) | kn175:27+kn172:3 |
| aime24_qwen3 | r_fuzzy | mid+high | 0.25 | 30 | 3.31 (2.51) | 23542 (19550) | 1.20 [1.06, 1.38]↑ | 0.96 [0.84, 1.13] | 0.97 · cross-node | 23% (20%) | 60% (70%) | kn175:27+kn174:3 |
| aime24_qwen3 | r_fuzzy | extra | 0.03 | 30 | 2.59 (2.51) | 20008 (19550) | 1.02 [0.90, 1.16] | 1.00 [0.87, 1.14] | 1.00 · cross-node | 20% (20%) | 67% (70%) | kn175:27+kn174:3 |
| aime24_qwen3 | spec_casc_tok | low | 0.35 | 30 | 2.80 (2.51) | 20184 (19550) | 1.03 [0.91, 1.19] | 0.95 [0.83, 1.11] | 0.96 · cross-node | 20% (20%) | 70% (70%) | kn173:27+kn172:3 |
| aime24_qwen3 | spec_casc_tok | mid+high | 0.8 | 30 | 3.09 (2.51) | 21452 (19550) | 1.10 [1.00, 1.23] | 0.93 [0.84, 1.06] | 0.94 · cross-node | 27% (20%) | 67% (70%) | kn174:27+kn173:3 |
| aime24_qwen3 | spec_casc_tok | extra | 0.15 | 30 | 2.76 (2.51) | 18404 (19550) | 0.94 [0.86, 1.03] | 0.87 [0.79, 0.95]↓ | 0.87 · cross-node | 10% (20%) | 80% (70%) | kn172:27+kn171:3 |

### Block 3a: openai/gpt-oss-20b + RedHatAI/gpt-oss-20b-speculator.eagle3, longbench_v2 (killarney)

GPU-h actual (lane journals): 11.3.

`campaign/addendum/tables/step9__gpt-oss-20b__rh-eagle3.csv` (eagle3, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| longbench_v2 | mentored_dec | low+mid+high | 0.75 | 150 | 0.09 (0.05) | 1502 (1403) | 1.07 [0.93, 1.23] | 1.03 [0.89, 1.19] | 1.00 · cross-node | 0% (1%) | 57% (54%) | kn174:147+kn169:3 |
| longbench_v2 | mentored_dec | extra | 0.15 | 150 | 0.06 (0.05) | 1375 (1403) | 0.98 [0.87, 1.10] | 0.97 [0.86, 1.09] | 0.95 · cross-node | 1% (1%) | 51% (54%) | kn173 |
| longbench_v2 | cactus | low | 0.03 | 150 | 0.91 (0.05) | 1493 (1403) | 1.06 [0.88, 1.29] | 0.62 [0.50, 0.76]↓ | 0.62 · cross-node | 0% (1%) | 36% (54%) | kn173 |
| longbench_v2 | cactus | mid | 0.08 | 150 | 1.57 (0.05) | 1839 (1403) | 1.31 [1.05, 1.62]↑ | 0.50 [0.42, 0.59]↓ | 0.51 · cross-node | 5% (1%) | 29% (54%) | kn169:147+kn175:3 |
| longbench_v2 | cactus | high | 0.35 | 150 | 3.38 (0.05) | 4089 (1403) | 2.92 [2.37, 3.56]↑ | 0.58 [0.49, 0.70]↓ | 0.58 · cross-node | 37% (1%) | 24% (54%) | kn175:147+kn176:3 |
| longbench_v2 | spec_casc_opt | low+mid+high | 0.05 | 150 | 0.18 (0.05) | 1414 (1403) | 1.01 [0.86, 1.18] | 0.92 [0.78, 1.08] | 0.90 · cross-node | 1% (1%) | 49% (54%) | kn171:147+kn175:3 |
| longbench_v2 | spec_casc_opt | extra | -0.3 | 150 | 0.06 (0.05) | 1414 (1403) | 1.01 [0.86, 1.18] | 1.01 [0.86, 1.18] | 1.00 · cross-node | 1% (1%) | 55% (54%) | kn174 |
| longbench_v2 | r_fuzzy | low+mid+high | 0.15 | 150 | 0.06 (0.05) | 1368 (1403) | 0.98 [0.86, 1.10] | 0.97 [0.86, 1.10] | 0.94 · cross-node | 1% (1%) | 57% (54%) | kn175:147+kn172:3 |
| longbench_v2 | r_fuzzy | extra | 0.03 | 150 | 0.06 (0.05) | 1430 (1403) | 1.02 [0.89, 1.16] | 1.02 [0.89, 1.16] | 0.99 · cross-node | 1% (1%) | 51% (54%) | kn171 |
| longbench_v2 | r_fuzzy | extra | 0.25 | 150 | 0.06 (0.05) | 1556 (1403) | 1.11 [0.97, 1.27] | 1.10 [0.96, 1.26] | 1.08 · cross-node | 2% (1%) | 57% (54%) | kn173 |
| longbench_v2 | spec_casc_tok | low+mid+high | 0.8 | 150 | 0.06 (0.05) | 1428 (1403) | 1.02 [0.88, 1.17] | 1.02 [0.88, 1.17] | 0.99 · cross-node | 2% (1%) | 51% (54%) | kn171:147+kn175:3 |
| longbench_v2 | spec_casc_tok | extra | 0.15 | 150 | 0.05 (0.05) | 1270 (1403) | 0.91 [0.80, 1.02] | 0.90 [0.81, 1.02] | 0.89 · cross-node | 0% (1%) | 57% (54%) | kn169:147+kn176:3 |

### Block 3b: Qwen/Qwen3-8B + deepseek-ai/dspark_qwen3_8b_block7, longbench_v2 (killarney)

GPU-h actual (lane journals): 8.8.

`campaign/addendum/tables/step9__qwen3-8b__dspark.csv` (dspark, V2 accept-test-only):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| longbench_v2_qwen3 | mentored_dec | low | 0.55 | 150 | 2.33 (1.88) | 2809 (2948) | 0.95 [0.89, 1.02] | 0.82 [0.77, 0.88]↓ | 0.84 · T same-node 0.83 (147 pairs) | 3% (4%) | 50% (47%) | kn175:147+kn173:3 |
| longbench_v2_qwen3 | mentored_dec | mid+high | 0.35 | 150 | 2.18 (1.88) | 2937 (2948) | 1.00 [0.93, 1.06] | 0.89 [0.84, 0.95]↓ | 0.90 · cross-node | 5% (4%) | 50% (47%) | kn171:147+kn175:3 |
| longbench_v2_qwen3 | mentored_dec | extra | 0.15 | 150 | 2.04 (1.88) | 2915 (2948) | 0.99 [0.93, 1.05] | 0.93 [0.87, 0.99]↓ | 0.95 · T same-node 0.95 (147 pairs) | 3% (4%) | 47% (47%) | kn175:147+kn174:3 |
| longbench_v2_qwen3 | cactus | low | 0.08 | 150 | 2.35 (1.88) | 3043 (2948) | 1.03 [0.97, 1.10] | 0.88 [0.82, 0.94]↓ | 0.91 · cross-node | 3% (4%) | 53% (47%) | kn169:147+kn172:3 |
| longbench_v2_qwen3 | cactus | mid+high | 0.35 | 150 | 2.73 (1.88) | 2869 (2948) | 0.97 [0.90, 1.05] | 0.74 [0.69, 0.80]↓ | 0.77 · T same-node 0.74 (84 pairs) | 5% (4%) | 47% (47%) | kn175:84+kn176:63+kn169:3 |
| longbench_v2_qwen3 | cactus | extra | 0.03 | 150 | 2.15 (1.88) | 2986 (2948) | 1.01 [0.94, 1.09] | 0.92 [0.85, 0.99]↓ | 0.93 · T same-node 0.92 (147 pairs) | 5% (4%) | 51% (47%) | kn175:147+kn169:3 |
| longbench_v2_qwen3 | spec_casc_opt | low | -0.3 | 150 | 2.37 (1.88) | 2983 (2948) | 1.01 [0.94, 1.09] | 0.84 [0.79, 0.90]↓ | 0.86 · T same-node 0.86 (147 pairs) | 7% (4%) | 44% (47%) | kn175:147+kn176:3 |
| longbench_v2_qwen3 | spec_casc_opt | mid | -0.02 | 150 | 3.01 (1.88) | 3105 (2948) | 1.05 [0.96, 1.15] | 0.73 [0.67, 0.80]↓ | 0.76 · cross-node | 9% (4%) | 45% (47%) | kn173:147+kn169:3 |
| longbench_v2_qwen3 | spec_casc_opt | high | 0.05 | 150 | 3.46 (1.88) | 3257 (2948) | 1.10 [1.01, 1.21]↑ | 0.67 [0.62, 0.74]↓ | 0.72 · cross-node | 17% (4%) | 42% (47%) | kn172:123+kn171:24+kn175:3 |
| longbench_v2_qwen3 | r_fuzzy | low | 0.15 | 150 | 2.22 (1.88) | 3156 (2948) | 1.07 [0.99, 1.16] | 0.95 [0.87, 1.03] | 0.96 · cross-node | 7% (4%) | 44% (47%) | kn176:81+kn174:66+kn171:3 |
| longbench_v2_qwen3 | r_fuzzy | mid+high | 0.25 | 150 | 2.62 (1.88) | 3124 (2948) | 1.06 [0.96, 1.16] | 0.83 [0.75, 0.91]↓ | 0.85 · cross-node | 10% (4%) | 39% (47%) | kn169:147+kn174:3 |
| longbench_v2_qwen3 | r_fuzzy | extra | 0.03 | 150 | 1.92 (1.88) | 3104 (2948) | 1.05 [0.99, 1.12] | 1.03 [0.97, 1.09] | 1.02 · cross-node | 4% (4%) | 49% (47%) | kn171:147+kn176:3 |
| longbench_v2_qwen3 | spec_casc_tok | low+mid+high | 0.8 | 150 | 2.29 (1.88) | 2777 (2948) | 0.94 [0.88, 1.00] | 0.81 [0.76, 0.87]↓ | 0.83 · cross-node | 3% (4%) | 50% (47%) | kn174:147+kn169:3 |
| longbench_v2_qwen3 | spec_casc_tok | extra | 0.15 | 150 | 2.00 (1.88) | 2864 (2948) | 0.97 [0.90, 1.04] | 0.93 [0.86, 1.00]↓ | 0.93 · T same-node 0.93 (134 pairs) | 3% (4%) | 47% (47%) | kn175:134+kn173:16 |

### Block 3c: meta-llama/Llama-3.1-8B-Instruct + yuhuili/EAGLE3-LLaMA3.1-Instruct-8B, longbench_v2 (killarney)

GPU-h actual (lane journals): 9.9.

`campaign/addendum/tables/step9__llama31-8b-instruct__eagle3.csv` (eagle3, V2 accept-test-only):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| longbench_v2_llama31 | mentored_dec | low+mid+high | 0.75 | 150 | 0.27 (0.06) | 1671 (525) | 3.18 [2.33, 4.25]↑ | 2.19 [1.68, 2.78]↑ | 1.98 | 3% (0%) | 37% (37%) | kn171 |
| longbench_v2_llama31 | mentored_dec | extra | 0.15 | 150 | 0.07 (0.06) | 770 (525) | 1.47 [1.05, 2.01]↑ | 1.36 [1.03, 1.76]↑ | 1.31 · T same-node 1.31 (147 pairs) | 1% (0%) | 35% (37%) | kn171:147+kn169:3 |
| longbench_v2_llama31 | cactus | low+mid | 0.03 | 150 | 2.65 (0.06) | 7537 (525) | 14.36 [11.24, 18.19]↑ | 4.47 [3.61, 5.45]↑ | 3.91 · cross-node | 83% (0%) | 25% (37%) | kn174:147+kn176:3 |
| longbench_v2_llama31 | cactus | high | 0.18 | 150 | 3.63 (0.06) | 6938 (525) | 13.22 [10.31, 16.78]↑ | 3.22 [2.62, 3.93]↑ | 2.87 · cross-node | 70% (0%) | 25% (37%) | kn169:147+kn175:3 |
| longbench_v2_llama31 | cactus | extra | 0.35 | 150 | 4.00 (0.06) | 6725 (525) | 12.81 [10.00, 16.23]↑ | 2.90 [2.34, 3.53]↑ | 2.58 · T same-node 2.56 (147 pairs) | 63% (0%) | 31% (37%) | kn171:147+kn173:3 |
| longbench_v2_llama31 | spec_casc_opt | low | -0.1 | 150 | 0.91 (0.06) | 2494 (525) | 4.75 [3.61, 6.19]↑ | 2.11 [1.68, 2.63]↑ | 1.92 | 13% (0%) | 27% (37%) | kn171 |
| longbench_v2_llama31 | spec_casc_opt | mid | -0.02 | 150 | 2.69 (0.06) | 3277 (525) | 6.24 [4.75, 8.12]↑ | 1.49 [1.18, 1.84]↑ | 1.41 · cross-node | 19% (0%) | 25% (37%) | kn169:147+kn171:3 |
| longbench_v2_llama31 | spec_casc_opt | high | 0.05 | 150 | 4.12 (0.06) | 4336 (525) | 8.26 [6.32, 10.57]↑ | 1.53 [1.22, 1.89]↑ | 1.46 · T same-node 1.45 (147 pairs) | 33% (0%) | 27% (37%) | kn171:147+kn175:3 |
| longbench_v2_llama31 | r_fuzzy | low+mid+high | 0.25 | 150 | 0.10 (0.06) | 1281 (525) | 2.44 [1.71, 3.27]↑ | 2.18 [1.61, 2.86]↑ | 2.00 · cross-node | 3% (0%) | 32% (37%) | kn175 |
| longbench_v2_llama31 | r_fuzzy | extra | 0.03 | 150 | 0.06 (0.06) | 536 (525) | 1.02 [1.00, 1.07] | 1.02 [1.00, 1.08] | 1.03 · cross-node | 0% (0%) | 38% (37%) | kn174:147+kn169:3 |
| longbench_v2_llama31 | spec_casc_tok | low+mid+high | 0.15 | 150 | 0.06 (0.06) | 557 (525) | 1.06 [0.83, 1.33] | 1.04 [0.85, 1.25] | 1.04 · cross-node | 0% (0%) | 37% (37%) | kn175:147+kn171:3 |
| longbench_v2_llama31 | spec_casc_tok | extra | 0.8 | 150 | 0.07 (0.06) | 555 (525) | 1.06 [0.78, 1.43] | 1.02 [0.81, 1.29] | 1.02 · cross-node | 1% (0%) | 39% (37%) | kn169:147+kn173:3 |

### Block 3d: meta-llama/Llama-3.1-8B-Instruct + yuhuili/EAGLE-LLaMA3.1-Instruct-8B, longbench_v2 (killarney)

GPU-h actual (lane journals): 9.7.

`campaign/addendum/tables/step9__llama31-8b-instruct__eagle1.csv` (eagle1, V2 accept-test-only):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| longbench_v2_llama31 | mentored_dec | low+mid+high | 0.35 | 150 | 1.03 (0.92) | 994 (705) | 1.41 [0.97, 2.04] | 1.37 [0.90, 2.11] | 1.32 · cross-node | 4% (1%) | 35% (35%) | kn177:91+kn171:59 |
| longbench_v2_llama31 | mentored_dec | extra | 0.15 | 150 | 0.98 (0.92) | 586 (705) | 0.83 [0.55, 1.26] | 0.77 [0.48, 1.22] | 0.80 · cross-node | 1% (1%) | 28% (35%) | kn175:147+kn169:3 |
| longbench_v2_llama31 | mentored_dec | extra | 0.75 | 150 | 1.05 (0.92) | 3083 (705) | 4.37 [3.16, 6.20]↑ | 3.94 [2.80, 5.84]↑ | 3.46 · cross-node | 19% (1%) | 26% (35%) | kn171:147+kn175:3 |
| longbench_v2_llama31 | cactus | low | 0.03 | 150 | 1.83 (0.92) | 6977 (705) | 9.89 [7.38, 13.78]↑ | 6.34 [4.61, 9.31]↑ | 5.47 · cross-node | 79% (1%) | 20% (35%) | kn173:147+kn175:3 |
| longbench_v2_llama31 | cactus | mid | 0.08 | 150 | 2.06 (0.92) | 6682 (705) | 9.48 [7.02, 13.21]↑ | 5.80 [4.16, 8.58]↑ | 5.03 · cross-node | 75% (1%) | 19% (35%) | kn175:147+kn171:3 |
| longbench_v2_llama31 | cactus | high | 0.35 | 150 | 2.78 (0.92) | 5734 (705) | 8.13 [6.02, 11.42]↑ | 4.26 [2.99, 6.34]↑ | 3.76 · cross-node | 57% (1%) | 22% (35%) | kn171:147+kn175:3 |
| longbench_v2_llama31 | spec_casc_opt | low | -0.3 | 150 | 1.19 (0.92) | 1186 (705) | 1.68 [1.15, 2.48]↑ | 1.14 [0.78, 1.74] | 1.13 · cross-node | 6% (1%) | 27% (35%) | kn174:147+kn173:3 |
| longbench_v2_llama31 | spec_casc_opt | mid | -0.02 | 150 | 2.21 (0.92) | 2228 (705) | 3.16 [2.22, 4.56]↑ | 1.28 [0.89, 1.95] | 1.25 · cross-node | 19% (1%) | 22% (35%) | kn173 |
| longbench_v2_llama31 | spec_casc_opt | high | 0.05 | 150 | 3.03 (0.92) | 2991 (705) | 4.24 [2.98, 6.10]↑ | 1.35 [0.94, 2.02] | 1.32 · cross-node | 28% (1%) | 21% (35%) | kn173:147+kn175:3 |
| longbench_v2_llama31 | r_fuzzy | low+mid+high | 0.03 | 150 | 0.88 (0.92) | 838 (705) | 1.19 [0.78, 1.82] | 1.25 [0.78, 2.04] | 1.21 · cross-node | 1% (1%) | 36% (35%) | kn175:100+kn171:50 |
| longbench_v2_llama31 | r_fuzzy | extra | 0.25 | 150 | 0.76 (0.92) | 4658 (705) | 6.61 [4.82, 9.34]↑ | 6.75 [4.85, 9.98]↑ | 5.81 · T same-node 5.30 (130 pairs) | 27% (1%) | 22% (35%) | kn169:130+kn174:20 |
| longbench_v2_llama31 | spec_casc_tok | low+mid+high | 0.55 | 150 | 1.04 (0.92) | 514 (705) | 0.73 [0.54, 1.02] | 0.62 [0.43, 0.92]↓ | 0.68 · T same-node 0.68 (147 pairs) | 0% (1%) | 36% (35%) | kn169:147+kn171:3 |
| longbench_v2_llama31 | spec_casc_tok | extra | 0.15 | 150 | 1.00 (0.92) | 516 (705) | 0.73 [0.51, 1.07] | 0.65 [0.44, 1.02] | 0.71 · cross-node | 0% (1%) | 35% (35%) | kn175 |
| longbench_v2_llama31 | spec_casc_tok | extra | 0.8 | 150 | 1.07 (0.92) | 486 (705) | 0.69 [0.50, 0.97]↓ | 0.57 [0.40, 0.86]↓ | 0.64 · cross-node | 0% (1%) | 37% (35%) | kn174 |

### Block 3e: deepseek-ai/DeepSeek-R1-Distill-Llama-8B + yuhuili/EAGLE3-DeepSeek-R1-Distill-LLaMA-8B, longbench_v2 (killarney)

GPU-h actual (lane journals): 15.1.

`campaign/addendum/tables/step9__r1-distill-llama-8b__eagle3.csv` (eagle3, V2 accept-test-only):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| longbench_v2_r1llama | mentored_dec | low+mid+high | 0.75 | 150 | 0.05 (0.03) | 1973 (1911) | 1.03 [0.94, 1.13] | 1.01 [0.92, 1.11] | 1.01 · cross-node | 1% (4%) | 35% (29%) | kn173:147+kn174:3 |
| longbench_v2_r1llama | mentored_dec | extra | 0.15 | 150 | 0.03 (0.03) | 1982 (1911) | 1.04 [0.96, 1.11] | 1.04 [0.97, 1.11] | 1.05 · cross-node | 6% (4%) | 34% (29%) | kn175:147+kn173:3 |
| longbench_v2_r1llama | cactus | low+mid | 0.03 | 150 | 2.80 (0.03) | 7413 (1911) | 3.88 [3.32, 4.58]↑ | 1.07 [0.92, 1.27] | 1.08 · cross-node | 85% (4%) | 26% (29%) | kn175:147+kn172:3 |
| longbench_v2_r1llama | cactus | high | 0.08 | 150 | 3.37 (0.03) | 7641 (1911) | 4.00 [3.43, 4.74]↑ | 0.99 [0.84, 1.18] | 1.01 · cross-node | 88% (4%) | 29% (29%) | kn174:147+kn176:3 |
| longbench_v2_r1llama | cactus | extra | 0.35 | 150 | 4.04 (0.03) | 7713 (1911) | 4.04 [3.45, 4.80]↑ | 0.86 [0.73, 1.02] | 0.87 · cross-node | 87% (4%) | 23% (29%) | kn173:147+kn172:3 |
| longbench_v2_r1llama | spec_casc_opt | low+mid+high | 0.05 | 150 | 0.43 (0.03) | 2352 (1911) | 1.23 [1.09, 1.39]↑ | 0.83 [0.75, 0.92]↓ | 0.84 · cross-node | 6% (4%) | 33% (29%) | kn174:147+kn175:3 |
| longbench_v2_r1llama | spec_casc_opt | extra | -0.3 | 150 | 0.07 (0.03) | 1815 (1911) | 0.95 [0.86, 1.05] | 0.91 [0.83, 1.00] | 0.92 · T same-node 0.87 (15 pairs) | 4% (4%) | 32% (29%) | kn169:132+kn171:15+kn172:3 |
| longbench_v2_r1llama | r_fuzzy | low+mid+high | 0.03 | 150 | 0.03 (0.03) | 1891 (1911) | 0.99 [0.97, 1.01] | 0.99 [0.97, 1.01] | 0.99 · T same-node 0.99 (147 pairs) | 3% (4%) | 29% (29%) | kn171:147+kn173:3 |
| longbench_v2_r1llama | r_fuzzy | extra | 0.25 | 150 | 0.04 (0.03) | 1935 (1911) | 1.01 [0.92, 1.11] | 1.01 [0.92, 1.11] | 1.01 · cross-node | 3% (4%) | 35% (29%) | kn173:147+kn175:3 |
| longbench_v2_r1llama | spec_casc_tok | low+mid+high | 0.15 | 150 | 0.03 (0.03) | 1936 (1911) | 1.01 [0.96, 1.07] | 1.01 [0.96, 1.07] | 1.02 · cross-node | 7% (4%) | 32% (29%) | kn169:147+kn175:3 |
| longbench_v2_r1llama | spec_casc_tok | extra | 0.8 | 150 | 0.03 (0.03) | 1954 (1911) | 1.02 [0.95, 1.10] | 1.02 [0.95, 1.09] | 1.02 · cross-node | 3% (4%) | 32% (29%) | kn173:143+kn175:7 |

### Block 4a: openai/gpt-oss-20b + RedHatAI/gpt-oss-20b-speculator.eagle3, humaneval (killarney)

GPU-h actual (lane journals): 6.6.

`campaign/addendum/tables/step9__gpt-oss-20b__rh-eagle3.csv` (eagle3, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| humaneval | mentored_dec | low | 0.55 | 150 | 2.51 (2.04) | 1137 (911) | 1.25 [1.11, 1.41]↑ | 1.11 [0.95, 1.30] | 1.13 · cross-node | 0% (0%) | 96% (98%) | kn169:147+kn171:3 |
| humaneval | mentored_dec | mid+high | 0.75 | 150 | 2.74 (2.04) | 1347 (911) | 1.48 [1.32, 1.65]↑ | 1.30 [1.08, 1.55]↑ | 1.33 · cross-node | 1% (0%) | 95% (98%) | kn175:147+kn174:3 |
| humaneval | mentored_dec | extra | 0.15 | 150 | 2.14 (2.04) | 977 (911) | 1.07 [0.94, 1.23] | 1.10 [0.91, 1.33] | 1.12 · T same-node 1.13 (147 pairs) | 1% (0%) | 95% (98%) | kn173:147+kn169:3 |
| humaneval | cactus | low | 0.03 | 150 | 2.94 (2.04) | 1649 (911) | 1.81 [1.58, 2.06]↑ | 1.41 [1.21, 1.63]↑ | 1.42 · cross-node | 4% (0%) | 87% (98%) | kn169:147+kn174:3 |
| humaneval | cactus | mid | 0.08 | 150 | 3.41 (2.04) | 2061 (911) | 2.26 [1.97, 2.57]↑ | 1.54 [1.31, 1.80]↑ | 1.57 · cross-node | 7% (0%) | 77% (98%) | kn175:147+kn173:3 |
| humaneval | cactus | high | 0.18 | 150 | 3.85 (2.04) | 2762 (911) | 3.03 [2.65, 3.44]↑ | 1.80 [1.57, 2.06]↑ | 1.79 · cross-node | 15% (0%) | 63% (98%) | kn175 |
| humaneval | spec_casc_opt | low | 0.05 | 150 | 2.52 (2.04) | 1477 (911) | 1.62 [1.46, 1.80]↑ | 1.43 [1.25, 1.63]↑ | 1.46 · T same-node 1.46 (147 pairs) | 1% (0%) | 84% (98%) | kn173:147+kn175:3 |
| humaneval | spec_casc_opt | mid+high | -0.02 | 150 | 2.47 (2.04) | 1192 (911) | 1.31 [1.14, 1.51]↑ | 1.16 [0.99, 1.38] | 1.18 · cross-node | 1% (0%) | 89% (98%) | kn175 |
| humaneval | spec_casc_opt | extra | -0.3 | 150 | 2.25 (2.04) | 920 (911) | 1.01 [0.92, 1.10] | 0.94 [0.84, 1.03] | 0.96 · cross-node | 0% (0%) | 93% (98%) | kn171:147+kn176:3 |
| humaneval | r_fuzzy | low | 0.15 | 150 | 2.37 (2.04) | 1556 (911) | 1.71 [1.56, 1.87]↑ | 1.63 [1.44, 1.83]↑ | 1.64 · cross-node | 0% (0%) | 47% (98%) | kn174:147+kn169:3 |
| humaneval | r_fuzzy | mid+high | 0.25 | 150 | 2.94 (2.04) | 2834 (911) | 3.11 [2.73, 3.51]↑ | 2.70 [2.29, 3.15]↑ | 2.68 · T same-node 2.67 (147 pairs) | 3% (0%) | 23% (98%) | kn173:147+kn176:3 |
| humaneval | r_fuzzy | extra | 0.03 | 150 | 2.03 (2.04) | 986 (911) | 1.08 [0.97, 1.21] | 1.10 [0.96, 1.24] | 1.11 · cross-node | 0% (0%) | 77% (98%) | kn175:91+kn169:59 |
| humaneval | spec_casc_tok | low+mid+high | 0.8 | 150 | 2.21 (2.04) | 976 (911) | 1.07 [0.96, 1.19] | 1.02 [0.90, 1.16] | 1.05 · T same-node 1.06 (147 pairs) | 0% (0%) | 97% (98%) | kn173:147+kn175:3 |
| humaneval | spec_casc_tok | extra | 0.15 | 150 | 2.02 (2.04) | 973 (911) | 1.07 [0.93, 1.22] | 1.12 [0.94, 1.32] | 1.12 · cross-node | 0% (0%) | 96% (98%) | kn176:147+kn174:3 |

### Block 4b: Qwen/Qwen3-8B + deepseek-ai/dspark_qwen3_8b_block7, humaneval (killarney)

GPU-h actual (lane journals): 8.1.

`campaign/addendum/tables/step9__qwen3-8b__dspark.csv` (dspark, V2 accept-test-only):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| humaneval_qwen3 | mentored_dec | low | 0.55 | 150 | 2.80 (2.50) | 3909 (3756) | 1.04 [0.97, 1.12] | 0.94 [0.88, 1.00] | 0.93 · cross-node | 12% (11%) | 85% (84%) | kn175:75+kn173:75 |
| humaneval_qwen3 | mentored_dec | mid+high | 0.75 | 150 | 2.98 (2.50) | 4122 (3756) | 1.10 [1.03, 1.17]↑ | 0.93 [0.88, 0.99]↓ | 0.93 · cross-node | 17% (11%) | 80% (84%) | kn175 |
| humaneval_qwen3 | mentored_dec | extra | 0.15 | 150 | 2.55 (2.50) | 3815 (3756) | 1.02 [0.94, 1.10] | 0.99 [0.92, 1.07] | 0.99 · T same-node 1.03 (64 pairs) | 9% (11%) | 85% (84%) | kn174:83+kn169:64+kn173:3 |
| humaneval_qwen3 | cactus | low | 0.08 | 150 | 2.76 (2.50) | 4083 (3756) | 1.09 [1.03, 1.15]↑ | 0.99 [0.94, 1.06] | 0.98 · cross-node | 15% (11%) | 83% (84%) | kn173:119+kn171:28+kn175:3 |
| humaneval_qwen3 | cactus | mid+high | 0.35 | 150 | 3.01 (2.50) | 4150 (3756) | 1.11 [1.04, 1.18]↑ | 0.93 [0.87, 1.00]↓ | 0.94 · cross-node | 15% (11%) | 82% (84%) | kn173 |
| humaneval_qwen3 | cactus | extra | 0.03 | 150 | 2.67 (2.50) | 3747 (3756) | 1.00 [0.93, 1.06] | 0.94 [0.88, 1.00] | 0.92 · cross-node | 8% (11%) | 89% (84%) | kn173:106+kn175:41+kn174:3 |
| humaneval_qwen3 | spec_casc_opt | low | -0.3 | 150 | 2.76 (2.50) | 4000 (3756) | 1.07 [1.00, 1.13]↑ | 0.97 [0.91, 1.04] | 0.96 · cross-node | 15% (11%) | 82% (84%) | kn174:147+kn169:3 |
| humaneval_qwen3 | spec_casc_opt | mid | -0.1 | 150 | 2.96 (2.50) | 4013 (3756) | 1.07 [1.00, 1.14]↑ | 0.92 [0.86, 0.98]↓ | 0.90 · cross-node | 13% (11%) | 81% (84%) | kn175:147+kn174:3 |
| humaneval_qwen3 | spec_casc_opt | high | 0.05 | 150 | 3.50 (2.50) | 5354 (3756) | 1.43 [1.33, 1.54]↑ | 1.09 [1.01, 1.17]↑ | 1.10 · cross-node | 27% (11%) | 61% (84%) | kn177:78+kn173:69+kn174:3 |
| humaneval_qwen3 | r_fuzzy | low | 0.15 | 150 | 2.91 (2.50) | 4165 (3756) | 1.11 [1.02, 1.20]↑ | 1.00 [0.92, 1.07] | 0.99 · cross-node | 14% (11%) | 70% (84%) | kn173:119+kn177:31 |
| humaneval_qwen3 | r_fuzzy | mid | 0.25 | 150 | 3.27 (2.50) | 4671 (3756) | 1.24 [1.15, 1.35]↑ | 1.01 [0.94, 1.09] | 1.02 · cross-node | 22% (11%) | 64% (84%) | kn176:147+kn171:3 |
| humaneval_qwen3 | r_fuzzy | high | 0.03 | 150 | 2.60 (2.50) | 3801 (3756) | 1.01 [0.94, 1.09] | 0.99 [0.92, 1.06] | 0.99 · cross-node | 9% (11%) | 80% (84%) | kn171:147+kn173:3 |
| humaneval_qwen3 | spec_casc_tok | low+mid+high | 0.8 | 150 | 2.75 (2.50) | 3931 (3756) | 1.05 [0.99, 1.11] | 0.95 [0.90, 1.01] | 0.94 · cross-node | 13% (11%) | 81% (84%) | kn176:147+kn174:3 |
| humaneval_qwen3 | spec_casc_tok | extra | 0.15 | 150 | 2.52 (2.50) | 3835 (3756) | 1.02 [0.95, 1.10] | 1.01 [0.95, 1.08] | 1.01 · T same-node 1.02 (54 pairs) | 9% (11%) | 85% (84%) | kn173:93+kn169:54+kn171:3 |

### Block 4c: meta-llama/Llama-3.1-8B-Instruct + yuhuili/EAGLE3-LLaMA3.1-Instruct-8B, humaneval (killarney)

GPU-h actual (lane journals): 5.4.

`campaign/addendum/tables/step9__llama31-8b-instruct__eagle3.csv` (eagle3, V2 accept-test-only):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| humaneval_llama31 | mentored_dec | low | 0.35 | 150 | 3.02 (2.70) | 623 (547) | 1.14 [0.99, 1.34] | 1.14 [0.84, 1.52] | 1.16 · cross-node | 0% (0%) | 53% (56%) | kn175:147+kn171:3 |
| humaneval_llama31 | mentored_dec | mid+high | 0.55 | 150 | 3.10 (2.70) | 702 (547) | 1.28 [1.10, 1.50]↑ | 1.37 [1.04, 1.79]↑ | 1.36 · cross-node | 0% (0%) | 45% (56%) | kn174:147+kn173:3 |
| humaneval_llama31 | mentored_dec | extra | 0.15 | 150 | 2.88 (2.70) | 566 (547) | 1.03 [0.94, 1.14] | 0.97 [0.79, 1.17] | 0.99 · cross-node | 0% (0%) | 47% (56%) | kn171:147+kn169:3 |
| humaneval_llama31 | cactus | low+mid | 0.03 | 150 | 3.62 (2.70) | 7088 (547) | 12.95 [11.64, 14.24]↑ | 9.54 [7.93, 11.03]↑ | 9.62 · cross-node | 61% (0%) | 13% (56%) | kn174:147+kn173:3 |
| humaneval_llama31 | cactus | high | 0.18 | 150 | 4.33 (2.70) | 7244 (547) | 13.23 [11.91, 14.55]↑ | 8.47 [7.00, 9.86]↑ | 8.58 · cross-node | 35% (0%) | 5% (56%) | kn175:147+kn173:3 |
| humaneval_llama31 | cactus | extra | 0.35 | 150 | 4.56 (2.70) | 7298 (547) | 13.33 [11.99, 14.75]↑ | 8.25 [6.85, 9.64]↑ | 8.21 · cross-node | 42% (0%) | 4% (56%) | kn176:147+kn174:3 |
| humaneval_llama31 | spec_casc_opt | low | -0.1 | 150 | 2.99 (2.70) | 746 (547) | 1.36 [1.15, 1.61]↑ | 1.37 [1.03, 1.80]↑ | 1.39 · cross-node | 0% (0%) | 42% (56%) | kn176:147+kn173:3 |
| humaneval_llama31 | spec_casc_opt | mid | -0.3 | 150 | 2.96 (2.70) | 622 (547) | 1.14 [1.00, 1.29]↑ | 1.08 [0.85, 1.38] | 1.10 · cross-node | 0% (0%) | 44% (56%) | kn176:147+kn173:3 |
| humaneval_llama31 | spec_casc_opt | high | 0.05 | 150 | 3.74 (2.70) | 1040 (547) | 1.90 [1.54, 2.34]↑ | 1.34 [1.05, 1.69]↑ | 1.35 · cross-node | 0% (0%) | 35% (56%) | kn175:147+kn171:3 |
| humaneval_llama31 | r_fuzzy | low | 0.25 | 150 | 0.92 (2.70) | 3856 (547) | 7.04 [6.29, 7.80]↑ | 15.04 [12.33, 17.55]↑ | 14.79 · cross-node | 1% (0%) | 16% (56%) | kn175:147+kn173:3 |
| humaneval_llama31 | r_fuzzy | mid+high | 0.08 | 150 | 2.03 (2.70) | 1517 (547) | 2.77 [2.32, 3.25]↑ | 5.16 [3.97, 6.45]↑ | 5.09 · T same-node 5.13 (147 pairs) | 0% (0%) | 27% (56%) | kn173:147+kn175:3 |
| humaneval_llama31 | r_fuzzy | extra | 0.03 | 150 | 2.58 (2.70) | 621 (547) | 1.13 [1.02, 1.27]↑ | 1.21 [0.97, 1.51] | 1.21 | 0% (0%) | 35% (56%) | kn173 |
| humaneval_llama31 | spec_casc_tok | low | 0.35 | 150 | 2.87 (2.70) | 560 (547) | 1.02 [0.93, 1.12] | 0.95 [0.78, 1.13] | 0.97 | 0% (0%) | 55% (56%) | kn173 |
| humaneval_llama31 | spec_casc_tok | mid+high | 0.55 | 150 | 2.97 (2.70) | 559 (547) | 1.02 [0.93, 1.11] | 0.89 [0.75, 1.02] | 0.91 · cross-node | 0% (0%) | 53% (56%) | kn175:147+kn169:3 |
| humaneval_llama31 | spec_casc_tok | extra | 0.15 | 150 | 2.86 (2.70) | 536 (547) | 0.98 [0.90, 1.06] | 0.88 [0.73, 1.01] | 0.90 · cross-node | 0% (0%) | 59% (56%) | kn174 |

### Block 4d: meta-llama/Llama-3.1-8B-Instruct + yuhuili/EAGLE-LLaMA3.1-Instruct-8B, humaneval (killarney)

GPU-h actual (lane journals): 4.1.

`campaign/addendum/tables/step9__llama31-8b-instruct__eagle1.csv` (eagle1, V2 accept-test-only):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| humaneval_llama31 | mentored_dec | low+mid+high | 0.15 | 150 | 1.83 (1.76) | 543 (529) | 1.03 [0.97, 1.09] | 1.00 [0.94, 1.08] | 1.01 · T same-node 1.01 (147 pairs) | 0% (0%) | 53% (58%) | kn177:147+kn173:3 |
| humaneval_llama31 | mentored_dec | extra | 0.75 | 150 | 2.09 (1.76) | 1075 (529) | 2.03 [1.67, 2.47]↑ | 1.93 [1.54, 2.40]↑ | 1.96 · cross-node | 1% (0%) | 33% (58%) | kn173:147+kn169:3 |
| humaneval_llama31 | cactus | low | 0.08 | 150 | 2.58 (1.76) | 5978 (529) | 11.31 [10.20, 12.44]↑ | 9.06 [8.04, 10.17]↑ | 9.35 · cross-node | 39% (0%) | 3% (58%) | kn171:131+kn175:19 |
| humaneval_llama31 | cactus | mid | 0.18 | 150 | 2.95 (1.76) | 6098 (529) | 11.54 [10.40, 12.70]↑ | 8.60 [7.58, 9.70]↑ | 8.70 · cross-node | 40% (0%) | 3% (58%) | kn175:147+kn173:3 |
| humaneval_llama31 | cactus | high | 0.35 | 150 | 4.09 (1.76) | 4953 (529) | 9.37 [8.24, 10.53]↑ | 4.98 [4.37, 5.64]↑ | 5.08 · cross-node | 29% (0%) | 1% (58%) | kn176:147+kn169:3 |
| humaneval_llama31 | spec_casc_opt | low | -0.3 | 150 | 1.97 (1.76) | 645 (529) | 1.22 [1.11, 1.36]↑ | 1.11 [1.03, 1.21]↑ | 1.12 · cross-node | 0% (0%) | 45% (58%) | kn169 |
| humaneval_llama31 | spec_casc_opt | mid+high | 0.05 | 150 | 2.69 (1.76) | 2580 (529) | 4.88 [4.01, 5.78]↑ | 3.33 [2.74, 3.97]↑ | 3.35 · T same-node 3.37 (147 pairs) | 15% (0%) | 8% (58%) | kn177:147+kn175:3 |
| humaneval_llama31 | r_fuzzy | low+mid+high | 0.03 | 150 | 1.70 (1.76) | 735 (529) | 1.39 [1.15, 1.69]↑ | 1.59 [1.23, 2.03]↑ | 1.59 · cross-node | 0% (0%) | 49% (58%) | kn175:147+kn173:3 |
| humaneval_llama31 | r_fuzzy | extra | 0.25 | 150 | 1.46 (1.76) | 4119 (529) | 7.79 [6.84, 8.79]↑ | 9.12 [7.97, 10.32]↑ | 9.21 · cross-node | 15% (0%) | 5% (58%) | kn169 |
| humaneval_llama31 | spec_casc_tok | low+mid+high | 0.8 | 150 | 1.99 (1.76) | 544 (529) | 1.03 [0.97, 1.09] | 0.94 [0.88, 1.00] | 0.97 · cross-node | 0% (0%) | 54% (58%) | kn175:147+kn173:3 |
| humaneval_llama31 | spec_casc_tok | extra | 0.15 | 150 | 1.84 (1.76) | 556 (529) | 1.05 [0.99, 1.12] | 1.02 [0.95, 1.09] | 1.03 · cross-node | 0% (0%) | 54% (58%) | kn174:147+kn177:3 |

### Block 4e: deepseek-ai/DeepSeek-R1-Distill-Llama-8B + yuhuili/EAGLE3-DeepSeek-R1-Distill-LLaMA-8B, humaneval (killarney)

GPU-h actual (lane journals): 14.8.

`campaign/addendum/tables/step9__r1-distill-llama-8b__eagle3.csv` (eagle3, V2 accept-test-only):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| humaneval_r1llama | mentored_dec | low | 0.15 | 150 | 1.97 (1.89) | 3965 (3739) | 1.06 [0.99, 1.14] | 1.05 [0.95, 1.18] | 1.06 · cross-node | 10% (7%) | 83% (86%) | kn169:147+kn173:3 |
| humaneval_r1llama | mentored_dec | mid+high | 0.55 | 150 | 2.30 (1.89) | 4053 (3739) | 1.08 [1.01, 1.16]↑ | 1.01 [0.91, 1.13] | 1.03 · cross-node | 11% (7%) | 84% (86%) | kn171:88+kn177:59+kn173:3 |
| humaneval_r1llama | mentored_dec | extra | 0.75 | 150 | 2.25 (1.89) | 4509 (3739) | 1.21 [1.12, 1.30]↑ | 1.12 [0.99, 1.26] | 1.13 · cross-node | 10% (7%) | 82% (86%) | kn173 |
| humaneval_r1llama | cactus | low | 0.03 | 150 | 2.52 (1.89) | 6677 (3739) | 1.79 [1.64, 1.95]↑ | 1.20 [1.06, 1.38]↑ | 1.22 · cross-node | 64% (7%) | 25% (86%) | kn174 |
| humaneval_r1llama | cactus | mid | 0.08 | 150 | 3.07 (1.89) | 6952 (3739) | 1.86 [1.70, 2.04]↑ | 1.05 [0.91, 1.21] | 1.08 · cross-node | 71% (7%) | 21% (86%) | kn177:147+kn173:3 |
| humaneval_r1llama | cactus | high | 0.18 | 150 | 3.60 (1.89) | 7370 (3739) | 1.97 [1.81, 2.16]↑ | 0.95 [0.83, 1.10] | 0.96 · cross-node | 77% (7%) | 16% (86%) | kn174:147+kn173:3 |
| humaneval_r1llama | spec_casc_opt | low | -0.1 | 150 | 2.19 (1.89) | 4211 (3739) | 1.13 [1.05, 1.20]↑ | 1.00 [0.91, 1.11] | 1.03 · cross-node | 11% (7%) | 79% (86%) | kn169:123+kn176:24+kn173:3 |
| humaneval_r1llama | spec_casc_opt | mid+high | 0.05 | 150 | 2.32 (1.89) | 4785 (3739) | 1.28 [1.18, 1.39]↑ | 1.01 [0.90, 1.14] | 1.01 · cross-node | 21% (7%) | 59% (86%) | kn173:147+kn174:3 |
| humaneval_r1llama | spec_casc_opt | extra | -0.3 | 150 | 2.16 (1.89) | 3937 (3739) | 1.05 [0.98, 1.14] | 1.00 [0.89, 1.12] | 1.03 · T same-node 1.05 (147 pairs) | 7% (7%) | 81% (86%) | kn175:147+kn171:3 |
| humaneval_r1llama | r_fuzzy | low | 0.08 | 150 | 1.80 (1.89) | 4462 (3739) | 1.19 [1.12, 1.27]↑ | 1.22 [1.10, 1.35]↑ | 1.25 · T same-node 1.28 (81 pairs) | 8% (7%) | 51% (86%) | kn175:81+kn171:69 |
| humaneval_r1llama | r_fuzzy | mid+high | 0.25 | 150 | 1.70 (1.89) | 6099 (3739) | 1.63 [1.51, 1.77]↑ | 1.63 [1.45, 1.86]↑ | 1.64 · cross-node | 17% (7%) | 17% (86%) | kn173:147+kn171:3 |
| humaneval_r1llama | r_fuzzy | extra | 0.03 | 150 | 1.84 (1.89) | 4090 (3739) | 1.09 [1.02, 1.17]↑ | 1.11 [1.00, 1.23]↑ | 1.13 · cross-node | 9% (7%) | 71% (86%) | kn176:147+kn173:3 |
| humaneval_r1llama | spec_casc_tok | low | 0.8 | 150 | 2.16 (1.89) | 3819 (3739) | 1.02 [0.95, 1.09] | 0.97 [0.87, 1.09] | 1.00 · cross-node | 10% (7%) | 81% (86%) | kn173 |
| humaneval_r1llama | spec_casc_tok | mid+high | 0.55 | 150 | 2.07 (1.89) | 3684 (3739) | 0.99 [0.91, 1.07] | 0.98 [0.86, 1.10] | 0.99 · cross-node | 7% (7%) | 83% (86%) | kn173 |
| humaneval_r1llama | spec_casc_tok | extra | 0.15 | 150 | 1.97 (1.89) | 3637 (3739) | 0.97 [0.91, 1.04] | 0.96 [0.86, 1.08] | 0.99 · cross-node | 9% (7%) | 87% (86%) | kn174:147+kn175:3 |

### Block 5a: meta-llama/Llama-3.1-8B-Instruct + yuhuili/EAGLE3-LLaMA3.1-Instruct-8B, aime24 (killarney)

GPU-h actual (lane journals): 3.4.

`campaign/addendum/tables/step9__llama31-8b-instruct__eagle3.csv` (eagle3, V2 accept-test-only):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aime24_llama31 | mentored_dec | low+mid+high | 0.75 | 30 | 1.63 (0.77) | 10479 (3661) | 2.86 [1.97, 4.03]↑ | 1.70 [1.19, 2.43]↑ | 1.76 · cross-node | 0% (0%) | 3% (3%) | kn176:27+kn173:3 |
| aime24_llama31 | mentored_dec | extra | 0.15 | 30 | 0.95 (0.77) | 4044 (3661) | 1.10 [0.75, 1.57] | 1.08 [0.72, 1.59] | 1.08 · T same-node 1.11 (27 pairs) | 0% (0%) | 7% (3%) | kn177:27+kn169:3 |
| aime24_llama31 | cactus | low+mid | 0.03 | 30 | 4.22 (0.77) | 17947 (3661) | 4.90 [3.52, 6.90]↑ | 1.43 [1.03, 2.04]↑ | 1.48 · cross-node | 20% (0%) | 0% (3%) | kn176:27+kn175:3 |
| aime24_llama31 | cactus | high | 0.18 | 30 | 4.86 (0.77) | 15006 (3661) | 4.10 [2.79, 6.00]↑ | 1.08 [0.73, 1.61] | 1.14 · cross-node | 13% (0%) | 0% (3%) | kn174:27+kn169:3 |
| aime24_llama31 | cactus | extra | 0.35 | 30 | 4.99 (0.77) | 11569 (3661) | 3.16 [2.12, 4.76]↑ | 0.80 [0.54, 1.21] | 0.83 · cross-node | 10% (0%) | 0% (3%) | kn169:27+kn173:3 |
| aime24_llama31 | spec_casc_opt | low | -0.1 | 30 | 1.25 (0.77) | 4091 (3661) | 1.12 [0.83, 1.51] | 0.94 [0.65, 1.35] | 0.93 · cross-node | 0% (0%) | 0% (3%) | kn173:27+kn176:3 |
| aime24_llama31 | spec_casc_opt | mid | 0.05 | 30 | 4.49 (0.77) | 2958 (3661) | 0.81 [0.57, 1.13] | 0.21 [0.15, 0.29]↓ | 0.21 · T same-node 0.20 (27 pairs) | 0% (0%) | 0% (3%) | kn177:27+kn169:3 |
| aime24_llama31 | spec_casc_opt | high | -0.02 | 30 | 4.12 (0.77) | 2334 (3661) | 0.64 [0.42, 0.93]↓ | 0.18 [0.12, 0.26]↓ | 0.18 · cross-node | 0% (0%) | 0% (3%) | kn173:27+kn175:3 |
| aime24_llama31 | r_fuzzy | low+mid+high | 0.03 | 30 | 0.69 (0.77) | 3875 (3661) | 1.06 [0.83, 1.34] | 1.08 [0.83, 1.39] | 1.06 · cross-node | 0% (0%) | 3% (3%) | kn175:27+kn169:3 |
| aime24_llama31 | r_fuzzy | extra | 0.25 | 30 | 0.80 (0.77) | 4903 (3661) | 1.34 [1.04, 1.76]↑ | 1.30 [1.00, 1.72] | 1.29 · cross-node | 0% (0%) | 0% (3%) | kn175:27+kn176:3 |
| aime24_llama31 | spec_casc_tok | low+mid+high | 0.8 | 30 | 1.52 (0.77) | 1449 (3661) | 0.40 [0.25, 0.58]↓ | 0.30 [0.16, 0.48]↓ | 0.30 · cross-node | 0% (0%) | 0% (3%) | kn173 |
| aime24_llama31 | spec_casc_tok | extra | 0.15 | 30 | 1.06 (0.77) | 2866 (3661) | 0.78 [0.51, 1.12] | 0.74 [0.44, 1.10] | 0.75 · cross-node | 0% (0%) | 3% (3%) | kn169:27+kn177:3 |

### Block 5b: meta-llama/Llama-3.1-8B-Instruct + yuhuili/EAGLE-LLaMA3.1-Instruct-8B, aime24 (killarney)

GPU-h actual (lane journals): 6.5.

`campaign/addendum/tables/step9__llama31-8b-instruct__eagle1.csv` (eagle1, V2 accept-test-only):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aime24_llama31 | mentored_dec | low | 0.75 | 30 | 1.44 (0.77) | 10093 (4842) | 2.08 [1.60, 2.85]↑ | 1.45 [1.11, 2.02]↑ | 1.45 · cross-node | 0% (0%) | 3% (3%) | kn169:21+kn174:6+kn173:3 |
| aime24_llama31 | mentored_dec | mid+high | 0.15 | 30 | 1.02 (0.77) | 3644 (4842) | 0.75 [0.50, 1.10] | 0.68 [0.45, 1.01] | 0.66 · cross-node | 0% (0%) | 0% (3%) | kn177:27+kn175:3 |
| aime24_llama31 | cactus | low | 0.35 | 30 | 3.38 (0.77) | 14642 (4842) | 3.02 [1.84, 4.85]↑ | 1.28 [0.74, 2.11] | 1.34 · cross-node | 30% (0%) | 0% (3%) | kn176:27+kn174:3 |
| aime24_llama31 | cactus | mid | 0.18 | 30 | 3.01 (0.77) | 16627 (4842) | 3.43 [2.32, 5.12]↑ | 1.51 [1.00, 2.31] | 1.55 · cross-node | 30% (0%) | 0% (3%) | kn176:27+kn169:3 |
| aime24_llama31 | cactus | high | 0.08 | 30 | 3.42 (0.77) | 21347 (4842) | 4.41 [3.01, 6.68]↑ | 1.64 [1.11, 2.49]↑ | 1.71 · cross-node | 53% (0%) | 0% (3%) | kn173 |
| aime24_llama31 | spec_casc_opt | low | -0.3 | 30 | 1.93 (0.77) | 9341 (4842) | 1.93 [0.99, 3.27] | 0.89 [0.47, 1.52] | 0.91 · T same-node 0.97 (27 pairs) | 23% (0%) | 0% (3%) | kn175:27+kn177:3 |
| aime24_llama31 | spec_casc_opt | mid | -0.1 | 30 | 4.02 (0.77) | 16627 (4842) | 3.43 [2.11, 5.43]↑ | 1.05 [0.63, 1.79] | 1.08 · T same-node 1.11 (27 pairs) | 43% (0%) | 0% (3%) | kn175:27+kn173:3 |
| aime24_llama31 | spec_casc_opt | high | -0.02 | 30 | 4.13 (0.77) | 13084 (4842) | 2.70 [1.52, 4.44]↑ | 0.80 [0.43, 1.37] | 0.83 · cross-node | 33% (0%) | 0% (3%) | kn169:27+kn177:3 |
| aime24_llama31 | r_fuzzy | low+mid+high | 0.25 | 30 | 1.45 (0.77) | 5341 (4842) | 1.10 [0.82, 1.51] | 0.76 [0.56, 1.05] | 0.75 · cross-node | 0% (0%) | 0% (3%) | kn173:27+kn176:3 |
| aime24_llama31 | r_fuzzy | extra | 0.03 | 30 | 0.76 (0.77) | 4538 (4842) | 0.94 [0.67, 1.30] | 0.93 [0.66, 1.31] | 0.92 · cross-node | 0% (0%) | 0% (3%) | kn173:27+kn176:3 |
| aime24_llama31 | spec_casc_tok | low+mid+high | 0.35 | 30 | 1.03 (0.77) | 2231 (4842) | 0.46 [0.27, 0.73]↓ | 0.41 [0.23, 0.69]↓ | 0.41 · cross-node | 0% (0%) | 3% (3%) | kn177:27+kn173:3 |
| aime24_llama31 | spec_casc_tok | extra | 0.15 | 30 | 0.93 (0.77) | 2518 (4842) | 0.52 [0.30, 0.85]↓ | 0.49 [0.27, 0.81]↓ | 0.48 · cross-node | 0% (0%) | 7% (3%) | kn173:27+kn175:3 |
| aime24_llama31 | spec_casc_tok | extra | 0.8 | 30 | 1.34 (0.77) | 2344 (4842) | 0.48 [0.19, 1.17] | 0.26 [0.15, 0.47]↓ | 0.26 | 3% (0%) | 3% (3%) | kn175 |

### Phase 2: standalone drafters at each rule's loosest alpha

### Block 6a: Qwen/Qwen3-8B + Qwen/Qwen3-1.7B, humaneval (killarney)

GPU-h actual (lane journals): 6.8.

`campaign/addendum/tables/step9__qwen3-8b__qwen3-1.7b.csv` (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| humaneval_qwen3 | mentored_dec | loosest | 0.75 | 150 | 4.55 (3.71) | 3510 (3876) | 0.91 [0.84, 0.97]↓ | 0.75 [0.70, 0.80]↓ | 0.74 · cross-node | 7% (13%) | 84% (84%) | kn171 |
| humaneval_qwen3 | cactus | loosest | 0.35 | 150 | 4.56 (3.71) | 3462 (3876) | 0.89 [0.83, 0.96]↓ | 0.73 [0.68, 0.79]↓ | 0.73 · cross-node | 9% (13%) | 83% (84%) | kn171 |
| humaneval_qwen3 | spec_casc_opt | loosest | 0.05 | 150 | 4.85 (3.71) | 3584 (3876) | 0.92 [0.86, 1.00]↓ | 0.74 [0.69, 0.80]↓ | 0.74 · cross-node | 9% (13%) | 85% (84%) | kn177 |
| humaneval_qwen3 | r_fuzzy | loosest | 0.25 | 150 | 4.72 (3.71) | 3642 (3876) | 0.94 [0.87, 1.02] | 0.75 [0.70, 0.81]↓ | 0.77 · cross-node | 10% (13%) | 82% (84%) | kn173 |
| humaneval_qwen3 | spec_casc_tok | loosest | 0.8 | 150 | 4.18 (3.71) | 3550 (3876) | 0.92 [0.85, 0.98]↓ | 0.82 [0.76, 0.88]↓ | 0.82 · cross-node | 9% (13%) | 85% (84%) | kn171 |

### Block 6b: Qwen/Qwen3-8B + Qwen/Qwen3-1.7B, longbench_v2 (killarney)

GPU-h actual (lane journals): 5.7.

`campaign/addendum/tables/step9__qwen3-8b__qwen3-1.7b.csv` (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| longbench_v2_qwen3 | mentored_dec | loosest | 0.75 | 150 | 4.46 (3.07) | 2410 (2896) | 0.83 [0.77, 0.90]↓ | 0.62 [0.57, 0.67]↓ | 0.64 · cross-node | 1% (4%) | 51% (45%) | kn171 |
| longbench_v2_qwen3 | cactus | loosest | 0.35 | 150 | 4.39 (3.07) | 2341 (2896) | 0.81 [0.75, 0.88]↓ | 0.61 [0.56, 0.66]↓ | 0.63 · cross-node | 1% (4%) | 44% (45%) | kn171 |
| longbench_v2_qwen3 | spec_casc_opt | loosest | 0.05 | 150 | 5.04 (3.07) | 2304 (2896) | 0.80 [0.72, 0.88]↓ | 0.54 [0.49, 0.60]↓ | 0.57 · cross-node | 2% (4%) | 33% (45%) | kn175 |
| longbench_v2_qwen3 | r_fuzzy | loosest | 0.25 | 150 | 4.24 (3.07) | 2458 (2896) | 0.85 [0.78, 0.92]↓ | 0.65 [0.60, 0.71]↓ | 0.67 · cross-node | 3% (4%) | 44% (45%) | kn176 |
| longbench_v2_qwen3 | spec_casc_tok | loosest | 0.8 | 150 | 3.98 (3.07) | 2495 (2896) | 0.86 [0.79, 0.94]↓ | 0.70 [0.64, 0.76]↓ | 0.71 · cross-node | 3% (4%) | 42% (45%) | kn176 |

### Block 6c: Qwen/Qwen3-8B + Qwen/Qwen3-1.7B, mtbench (killarney)

GPU-h actual (lane journals): 1.4.

`campaign/addendum/tables/step9__qwen3-8b__qwen3-1.7b.csv` (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mtbench_qwen3 | mentored_dec | loosest | 0.75 | 80 | 4.48 (3.04) | 1914 (2098) | 0.91 [0.85, 0.97]↓ | 0.67 [0.63, 0.71]↓ | 0.69 · cross-node | 10% (18%) | - (-) | kn173 |
| mtbench_qwen3 | cactus | loosest | 0.35 | 80 | 4.51 (3.04) | 1925 (2098) | 0.92 [0.85, 0.98]↓ | 0.67 [0.62, 0.71]↓ | 0.70 · cross-node | 14% (18%) | - (-) | kn173 |
| mtbench_qwen3 | spec_casc_opt | loosest | 0.05 | 80 | 4.64 (3.04) | 1946 (2098) | 0.93 [0.86, 1.00]↓ | 0.67 [0.62, 0.72]↓ | 0.68 · cross-node | 12% (18%) | - (-) | kn176 |
| mtbench_qwen3 | r_fuzzy | loosest | 0.25 | 80 | 4.46 (3.04) | 1889 (2098) | 0.90 [0.84, 0.96]↓ | 0.66 [0.62, 0.70]↓ | 0.66 · cross-node | 9% (18%) | - (-) | kn174 |
| mtbench_qwen3 | spec_casc_tok | loosest | 0.8 | 80 | 3.88 (3.04) | 1948 (2098) | 0.93 [0.87, 0.99]↓ | 0.77 [0.72, 0.83]↓ | 0.78 · cross-node | 12% (18%) | - (-) | kn174 |

### Block 6d: Qwen/Qwen3-8B + Qwen/Qwen3-1.7B, aime24 (killarney)

GPU-h actual (lane journals): 5.5.

`campaign/addendum/tables/step9__qwen3-8b__qwen3-1.7b.csv` (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aime24_qwen3 | mentored_dec | loosest | 0.75 | 30 | 5.43 (4.15) | 16221 (19469) | 0.83 [0.76, 0.90]↓ | 0.66 [0.60, 0.71]↓ | 0.60 · cross-node | 7% (20%) | 80% (73%) | kn176 |
| aime24_qwen3 | cactus | loosest | 0.35 | 30 | 5.45 (4.15) | 16560 (19469) | 0.85 [0.78, 0.94]↓ | 0.67 [0.61, 0.74]↓ | 0.61 · cross-node | 3% (20%) | 70% (73%) | kn174 |
| aime24_qwen3 | spec_casc_opt | loosest | 0.05 | 30 | 5.30 (4.15) | 17886 (19469) | 0.92 [0.80, 1.06] | 0.74 [0.64, 0.85]↓ | 0.68 · cross-node | 7% (20%) | 73% (73%) | kn176 |
| aime24_qwen3 | r_fuzzy | loosest | 0.25 | 30 | 5.50 (4.15) | 15323 (19469) | 0.79 [0.68, 0.90]↓ | 0.61 [0.53, 0.71]↓ | 0.56 · cross-node | 3% (20%) | 77% (73%) | kn171 |
| aime24_qwen3 | spec_casc_tok | loosest | 0.8 | 30 | 4.88 (4.15) | 17269 (19469) | 0.89 [0.78, 1.01] | 0.77 [0.68, 0.87]↓ | 0.77 · cross-node | 7% (20%) | 80% (73%) | kn176 |

### Block 7a: Qwen/Qwen3-8B + Qwen/Qwen3-0.6B, humaneval (killarney)

GPU-h actual (lane journals): 4.9.

`campaign/addendum/tables/step9__qwen3-8b__qwen3-0.6b.csv` (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| humaneval_qwen3 | mentored_dec | loosest | 0.75 | 150 | 3.43 (2.90) | 3509 (3814) | 0.92 [0.86, 0.98]↓ | 0.79 [0.74, 0.84]↓ | 0.77 · cross-node | 7% (13%) | 87% (84%) | kn176 |
| humaneval_qwen3 | cactus | loosest | 0.35 | 150 | 3.66 (2.90) | 3593 (3814) | 0.94 [0.88, 1.01] | 0.76 [0.71, 0.81]↓ | 0.76 · cross-node | 7% (13%) | 87% (84%) | kn174 |
| humaneval_qwen3 | spec_casc_opt | loosest | 0.05 | 150 | 3.20 (2.90) | 3608 (3814) | 0.95 [0.88, 1.02] | 0.86 [0.80, 0.92]↓ | 0.92 · cross-node | 12% (13%) | 83% (84%) | kn172 |
| humaneval_qwen3 | r_fuzzy | loosest | 0.25 | 150 | 4.54 (2.90) | 3920 (3814) | 1.03 [0.97, 1.09] | 0.71 [0.67, 0.75]↓ | 0.72 · cross-node | 9% (13%) | 85% (84%) | kn169 |
| humaneval_qwen3 | spec_casc_tok | loosest | 0.8 | 150 | 3.03 (2.90) | 3612 (3814) | 0.95 [0.89, 1.00] | 0.90 [0.85, 0.96]↓ | 0.88 · cross-node | 10% (13%) | 87% (84%) | kn176 |

### Block 7b: Qwen/Qwen3-8B + Qwen/Qwen3-0.6B, longbench_v2 (killarney)

GPU-h actual (lane journals): 4.3.

`campaign/addendum/tables/step9__qwen3-8b__qwen3-0.6b.csv` (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| longbench_v2_qwen3 | mentored_dec | loosest | 0.75 | 150 | 3.40 (2.51) | 2486 (2989) | 0.83 [0.77, 0.89]↓ | 0.65 [0.61, 0.70]↓ | 0.71 · cross-node | 3% (5%) | 44% (46%) | kn173 |
| longbench_v2_qwen3 | cactus | loosest | 0.35 | 150 | 3.84 (2.51) | 2259 (2989) | 0.76 [0.70, 0.82]↓ | 0.54 [0.50, 0.59]↓ | 0.57 · cross-node | 3% (5%) | 43% (46%) | kn174 |
| longbench_v2_qwen3 | spec_casc_opt | loosest | 0.05 | 150 | 3.27 (2.51) | 2399 (2989) | 0.80 [0.73, 0.88]↓ | 0.65 [0.60, 0.71]↓ | 0.67 · cross-node | 5% (5%) | 45% (46%) | kn177 |
| longbench_v2_qwen3 | r_fuzzy | loosest | 0.25 | 150 | 4.03 (2.51) | 2432 (2989) | 0.81 [0.74, 0.89]↓ | 0.56 [0.51, 0.61]↓ | 0.60 · cross-node | 3% (5%) | 39% (46%) | kn175 |
| longbench_v2_qwen3 | spec_casc_tok | loosest | 0.8 | 150 | 2.87 (2.51) | 2528 (2989) | 0.85 [0.79, 0.91]↓ | 0.77 [0.72, 0.82]↓ | 0.78 | 3% (5%) | 51% (46%) | kn176 |

### Block 7c: Qwen/Qwen3-8B + Qwen/Qwen3-0.6B, mtbench (killarney)

GPU-h actual (lane journals): 1.5.

`campaign/addendum/tables/step9__qwen3-8b__qwen3-0.6b.csv` (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mtbench_qwen3 | mentored_dec | loosest | 0.75 | 80 | 3.35 (2.38) | 1876 (1997) | 0.94 [0.88, 1.00]↓ | 0.73 [0.68, 0.77]↓ | 0.72 | 14% (15%) | - (-) | kn171 |
| mtbench_qwen3 | cactus | loosest | 0.35 | 80 | 4.05 (2.38) | 1823 (1997) | 0.91 [0.84, 0.99]↓ | 0.60 [0.55, 0.65]↓ | 0.61 · cross-node | 10% (15%) | - (-) | kn175 |
| mtbench_qwen3 | spec_casc_opt | loosest | 0.05 | 80 | 3.20 (2.38) | 1740 (1997) | 0.87 [0.81, 0.94]↓ | 0.70 [0.65, 0.75]↓ | 0.69 | 11% (15%) | - (-) | kn171 |
| mtbench_qwen3 | r_fuzzy | loosest | 0.25 | 80 | 3.99 (2.38) | 1772 (1997) | 0.89 [0.82, 0.95]↓ | 0.58 [0.54, 0.62]↓ | 0.58 · cross-node | 12% (15%) | - (-) | kn174 |
| mtbench_qwen3 | spec_casc_tok | loosest | 0.8 | 80 | 2.75 (2.38) | 1937 (1997) | 0.97 [0.90, 1.04] | 0.88 [0.83, 0.95]↓ | 0.88 · cross-node | 10% (15%) | - (-) | kn177 |

### Block 7d: Qwen/Qwen3-8B + Qwen/Qwen3-0.6B, aime24 (killarney)

GPU-h actual (lane journals): 4.0.

`campaign/addendum/tables/step9__qwen3-8b__qwen3-0.6b.csv` (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aime24_qwen3 | mentored_dec | loosest | 0.75 | 30 | 4.73 (3.58) | 17522 (17807) | 0.98 [0.85, 1.13] | 0.78 [0.68, 0.90]↓ | 0.76 · cross-node | 7% (10%) | 70% (67%) | kn171 |
| aime24_qwen3 | cactus | loosest | 0.35 | 30 | 5.02 (3.58) | 16199 (17807) | 0.91 [0.77, 1.07] | 0.69 [0.58, 0.80]↓ | 0.67 · cross-node | 7% (10%) | 77% (67%) | kn175 |
| aime24_qwen3 | spec_casc_opt | loosest | 0.05 | 30 | 4.38 (3.58) | 16859 (17807) | 0.95 [0.84, 1.05] | 0.80 [0.71, 0.88]↓ | 0.85 · cross-node | 3% (10%) | 70% (67%) | kn172 |
| aime24_qwen3 | r_fuzzy | loosest | 0.25 | 30 | 5.24 (3.58) | 18928 (17807) | 1.06 [0.91, 1.23] | 0.77 [0.66, 0.90]↓ | 0.77 · cross-node | 17% (10%) | 50% (67%) | kn173 |
| aime24_qwen3 | spec_casc_tok | loosest | 0.8 | 30 | 4.05 (3.58) | 17354 (17807) | 0.97 [0.84, 1.12] | 0.88 [0.76, 0.99]↓ | 0.87 · cross-node | 13% (10%) | 67% (67%) | kn174 |

### Block 8a: Qwen/Qwen3-8B + RedHatAI/Qwen3-8B-speculator.peagle, humaneval (killarney)

GPU-h actual (lane journals): 3.0.

`campaign/addendum/tables/step9__qwen3-8b__peagle.csv` (eagle3, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| humaneval_qwen3 | mentored_dec | loosest | 0.75 | 150 | 2.22 (2.05) | 3976 (3863) | 1.03 [0.96, 1.10] | 0.97 [0.92, 1.04] | 0.97 · cross-node | 15% (10%) | 80% (85%) | kn171 |
| humaneval_qwen3 | cactus | loosest | 0.35 | 150 | 2.29 (2.05) | 4102 (3863) | 1.06 [1.01, 1.12]↑ | 0.98 [0.94, 1.03] | 0.97 · cross-node | 13% (10%) | 78% (85%) | kn174 |
| humaneval_qwen3 | spec_casc_opt | loosest | 0.05 | 150 | 2.22 (2.05) | 4410 (3863) | 1.14 [1.08, 1.21]↑ | 1.08 [1.03, 1.14]↑ | 1.06 · cross-node | 14% (10%) | 71% (85%) | kn173 |
| humaneval_qwen3 | r_fuzzy | loosest | 0.25 | 150 | 2.62 (2.05) | 6445 (3863) | 1.67 [1.55, 1.82]↑ | 1.42 [1.32, 1.54]↑ | 1.40 · cross-node | 37% (10%) | 25% (85%) | kn171 |
| humaneval_qwen3 | spec_casc_tok | loosest | 0.8 | 150 | 2.14 (2.05) | 3857 (3863) | 1.00 [0.94, 1.06] | 0.97 [0.91, 1.02] | 0.96 · cross-node | 12% (10%) | 81% (85%) | kn176 |

### Block 8b: Qwen/Qwen3-8B + RedHatAI/Qwen3-8B-speculator.peagle, longbench_v2 (killarney)

GPU-h actual (lane journals): 1.7.

`campaign/addendum/tables/step9__qwen3-8b__peagle.csv` (eagle3, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| longbench_v2_qwen3 | mentored_dec | loosest | 0.75 | 150 | 1.59 (1.38) | 3131 (3023) | 1.04 [0.96, 1.12] | 0.95 [0.88, 1.02] | 0.94 · cross-node | 5% (2%) | 51% (55%) | kn171 |
| longbench_v2_qwen3 | cactus | loosest | 0.35 | 150 | 2.14 (1.38) | 3237 (3023) | 1.07 [0.99, 1.16] | 0.82 [0.76, 0.88]↓ | 0.84 · cross-node | 6% (2%) | 47% (55%) | kn177 |
| longbench_v2_qwen3 | spec_casc_opt | loosest | 0.05 | 150 | 1.67 (1.38) | 3324 (3023) | 1.10 [1.01, 1.19]↑ | 0.95 [0.88, 1.03] | 0.97 · cross-node | 11% (2%) | 48% (55%) | kn173 |
| longbench_v2_qwen3 | r_fuzzy | loosest | 0.25 | 150 | 1.75 (1.38) | 3440 (3023) | 1.14 [1.05, 1.23]↑ | 0.98 [0.90, 1.06] | 0.98 | 13% (2%) | 45% (55%) | kn174 |
| longbench_v2_qwen3 | spec_casc_tok | loosest | 0.8 | 150 | 1.48 (1.38) | 2996 (3023) | 0.99 [0.92, 1.07] | 0.95 [0.88, 1.02] | 0.95 · cross-node | 4% (2%) | 47% (55%) | kn176 |

### Block 8c: Qwen/Qwen3-8B + RedHatAI/Qwen3-8B-speculator.peagle, mtbench (killarney)

GPU-h actual (lane journals): 1.1.

`campaign/addendum/tables/step9__qwen3-8b__peagle.csv` (eagle3, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mtbench_qwen3 | mentored_dec | loosest | 0.75 | 80 | 1.87 (1.57) | 2218 (2112) | 1.05 [0.99, 1.12] | 0.94 [0.89, 1.00]↓ | 0.92 · cross-node | 21% (14%) | - (-) | kn176 |
| mtbench_qwen3 | cactus | loosest | 0.35 | 80 | 2.50 (1.57) | 2416 (2112) | 1.14 [1.07, 1.23]↑ | 0.84 [0.78, 0.91]↓ | 0.84 · cross-node | 20% (14%) | - (-) | kn175 |
| mtbench_qwen3 | spec_casc_opt | loosest | 0.05 | 80 | 1.89 (1.57) | 2144 (2112) | 1.02 [0.96, 1.08] | 0.89 [0.84, 0.95]↓ | 0.89 · cross-node | 20% (14%) | - (-) | kn171 |
| mtbench_qwen3 | r_fuzzy | loosest | 0.25 | 80 | 2.09 (1.57) | 2581 (2112) | 1.22 [1.13, 1.32]↑ | 1.01 [0.94, 1.09] | 1.00 · cross-node | 30% (14%) | - (-) | kn176 |
| mtbench_qwen3 | spec_casc_tok | loosest | 0.8 | 80 | 1.69 (1.57) | 2157 (2112) | 1.02 [0.96, 1.09] | 0.97 [0.91, 1.03] | 0.95 · cross-node | 15% (14%) | - (-) | kn171 |

### Block 8d: Qwen/Qwen3-8B + RedHatAI/Qwen3-8B-speculator.peagle, aime24 (killarney)

GPU-h actual (lane journals): 1.9.

`campaign/addendum/tables/step9__qwen3-8b__peagle.csv` (eagle3, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aime24_qwen3 | mentored_dec | loosest | 0.75 | 30 | 2.59 (2.26) | 19549 (18758) | 1.04 [0.94, 1.14] | 0.95 [0.86, 1.04] | 1.03 · cross-node | 20% (10%) | 70% (73%) | kn176 |
| aime24_qwen3 | cactus | loosest | 0.35 | 30 | 2.70 (2.26) | 22529 (18758) | 1.20 [1.07, 1.36]↑ | 1.04 [0.92, 1.20] | 1.12 · cross-node | 30% (10%) | 60% (73%) | kn172 |
| aime24_qwen3 | spec_casc_opt | loosest | 0.05 | 30 | 2.57 (2.26) | 20206 (18758) | 1.08 [0.95, 1.22] | 0.98 [0.86, 1.11] | 0.98 · cross-node | 30% (10%) | 67% (73%) | kn175 |
| aime24_qwen3 | r_fuzzy | loosest | 0.25 | 30 | 2.69 (2.26) | 28149 (18758) | 1.50 [1.30, 1.76]↑ | 1.30 [1.14, 1.54]↑ | 1.36 · cross-node | 60% (10%) | 37% (73%) | kn169 |
| aime24_qwen3 | spec_casc_tok | loosest | 0.8 | 30 | 2.49 (2.26) | 18391 (18758) | 0.98 [0.86, 1.11] | 0.91 [0.80, 1.04] | 0.93 · cross-node | 23% (10%) | 73% (73%) | kn173 |

### Block 9a: meta-llama/Llama-3.1-8B-Instruct + meta-llama/Llama-3.2-1B-Instruct, humaneval (killarney)

GPU-h actual (lane journals): 0.6.

`campaign/addendum/tables/step9__llama31-8b-instruct__llama32-1b.csv` (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| humaneval_llama31 | mentored_dec | loosest | 0.75 | 150 | 5.22 (3.97) | 572 (544) | 1.05 [1.00, 1.11] | 0.83 [0.79, 0.88]↓ | 0.84 · cross-node | 0% (0%) | 40% (55%) | kn171 |
| humaneval_llama31 | cactus | loosest | 0.35 | 150 | 5.49 (3.97) | 623 (544) | 1.15 [1.04, 1.28]↑ | 0.87 [0.79, 0.96]↓ | 0.86 | 0% (0%) | 38% (55%) | kn176 |
| humaneval_llama31 | spec_casc_opt | loosest | 0.05 | 150 | 4.84 (3.97) | 582 (544) | 1.07 [1.01, 1.14]↑ | 0.90 [0.84, 0.96]↓ | 0.91 · cross-node | 0% (0%) | 41% (55%) | kn171 |
| humaneval_llama31 | r_fuzzy | loosest | 0.25 | 150 | 5.55 (3.97) | 652 (544) | 1.20 [1.06, 1.37]↑ | 0.90 [0.80, 1.01] | 0.91 · cross-node | 0% (0%) | 23% (55%) | kn171 |
| humaneval_llama31 | spec_casc_tok | loosest | 0.8 | 150 | 4.51 (3.97) | 512 (544) | 0.94 [0.89, 0.99]↓ | 0.84 [0.80, 0.89]↓ | 0.84 · cross-node | 0% (0%) | 57% (55%) | kn174 |

### Block 9b: meta-llama/Llama-3.1-8B-Instruct + meta-llama/Llama-3.2-1B-Instruct, longbench_v2 (killarney)

GPU-h actual (lane journals): 1.4.

`campaign/addendum/tables/step9__llama31-8b-instruct__llama32-1b.csv` (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| longbench_v2_llama31 | mentored_dec | loosest | 0.75 | 150 | 4.64 (3.11) | 703 (665) | 1.06 [0.74, 1.55] | 0.77 [0.56, 1.07] | 0.83 | 0% (1%) | 33% (37%) | kn176 |
| longbench_v2_llama31 | cactus | loosest | 0.35 | 150 | 5.55 (3.11) | 1631 (665) | 2.45 [1.71, 3.50]↑ | 1.58 [1.14, 2.17]↑ | 1.42 · cross-node | 3% (1%) | 24% (37%) | kn171:137+kn174:13 |
| longbench_v2_llama31 | spec_casc_opt | loosest | 0.05 | 150 | 4.45 (3.11) | 565 (665) | 0.85 [0.60, 1.21] | 0.65 [0.48, 0.88]↓ | 0.74 · cross-node | 0% (1%) | 29% (37%) | kn171 |
| longbench_v2_llama31 | r_fuzzy | loosest | 0.25 | 150 | 5.39 (3.11) | 1282 (665) | 1.93 [1.32, 2.81]↑ | 1.26 [0.90, 1.77] | 1.19 · cross-node | 1% (1%) | 21% (37%) | kn174 |
| longbench_v2_llama31 | spec_casc_tok | loosest | 0.8 | 150 | 3.66 (3.11) | 390 (665) | 0.59 [0.44, 0.81]↓ | 0.56 [0.43, 0.73]↓ | 0.67 | 0% (1%) | 36% (37%) | kn176 |

### Block 9c: meta-llama/Llama-3.1-8B-Instruct + meta-llama/Llama-3.2-1B-Instruct, mtbench (killarney)

GPU-h actual (lane journals): 0.4.

`campaign/addendum/tables/step9__llama31-8b-instruct__llama32-1b.csv` (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mtbench_llama31 | mentored_dec | loosest | 0.75 | 80 | 4.78 (3.26) | 578 (430) | 1.35 [0.92, 1.94] | 0.94 [0.68, 1.30] | 0.93 · cross-node | 2% (1%) | - (-) | kn176 |
| mtbench_llama31 | cactus | loosest | 0.35 | 80 | 5.46 (3.26) | 1051 (430) | 2.45 [1.70, 3.36]↑ | 1.55 [1.10, 2.07]↑ | 1.64 · cross-node | 9% (1%) | - (-) | kn173 |
| mtbench_llama31 | spec_casc_opt | loosest | 0.05 | 80 | 4.60 (3.26) | 460 (430) | 1.07 [0.83, 1.35] | 0.81 [0.65, 0.99]↓ | 0.81 · cross-node | 0% (1%) | - (-) | kn175 |
| mtbench_llama31 | r_fuzzy | loosest | 0.25 | 80 | 5.32 (3.26) | 688 (430) | 1.60 [1.15, 2.16]↑ | 1.05 [0.77, 1.38] | 1.04 · cross-node | 1% (1%) | - (-) | kn174 |
| mtbench_llama31 | spec_casc_tok | loosest | 0.8 | 80 | 3.81 (3.26) | 395 (430) | 0.92 [0.74, 1.08] | 0.83 [0.69, 0.96]↓ | 0.82 · cross-node | 0% (1%) | - (-) | kn176 |

### Block 9d: meta-llama/Llama-3.1-8B-Instruct + meta-llama/Llama-3.2-1B-Instruct, aime24 (killarney)

GPU-h actual (lane journals): 0.7.

`campaign/addendum/tables/step9__llama31-8b-instruct__llama32-1b.csv` (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aime24_llama31 | mentored_dec | loosest | 0.75 | 30 | 5.33 (3.56) | 1875 (5380) | 0.35 [0.21, 0.57]↓ | 0.26 [0.16, 0.40]↓ | 0.25 · cross-node | 0% (0%) | 3% (0%) | kn173 |
| aime24_llama31 | cactus | loosest | 0.35 | 30 | 5.76 (3.56) | 3015 (5380) | 0.56 [0.32, 0.94]↓ | 0.40 [0.23, 0.66]↓ | 0.39 · cross-node | 0% (0%) | 0% (0%) | kn174 |
| aime24_llama31 | spec_casc_opt | loosest | 0.05 | 30 | 4.92 (3.56) | 1619 (5380) | 0.30 [0.17, 0.51]↓ | 0.23 [0.14, 0.39]↓ | 0.23 | 0% (0%) | 7% (0%) | kn171 |
| aime24_llama31 | r_fuzzy | loosest | 0.25 | 30 | 5.72 (3.56) | 2936 (5380) | 0.55 [0.31, 0.94]↓ | 0.39 [0.22, 0.65]↓ | 0.39 · cross-node | 0% (0%) | 0% (0%) | kn174 |
| aime24_llama31 | spec_casc_tok | loosest | 0.8 | 30 | 4.52 (3.56) | 5738 (5380) | 1.07 [0.39, 2.14] | 0.80 [0.31, 1.53] | 0.89 · cross-node | 13% (0%) | 3% (0%) | kn176 |

### Block 10a: deepseek-ai/DeepSeek-R1-Distill-Llama-8B + meta-llama/Llama-3.2-1B-Instruct, humaneval (killarney)

GPU-h actual (lane journals): 5.7.

`campaign/addendum/tables/step9__r1-distill-llama-8b__llama32-1b.csv` (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| humaneval_r1llama | mentored_dec | loosest | 0.75 | 150 | 2.56 (1.69) | 4841 (3857) | 1.26 [1.16, 1.36]↑ | 0.93 [0.86, 1.00] | 0.91 · cross-node | 21% (6%) | 76% (89%) | kn176 |
| humaneval_r1llama | cactus | loosest | 0.35 | 150 | 5.20 (1.69) | 7250 (3857) | 1.88 [1.71, 2.08]↑ | 0.80 [0.73, 0.88]↓ | 0.79 · cross-node | 59% (6%) | 26% (89%) | kn173 |
| humaneval_r1llama | spec_casc_opt | loosest | 0.05 | 150 | 2.92 (1.69) | 5386 (3857) | 1.40 [1.28, 1.53]↑ | 0.97 [0.89, 1.06] | 0.97 · cross-node | 21% (6%) | 64% (89%) | kn175 |
| humaneval_r1llama | r_fuzzy | loosest | 0.25 | 150 | 2.28 (1.69) | 5839 (3857) | 1.51 [1.39, 1.65]↑ | 1.26 [1.16, 1.38]↑ | 1.24 · cross-node | 4% (6%) | 45% (89%) | kn174 |
| humaneval_r1llama | spec_casc_tok | loosest | 0.8 | 150 | 2.22 (1.69) | 3847 (3857) | 1.00 [0.91, 1.09] | 0.81 [0.74, 0.88]↓ | 0.79 · cross-node | 12% (6%) | 77% (89%) | kn174 |

### Block 10b: deepseek-ai/DeepSeek-R1-Distill-Llama-8B + meta-llama/Llama-3.2-1B-Instruct, longbench_v2 (killarney)

GPU-h actual (lane journals): 4.0.

`campaign/addendum/tables/step9__r1-distill-llama-8b__llama32-1b.csv` (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| longbench_v2_r1llama | mentored_dec | loosest | 0.75 | 150 | 2.65 (1.62) | 1712 (1802) | 0.95 [0.83, 1.09] | 0.68 [0.60, 0.77]↓ | 0.65 · cross-node | 5% (3%) | 31% (34%) | kn171 |
| longbench_v2_r1llama | cactus | loosest | 0.35 | 150 | 5.06 (1.62) | 4756 (1802) | 2.64 [2.22, 3.17]↑ | 1.11 [0.95, 1.31] | 1.02 · cross-node | 33% (3%) | 25% (34%) | kn176 |
| longbench_v2_r1llama | spec_casc_opt | loosest | 0.05 | 150 | 3.40 (1.62) | 5915 (1802) | 3.28 [2.79, 3.91]↑ | 2.05 [1.74, 2.42]↑ | 1.83 · cross-node | 60% (3%) | 34% (34%) | kn176 |
| longbench_v2_r1llama | r_fuzzy | loosest | 0.25 | 150 | 2.40 (1.62) | 1494 (1802) | 0.83 [0.70, 0.99]↓ | 0.73 [0.60, 0.87]↓ | 0.69 · cross-node | 1% (3%) | 33% (34%) | kn171 |
| longbench_v2_r1llama | spec_casc_tok | loosest | 0.8 | 150 | 2.24 (1.62) | 1698 (1802) | 0.94 [0.81, 1.08] | 0.72 [0.63, 0.81]↓ | 0.70 · cross-node | 6% (3%) | 33% (34%) | kn173 |

### Block 10c: deepseek-ai/DeepSeek-R1-Distill-Llama-8B + meta-llama/Llama-3.2-1B-Instruct, mtbench (killarney)

GPU-h actual (lane journals): 1.4.

`campaign/addendum/tables/step9__r1-distill-llama-8b__llama32-1b.csv` (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mtbench_r1llama | mentored_dec | loosest | 0.75 | 80 | 2.42 (1.64) | 1406 (1373) | 1.02 [0.95, 1.10] | 0.75 [0.70, 0.82]↓ | 0.74 | 11% (11%) | - (-) | kn169 |
| mtbench_r1llama | cactus | loosest | 0.35 | 80 | 5.04 (1.64) | 3322 (1373) | 2.42 [2.03, 2.93]↑ | 0.96 [0.81, 1.16] | 1.01 · cross-node | 70% (11%) | - (-) | kn176 |
| mtbench_r1llama | spec_casc_opt | loosest | 0.05 | 80 | 3.02 (1.64) | 2169 (1373) | 1.58 [1.28, 1.95]↑ | 0.99 [0.82, 1.19] | 1.04 · cross-node | 30% (11%) | - (-) | kn176 |
| mtbench_r1llama | r_fuzzy | loosest | 0.25 | 80 | 2.43 (1.64) | 2087 (1373) | 1.52 [1.32, 1.78]↑ | 1.19 [1.01, 1.41]↑ | 1.17 · cross-node | 15% (11%) | - (-) | kn171 |
| mtbench_r1llama | spec_casc_tok | loosest | 0.8 | 80 | 2.00 (1.64) | 1259 (1373) | 0.92 [0.83, 1.02] | 0.77 [0.70, 0.85]↓ | 0.76 · cross-node | 8% (11%) | - (-) | kn174 |

### Block 10d: deepseek-ai/DeepSeek-R1-Distill-Llama-8B + meta-llama/Llama-3.2-1B-Instruct, aime24 (killarney)

GPU-h actual (lane journals): 4.2.

`campaign/addendum/tables/step9__r1-distill-llama-8b__llama32-1b.csv` (draft_model, V1 full patches):

| dataset | rule | setting | alpha | n | l_bar (lossless) | tokens (lossless) | lambda [95%] | R [95%] | T | cap-out (lossless) | acc (lossless) | nodes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aime24_r1llama | mentored_dec | loosest | 0.75 | 30 | 2.70 (1.83) | 10982 (11025) | 1.00 [0.85, 1.18] | 0.76 [0.63, 0.91]↓ | 0.75 | 0% (0%) | 20% (43%) | kn171 |
| aime24_r1llama | cactus | loosest | 0.35 | 30 | 5.79 (1.83) | 26743 (11025) | 2.43 [2.02, 2.93]↑ | 0.98 [0.81, 1.19] | 1.04 · T same-node 1.03 (28 pairs) | 73% (0%) | 0% (43%) | kn171:28+kn173:2 |
| aime24_r1llama | spec_casc_opt | loosest | 0.05 | 30 | 3.02 (1.83) | 15973 (11025) | 1.45 [1.08, 1.93]↑ | 0.99 [0.73, 1.32] | 1.02 · cross-node | 17% (0%) | 17% (43%) | kn174 |
| aime24_r1llama | r_fuzzy | loosest | 0.25 | 30 | 1.79 (1.83) | 7230 (11025) | 0.66 [0.51, 0.86]↓ | 0.69 [0.52, 0.96]↓ | 0.70 · cross-node | 0% (0%) | 3% (43%) | kn169 |
| aime24_r1llama | spec_casc_tok | loosest | 0.8 | 30 | 2.76 (1.83) | 15051 (11025) | 1.37 [1.15, 1.59]↑ | 1.00 [0.85, 1.15] | 1.11 · cross-node | 3% (0%) | 37% (43%) | kn176 |

Step 9 GPU-h so far (lane journals): 187.2 over 34 blocks.

## Observations, failures and anything that looked wrong

### Findings worth a sentence in the paper (step 1)

- **Qwen3 cactus inflates in the answer, not the thinking.** AIME24, cactus
  alpha 0.35: lambda_think 1.06 but lambda_answer 9.38; 87% of the extra
  characters fall after `</think>` (`analysis/split_inflation.csv`, row
  qwen3-8b/aime24/cactus). Of its 30 outputs, 13 open and close one think
  block, 6 never close it, and 11 re-open `<think>` or close it more than
  once (case_014: 121K answer characters). Every GPT-OSS cell puts 93-103%
  of its extra length in the analysis channel instead.
- **GPT-OSS inflation is not exact looping.** GPT-OSS AIME24 relaxed arms
  have at most 0.16% of tokens inside a repeated 50-gram (strict: 0%);
  Qwen3 AIME24 spec_casc_opt has 15.1% and a mean longest repeat of 2,728
  tokens (`analysis/repetition.csv`).
- **Time per round is flat in output length** (R^2 about 0.01-0.02 for both
  targets, strict and all runs), yet it rises with lambda across cells
  (Spearman 0.58): inflating arms also pay more per round
  (`analysis/time_per_round*.csv`).

### Things that looked wrong, and what was done

- **`cascade/cluster/sync_to_nibi.sh` would delete Nibi's runs and venvs**
  (`--delete-excluded` + excluded `/runs/`, `/logs/`, `.venv*`). Not used;
  code is pushed with tar (no deletes). Worth fixing in the repo.
- **Nibi's repo copies hold September E1/E1F/E1P runs at campaign paths**
  (e.g. `runs/gsm8k/strict/strict/case_*/seed_{0,1,2}`), different runs
  from the Mac's seed-0 data. The addendum never reads them (clean run roots
  on scratch); they stay untouched. The E1P strict seeds 1-2 could later
  serve as a same-hardware, same-seed reproducibility check of the
  addendum's strict seeds 1-2.
- **mentored-dec's self-test fails on Nibi** because it also checks the V2
  module (not installed there). First switch to mentored-dec in lane A
  failed (job 22880871, 06:23Z); fixed by scoping the check (README
  deviation 5). The V1 kernel checks passed on the GPU before the fix.
- **MT-Bench case_007's source text has a typo** ("reprompt top-5 words" in
  HuggingFaceH4/mt_bench_prompts vs FastChat q121's "returns"); the models
  answered the typo'd text.
- **Qwen3 proposal traces are empty files**: the tracer hooks the V1 sampler
  and Qwen3-8B runs on V2, so every Qwen3 trace-based statistic is GPT-OSS only.

### Determinism and the ordinal effect, measured on Nibi (2026-09-29)

- **Identical request history -> bit-identical output, across days and
  nodes.** The addendum's GPT-OSS gsm8k strict seeds 1 and 2 (lane A, node
  g3, 2026-09-29) reproduce the September E1P runs of the same seeds
  (2026-09-15) in 300/300 cases (same text, same token counts; both runs
  served cases 001-150 in order from a fresh server). livecodebench strict
  seed 0: step-0.5 `nibiref` (lane B, g18) = E1P seed 0 in 90/90 cases.
- **Different request history -> a different realization of the same
  case and seed.** E1P's gsm8k strict seed 0 was collected in three server
  sessions (case_001 alone on 09-11; cases 002-030 at ordinals 1-29 on
  09-11; cases 031-150 at ordinals 1-120 on 09-15). Against `nibiref` (one
  session, ordinals 1-150) only case_001 -- ordinal 1 in both -- matches;
  the other 149 differ (case_002: 88 tokens at ordinal 1 vs 151 at ordinal
  2). This is the request-history confound of `remote/ENVIRONMENT.md`,
  reproduced directly: per-case outputs depend on the engine's history, so
  per-case comparisons are only clean between runs that share it, which
  every addendum arm does (one fresh server per arm+seed, cases in order).

### Step 3 (GPT-OSS half): the lossless draft-length sweep

- Paired against the Nibi strict reference at N_draft 6 on the same cases
  (`tables/nspec__{gsm8k,livecodebench}.csv`, columns `*_vs_nibiref`): N 2-4
  are 5-9% faster (gsm8k 0.91-0.93, livecodebench 0.91-0.95; every 95%
  interval touches 1.0), N 8 is slower (gsm8k 1.06 n.s., livecodebench 1.13
  [1.01, 1.25]) and N 10 clearly slower (1.22 [1.10, 1.36] and 1.24 [1.10,
  1.38]). Rounds fall with N (N 2: 1.39x / 1.36x the N=6 rounds) and l_bar
  rises (gsm8k 1.43 -> 2.88), but the extra draft positions cost more than
  the rounds they save beyond N ~ 4-6. The paper's N_draft 6 lossless
  baseline is therefore within ~9% of the fastest lossless draft length in
  this regime (EAGLE-3 drafter, H100 SXM, batch 1); lambda stays 0.96-1.06
  (lossless decoding does not change the length distribution).

### Step 4.1 (GPT-OSS half): temperature alone, lossless

- Strict decoding at T 1.2 vs the Nibi T 1.0 reference (same cases,
  `tables/temp__{gsm8k,livecodebench}.csv`, `*_vs_nibiref`): gsm8k lambda
  1.27 [1.10, 1.47], rounds 1.37x, time 1.35x, accuracy unchanged (0.96 vs
  0.97); livecodebench lambda 1.07 [0.99, 1.17], time 1.16x. A +0.2
  temperature change inflates gsm8k about as much as mentored_dec at its
  loosest alpha does at T 1.0 (lambda 1.16), without any relaxation.
- T 1.5 breaks gsm8k (lambda 3.94, 48% of runs hit the 2,048-token cap,
  accuracy 0.31); livecodebench lambda 1.82 [1.44, 2.27], time 2.51x. l_bar
  falls as T rises (gsm8k 2.58 -> 2.36 -> 1.79): the EAGLE-3 drafter is
  trained at the target's T 1.0 distribution, so lossless acceptance drops.

### The paper's time ratios are hardware-dependent (found in step 2)

- **lambda and the rounds ratio replicate across machines; the time ratio
  does not** (`analysis/seed_shift.csv`, 25 GPT-OSS cells with seeds 0-2):
  mean lambda 1.47 (seed 0, old box) vs 1.41 / 1.46 (seeds 1 / 2, Nibi);
  rounds ratio 1.03 vs 0.99 / 1.02; time ratio 1.18 vs 1.00 / 1.02, lower
  on Nibi in 22 and 23 of 25 cells while the two Nibi seeds agree to 0.02
  on average. 8 of 25 cells change time win/loss across the three seeds.
- **Cause: a cost per emitted token on the old box** (`analysis/
  hardware_tpr_model.csv`). There, time per round = 12-14 ms + 2.5-3.2 ms
  per emitted token (R^2 0.39-0.87 outside gsm8k), so a rule that accepts
  more tokens per round also gets slower rounds: time-per-round ratio
  relaxed / strict 1.13 on average, above 1.05 in 24/25 cells (`analysis/
  hardware_tpr_ratio.csv`), even for mentored_dec, which ran on the same
  V1 patch file as the old box's strict arm. On Nibi a round costs 7.1-7.6
  ms whatever it emits (0.02-0.08 ms per token, R^2 ~ 0) and the
  time-per-round ratio is 1.01 / 1.00: time ratio = rounds ratio.
- **Consequence for the paper**: Eq. 4 is a round-count model, so the six
  "Eq. 4 wins that are time losses" and eleven "rounds wins that are time
  losses" in the paper's tables are (mostly) the old box's per-token cost,
  not a property of the rules. On the faster machine the time ratio tracks
  the rounds ratio. The tracer is not the cause: the penalty is the same in
  the traced first 12 cases and the untraced cases 13+.
- **Eq. 4 vs measured on the same 25 GPT-OSS cells, per seed**
  (`analysis/eq4_vs_measured.csv` restricted to those cells vs
  `analysis/eq4_vs_measured__seed{1,2}.csv`): old box seed 0 -- Eq. 4 wins
  10, rounds wins 13, time wins 8, Eq. 4 wins that are time losses 2,
  rounds wins that are time losses 5; Nibi seed 1 -- 13 / 14 / 14 / 0 / 0;
  Nibi seed 2 -- 10 / 12 / 12 / 0 / 0. Rounds wins barely move with the
  machine; only the time verdict does, and on Nibi every rounds win and
  every Eq. 4 win is a time win.

### Step 6 (GPT-OSS half): AIME24 accuracy over five seeds

- `aime24_repeats.csv` (seeds 0-4, 30 problems; interval = two-level
  bootstrap over problems and seeds): strict 0.79 [0.65, 0.91];
  mentored_dec 0.68 [0.53, 0.82]; spec_casc_tok 0.69 [0.54, 0.82]; cactus
  0.51 [0.36, 0.67]; r_fuzzy 0.48 [0.33, 0.63]; spec_casc_opt 0.39 [0.25,
  0.53]. Seed-to-seed sd of accuracy is
  0.04-0.06 (1-2 problems). The cactus / r_fuzzy / spec_casc_opt losses hold
  on every seed; mentored_dec and spec_casc_tok sit ~10 points below strict
  with overlapping intervals. lambda varies widely across seeds on 30
  problems (spec_casc_tok 0.96-1.52; mentored_dec 1.28-2.15): single-seed
  AIME24 lambdas should be quoted with that spread.

### MT-Bench quality (step 1.9)

- **The rules that inflate MT-Bench most also lose the most judged
  quality** (`analysis/mtbench_judge_summary.csv`, seed 0, loosest alpha,
  claude-fable-5-1 as FastChat single-answer judge, score /10): GPT-OSS
  strict 7.29 [6.75, 7.81] vs spec_casc_tok 7.49, mentored_dec 6.41,
  spec_casc_opt 5.74, r_fuzzy 4.58, cactus 4.51; Qwen3 strict 6.94 vs
  spec_casc_tok 7.21, mentored_dec 6.40, spec_casc_opt 3.95, r_fuzzy 3.05,
  cactus 2.99. Part of the Qwen3 drop is runs that never leave `<think>`
  (no answer, scored 1): cactus 22 of 80 vs strict 10; answered-only means
  are in the same file. spec_casc_tok is the one rule with no quality cost
  on either target.
- Judge mechanics: 2070 batch requests, 1 refusal (GPT-OSS mentored_dec
  0.15, case_054, a roleplay prompt), no parse errors; $45.16 at batch
  price. The batch sat at 0 processed for ~9 h, then finished in ~1 h.

### Step 5 (GPT-OSS half): the best settings on a second seed

- `best_setting.csv`: the seed-0 choice (lowest time ratio within 2
  accuracy points of strict) holds on Nibi seed 1 for 7 of 12 (dataset,
  rule) pairs. It fails on aime24 (mentored_dec 0.55: accuracy 0.70 vs 0.80;
  spec_casc_tok 0.15: time 1.12), livecodebench mentored_dec (0.87 vs 0.90)
  and longbench_v2 (both rules slower: rounds 1.09). The accuracy failures
  are 3 problems each (aime24 21 vs 24 of 30, livecodebench 78 vs 81 of 90);
  AIME24's seed-to-seed accuracy sd in step 6 is 1-2 problems. On
  longbench_v2 the rounds ratio itself changes side (0.89 / 0.97 on seed 0,
  1.09 / 1.09 on seed 1, with lambda 1.11 -> 1.38 and 1.06 -> 1.20).

### Hardware, longbench_v2 direction

- On longbench_v2 the old box made relaxed rules look *cheaper* in time,
  the opposite of the other datasets: it was prefill-bound there (72.6 vs
  4.7 s per strict case), so the rules' extra decode time was a small share
  of the total. spec_casc_opt time ratio 1.07 (old box) vs 1.29 / 1.24 (Nibi
  seeds 1 / 2) at rounds 1.31 / 1.35 / 1.27 (`seeds/summary.csv`).

### Operations on 2026-09-29 (nothing lost)

- Lane B job 22881159 hit its 12 h limit 10 min into longbench_v2
  spec_casc_opt seed 2: 59 cases done, one partial dir quarantined, the
  other 91 run by 22881281.
- The Mac stopped running the session from about 21:19Z to 00:20Z; the
  Nibi ControlMaster dropped with it. The lanes kept running; their runs
  wait on Nibi until one Duo push is approved (PROGRESS.md, Needs Bill 6).

### Step 7: the token-budget pilot sits on its boundary for Qwen3

- Qwen3-8B's strict reasoning pilot capped out on 2 of its first 20 cases
  at 8192 tokens (`tables/speedbench_pilot__qwen3-8b.csv`, row reasoning):
  exactly 10%, and the rule raises the budget only above 10%, so Qwen3
  reasoning runs at 8192 like GPT-OSS (0/20). Qwen3 is ~3x longer here
  (mean 2352 vs 820 completion tokens); expect a few Qwen3 reasoning
  cap-outs in the step-7 tables, which report cap-out rates per category.

### MT-Bench quality along the alpha grid (GPT-OSS, seed 0)

- `analysis/mtbench_judge_summary.csv` (every cell 80 runs, after the
  step-5.1 fills were judged): mentored_dec falls steadily with alpha --
  0.15: 7.33, 0.35: 7.14, 0.55: 6.71, 0.75: 6.41 (strict 7.29) -- while
  spec_casc_tok stays flat at or above strict (0.15: 7.51, 0.35: 7.36,
  0.55: 7.50, 0.8: 7.49). So step 5.2's rounds-ratio stand-in for MT-Bench
  picked mentored_dec 0.75, the loosest and lowest-scoring cell (-0.9 vs
  strict); spec_casc_tok's pick (0.55) costs nothing. Top-up batch for the
  230 fill runs: $5.37, ended 2026-09-30 03:53Z (judge total $50.53).

### Killarney: time ratios depend on the node (step 4.2)

- Mean time per round, step 4.2 (Qwen3 at T 0.6, top-p 0.95, top-k 20):
  K1 arms on kn173/kn169 -- strict 9.47 / 9.64 ms (gsm8k / livecodebench),
  mentored_dec 9.47 / 9.65, r_fuzzy 9.55 / 9.58 -- vs K2 arms on kn176 --
  cactus 10.48 / 10.71, spec_casc_opt 10.74 / 10.82, spec_casc_tok 10.52 /
  10.78. Within K1 a relaxed round costs what a strict one does (as on
  Nibi); kn176 is ~11% slower per round whatever the rule. So
  `tables/qwenT0.6__*.csv` time ratios for cactus, spec_casc_opt and
  spec_casc_tok (gsm8k 1.07 / 1.08 / 1.07) are inflated by the node; their
  rounds ratios (0.96 / 0.95 / 0.96) are not. README deviation 13.

### Same-node pairs: the node effect is real but not fixed (2026-10-02)

- Every table that pairs an arm with strict now says where each side ran
  (`nodes`, `nodes_strict`), how many case pairs shared a node
  (`same_node_pairs`) and the time ratio over those pairs alone
  (`time_ratio_same_node`; README deviations 13, 15, 17). Nodes come from
  the lane journals (`lanes/<lane>_status.jsonl`), matched by each run's
  config.json timestamp; run directories do not record them.
- The kn176 penalty of step 4.2 (~11% per round) did not hold later: in
  step 4.3 the kn176 arms' time-per-round ratios (0.88-0.98) match the
  same-node cactus arm's (0.93 / 0.98). So a cross-node time ratio is not
  a fixed offset from the same-node one; quote the rounds ratio, or the
  same-node time ratio where there are enough pairs.
- Where it matters: SPEED-Bench Qwen3 mentored_dec reads T 1.02 over all
  672 pairs but 0.91 over its 249 same-node pairs (rounds 0.93,
  `tables/speedbench__qwen3-8b.csv` row `mentored_dec`, category `all`);
  spec_casc_opt 1.13 vs 1.06 (93 pairs). On Nibi (GPT-OSS SPEED-Bench, lanes
  A and B on disjoint node sets) many arms are cross-node too, but rounds
  and time agree in every category there.

### Killarney's rolling reboot and two Qwen3-only failures (2026-10-01/02)

- Killarney rebooted every H100 node from 2026-10-01 ~18:40Z; rebooted nodes
  run NVIDIA driver 580.178.04 (was 580.159.03; README deviation 17). Runs
  straddle the change; same-node pairs on one side of it agree with
  cross-driver ones where both exist (step 3 N 8: 1.08 on gsm8k, same node,
  and on livecodebench, across the reboot).
- Qwen3 at 10 draft tokens ran out of memory in vLLM's sampler warmup at
  GPU_UTIL 0.85 (README deviation 18); it ran at 0.80.
- Qwen3 longbench_v2 crashed on Killarney once a sequence passed 40960
  positions: the EAGLE-3 drafter's own config caps its rope table there
  (README deviation 19). The old box ran 339 such cases without the
  repository recording how; the Killarney rows draft with a copy whose
  config allows 65536 positions, identical below 40960.

### SPEED-Bench without the HLE prompts (2026-10-02)

- The 208 `cais/hle` prompts were not run (README deviation 21), so every
  arm has 672 of 880 prompts. Humanities, Math and STEM rest on 8, 18 and 6
  prompts per arm: read their rows as indicative only (e.g. Qwen3
  spec_casc_opt's Math lambda 2.04 / rounds 1.47 is 18 prompts). The
  overall (`all`) rows and the eight complete categories carry the step-7
  conclusions.

- **Step 8, Block 1 (R1-Distill-Llama-8B + yuhuili EAGLE-3), complete 2026-10-04 08:03Z, 34.0 GPU-h.**
  The published drafter stops drafting past ~2048 positions (Block 0 profile: segment l_bar 2.2-3.4 below
  2048, 0.67-1.23 at 2048-4096, 0.23 beyond), so lossless l_bar is 3.07 on GSM8K but 0.77 on LiveCodeBench
  and 0.60 on AIME24. No rule gives a rounds speedup on GSM8K without an accuracy cost (R 0.87-1.12;
  accuracy 47-77% vs 77% lossless; the best points are spec_casc_tok 0.8, R 0.90 / 75%, and mentored_dec
  0.75, R 0.87 / 69%). cactus (V2: accept-test-only) runs away on the long benchmarks: 90-98% of its
  LiveCodeBench and AIME24 answers hit the token cap and accuracy falls to 0-3%.
- **AIME grader quirk (affects every row, unchanged).** `scripts/grade_aime.py` accepts only a 1-3 digit
  `\boxed{}`; a longer boxed number falls through to the last 1-3 digit integer of the answer. R1 lossless
  case_008 boxed 78125 (reference 025) and is scored correct from "3125 \cdot 25"; by strict boxed matching
  R1's lossless AIME24 accuracy is 7/30, not 8/30. The grader is the campaign's own and is left as is.
- **Step 8, Block 2 (Llama-3.1-8B-Instruct), complete 2026-10-04 10:33Z, 32.9 GPU-h** (estimate 11: the
  matched-l_bar protocol's many short arms each pay a server start). Medusa dropped (deviation 36).
  spec_casc_tok is the one rule that speeds Llama up without an accuracy cost, with every drafter: rounds
  ratio 0.63-0.78 with shorter answers (lambda 0.77-0.88) and accuracy within noise of lossless (EAGLE-3,
  EAGLE-1, Llama-3.2-1B standalone, on GSM8K, LiveCodeBench and MT-Bench). cactus (V2 accept-test-only for
  EAGLE-3/-1) inflates answers 4-14x with cap-outs of 40-82% and near-zero accuracy; r_fuzzy at its looser
  alphas also inflates (lambda 2.4-6.4) and its accepted length falls below lossless (degenerate repetitive
  text). With the standalone Llama-3.2-1B drafter (V1, full patches) cactus and r_fuzzy inflate far less
  (lambda 1.2-1.5), mentored_dec and spec_casc_opt reach R 0.68-0.74 at a 3-9 point accuracy cost.
  Bootstrap intervals on the EAGLE rows are wide (cap-out runs dominate the means).
- **Step 8, Block 3 (Qwen3-8B: DSpark, Qwen3-1.7B), complete 2026-10-04 13:03Z, 25.2 GPU-h.** With DSpark (V2:
  cactus and spec_casc_tok accept-test-only) every rule gives a modest, tight rounds gain (R 0.77-0.95, intervals
  +-0.04) with lengths near lossless (lambda 0.91-1.10); accuracy holds at the gentler settings and falls at the
  loosest (LiveCodeBench: spec_casc_opt 0.05 30%, r_fuzzy 0.25 32%, vs 74% lossless). With the standalone
  Qwen3-1.7B drafter (V1, full patches; lossless l_bar 3.8) all five rules at their loosest alpha reach R
  0.69-0.83 with slightly shorter answers and accuracy at or above lossless (GSM8K 81-85% vs 79%, LiveCodeBench
  71-80% vs 69%): a strong drafter leaves little for the relaxation to break. Lossless GSM8K cap-outs are 25-30%
  for Qwen3 at the paper's 2048-token budget (thinking traces), as in the paper's own Qwen3 rows.
- **Step 8, Block 6 (the fix on Qwen3-8B + its EAGLE-3 head, V2 port), complete 2026-10-04 13:34Z.** Against the
  Killarney lossless reference (runs/addendum/nibiref): spec_casc_tok_lt 0.15 and 0.2 and spec_casc_opt_head
  (0.05, beta 0.15) all give l_bar 1.54 vs 1.50 (GSM8K) and 1.17 vs 1.13 (LiveCodeBench), rounds ratio 0.99
  [0.95, 1.03], lambda 1.01, accuracy unchanged (79% vs 80%, 74% vs 73%). The three settings produce byte-identical
  outputs on all 240 cases (opt_head on 238): with this drafter (lossless l_bar 1.5, as in the paper's Qwen3 rows)
  the drafted token is almost never within 80-85% of the target's top probability while failing the lossless
  test. The masks are live: tok_lt at 0.55 changes all 30 of 30 GSM8K outputs against 0.15 (check job 5926723)
  but moves l_bar only 1.55 -> 1.56. On Qwen3 the head-restricted fix is safe and nearly inert (+3% acceptance),
  against +12% on GPT-OSS-20B (`tables/fix__gpt-oss-20b.csv`, 3 seeds). Time ratios pair Killarney arms with a
  Killarney reference on another node (kn175/kn176): read the rounds ratio.
- **Step 8, Block 4 (GPT-OSS-20B + RedHatAI EAGLE-3, V1 full patches, on Killarney: deviation 39), complete
  2026-10-04 ~14:30Z, 16.9 GPU-h** (estimate 6). Lossless l_bar 2.13 / 1.57 / 1.82 (GSM8K / LiveCodeBench /
  MT-Bench), below the paper's nebius head. spec_casc_tok is the only rule with a rounds gain at unchanged accuracy,
  and only on GSM8K (R 0.83 [0.75, 0.91], 97% = lossless); on LiveCodeBench no rule speeds up (R 1.01-2.28) and the
  looser cactus / r_fuzzy / spec_casc_opt settings lose 34-72 accuracy points; on MT-Bench cactus reaches R 0.74 with
  answers 1.4-1.7x longer. With a weaker drafter than the paper's, the relaxations mostly buy longer answers.
- **Step 8, Block 5 (R1-Distill-Llama-8B + Llama-3.2-1B standalone, V1, loosest), complete 2026-10-04 ~14:30Z,
  7.5 GPU-h.** The 1B drafter keeps drafting on long answers (lossless l_bar 1.56 on LiveCodeBench vs 0.77 for the
  EAGLE-3 head of Block 1; 2.71 on GSM8K) despite the 7 mismatched special tokens (deviation 38). GSM8K:
  spec_casc_tok 0.8 R 0.89 [0.82, 0.95] at 77% vs 71% lossless and mentored_dec 0.75 R 0.87 at 73%; cactus,
  spec_casc_opt and r_fuzzy inflate (lambda 2.0-3.2, R 1.4-2.3, accuracy 44-51%). LiveCodeBench: every rule cuts
  rounds (R 0.50-0.84) but every one loses accuracy (4-42% vs 56%).
- **Step 8, Block 7 (optional: Qwen3-8B + RedHatAI P-EAGLE, parallel drafting, V1 full patches, loosest),
  complete 2026-10-04 ~16:00Z, 5.2 GPU-h.** P-EAGLE drafts better than the paper's Qwen3 EAGLE-3 head (lossless
  l_bar 2.16 vs 1.50 on GSM8K, 1.84 on LiveCodeBench) and passes its probabilities to the sampler (every rule moves
  l_bar). Gains are small: R 0.92-0.98 for mentored_dec, cactus, spec_casc_opt and spec_casc_tok, with accuracy
  costs from 2 points (mentored_dec, GSM8K) to 22 (spec_casc_opt, LiveCodeBench); r_fuzzy 0.25 inflates (lambda
  1.3, 56-70% cap-outs, LiveCodeBench accuracy 3% vs 73%).
- **Step 8 totals:** blocks 1-7 used 124.2 GPU-h on Killarney H100s (1: 34.0, 2: 32.9, 3: 25.2, 4: 16.9, 5: 7.5,
  6: 2.5, 7: 5.2), plus 6.2 for Block 0. Across the eight completed target-drafter pairs of blocks 1-5, at each
  rule's loosest setting: cactus +123% l_bar with completions 2.85x longer, spec_casc_opt +55% / 1.48x, mentored_dec
  +32% / 1.30x, r_fuzzy +23% / 1.78x, spec_casc_tok +16% / 0.92x; spec_casc_tok is the only rule with a rounds
  saving in 20 of 22 arms (mean R 0.82) at lossless accuracy. The paper's pattern (acceptance up, length up, the
  head-restricted rule the exception) holds on every new family and drafter; it fades with drafters close to the
  target (Qwen3-1.7B, DSpark, P-EAGLE).
- **Step 9, Block 1 (GPT-OSS-20B + RedHatAI EAGLE-3, AIME24, Killarney), complete 2026-10-05 21:32Z, 10.6 GPU-h.**
  Lossless l_bar 1.34 (the RH head drafts poorly on long answers; step9/BLOCK0.md), accuracy 77%. Only cactus saves
  rounds (R 0.46-0.56) and it pays 27-57 accuracy points (20-50%); mentored_dec, spec_casc_opt, r_fuzzy and
  spec_casc_tok sit at R 0.88-1.67 with intervals spanning 1 and longer answers (lambda up to 1.68); spec_casc_tok
  0.8 keeps accuracy (77%) at R 1.33 [1.01, 1.86]. n = 30: wide intervals.
- **Step 9, Block 2 (Qwen3-8B + DSpark, AIME24, Killarney), complete 2026-10-05 22:12Z, 12.6 GPU-h.** Lossless l_bar
  2.51, accuracy 70%, 20% cap-outs at 32,768. As on step 8's datasets, DSpark leaves modest, tight gains: mentored_dec
  0.35, cactus 0.03 and spec_casc_tok 0.15 reach R 0.85-0.89 (intervals below 1) at 70-80% accuracy; the looser
  spec_casc_opt / r_fuzzy settings lengthen answers (lambda 1.2-1.5, cap-outs up to 70%) and lose 7-33 points.
- **Step 9, Block 3b (Qwen3-8B + DSpark, LongBench-v2, 65536-position head copy, Killarney), complete 2026-10-05
  23:36Z, 8.9 GPU-h.** Lossless l_bar 1.88, accuracy 47%. Every rule saves rounds with tight intervals at near-unchanged
  length (lambda 0.94-1.10): spec_casc_opt 0.05 R 0.67 [0.62, 0.74], -0.02 R 0.73, cactus 0.35 R 0.74, spec_casc_tok
  0.8 R 0.81, mentored_dec 0.55 R 0.82; accuracy within ~5 points of lossless (42-53%) except r_fuzzy 0.25 (39%).
- **Step 9, Block 3c (Llama-3.1-8B-Instruct + EAGLE-3, LongBench-v2, Killarney), complete 2026-10-06 00:29Z,
  9.9 GPU-h.** The head barely drafts at these positions (lossless l_bar 0.06; prompts of 10k-45k tokens), accuracy
  37%. Relaxing a head that proposes nothing useful only buys runaway answers: cactus raises l_bar to 2.7-4.0 but
  answers grow 13-14x (63-83% cap-outs at 8,192) and R rises to 2.9-4.5; spec_casc_opt grows them 4.8-8.3x (R
  1.5-2.1); mentored_dec 0.75 and r_fuzzy 0.25 2.4-3.2x (R ~2.2); accuracy falls to 25-32%. Only spec_casc_tok and
  the gentlest r_fuzzy stay at lossless (R 1.02-1.04, 37-39%).
- **Step 9, Block 3a (GPT-OSS-20B + RedHatAI EAGLE-3, LongBench-v2, Killarney), complete 2026-10-06 00:56Z,
  11.3 GPU-h.** Lossless l_bar 0.05 (the RH head does not draft at 10k-45k positions; BLOCK0), accuracy 54%. Only
  cactus moves acceptance (l_bar 0.9-3.4) and saves rounds (R 0.50-0.62) at a 18-30 point accuracy cost (24-36%),
  answers 1.1-2.9x longer; every other rule stays at lossless within noise (R 0.90-1.10, accuracy 49-57%).
- **Step 9, Block 4a (GPT-OSS-20B + RedHatAI EAGLE-3, HumanEval, Killarney), complete 2026-10-06 02:17Z, 6.6 GPU-h.**
  Lossless l_bar 2.04, accuracy 98%. No rule saves rounds: acceptance rises (l_bar up to 3.85) but answers grow faster
  (lambda 1.25-3.11), so R is 1.02-2.70 everywhere except spec_casc_opt -0.3 (R 0.94 [0.84, 1.03], 93%). Accuracy
  holds for mentored_dec and spec_casc_tok (95-97%) and falls with the looser cactus (63-87%) and r_fuzzy (23-77%).
  As on step 8's LiveCodeBench with this head, the relaxations buy length, not speed.
- **Step 9, Block 3e (R1-Distill-Llama-8B + yuhuili EAGLE-3, LongBench-v2, Killarney), complete 2026-10-06 02:37Z,
  15.2 GPU-h.** Lossless l_bar 0.03 (the head does not draft past ~2,048 positions; every prompt is 10k-45k tokens),
  accuracy 29%, reported as is. cactus pushes l_bar to 2.8-4.0 by accepting what the collapsed head proposes, and the
  answers run to the cap (lambda 3.9-4.0, 85-88% cap-outs vs 4%) for R 0.86-1.07 and 23-29% accuracy; spec_casc_opt
  0.05 saves rounds (R 0.83 [0.75, 0.92], lambda 1.23) at 33%; the other rules match lossless (R 0.99-1.04).
- **Step 9, Block 3d (Llama-3.1-8B-Instruct + EAGLE-1, LongBench-v2, Killarney), complete 2026-10-06 03:07Z,
  9.7 GPU-h.** EAGLE-1 still drafts at these positions (lossless l_bar 0.92, against EAGLE-3's 0.06 in Block 3c),
  accuracy 35%. spec_casc_tok is again the one rule that speeds Llama up: R 0.57-0.65 with shorter answers (lambda
  0.69-0.73) at 35-37% accuracy, as on step 8's datasets. cactus, r_fuzzy 0.25 and mentored_dec 0.75 inflate answers
  4-10x (cap-outs up to 79%, R 3.9-6.8, accuracy 19-26%); spec_casc_opt lengthens them 1.7-4.2x (R 1.1-1.4).
- **Step 9, Block 4b (Qwen3-8B + DSpark, HumanEval, Killarney), complete 2026-10-06 03:08Z, 8.1 GPU-h.** Lossless l_bar
  2.50, accuracy 84% (11% cap-outs at 9,000). Small, tight gains as on Qwen3's other datasets: R 0.92-0.95 for
  mentored_dec, cactus 0.03 / 0.35, spec_casc_opt -0.1 and spec_casc_tok 0.8 at 80-89% accuracy; spec_casc_opt 0.05
  (R 1.09, 61%) and r_fuzzy 0.15 / 0.25 (64-70%) cost accuracy without saving rounds.
- **Step 9, Block 4c (Llama-3.1-8B-Instruct + EAGLE-3, HumanEval, Killarney), complete 2026-10-06 03:53Z, 5.4 GPU-h.**
  Lossless l_bar 2.70, accuracy 56% by the campaign's grader, which runs the last code block: 189 of this block's runs
  (9 lossless) end with a usage block after the defining one and score as failures (`step9/humaneval_lastblock.csv`,
  for a later re-grade), so every Llama HumanEval accuracy here is a lower bound. spec_casc_tok saves rounds at
  unchanged accuracy (R 0.88-0.95, 53-59%); cactus inflates answers ~13x (R 8.3-9.5, 35-61% cap-outs, 4-13%) and
  r_fuzzy 0.08 / 0.25 3-7x with accepted length below lossless (degenerate text; R 5.2-15.0); mentored_dec and
  spec_casc_opt lengthen answers (lambda 1.1-1.9) at 35-53%.
- **Step 9, Block 5a (Llama-3.1-8B-Instruct + EAGLE-3, AIME24, Killarney), complete 2026-10-06 04:56Z, 3.4 GPU-h.**
  Llama-3.1-8B is at the floor here (lossless accuracy 3%, 1 of 30; every arm 0-7%), so accuracy cannot separate the
  rules; lossless l_bar 0.77 on long answers. spec_casc_tok 0.8 and spec_casc_opt -0.02 / 0.05 cut rounds hard (R
  0.18-0.30) by shortening the answers (lambda 0.40-0.81) at l_bar 1.5-4.5; cactus raises l_bar to 4.2-5.0 but
  lengthens answers 3-5x (R 0.80-1.43); mentored_dec 0.75 lambda 2.9, R 1.70. n = 30 at the accuracy floor: read the
  length and rounds columns only.
- **Step 9, Block 4d (Llama-3.1-8B-Instruct + EAGLE-1, HumanEval, Killarney), complete 2026-10-06 04:58Z, 4.1 GPU-h.**
  Lossless l_bar 1.76, accuracy 58% (a lower bound: 344 of this block's runs end with a usage block, as in Block 4c).
  spec_casc_tok 0.8 saves rounds (R 0.94 [0.88, 1.00]) at 54%; cactus inflates answers 9-12x (R 5.0-9.1, accuracy
  1-3%), r_fuzzy 0.25 8x (R 9.1, 5%), spec_casc_opt 0.05 5x (R 3.3, 8%); the gentle settings cost 4-13 points at
  R 1.0-1.6.
- **Step 9, Block 4e (R1-Distill-Llama-8B + yuhuili EAGLE-3, HumanEval, Killarney), complete 2026-10-06 05:04Z,
  14.8 GPU-h.** Lossless l_bar 1.89, accuracy 86% (7% cap-outs at 9,000). No rule saves rounds (R 0.95-1.63);
  spec_casc_tok (R 0.96-0.98, 81-87%) and mentored_dec / spec_casc_opt -0.3 / -0.1 (R 1.00-1.12, 79-84%) stay near
  lossless; cactus runs to the cap (64-77% cap-outs, 16-25%) and r_fuzzy 0.08 / 0.25 lose 35-69 points.
- **Step 9, Block 5b (Llama-3.1-8B-Instruct + EAGLE-1, AIME24, Killarney), complete 2026-10-06 05:25Z, 6.1 GPU-h.**
  At the accuracy floor like Block 5a (lossless 3%, arms 0-7%). spec_casc_tok shortens answers (lambda 0.46-0.52)
  and cuts rounds (R 0.26-0.49); cactus and spec_casc_opt lengthen them 1.9-4.4x (cap-outs 23-53%). Rounds and length
  only.
- **Step 9 Phase 1 totals (2026-10-06 05:25Z):** all 14 blocks done on Killarney H100s in ~11 h of wall time
  (Block 0 at 19:23Z to the last block at 05:25Z), 126.7 GPU-h of arm time (estimate 124; per block 3.4-15.2), up to
  16 lanes at once. Across the five pairs the step-8 picture holds on the new datasets: acceptance rises with every
  rule, answers lengthen, and spec_casc_tok is the one rule that saves rounds at lossless accuracy wherever the head
  drafts (Llama, Qwen3 DSpark); with heads that stop drafting at long positions (R1, the RH GPT-OSS head and
  Llama EAGLE-3 on LongBench-v2) the relaxations either change nothing or, cactus above all, only buy runaway
  answers.
- **Step 9 Phase 2 (standalone drafters, each rule at its loosest grid alpha + lossless; HumanEval, LongBench-v2,
  MT-Bench, AIME24; Killarney), started 2026-10-06 05:30Z once Phase 1 was done, all 20 blocks complete by ~11:20Z.**
  Qwen3-1.7B / 0.6B / P-EAGLE use 65536-position config copies on LongBench-v2 only (README deviation 40).
  - Qwen3-8B + Qwen3-1.7B (blocks 6a-6d; lossless l_bar 3.0-4.2): every rule saves rounds with shorter answers, R
    0.54-0.82, lambda 0.79-0.94, accuracy at or near lossless (HumanEval 82-85% vs 84%, AIME24 70-80% vs 73%,
    LongBench-v2 42-51% vs 45% except spec_casc_opt 33%): the strong-drafter case of step 8, now on all four datasets.
  - Qwen3-8B + Qwen3-0.6B (7a-7d; l_bar 2.4-3.6): the same, slightly weaker (R 0.54-0.90), accuracy within noise
    except r_fuzzy 0.25 on AIME24 (50% vs 67%).
  - Qwen3-8B + P-EAGLE (8a-8d; l_bar 1.4-2.3): little to gain, as in step 8 (R 0.82-0.98 at best); r_fuzzy 0.25
    inflates (HumanEval R 1.42, 25%; AIME24 R 1.30, 37%) and the other rules cost 0-12 accuracy points.
  - Llama-3.1-8B-Instruct + Llama-3.2-1B (9a-9d; l_bar 3.1-4.0): spec_casc_tok saves rounds at lossless accuracy
    (HumanEval R 0.84, 57% vs 55%; LongBench-v2 R 0.56, 36% vs 37%; MT-Bench R 0.83); the other rules save rounds on
    HumanEval but lose 14-32 points, and cactus / r_fuzzy lengthen LongBench-v2 and MT-Bench answers 1.6-2.5x. AIME24
    sits at the accuracy floor (0-7%), where every rule shortens answers.
  - R1-Distill-Llama-8B + Llama-3.2-1B (10a-10d; l_bar 1.6-1.8): mentored_dec and spec_casc_tok save rounds on
    LongBench-v2 and MT-Bench (R 0.68-0.77) at near-lossless accuracy; on HumanEval only spec_casc_tok keeps accuracy
    (R 0.81, 77% vs 89%), cactus and spec_casc_opt lengthen answers 1.4-3.3x and lose 25-63 points. On AIME24
    (lossless 43%) every rule loses accuracy without a real saving (spec_casc_tok R 0.99 at 37%, mentored_dec R 0.76
    at 20%, cactus / r_fuzzy 0-3%).
- **Step 9 totals:** 34 blocks (Phase 1: 14 dedicated-drafter blocks; Phase 2: 20 standalone blocks), 597 manifest
  items, all done in ~16 h of wall time (2026-10-05 19:23Z to 2026-10-06 ~11:20Z) on Killarney H100s, up to 16 lanes.
  GPU-h (item wall time from the lane journals, as step 8): Phase 1 126.9, Phase 2 60.3, Block 0 smoke + warm-ups 2.1,
  total 189.3. Open items for a later re-grade (graders unchanged): 101 AIME24 runs whose last boxed answer has more
  than 3 digits (`step9/aime_boxed_long.csv`), 847 HumanEval runs whose last code block is not the solution
  (`step9/humaneval_lastblock.csv`, almost all Llama-3.1: its HumanEval accuracies are lower bounds).
- **MT-Bench judge scores for steps 8 and 9 (2026-10-06, `step9/mtbench_judge/mtbench_vs_lossless.csv`; deviation 45,
  $162.28).** Paired by question against the pair's own lossless run (1-10): spec_casc_tok never loses quality (every
  arm within noise of lossless or above: +1.01 [0.47, 1.59] with Llama-3.2-1B, +0.57 with Llama EAGLE-3 at 0.8);
  cactus and the loose r_fuzzy / spec_casc_opt settings lose 1.4-4.8 points wherever the drafter is weak (GPT-OSS RH
  head, both Llama heads, R1-Distill, P-EAGLE: e.g. Llama EAGLE-1 cactus 1.3-2.0 vs 6.0); with drafters close to the
  target (Qwen3-1.7B, 0.6B, DSpark at its gentler settings) every rule is near neutral (-0.7 to +0.5). The same
  ordering as the accuracy columns of the other benchmarks.
- **HumanEval grader check (deviation 45, `step9/humaneval_regrade.csv`).** Executing the last code block that
  defines the entry point instead of the last block flips 315 of 897 flagged runs to passed: lossless +0 to +4.0
  points (Llama-3.1 +0.7 to +4.0, Qwen3 +0 to +3.3), arms +0.7 to +10 points (mostly Llama). It does not make the
  lossless references of one target agree better and changes no conclusion; the tables keep the campaign's grader.
- **Qwen3-8B + Qwen3-0.6B, GSM8K / LiveCodeBench, the two missing rules (deviation 46).** lambda (accuracy): GSM8K
  spec_casc_opt 0.05 0.98 (79%), r_fuzzy 0.25 1.01 (76%), lossless 77%; LiveCodeBench spec_casc_opt 0.95 (70%), r_fuzzy
  1.02 (61%), lossless 72%. Rounds ratio 0.87 / 0.72 (GSM8K) and 0.83 / 0.68 (LiveCodeBench). With this drafter every
  rule saves rounds; r_fuzzy 0.25 costs 11 points on LiveCodeBench.

