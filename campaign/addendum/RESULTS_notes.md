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
