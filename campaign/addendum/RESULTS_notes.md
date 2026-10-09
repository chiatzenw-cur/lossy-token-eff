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
