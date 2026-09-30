# NAACL-2027 addendum: results

Generated 2026-09-30 19:12 UTC by `scripts/addendum_results.py` from the CSVs it names; hand-written observations are in the last section (from `RESULTS_notes.md`). Settings and deviations: `campaign/addendum/README.md`.

## Status

Source: `campaign/addendum/manifest.csv` (278 rows). GPU-hours used so far (sum of `gpu_hours_actual`): 54.6; estimated remaining, runnable rows: 53.1; blocked rows: 1.6.

| step | done | running | queued | pending | blocked |
|---|---:|---:|---:|---:|---:|
| 0.5 | 6 | 0 | 6 | 0 | 0 |
| 2.1 | 92 | 0 | 4 | 0 | 0 |
| 2.2 | 20 | 0 | 6 | 0 | 0 |
| 3 | 10 | 0 | 10 | 0 | 0 |
| 4.1 | 4 | 0 | 4 | 0 | 0 |
| 4.2 | 0 | 0 | 12 | 0 | 0 |
| 4.3 | 0 | 0 | 8 | 0 | 0 |
| 5.1 | 18 | 0 | 23 | 0 | 0 |
| 5.2 | 11 | 0 | 0 | 0 | 0 |
| 6 | 12 | 0 | 18 | 0 | 0 |
| 7 | 0 | 0 | 6 | 0 | 8 |

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
| qwen3-8b | strict | strict | 6.94 [6.29, 7.55] | 7.79 | 10 | 0 |
| qwen3-8b | mentored_dec | 0.75 | 6.40 [5.71, 7.06] | 7.45 | 13 | 0 |
| qwen3-8b | cactus | 0.35 | 2.99 [2.40, 3.64] | 3.74 | 22 | 0 |
| qwen3-8b | spec_casc_opt | 0.05 | 3.95 [3.40, 4.50] | 5.07 | 22 | 0 |
| qwen3-8b | r_fuzzy | 0.25 | 3.05 [2.61, 3.51] | 3.73 | 20 | 0 |
| qwen3-8b | spec_casc_tok | 0.8 | 7.21 [6.59, 7.80] | 8.00 | 9 | 0 |

## Step 2: seeds on the relaxed arms

Source: `campaign/addendum/seeds/summary.csv` (per-seed tables `campaign/addendum/seeds/<dataset>__seed<k>.csv`). Seed 0 is the campaign's run (old box, H100 PCIe); seeds 1-2 ran on Nibi (H100 SXM). Ratios pair each seed's relaxed arm with strict of the same seed; '-' = that seed is not complete yet.

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
| qwen3-8b | aime24 | spec_casc_opt | 0.05 | 1.42 | - | - | - | - | - | 1.42 (-) | 1.14 | - | - | - | - | - | 1.14 (-) | 30% | - | - | - | - | - |
| qwen3-8b | aime24 | r_fuzzy | 0.25 | 1.29 | - | - | - | - | - | 1.29 (-) | 1.18 | - | - | - | - | - | 1.18 (-) | 40% | - | - | - | - | - |
| qwen3-8b | humaneval | mentored_dec | 0.75 | 1.08 | 1.05 | 1.08 | - | - | 0.02 | 1.07 (0.02) | 1.02 | 0.97 | 0.99 | - | - | 0.02 | 0.99 (0.02) | 85% | 79% | 81% | - | - | 3% |
| qwen3-8b | humaneval | cactus | 0.35 | 1.14 | 1.09 | 1.08 | - | - | 0.03 | 1.11 (0.03) | 1.01 | 0.90 | 0.90 | - | - | 0.06 | 0.94 (0.06) | 75% | 79% | 77% | - | - | 2% |
| qwen3-8b | humaneval | spec_casc_opt | 0.05 | 1.72 | 1.60 | 1.67 | - | - | 0.06 | 1.66 (0.06) | 1.46 | 1.30 | 1.33 | - | - | 0.08 | 1.36 (0.08) | 49% | 48% | 51% | - | - | 1% |
| qwen3-8b | humaneval | r_fuzzy | 0.25 | 1.65 | 1.52 | 1.46 | - | - | 0.10 | 1.54 (0.10) | 1.41 | 1.22 | 1.19 | - | - | 0.12 | 1.27 (0.12) | 16% | 13% | 12% | - | - | 2% |
| qwen3-8b | humaneval | spec_casc_tok | 0.8 | 1.08 | 1.03 | 1.01 | - | - | 0.03 | 1.04 (0.03) | 1.05 | 1.01 | 0.97 | - | - | 0.04 | 1.01 (0.04) | 85% | 83% | 88% | - | - | 3% |
| qwen3-8b | livecodebench | mentored_dec | 0.75 | 1.05 | 1.05 | 1.06 | - | - | 0.01 | 1.05 (0.01) | 0.95 | 0.95 | 0.96 | - | - | 0.01 | 0.95 (0.01) | 63% | 62% | 64% | - | - | 1% |
| qwen3-8b | livecodebench | cactus | 0.35 | 1.15 | 1.11 | 1.15 | - | - | 0.02 | 1.14 (0.02) | 0.82 | 0.68 | 0.69 | - | - | 0.08 | 0.73 (0.08) | 44% | 37% | 46% | - | - | 5% |
| qwen3-8b | livecodebench | spec_casc_opt | 0.05 | 1.27 | 1.22 | 1.25 | - | - | 0.03 | 1.24 (0.03) | 1.09 | 1.01 | 1.06 | - | - | 0.04 | 1.05 (0.04) | 33% | 30% | 32% | - | - | 2% |
| qwen3-8b | livecodebench | r_fuzzy | 0.25 | 1.07 | - | - | - | - | - | 1.07 (-) | 0.92 | - | - | - | - | - | 0.92 (-) | 2% | - | - | - | - | - |
| qwen3-8b | livecodebench | spec_casc_tok | 0.8 | 1.00 | - | - | - | - | - | 1.00 (-) | 0.96 | - | - | - | - | - | 0.96 (-) | 71% | - | - | - | - | - |
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

| n_draft | source | n_cases | mean_l_bar | mean_l_bar_ci_lo | mean_l_bar_ci_hi | mean_completion_tokens | mean_completion_tokens_ci_lo | mean_completion_tokens_ci_hi | mean_verifier_rounds | mean_verifier_rounds_ci_lo | mean_verifier_rounds_ci_hi | mean_wall_time_s | mean_wall_time_s_ci_lo | mean_wall_time_s_ci_hi | accuracy | accuracy_ci_lo | accuracy_ci_hi | capout_rate | n_pairs_vs_nibiref | lambda_vs_nibiref | rounds_ratio_vs_nibiref | time_ratio_vs_nibiref | lambda_vs_nibiref_ci_lo | lambda_vs_nibiref_ci_hi | rounds_ratio_vs_nibiref_ci_lo | rounds_ratio_vs_nibiref_ci_hi | time_ratio_vs_nibiref_ci_lo | time_ratio_vs_nibiref_ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2.000 | nspec2 (Nibi) | 150.000 | 1.427 | 1.410 | 1.444 | 308.413 | 264.260 | 357.495 | 129.100 | 110.100 | 150.088 | 0.666 | 0.571 | 0.774 | 0.973 | 0.947 | 0.993 | 0.013 | 150.000 | 0.959 | 1.387 | 0.928 | 0.852 | 1.075 | 1.233 | 1.555 | 0.828 | 1.036 |
| 3.000 | nspec3 (Nibi) | 150.000 | 1.876 | 1.846 | 1.906 | 323.420 | 265.127 | 389.107 | 115.133 | 94.059 | 138.894 | 0.662 | 0.546 | 0.793 | 0.960 | 0.927 | 0.987 | 0.033 | 150.000 | 1.006 | 1.237 | 0.923 | 0.899 | 1.113 | 1.094 | 1.381 | 0.820 | 1.028 |
| 4.000 | nspec4 (Nibi) | 150.000 | 2.195 | 2.153 | 2.237 | 312.920 | 264.220 | 367.280 | 101.300 | 84.466 | 119.633 | 0.654 | 0.550 | 0.772 | 0.967 | 0.933 | 0.993 | 0.013 | 150.000 | 0.973 | 1.088 | 0.911 | 0.852 | 1.109 | 0.951 | 1.248 | 0.804 | 1.040 |
| 6.000 | campaign seed 0 (old box, H100 PCIe) | 150.000 | 2.567 | 2.502 | 2.631 | 322.187 | 270.218 | 380.896 | 94.020 | 77.873 | 112.361 | 2.418 | 2.073 | 2.827 | 0.960 | 0.927 | 0.987 | 0.020 | - | - | - | - | - | - | - | - | - | - |
| 6.000 | nibiref (Nibi, campaign settings) | 150.000 | 2.582 | 2.518 | 2.647 | 321.627 | 267.113 | 383.728 | 93.087 | 76.847 | 111.714 | 0.718 | 0.598 | 0.854 | 0.967 | 0.933 | 0.993 | 0.013 | - | - | - | - | - | - | - | - | - | - |
| 8.000 | nspec8 (Nibi) | 150.000 | 2.772 | 2.699 | 2.846 | 314.493 | 265.833 | 368.707 | 87.180 | 73.193 | 103.427 | 0.760 | 0.641 | 0.894 | 0.960 | 0.927 | 0.987 | 0.013 | 150.000 | 0.978 | 0.937 | 1.059 | 0.848 | 1.127 | 0.809 | 1.089 | 0.921 | 1.227 |
| 10.000 | nspec10 (Nibi) | 150.000 | 2.878 | 2.801 | 2.957 | 333.907 | 277.693 | 397.048 | 90.020 | 74.246 | 108.460 | 0.873 | 0.721 | 1.049 | 0.953 | 0.920 | 0.987 | 0.027 | 150.000 | 1.038 | 0.967 | 1.217 | 0.945 | 1.151 | 0.875 | 1.081 | 1.104 | 1.360 |

`campaign/addendum/tables/nspec__gsm8k_qwen3.csv`:

| n_draft | source | n_cases | mean_l_bar | mean_l_bar_ci_lo | mean_l_bar_ci_hi | mean_completion_tokens | mean_completion_tokens_ci_lo | mean_completion_tokens_ci_hi | mean_verifier_rounds | mean_verifier_rounds_ci_lo | mean_verifier_rounds_ci_hi | mean_wall_time_s | mean_wall_time_s_ci_lo | mean_wall_time_s_ci_hi | accuracy | accuracy_ci_lo | accuracy_ci_hi | capout_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 6.000 | campaign seed 0 (old box, H100 PCIe) | 150.000 | 1.514 | 1.487 | 1.542 | 1291.930 | 1202.220 | 1381.780 | 510.080 | 475.367 | 545.607 | 10.299 | 9.576 | 11.023 | 0.800 | 0.733 | 0.860 | 0.247 |

`campaign/addendum/tables/nspec__livecodebench.csv`:

| n_draft | source | n_cases | mean_l_bar | mean_l_bar_ci_lo | mean_l_bar_ci_hi | mean_completion_tokens | mean_completion_tokens_ci_lo | mean_completion_tokens_ci_hi | mean_verifier_rounds | mean_verifier_rounds_ci_lo | mean_verifier_rounds_ci_hi | mean_wall_time_s | mean_wall_time_s_ci_lo | mean_wall_time_s_ci_hi | accuracy | accuracy_ci_lo | accuracy_ci_hi | capout_rate | n_pairs_vs_nibiref | lambda_vs_nibiref | rounds_ratio_vs_nibiref | time_ratio_vs_nibiref | lambda_vs_nibiref_ci_lo | lambda_vs_nibiref_ci_hi | rounds_ratio_vs_nibiref_ci_lo | rounds_ratio_vs_nibiref_ci_hi | time_ratio_vs_nibiref_ci_lo | time_ratio_vs_nibiref_ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2.000 | nspec2 (Nibi) | 90.000 | 1.287 | 1.270 | 1.305 | 3406.870 | 2925.840 | 3919.290 | 1518.030 | 1291.300 | 1773.180 | 7.601 | 6.458 | 8.843 | 0.878 | 0.811 | 0.944 | 0.044 | 90.000 | 1.004 | 1.355 | 0.912 | 0.918 | 1.090 | 1.219 | 1.494 | 0.821 | 1.006 |
| 3.000 | nspec3 (Nibi) | 90.000 | 1.660 | 1.631 | 1.690 | 3603.570 | 3057.700 | 4193.650 | 1395.490 | 1172.010 | 1633.890 | 7.811 | 6.571 | 9.177 | 0.922 | 0.867 | 0.967 | 0.044 | 90.000 | 1.062 | 1.246 | 0.937 | 0.970 | 1.166 | 1.128 | 1.383 | 0.847 | 1.040 |
| 4.000 | nspec4 (Nibi) | 90.000 | 1.914 | 1.870 | 1.957 | 3540.600 | 2963.740 | 4138.680 | 1270.980 | 1045.980 | 1508.860 | 7.937 | 6.587 | 9.467 | 0.911 | 0.856 | 0.967 | 0.022 | 90.000 | 1.043 | 1.135 | 0.952 | 0.937 | 1.163 | 1.016 | 1.270 | 0.851 | 1.066 |
| 6.000 | campaign seed 0 (old box, H100 PCIe) | 90.000 | 2.164 | 2.106 | 2.223 | 3456.240 | 2921.260 | 4034.700 | 1150.830 | 948.751 | 1360.840 | 25.190 | 21.284 | 29.693 | 0.889 | 0.822 | 0.956 | 0.022 | - | - | - | - | - | - | - | - | - | - |
| 6.000 | nibiref (Nibi, campaign settings) | 90.000 | 2.213 | 2.153 | 2.275 | 3394.530 | 2879.360 | 3957.580 | 1120.230 | 921.554 | 1331.580 | 8.333 | 6.899 | 9.934 | 0.911 | 0.844 | 0.967 | 0.044 | - | - | - | - | - | - | - | - | - | - |
| 8.000 | nspec8 (Nibi) | 90.000 | 2.330 | 2.258 | 2.402 | 3460.600 | 2926.240 | 4051.970 | 1112.770 | 912.841 | 1332.430 | 9.381 | 7.733 | 11.174 | 0.867 | 0.789 | 0.933 | 0.033 | 90.000 | 1.019 | 0.993 | 1.126 | 0.926 | 1.122 | 0.890 | 1.107 | 1.010 | 1.251 |
| 10.000 | nspec10 (Nibi) | 90.000 | 2.403 | 2.326 | 2.480 | 3462.240 | 2933.890 | 4055.140 | 1092.430 | 894.754 | 1323.660 | 10.314 | 8.434 | 12.468 | 0.889 | 0.822 | 0.956 | 0.067 | 90.000 | 1.020 | 0.975 | 1.238 | 0.922 | 1.128 | 0.870 | 1.091 | 1.104 | 1.383 |

`campaign/addendum/tables/nspec__livecodebench_qwen3.csv`:

| n_draft | source | n_cases | mean_l_bar | mean_l_bar_ci_lo | mean_l_bar_ci_hi | mean_completion_tokens | mean_completion_tokens_ci_lo | mean_completion_tokens_ci_hi | mean_verifier_rounds | mean_verifier_rounds_ci_lo | mean_verifier_rounds_ci_hi | mean_wall_time_s | mean_wall_time_s_ci_lo | mean_wall_time_s_ci_hi | accuracy | accuracy_ci_lo | accuracy_ci_hi | capout_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 6.000 | campaign seed 0 (old box, H100 PCIe) | 90.000 | 1.205 | 1.181 | 1.230 | 8028.540 | 7257.280 | 8783.430 | 3703.370 | 3333.140 | 4069.680 | 71.423 | 64.069 | 78.699 | 0.700 | 0.600 | 0.800 | 0.322 |

## Step 4.1: temperature (strict, seed 0)

`campaign/addendum/tables/temp__gsm8k.csv`:

| temperature | source | n_cases | mean_l_bar | mean_l_bar_ci_lo | mean_l_bar_ci_hi | mean_completion_tokens | mean_completion_tokens_ci_lo | mean_completion_tokens_ci_hi | mean_verifier_rounds | mean_verifier_rounds_ci_lo | mean_verifier_rounds_ci_hi | mean_wall_time_s | mean_wall_time_s_ci_lo | mean_wall_time_s_ci_hi | accuracy | accuracy_ci_lo | accuracy_ci_hi | capout_rate | n_pairs_vs_nibiref | lambda_vs_nibiref | rounds_ratio_vs_nibiref | time_ratio_vs_nibiref | lambda_vs_nibiref_ci_lo | lambda_vs_nibiref_ci_hi | rounds_ratio_vs_nibiref_ci_lo | rounds_ratio_vs_nibiref_ci_hi | time_ratio_vs_nibiref_ci_lo | time_ratio_vs_nibiref_ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.000 | campaign seed 0 (old box, H100 PCIe) | 150.000 | 2.567 | 2.503 | 2.630 | 322.187 | 270.546 | 379.964 | 94.020 | 77.787 | 112.314 | 2.418 | 2.078 | 2.821 | 0.960 | 0.927 | 0.987 | 0.020 | - | - | - | - | - | - | - | - | - | - |
| 1.000 | nibiref (Nibi, campaign settings) | 150.000 | 2.582 | 2.516 | 2.646 | 321.627 | 266.393 | 382.822 | 93.087 | 76.793 | 111.081 | 0.718 | 0.600 | 0.855 | 0.967 | 0.933 | 0.993 | 0.013 | - | - | - | - | - | - | - | - | - | - |
| 1.200 | temp1.2 (Nibi) | 150.000 | 2.359 | 2.299 | 2.421 | 408.113 | 342.573 | 480.314 | 127.633 | 106.047 | 152.460 | 0.966 | 0.803 | 1.140 | 0.960 | 0.927 | 0.987 | 0.033 | 150.000 | 1.269 | 1.371 | 1.347 | 1.097 | 1.468 | 1.176 | 1.583 | 1.159 | 1.556 |
| 1.500 | temp1.5 (Nibi) | 150.000 | 1.791 | 1.751 | 1.833 | 1266.230 | 1139.000 | 1392.990 | 459.013 | 412.151 | 504.961 | 3.365 | 3.027 | 3.696 | 0.313 | 0.240 | 0.387 | 0.480 | 150.000 | 3.937 | 4.931 | 4.690 | 3.290 | 4.711 | 4.105 | 5.930 | 3.942 | 5.623 |

`campaign/addendum/tables/temp__gsm8k_qwen3.csv`:

| temperature | source | n_cases | mean_l_bar | mean_l_bar_ci_lo | mean_l_bar_ci_hi | mean_completion_tokens | mean_completion_tokens_ci_lo | mean_completion_tokens_ci_hi | mean_verifier_rounds | mean_verifier_rounds_ci_lo | mean_verifier_rounds_ci_hi | mean_wall_time_s | mean_wall_time_s_ci_lo | mean_wall_time_s_ci_hi | accuracy | accuracy_ci_lo | accuracy_ci_hi | capout_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.000 | campaign seed 0 (old box, H100 PCIe) | 150.000 | 1.514 | 1.488 | 1.541 | 1291.930 | 1200.620 | 1381.830 | 510.080 | 475.479 | 544.813 | 10.299 | 9.575 | 11.022 | 0.800 | 0.733 | 0.860 | 0.247 |

`campaign/addendum/tables/temp__livecodebench.csv`:

| temperature | source | n_cases | mean_l_bar | mean_l_bar_ci_lo | mean_l_bar_ci_hi | mean_completion_tokens | mean_completion_tokens_ci_lo | mean_completion_tokens_ci_hi | mean_verifier_rounds | mean_verifier_rounds_ci_lo | mean_verifier_rounds_ci_hi | mean_wall_time_s | mean_wall_time_s_ci_lo | mean_wall_time_s_ci_hi | accuracy | accuracy_ci_lo | accuracy_ci_hi | capout_rate | n_pairs_vs_nibiref | lambda_vs_nibiref | rounds_ratio_vs_nibiref | time_ratio_vs_nibiref | lambda_vs_nibiref_ci_lo | lambda_vs_nibiref_ci_hi | rounds_ratio_vs_nibiref_ci_lo | rounds_ratio_vs_nibiref_ci_hi | time_ratio_vs_nibiref_ci_lo | time_ratio_vs_nibiref_ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.000 | campaign seed 0 (old box, H100 PCIe) | 90.000 | 2.164 | 2.106 | 2.225 | 3456.240 | 2920.010 | 4045.980 | 1150.830 | 949.597 | 1369.160 | 25.190 | 21.249 | 29.584 | 0.889 | 0.822 | 0.944 | 0.022 | - | - | - | - | - | - | - | - | - | - |
| 1.000 | nibiref (Nibi, campaign settings) | 90.000 | 2.213 | 2.153 | 2.274 | 3394.530 | 2871.870 | 3975.880 | 1120.230 | 923.710 | 1338.350 | 8.333 | 6.889 | 9.922 | 0.911 | 0.844 | 0.967 | 0.044 | - | - | - | - | - | - | - | - | - | - |
| 1.200 | temp1.2 (Nibi) | 90.000 | 2.004 | 1.945 | 2.065 | 3646.640 | 3096.530 | 4255.330 | 1296.980 | 1071.020 | 1547.700 | 9.625 | 7.946 | 11.476 | 0.867 | 0.789 | 0.933 | 0.056 | 90.000 | 1.074 | 1.158 | 1.155 | 0.986 | 1.174 | 1.047 | 1.280 | 1.048 | 1.277 |
| 1.500 | temp1.5 (Nibi) | 90.000 | 1.254 | 1.194 | 1.315 | 6193.010 | 5409.290 | 6961.310 | 2932.840 | 2543.210 | 3320.470 | 20.889 | 18.162 | 23.727 | 0.078 | 0.033 | 0.133 | 0.022 | 90.000 | 1.824 | 2.618 | 2.507 | 1.466 | 2.288 | 2.038 | 3.341 | 1.945 | 3.220 |

`campaign/addendum/tables/temp__livecodebench_qwen3.csv`:

| temperature | source | n_cases | mean_l_bar | mean_l_bar_ci_lo | mean_l_bar_ci_hi | mean_completion_tokens | mean_completion_tokens_ci_lo | mean_completion_tokens_ci_hi | mean_verifier_rounds | mean_verifier_rounds_ci_lo | mean_verifier_rounds_ci_hi | mean_wall_time_s | mean_wall_time_s_ci_lo | mean_wall_time_s_ci_hi | accuracy | accuracy_ci_lo | accuracy_ci_hi | capout_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.000 | campaign seed 0 (old box, H100 PCIe) | 90.000 | 1.205 | 1.181 | 1.230 | 8028.540 | 7266.830 | 8783.630 | 3703.370 | 3332.720 | 4077.010 | 71.423 | 63.994 | 78.646 | 0.700 | 0.600 | 0.789 | 0.322 |

## Step 4.2: Qwen3 at its recommended sampler

Pending.

## Step 4.3: standalone LM drafter (Qwen3-0.6B)

Pending.

## Step 5: alpha grid completion and best-setting validation

Source: `campaign/addendum/best_setting.csv`, one row per (target, dataset, method). Chosen alpha = the grid alpha with the lowest seed-0 time ratio among those whose accuracy is within 2 points of strict (mtbench, ungraded: rounds ratio < 1); `chosen_alpha_by_rounds_ratio` = the same choice made on the rounds ratio. Time ratios of Nibi-run cells (the step-5.1 additions) are taken against the Nibi strict reference (`s0_time_ratio_basis`). Seed 1 = the step-5.2 validation run on Nibi, paired with Nibi strict seed 1 ('-' = not complete yet); validated = seed-1 time ratio < 1 and the same accuracy rule holds on seed 1.

| target | dataset | method | grid complete | chosen alpha (by rounds) | s0 lambda | s0 rounds ratio | s0 time ratio | s0 acc / strict | s1 lambda | s1 rounds ratio | s1 time ratio | s1 acc / strict | validated |
|---|---|---|---|---|---:|---:|---:|---|---:|---:|---:|---|---|
| gpt-oss-20b | gsm8k | mentored_dec | True | 0.55 (0.55) | 1.10 | 0.86 | 0.84 | 95% / 96% | 0.98 | 0.76 | 0.75 | 97% / 96% | yes |
| gpt-oss-20b | gsm8k | spec_casc_tok | True | 0.55 (0.8) | 0.92 | 0.83 | 0.85 | 98% / 96% | 0.92 | 0.85 | 0.85 | 97% / 96% | yes |
| gpt-oss-20b | aime24 | mentored_dec | True | 0.55 (0.55) | 1.18 | 0.92 | 0.94 | 80% / 77% | 1.07 | 0.87 | 0.87 | 70% / 80% | no |
| gpt-oss-20b | aime24 | spec_casc_tok | True | 0.15 (0.15) | 1.00 | 0.91 | 0.95 | 83% / 77% | 1.15 | 1.12 | 1.12 | 77% / 80% | no |
| gpt-oss-20b | humaneval | mentored_dec | True | 0.55 (0.55) | 1.09 | 0.89 | 0.94 | 95% / 96% | 1.18 | 0.96 | 0.96 | 95% / 95% | yes |
| gpt-oss-20b | humaneval | spec_casc_tok | True | 0.35 (0.35) | 0.95 | 0.90 | 0.95 | 96% / 96% | 1.01 | 0.98 | 0.99 | 97% / 95% | yes |
| gpt-oss-20b | livecodebench | mentored_dec | True | 0.55 (0.55) | 1.20 | 0.96 | 0.95 | 88% / 89% | 1.15 | 0.93 | 0.92 | 87% / 90% | no |
| gpt-oss-20b | livecodebench | spec_casc_tok | True | 0.35 (0.35) | 1.01 | 0.94 | 0.96 | 91% / 89% | 1.02 | 0.96 | 0.94 | 93% / 90% | yes |
| gpt-oss-20b | mtbench | mentored_dec | True | 0.75 (0.75) | 1.10 | 0.75 | 0.87 | - / - | 1.14 | 0.76 | 0.78 | - / - | yes |
| gpt-oss-20b | mtbench | spec_casc_tok | True | 0.55 (0.8) | 0.97 | 0.93 | 0.89 | - / - | 1.00 | 0.95 | 0.95 | - / - | yes |
| gpt-oss-20b | longbench_v2 | mentored_dec | True | 0.55 (0.55) | 1.11 | 0.89 | 1.00 | 57% / 56% | 1.38 | 1.09 | 1.03 | 55% / 57% | no |
| gpt-oss-20b | longbench_v2 | spec_casc_tok | True | 0.55 (0.55) | 1.06 | 0.97 | 0.94 | 57% / 56% | 1.20 | 1.09 | 1.04 | 55% / 57% | no |
| qwen3-8b | gsm8k | mentored_dec | False | - (-) | - | - | - | - / - | - | - | - | - | - |
| qwen3-8b | gsm8k | spec_casc_tok | False | 0.8 (0.8) | 0.99 | 0.95 | 0.96 | 79% / 80% | 1.00 | 0.95 | 0.97 | 82% / 81% | yes |
| qwen3-8b | aime24 | mentored_dec | False | 0.15 (0.15) | 0.91 | 0.88 | 0.89 | 73% / 70% | - | - | - | - | - |
| qwen3-8b | aime24 | spec_casc_tok | False | 0.8 (0.8) | 0.98 | 0.93 | 0.93 | 70% / 70% | - | - | - | - | - |
| qwen3-8b | humaneval | mentored_dec | False | 0.75 (0.75) | 1.08 | 0.99 | 1.02 | 85% / 83% | 1.05 | 0.96 | 0.97 | 79% / 84% | no |
| qwen3-8b | humaneval | spec_casc_tok | False | 0.8 (0.8) | 1.08 | 1.04 | 1.05 | 85% / 83% | 1.03 | 1.00 | 1.01 | 83% / 84% | no |
| qwen3-8b | livecodebench | mentored_dec | False | 0.15 (0.15) | 1.02 | 0.99 | 0.99 | 73% / 70% | - | - | - | - | - |
| qwen3-8b | livecodebench | spec_casc_tok | False | 0.8 (0.8) | 1.00 | 0.94 | 0.96 | 71% / 70% | - | - | - | - | - |
| qwen3-8b | mtbench | mentored_dec | False | 0.75 (0.75) | 1.04 | 0.89 | 0.93 | - / - | 1.04 | 0.88 | 0.86 | - / - | yes |
| qwen3-8b | mtbench | spec_casc_tok | False | 0.8 (0.8) | 1.04 | 0.96 | 0.99 | - / - | 1.02 | 0.96 | 0.96 | - / - | yes |
| qwen3-8b | longbench_v2 | mentored_dec | False | 0.75 (0.75) | 1.06 | 0.98 | 0.99 | 51% / 53% | - | - | - | - | - |
| qwen3-8b | longbench_v2 | spec_casc_tok | False | 0.15 (0.15) | 1.05 | 1.03 | 1.03 | 51% / 53% | - | - | - | - | - |

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
| qwen3-8b | strict | strict | 70% | - | - | - | - | 70.0% [53.3%, 86.7%] | - | 0 |
| qwen3-8b | mentored_dec | 0.75 | 73% | - | - | - | - | 73.3% [56.7%, 86.7%] | - | 0 |
| qwen3-8b | cactus | 0.35 | 23% | - | - | - | - | 23.3% [10.0%, 40.0%] | - | 0 |
| qwen3-8b | spec_casc_opt | 0.05 | 30% | - | - | - | - | 30.0% [13.3%, 46.7%] | - | 0 |
| qwen3-8b | r_fuzzy | 0.25 | 40% | - | - | - | - | 40.0% [23.3%, 56.7%] | - | 0 |
| qwen3-8b | spec_casc_tok | 0.8 | 70% | - | - | - | - | 70.0% [53.3%, 86.7%] | - | 0 |

## Step 7: SPEED-Bench qualitative split (seed 0, Nibi)

**Token-budget pilot, gpt-oss-20b** (`campaign/addendum/tables/speedbench_pilot__gpt-oss-20b.csv`; strict at 8192 on each category's first 20 cases, >10% cap-outs would raise the category to 16384): reasoning 0/20 cap-outs of 20 (mean 820, max 3269 tokens) -> budget 8192; math 0/4 cap-outs of 20 (mean 357, max 636 tokens) -> budget pending.

### gpt-oss-20b

Source: `campaign/addendum/tables/speedbench__gpt-oss-20b.csv`, one row per (method, category); Eq. 4 per (method, category): `campaign/addendum/tables/speedbench_eq4__gpt-oss-20b.csv`; per-method counts: `campaign/addendum/tables/speedbench_eq4_summary__gpt-oss-20b.csv`. Cell = lambda (completion tokens relaxed / strict) · R = verifier rounds ratio · T = wall-time ratio, all vs strict on the same cases; ↓/↑ = the 95% paired bootstrap interval lies entirely below/above 1. Strict column: mean completion tokens and cap-out rate.

| category | strict tokens (cap-out) | mentored_dec (0.75) | cactus (0.35) | spec_casc_opt (0.05) | r_fuzzy (0.25) | spec_casc_tok (0.8) |
|---|---:|---|---|---|---|---|
| all | 1266 (1%) | λ 1.15↑ · R 0.76↓ · T 0.75↓ (n=672) | λ 1.26↑ · R 0.63↓ · T 0.62↓ (n=672) | λ 1.23↑ · R 0.82↓ · T 0.82↓ (n=672) | λ 1.20↑ · R 0.77↓ · T 0.75↓ (n=672) | λ 1.09↑ · R 0.95↓ · T 0.92↓ (n=672) |
| coding | 1686 (5%) | λ 1.17↑ · R 0.85↓ · T 0.84↓ (n=80) | λ 1.52↑ · R 0.87 · T 0.86 (n=80) | λ 1.41↑ · R 1.01 · T 1.01 (n=80) | λ 1.28↑ · R 0.89 · T 0.88 (n=80) | λ 1.05 · R 0.92 · T 0.90 (n=80) |
| math | 370 (0%) | λ 1.11 · R 0.88 · T 0.88 (n=18) | λ 1.15 · R 0.84 · T 0.83 (n=18) | λ 1.30↑ · R 1.02 · T 1.03 (n=18) | λ 1.71↑ · R 1.28↑ · T 1.26 (n=18) | λ 1.00 · R 0.87↓ · T 0.86↓ (n=18) |
| humanities | 2324 (0%) | λ 0.93 · R 0.59↓ · T 0.58↓ (n=8) | λ 1.11 · R 0.48↓ · T 0.47↓ (n=8) | λ 1.16 · R 0.75↓ · T 0.75↓ (n=8) | λ 0.83 · R 0.49↓ · T 0.49↓ (n=8) | λ 0.96 · R 0.86 · T 0.84 (n=8) |
| stem | 1596 (0%) | λ 1.22↑ · R 0.83 · T 0.83↓ (n=6) | λ 1.35↑ · R 0.63↓ · T 0.62↓ (n=6) | λ 1.35↑ · R 0.93 · T 0.93 (n=6) | λ 1.28↑ · R 0.84 · T 0.83 (n=6) | λ 1.08 · R 0.99 · T 0.97 (n=6) |
| writing | 3042 (0%) | λ 0.94 · R 0.56↓ · T 0.55↓ (n=80) | λ 0.85↓ · R 0.36↓ · T 0.36↓ (n=80) | λ 1.01 · R 0.60↓ · T 0.60↓ (n=80) | λ 0.89↓ · R 0.55↓ · T 0.54↓ (n=80) | λ 1.02 · R 0.89↓ · T 0.86↓ (n=80) |
| summarization | 334 (0%) | λ 1.10 · R 0.86↓ · T 0.82↓ (n=80) | λ 1.38↑ · R 0.71↓ · T 0.67↓ (n=80) | λ 1.10 · R 0.85↓ · T 0.81↓ (n=80) | λ 1.15↑ · R 0.90↓ · T 0.84↓ (n=80) | λ 1.00 · R 0.91↓ · T 0.85↓ (n=80) |
| roleplay | 656 (0%) | λ 1.20↑ · R 0.68↓ · T 0.66↓ (n=80) | λ 1.28↑ · R 0.53↓ · T 0.52↓ (n=80) | λ 1.18↑ · R 0.74↓ · T 0.73↓ (n=80) | λ 1.19↑ · R 0.62↓ · T 0.60↓ (n=80) | λ 1.25↑ · R 1.10 · T 1.04 (n=80) |
| rag | 837 (0%) | λ 1.16 · R 0.78↓ · T 0.76↓ (n=80) | λ 1.37↑ · R 0.71↓ · T 0.68↓ (n=80) | λ 1.03 · R 0.72↓ · T 0.71↓ (n=80) | λ 1.15 · R 0.74↓ · T 0.71↓ (n=80) | λ 1.06 · R 0.88 · T 0.84↓ (n=80) |
| multilingual | 968 (1%) | λ 1.43↑ · R 1.07 · T 1.07 (n=80) | λ 1.72↑ · R 0.96 · T 0.95 (n=80) | λ 1.87↑ · R 1.31↑ · T 1.32↑ (n=80) | λ 1.86↑ · R 1.32↑ · T 1.30↑ (n=80) | λ 1.03 · R 0.96 · T 0.94 (n=80) |
| reasoning | 1104 (0%) | λ 1.21↑ · R 0.83↓ · T 0.83↓ (n=80) | λ 1.48↑ · R 0.80↓ · T 0.79↓ (n=80) | λ 1.37↑ · R 0.97 · T 0.98 (n=80) | λ 1.37↑ · R 0.89 · T 0.88 (n=80) | λ 1.05 · R 0.92 · T 0.90 (n=80) |
| qa | 1575 (0%) | λ 1.34↑ · R 0.82↓ · T 0.82↓ (n=80) | λ 1.27↑ · R 0.61↓ · T 0.60↓ (n=80) | λ 1.15 · R 0.75↓ · T 0.76↓ (n=80) | λ 1.25↑ · R 0.70↓ · T 0.69↓ (n=80) | λ 1.32↑ · R 1.08 · T 1.07 (n=80) |

- **spec_casc_opt** (alpha 0.05, `campaign/addendum/tables/speedbench_eq4_summary__gpt-oss-20b.csv` row `spec_casc_opt`): fewer verifier rounds in 8/11 categories (humanities, stem, writing, summarization, roleplay, rag, reasoning, qa); less wall time in 8/11 (humanities, stem, writing, summarization, roleplay, rag, reasoning, qa); Eq. 4 predicts a win in 8/11; completions longer by lambda 1.01 (writing) to 1.87 (multilingual); rounds and time disagree in: none.
- **mentored_dec** (alpha 0.75, `campaign/addendum/tables/speedbench_eq4_summary__gpt-oss-20b.csv` row `mentored_dec`): fewer verifier rounds in 10/11 categories (coding, math, humanities, stem, writing, summarization, roleplay, rag, reasoning, qa); less wall time in 10/11 (coding, math, humanities, stem, writing, summarization, roleplay, rag, reasoning, qa); Eq. 4 predicts a win in 10/11; completions longer by lambda 0.93 (humanities) to 1.43 (multilingual); rounds and time disagree in: none.
- **cactus** (alpha 0.35, `campaign/addendum/tables/speedbench_eq4_summary__gpt-oss-20b.csv` row `cactus`): fewer verifier rounds in 11/11 categories (coding, math, humanities, stem, writing, summarization, roleplay, rag, multilingual, reasoning, qa); less wall time in 11/11 (coding, math, humanities, stem, writing, summarization, roleplay, rag, multilingual, reasoning, qa); Eq. 4 predicts a win in 10/11; completions longer by lambda 0.85 (writing) to 1.72 (multilingual); rounds and time disagree in: none.
- **r_fuzzy** (alpha 0.25, `campaign/addendum/tables/speedbench_eq4_summary__gpt-oss-20b.csv` row `r_fuzzy`): fewer verifier rounds in 9/11 categories (coding, humanities, stem, writing, summarization, roleplay, rag, reasoning, qa); less wall time in 9/11 (coding, humanities, stem, writing, summarization, roleplay, rag, reasoning, qa); Eq. 4 predicts a win in 9/11; completions longer by lambda 0.83 (humanities) to 1.86 (multilingual); rounds and time disagree in: none.
- **spec_casc_tok** (alpha 0.8, `campaign/addendum/tables/speedbench_eq4_summary__gpt-oss-20b.csv` row `spec_casc_tok`): fewer verifier rounds in 9/11 categories (coding, math, humanities, stem, writing, summarization, rag, multilingual, reasoning); less wall time in 9/11 (coding, math, humanities, stem, writing, summarization, rag, multilingual, reasoning); Eq. 4 predicts a win in 9/11; completions longer by lambda 0.96 (humanities) to 1.32 (qa); rounds and time disagree in: none.

**Token-budget pilot, qwen3-8b** (`campaign/addendum/tables/speedbench_pilot__qwen3-8b.csv`; strict at 8192 on each category's first 20 cases, >10% cap-outs would raise the category to 16384): reasoning 2/20 cap-outs of 20 (mean 2352, max 8192 tokens) -> budget 8192; math 0/4 cap-outs of 20 (mean 2448, max 2946 tokens) -> budget pending.

### qwen3-8b

Source: `campaign/addendum/tables/speedbench__qwen3-8b.csv`, one row per (method, category); Eq. 4 per (method, category): `campaign/addendum/tables/speedbench_eq4__qwen3-8b.csv`; per-method counts: `campaign/addendum/tables/speedbench_eq4_summary__qwen3-8b.csv`. Cell = lambda (completion tokens relaxed / strict) · R = verifier rounds ratio · T = wall-time ratio, all vs strict on the same cases; ↓/↑ = the 95% paired bootstrap interval lies entirely below/above 1. Strict column: mean completion tokens and cap-out rate.

| category | strict tokens (cap-out) | mentored_dec (0.75) | cactus (0.35) | spec_casc_opt (0.05) | r_fuzzy (0.25) | spec_casc_tok (0.8) |
|---|---:|---|---|---|---|---|
| all | 2048 (5%) | λ 1.12 · R 0.97 · T 0.97 (n=40) | λ 1.74↑ · R 0.88 · T 0.88 (n=40) | λ 1.66↑ · R 1.17↑ · T 1.18↑ (n=40) | λ 1.47↑ · R 1.14 · T 1.15 (n=40) | λ 0.99 · R 0.93 · T 0.93 (n=40) |
| coding | 4060 (20%) | λ 1.18 · R 1.02 · T 1.03 (n=5) | λ 1.48↑ · R 0.83 · T 0.83 (n=5) | λ 1.56↑ · R 1.23 · T 1.23 (n=5) | λ 1.66↑ · R 1.37 · T 1.38 (n=5) | λ 1.04 · R 0.98 · T 0.98 (n=5) |
| humanities | 2864 (0%) | λ 0.89 · R 0.77 · T 0.77 (n=1) | λ 1.00 · R 0.47 · T 0.48 (n=1) | λ 2.78 · R 1.61 · T 1.63 (n=1) | λ 0.81 · R 0.66 · T 0.66 (n=1) | λ 1.08 · R 1.07 · T 1.07 (n=1) |
| writing | 2449 (0%) | λ 1.13 · R 0.95 · T 0.94 (n=5) | λ 2.27↑ · R 0.96 · T 0.97 (n=5) | λ 1.87↑ · R 1.10 · T 1.11 (n=5) | λ 1.08 · R 0.80↓ · T 0.80↓ (n=5) | λ 0.87 · R 0.83 · T 0.83 (n=5) |
| summarization | 648 (0%) | λ 1.10 · R 0.97 · T 0.97 (n=5) | λ 1.21 · R 0.71↓ · T 0.72↓ (n=5) | λ 0.89 · R 0.76↓ · T 0.77↓ (n=5) | λ 0.91 · R 0.75 · T 0.75 (n=5) | λ 0.90 · R 0.84 · T 0.84 (n=5) |
| roleplay | 897 (0%) | λ 1.70 · R 1.46 · T 1.47 (n=4) | λ 3.32 · R 1.37 · T 1.39 (n=4) | λ 1.74 · R 1.31 · T 1.32 (n=4) | λ 1.78 · R 1.44 · T 1.44 (n=4) | λ 1.08 · R 1.03 · T 1.03 (n=4) |
| rag | 908 (0%) | λ 1.18 · R 0.99 · T 0.99 (n=5) | λ 1.02 · R 0.59↓ · T 0.60↓ (n=5) | λ 0.92 · R 0.77 · T 0.77 (n=5) | λ 1.02 · R 0.77 · T 0.78 (n=5) | λ 1.10 · R 1.00 · T 1.00 (n=5) |
| multilingual | 3053 (0%) | λ 1.26↑ · R 1.11 · T 1.11 (n=5) | λ 1.77↑ · R 0.92 · T 0.93 (n=5) | λ 1.96↑ · R 1.38↑ · T 1.40↑ (n=5) | λ 1.69↑ · R 1.31↑ · T 1.33↑ (n=5) | λ 1.09 · R 1.04 · T 1.04 (n=5) |
| reasoning | 2873 (20%) | λ 0.81 · R 0.68 · T 0.67 (n=5) | λ 1.41 · R 0.74 · T 0.75 (n=5) | λ 1.50↑ · R 1.04 · T 1.04 (n=5) | λ 1.51↑ · R 1.14 · T 1.15 (n=5) | λ 0.87 · R 0.78 · T 0.78 (n=5) |
| qa | 1100 (0%) | λ 1.07 · R 0.88 · T 0.88 (n=5) | λ 2.61↑ · R 1.26 · T 1.28 (n=5) | λ 1.56 · R 1.10 · T 1.10 (n=5) | λ 1.76 · R 1.18 · T 1.19 (n=5) | λ 0.95 · R 0.91 · T 0.91 (n=5) |

- **spec_casc_opt** (alpha 0.05, `campaign/addendum/tables/speedbench_eq4_summary__qwen3-8b.csv` row `spec_casc_opt`): fewer verifier rounds in 2/9 categories (summarization, rag); less wall time in 2/9 (summarization, rag); Eq. 4 predicts a win in 2/9; completions longer by lambda 0.89 (summarization) to 2.78 (humanities); rounds and time disagree in: none.
- **mentored_dec** (alpha 0.75, `campaign/addendum/tables/speedbench_eq4_summary__qwen3-8b.csv` row `mentored_dec`): fewer verifier rounds in 6/9 categories (humanities, writing, summarization, rag, reasoning, qa); less wall time in 6/9 (humanities, writing, summarization, rag, reasoning, qa); Eq. 4 predicts a win in 5/9; completions longer by lambda 0.81 (reasoning) to 1.70 (roleplay); rounds and time disagree in: none.
- **cactus** (alpha 0.35, `campaign/addendum/tables/speedbench_eq4_summary__qwen3-8b.csv` row `cactus`): fewer verifier rounds in 7/9 categories (coding, humanities, writing, summarization, rag, multilingual, reasoning); less wall time in 7/9 (coding, humanities, writing, summarization, rag, multilingual, reasoning); Eq. 4 predicts a win in 6/9; completions longer by lambda 1.00 (humanities) to 3.32 (roleplay); rounds and time disagree in: none.
- **r_fuzzy** (alpha 0.25, `campaign/addendum/tables/speedbench_eq4_summary__qwen3-8b.csv` row `r_fuzzy`): fewer verifier rounds in 4/9 categories (humanities, writing, summarization, rag); less wall time in 4/9 (humanities, writing, summarization, rag); Eq. 4 predicts a win in 4/9; completions longer by lambda 0.81 (humanities) to 1.78 (roleplay); rounds and time disagree in: none.
- **spec_casc_tok** (alpha 0.8, `campaign/addendum/tables/speedbench_eq4_summary__qwen3-8b.csv` row `spec_casc_tok`): fewer verifier rounds in 6/9 categories (coding, writing, summarization, rag, reasoning, qa); less wall time in 6/9 (coding, writing, summarization, rag, reasoning, qa); Eq. 4 predicts a win in 6/9; completions longer by lambda 0.87 (reasoning) to 1.10 (rag); rounds and time disagree in: none.

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

