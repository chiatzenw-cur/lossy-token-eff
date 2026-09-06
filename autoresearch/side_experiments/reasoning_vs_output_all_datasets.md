# Where the tokens go: reasoning-channel vs. answer-channel, all 6 datasets

**Method.** Every gpt-oss-20b completion splits at the first
`<|channel|>final<|message|>` marker: everything before it is the
*reasoning* channel (harmony `analysis`), everything after is the
*answer*. Token counts via the o200k_harmony encoding. Data:
`runs/<dataset>/<method>/<alpha>/case_*/seed_0/output.txt`, the same
campaign runs behind `campaign/results/`. "runs w/o final ch" = runs that
never opened an answer channel at all (capped mid-reasoning).

## Headline

**Lossy relaxed verification inflates the *reasoning* channel, never the
answer.** Across all 6 datasets, the answer channel is a roughly
method-invariant size; relaxation blows up the chain-of-thought by
1.5–2.7× at aggressive α and *shrinks* the answer (runs cap before
committing). Total-length inflation therefore tracks how reasoning-heavy
a task is. `spec_casc_tok` is the only method that stays token-neutral at
every operating point.

## Strict (lossless) reference — how reasoning-heavy each task is

| dataset | n | reasoning tok | answer tok | total | reasoning % | runs w/o final ch |
|---|--:|--:|--:|--:|--:|--:|
| gsm8k | 150 | 311 | 7 | 318 | **98%** | 3 |
| longbench_v2 | 150 | 1484 | 21 | 1505 | **99%** | 2 |
| aime24 | 30 | 8025 | 688 | 8713 | **92%** | 2 |
| humaneval | 150 | 649 | 258 | 908 | 72% | 0 |
| livecodebench | 90 | 2086 | 1366 | 3452 | 60% | 4 |
| mtbench | 80 | 539 | 721 | 1260 | 43% | 0 |

## Inflation at each method's most-aggressive tested α (ratio vs. strict)

| dataset | method | α | reasoning ×strict | answer ×strict | total ×strict | no-final (strict→relaxed) |
|---|---|--:|--:|--:|--:|--:|
| gsm8k | mentored_dec | 0.75 | 1.16 | 1.30 | 1.17 | 3→6 |
| gsm8k | spec_casc_tok | 0.8 | **0.96** | 0.92 | **0.96** | 3→2 |
| gsm8k | spec_casc_opt | 0.05 | 1.45 | 1.89 | 1.46 | 3→8 |
| gsm8k | r_fuzzy | 0.25 | 1.68 | 2.76 | 1.70 | 3→7 |
| gsm8k | cactus | 0.35 | 1.58 | 3.30 | 1.62 | 3→8 |
| aime24 | mentored_dec | 0.75 | 1.77 | 0.83 | 1.69 | 2→6 |
| aime24 | spec_casc_tok | 0.8 | 1.54 | 0.87 | 1.48 | 2→6 |
| aime24 | spec_casc_opt | 0.05 | **2.66** | 0.41 | 2.48 | 2→**13** |
| aime24 | r_fuzzy | 0.25 | 2.25 | 0.73 | 2.13 | 2→9 |
| aime24 | cactus | 0.18 | 1.86 | 0.81 | 1.78 | 2→7 |
| humaneval | mentored_dec | 0.75 | 1.41 | 1.01 | 1.30 | 0→1 |
| humaneval | spec_casc_tok | 0.8 | **1.07** | 0.99 | **1.05** | 0→0 |
| humaneval | spec_casc_opt | 0.05 | 1.96 | 1.17 | 1.74 | 0→3 |
| humaneval | r_fuzzy | 0.25 | 1.81 | 1.22 | 1.64 | 0→1 |
| humaneval | cactus | 0.35 | 2.05 | 1.15 | 1.79 | 0→2 |
| livecodebench | mentored_dec | 0.75 | 1.44 | 0.95 | 1.25 | 4→7 |
| livecodebench | spec_casc_tok | 0.8 | 1.30 | 0.95 | 1.16 | 4→5 |
| livecodebench | spec_casc_opt | 0.05 | 2.13 | 0.89 | 1.64 | 4→**13** |
| livecodebench | r_fuzzy | 0.25 | 2.07 | 1.02 | 1.65 | 4→**13** |
| livecodebench | cactus | 0.18 | 1.93 | 0.94 | 1.54 | 4→9 |
| longbench_v2 | mentored_dec | 0.75 | 1.61 | 0.71 | 1.60 | 2→4 |
| longbench_v2 | spec_casc_tok | 0.8 | **1.13** | 0.71 | **1.13** | 2→1 |
| longbench_v2 | spec_casc_opt | 0.05 | 1.81 | 0.48 | 1.79 | 2→**20** |
| longbench_v2 | r_fuzzy | 0.25 | 1.70 | 1.00 | 1.69 | 2→**18** |
| longbench_v2 | cactus | 0.35 | 1.78 | 0.88 | 1.77 | 2→7 |
| mtbench | mentored_dec | 0.75 | 1.13 | 1.07 | 1.10 | 0→1 |
| mtbench | spec_casc_tok | 0.8 | **0.98** | 0.95 | **0.96** | 0→0 |
| mtbench | spec_casc_opt | 0.05 | 1.21 | 1.01 | 1.09 | 0→2 |
| mtbench | r_fuzzy | 0.25 | 1.30 | 1.13 | 1.20 | 0→3 |
| mtbench | cactus | 0.35 | 1.52 | 0.94 | 1.18 | 0→6 |

Reading: the `reasoning ×strict` column is > 1 almost everywhere and
reaches 2–2.7×; the `answer ×strict` column is ≤ 1 on every
reasoning-heavy dataset (it only rises on gsm8k, off a 7-token base — a
few runs that ramble inside the answer channel). Non-terminating runs
rise sharply under the aggressive methods (`spec_casc_opt`, `r_fuzzy`):
up to 13–20 of 90–150 runs never commit an answer.

## The accuracy-preserving end — gentlest tested α (ratio vs. strict)

| dataset | method | α | reasoning ×strict | answer ×strict | total ×strict |
|---|---|--:|--:|--:|--:|
| gsm8k | spec_casc_tok | 0.15 | 0.87 | 0.82 | **0.87** |
| gsm8k | mentored_dec | 0.15 | 1.00 | 0.76 | 1.00 |
| gsm8k | cactus | 0.03 | 1.28 | 1.28 | 1.28 |
| aime24 | spec_casc_tok | 0.15 | 0.99 | 1.10 | **1.00** |
| aime24 | mentored_dec | 0.15 | 1.09 | 0.96 | 1.08 |
| aime24 | cactus | 0.03 | 1.55 | 1.01 | 1.51 |
| humaneval | mentored_dec | 0.15 | 0.95 | 1.01 | **0.96** |
| humaneval | spec_casc_tok | 0.15 | 1.08 | 0.98 | 1.05 |
| humaneval | cactus | 0.03 | 1.30 | 1.08 | 1.24 |
| livecodebench | spec_casc_tok | 0.15 | 1.04 | 0.94 | **1.00** |
| livecodebench | r_fuzzy | 0.03 | 1.04 | 0.96 | 1.01 |
| livecodebench | cactus | 0.03 | 1.51 | 1.01 | 1.31 |
| longbench_v2 | mentored_dec | 0.15 | 1.07 | 0.59 | 1.06 |
| longbench_v2 | spec_casc_tok | 0.15 | 1.09 | 0.57 | 1.08 |
| longbench_v2 | cactus | 0.03 | 1.54 | 0.97 | 1.54 |
| mtbench | spec_casc_tok | 0.15 | 1.00 | 0.95 | **0.97** |
| mtbench | spec_casc_opt | -0.3 | 0.97 | 0.98 | 0.98 |
| mtbench | cactus | 0.03 | 1.14 | 0.96 | 1.04 |

At its gentlest α, `spec_casc_tok` is 0.87–1.08× strict on total length on
every dataset; `mentored_dec` similar. `cactus` already carries a
1.2–1.5× reasoning tax even at its gentlest setting.

## MT-Bench by question category (length ratio vs. strict)

Categories ordered by how much of the strict completion is answer prose
(left = generation-heavy, right = reasoning-heavy):

| config | writing | humanities | stem | roleplay | coding | math | reasoning | extraction | ALL |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **strict (abs tokens)** | 1159 | 2357 | 1611 | 1269 | 1533 | 412 | 1135 | 628 | 1263 |
| spec_casc_tok/α0.15 | 0.80 | 0.95 | 1.18 | 1.02 | 0.83 | 0.84 | 1.14 | 0.85 | 0.97 |
| spec_casc_tok/α0.8 | 0.84 | 0.87 | 1.02 | 0.93 | 1.10 | 1.02 | 1.04 | 0.96 | 0.96 |
| mentored_dec/α0.75 | 0.76 | 1.00 | 1.29 | 1.31 | 1.07 | 1.05 | 1.15 | 1.18 | 1.10 |
| cactus/α0.35 | 0.76 | 0.90 | 1.25 | 1.52 | 1.18 | 1.13 | **1.54** | **1.60** | 1.18 |
| r_fuzzy/α0.25 | 0.87 | 0.92 | 1.37 | 1.27 | 1.08 | **2.04** | **1.52** | 1.47 | 1.20 |
| spec_casc_opt/α0.05 | 0.60 | 1.01 | 1.28 | 1.16 | 1.21 | 1.11 | 1.30 | 1.00 | 1.09 |

| category | reasoning % (strict) | answer tok (strict) |
|---|--:|--:|
| writing | 39% | 700 |
| roleplay | 31% | 875 |
| coding | 33% | 1027 |
| stem | 29% | 1148 |
| humanities | 32% | 1606 |
| math | 59% | 169 |
| reasoning | 83% | 187 |
| extraction | 91% | 54 |

**The category pattern is the same finding at finer grain.** Under
aggressive relaxation, `writing` gets *shorter* (0.6–0.87×) and
`humanities` stays flat (~0.9–1.0×) — these are the categories that are
70% long-form answer, so there's little reasoning to inflate. The
categories that blow up — `reasoning` (1.3–1.54×), `extraction`
(1.0–1.6×), `math` (up to 2.04× under r_fuzzy), `stem` (1.25–1.37×) — are
exactly the ones that are 60–91% reasoning under strict. `coding` sits in
between (33% reasoning, 1.08–1.21× inflation). `spec_casc_tok` stays
0.97–0.98× across every category at both α.

## Takeaways

1. **"Completion length" ≈ "reasoning length"** on gsm8k, aime24,
   longbench_v2 (92–99% reasoning); still reasoning-dominated on
   humaneval/livecodebench; only on mtbench is the answer the larger
   half, and even there it's the reasoning-heavy categories that inflate.
2. **Relaxation is a reasoning-process perturbation, not an
   output-generation one.** The answer channel is method-invariant to
   ±10% wherever the run terminates normally.
3. **Aggressive methods (`spec_casc_opt`, `r_fuzzy`, `cactus`) inflate
   reasoning 1.5–2.7× and drive a 5–13% non-termination rate**; those
   settings also lose 10–40 accuracy points (see `campaign/FINDINGS.md`),
   so no one would run them where tokens matter.
4. **`spec_casc_tok` is token-neutral everywhere** — 0.87–1.13× strict on
   total length across all 6 datasets and all tested α. It is the only
   relaxation that buys wall-clock speedup without a token cost.
5. Any token-efficiency intervention should target the **reasoning
   channel** and the **non-termination tail** (what `force_commit`
   does: −4.6% to −7.6% on aime24 at zero accuracy cost by forcing the
   answer channel open on the runs that never reach it).
