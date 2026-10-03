# NAACL-2027 addendum: results

Generated 2026-10-02 23:13 UTC by `scripts/addendum_results.py` from the CSVs it names; hand-written observations are in the last section (from `RESULTS_notes.md`). Settings and deviations: `campaign/addendum/README.md`.

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

`campaign/addendum/tables/lmdraft__livecodebench_qwen3.csv`:

| condition | dataset | method | alpha | n_pairs | l_bar | l_bar_strict | mean_tokens | mean_tokens_strict | lambda | rounds_ratio | time_ratio | accuracy | accuracy_strict | capout_rate | capout_rate_strict | time_per_round_ratio | nodes | nodes_strict | same_node_pairs | same_node | lambda_ci_lo | lambda_ci_hi | rounds_ratio_ci_lo | rounds_ratio_ci_hi | time_ratio_ci_lo | time_ratio_ci_hi | time_ratio_same_node |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lmdraft | livecodebench_qwen3 | mentored_dec | 0.750 | 90.000 | 3.899 | 3.014 | 7435.800 | 8076.410 | 0.921 | 0.735 | 0.713 | 0.722 | 0.722 | 0.267 | 0.289 | 0.970 | kn176 | kn169 | 0.000 | False | 0.883 | 0.959 | 0.709 | 0.764 | 0.687 | 0.741 | - |
| lmdraft | livecodebench_qwen3 | cactus | 0.350 | 90.000 | 4.312 | 3.014 | 7649.500 | 8076.410 | 0.947 | 0.695 | 0.683 | 0.756 | 0.722 | 0.244 | 0.289 | 0.983 | kn169 | kn169 | 90.000 | True | 0.908 | 0.988 | 0.668 | 0.725 | 0.656 | 0.713 | 0.683 |
| lmdraft | livecodebench_qwen3 | spec_casc_tok | 0.800 | 90.000 | 3.275 | 3.014 | 7551.780 | 8076.410 | 0.935 | 0.871 | 0.853 | 0.789 | 0.722 | 0.211 | 0.289 | 0.980 | kn176 | kn169 | 0.000 | False | 0.896 | 0.975 | 0.835 | 0.907 | 0.818 | 0.889 | - |

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

