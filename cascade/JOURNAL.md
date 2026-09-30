# cascade/ journal

Newest entry last. Dates are UTC-ish calendar days.

## 2026-09-11 — workspace created

- **Context.** Results review with HaoChen and Chiatzen concluded no
  training-free lossy method is a free lunch; `spec_casc_tok` is the one
  that never inflates length. Bill's assignments: explore cascades
  further, try modifications, and check what speed is achievable if
  accuracy is ignored but garbage output is excluded. HaoChen to ask Prof.
  Zhang for a single H100 for Bill.
- **Compute.** Alliance (CCDB) account approved, RAPs
  `def-hongyanz` (default allocation, Nibi etc.) and `aip-hongyanz` (PAICE,
  AI clusters). SSH key + Duo verified end-to-end against
  `nibi.alliancecan.ca`; login still closes right after "Success. Logging
  you in..." — Nibi shows healthy, so this reads as account provisioning
  lag. See `cluster/README.md`.
- **Analysis (no GPU).** `analysis/speed_ignoring_accuracy.py` over
  `campaign/tables/*.csv`. Headline: best *clean* end-to-end speedup
  (rounds) on graded GPT-OSS datasets is 1.04x-1.21x; `spec_casc_tok` is
  that point on gsm8k (1.21x, a=0.8), aime24 (1.09x, a=0.15) and
  livecodebench (1.04x, a=0.15), each with accuracy >= strict.
  `spec_casc_opt` at a=0.05 is a net *slowdown* on every long-form dataset
  (0.59x on aime24). Qwen3 cascade points all within 0.94x-1.07x. Full
  tables in `results/speed_ignoring_accuracy.md`.
- **Mechanism hypothesis** written up in README.md section 2: inflation
  is driven by committing draft tokens outside the verifier's head; tok is
  the only rule that never does that more often than lossless.
- **Two variants implemented** as V1 patches (GPT-OSS only for now),
  derived offline from the pristine v0.26.0 sampler (hash matches the
  manifest's `upstream`): `spec_casc_tok_lt` (tok's head free pass, lossless
  tail) and `spec_casc_opt_ent` (opt with the entropy plug-in of Lemma 4).
  Wired into `lossy_methods.py`, `apply.sh`, `HASHES.txt`,
  `run_server_vllm.sh`, `campaign_run.py`; tests written; **neither has run
  on a GPU yet**. First thing to do on a GPU: `bash patches/apply.sh
  spec-casc-tok-lt` and watch the kernel test pass.
- **Found while wiring:** the consolidated V2 sampler (needed for Qwen3)
  exists only on the old box, and its cactus/tok ports are accept-test-only
  (DIRECTIONS.md D8).
- **Next:** once a GPU is available, D1 on gsm8k first (cheap, fast
  feedback), then D4 timing, then D1 on aime24. Meanwhile D2 if the
  `proposals.jsonl` traces can be pulled from the old box.

## 2026-09-11, later — runnable plan + trace result

- **E7 done (no GPU).** `old_runs/` holds 1,226 git-tracked
  `proposals.jsonl` traces (HumanEval 164 x 6 arms, AIME24 30 x 6 arms +
  tok at a=0.5/0.7/1.0). `analysis/trace_rank_analysis.py` ->
  `results/trace_rank_analysis.md`. `spec_casc_tok` has **zero**
  out-of-head lossy-only accepts at every alpha and never inflates; every
  inflating rule commits 16–155 such tokens per 1k, ordered like its
  inflation (cactus 155/1k 1.86x, r_fuzzy 141/1k 1.94x, opt 65/1k 2.13x,
  mentored 16/1k 1.23x); tok at a=1 (no head restriction) inflates 19x.
  Per-case rates do *not* predict which cases loop within an arm (r ~ 0
  on HumanEval, negative on AIME24). Rule-level exposure effect.
- **Three more variants built** the same way (offline from pristine,
  hashes in `HASHES.txt`, tests written, wired everywhere):
  `spec_casc_diff` (Eq. 5), `spec_casc_chow` (Eq. 2), `spec_casc_opt_head`
  (opt's trigger + tok's head restriction, second knob beta via
  `--spec-casc-opt-head-beta`, params dir `alpha<a>_beta<b>`). Still
  untested on a GPU, like the first two.
- **Runnable plan:** `EXPERIMENTS.md` (E0–E8 with commands, costs,
  predictions, decision rules), `run.sh` (all ids dry-run checked, box or
  Nibi target, fresh or persistent mode), `cluster/nibi_run.sbatch`
  (generic job wrapper), `analysis/timing_report.py` (E3/E4 read-out;
  smoke-tested on old_runs). Supplementary docs: `METHODS.md`,
  `METRICS.md`, `SETUP.md`.
- **Predictions on record** (EXPERIMENTS.md): E1 tok_lt no inflation, l̄
  up; E6 opt_head(beta=0.8) len ~1.0 with about half of opt's l̄ gain.
- Nibi login still closes after Duo success (3rd reproduction).
- **Cluster, evening.** Root cause of the all-day login failure: CCDB's
  per-system *Access Systems* page had every cluster at "Not responded";
  requesting access for Nibi + Killarney fixed it within the hour (Bill,
  in the browser). First login facts in `cluster/README.md`. Repo rsynced
  to project space; `setup_nibi.sh` built the environment (two fixes found
  live: the Alliance python module re-sets `PIP_CONFIG_FILE` after `module
  load`, which silently swapped in `torch-2.11.0+computecanada` — override
  moved after the load, `PYTHONPATH` unset; and `torchcodec` ships linked
  to CUDA 13 libs the cu129 env lacks, breaking the sampler import —
  uninstalled). **`spec-casc-tok-lt` passed all checks on an H100 in E0,
  including the Triton kernel test** — first hardware verification of any
  new variant. E0's loop then tripped over `apply.sh`'s refusal to switch
  patches; added `cluster/patch_cycle_test.sh` (reverse-then-apply) and
  resubmitted E0 (21759794) with `SAMPLE-gsm8k` (21759795) chained.
- **E0 passed on Nibi (job 21759794, 10 min): all five patches installed
  with matching hashes and passed plumbing + formula + Triton kernel tests
  on an H100.** The chained sample failed on the strict arm because the
  strict "trace carrier" (`mentored_dec`) has a self-test that asserts the
  V2 runner file is patched — only true on the old box (D8). Carrier
  switched to `spec_casc_opt` (`scripts/lossy_methods.py`), which is
  V1-only and strict at its −∞ neutral value.
- **First real run on the cluster — `SAMPLE-gsm8k`, job 21760344, one
  H100, 16.5 min:** `strict` case_001 → 156 tokens, 38 rounds, l̄ 3.16,
  stop; `spec_casc_tok_lt` α=0.55 → 236 tokens, 46 rounds, l̄ 4.13, stop.
  One case = anecdote, not evidence; the point is the pipeline runs. Fresh
  server start was 657 s cold (torch.compile + CUDA-graph capture, cache on
  node-local disk) and 334 s warm within the job; job scripts now put the
  vLLM/Triton/Inductor caches in `$SCRATCH` so later jobs reuse them.
- **E1-gsm8k quick look (job 21761299, 37 min, one H100, warm servers,
  30 cases, seed 0)** — `campaign/{results,tables,graphs}/gsm8k_quick.*`,
  scored in `cascade/results/speed_ignoring_accuracy.md` (dataset
  `gsm8k_quick`). Paired against strict (l̄ 2.64, 280 tokens, 79.8 rounds,
  acc 1.00):

  | arm | α | l̄ | len ratio | rounds speedup | acc |
  |---|---:|---:|---:|---:|---:|
  | tok | 0.15 / 0.35 / 0.55 / 0.8 | 2.65 / 2.64 / 2.92 / 3.19 | 0.93 / 0.82 / 0.86 / 0.93 | 1.09 / 1.22 / 1.24 / 1.22 | 0.97 / 1.00 / 0.97 / 1.00 |
  | **tok_lt** | 0.15 / 0.35 / 0.55 / 0.8 | **2.95 / 2.99 / 3.08 / 3.23** | 1.03 / 0.98 / 0.90 / 0.92 | 1.03 / 1.10 / 1.22 / 1.27 | 0.97 / 0.97 / 0.97 / 1.00 |

  Read-out: the acceptance half of the E1 prediction holds cleanly —
  tok_lt accepts more per round than tok at every alpha (+0.30, +0.35,
  +0.16, +0.03), most where tok's out-of-set penalty bites hardest (tight
  alpha) and vanishing at alpha 0.8 where almost everything is in-set.
  The length half is consistent with "no inflation" (0.90–1.03x, zero
  budget hits, accuracy 0.97–1.00) but underpowered: 30 short gsm8k
  answers cannot resolve the ±15% swings seen even between tok's own
  alphas, and gsm8k barely inflates under any rule. The decisive run is
  aime24 (E1-aime24; ~5 h either mode since generation dominates there).
- **E1-aime24 quick look submitted** (job 21765298, persistent mode, 12 h
  limit; 4 alphas × tok_lt, 4 × tok, strict; 30 AIME24 problems, 32k
  budget). Persistent, not fresh: on Nibi a fresh vLLM start is ~5 min, so
  fresh-per-measurement E1-aime24 would be ~200 starts ≈ a day; persistent
  is ~9 starts + ~270 generations ≈ 6 h. Outputs will land in
  `campaign/{results,tables,graphs}/aime24_quick.*` on Nibi; pull them to
  the Mac and rerun `speed_ignoring_accuracy.py`. Decision rule (E1):
  tok_lt len_ratio <= 1.05 with l̄ above tok's -> mechanism supported;
  len_ratio > 1.15 -> the eta penalty was load-bearing.
## 2026-09-12 — E1-aime24 quick look (job 21765298, 2 h 32 m, one H100)

Persistent mode, 30 AIME24 problems, 32k budget, seed 0. Files:
`campaign/{results,tables,graphs}/aime24_quick.*`; scored as dataset
`aime24_quick` in `cascade/results/speed_ignoring_accuracy.md`. Paired
against strict (l̄ 2.22, mean 8481 / median 7228 tokens, 2 of 30 hit the
budget, acc 0.80):

| arm | α | l̄ | mean len ratio | median len | loops /30 | rounds speedup | acc |
|---|---:|---:|---:|---:|---:|---:|---:|
| tok | 0.15 / 0.35 / 0.55 / 0.8 | 2.40 / 2.41 / 2.49 / 2.70 | 1.51 / 1.29 / 1.51 / 1.39 | 7466 / 6566 / 7424 / 6385 | 5 / 3 / 4 / 4 | 0.71 / 0.84 / 0.73 / 0.86 | 0.80 / 0.77 / 0.73 / 0.77 |
| **tok_lt** | 0.15 / 0.35 / 0.55 / 0.8 | 2.53 / 2.52 / 2.55 / 2.76 | **1.03** / 1.20 / 1.33 / 1.51 | 6331 / 6212 / 7658 / 9544 | **0** / 3 / 4 / 5 | **1.08** / 0.93 / 0.84 / 0.79 | **0.83** / 0.77 / 0.80 / 0.67 |

Read-out:
- **`tok_lt` α=0.15 is the best point in the run on every axis**: +14%
  acceptance over tok at the same α, mean length 1.03× strict, zero
  budget-exhausted runs (strict itself had 2), highest accuracy (0.83 vs
  0.80), 1.08× fewer verifier rounds. At matched l̄ ≈ 2.5 it beats tok
  (tok α=0.55: 1.51× length). This is the prediction, at the tightest
  setting.
- **Looser settings inflate — for both rules.** tok_lt's mean length
  climbs monotonically with α (1.03 → 1.20 → 1.33 → 1.51) and its loop
  count with it (0 → 3 → 4 → 5); at α=0.8 it is no better than tok. So
  the head restriction protects only while the head is *narrow*: α=0.15
  means a free pass only for tokens within 15% of the verifier's top
  choice; α=0.35 (within 35%) already admits tokens the verifier likes
  noticeably less, and on long reasoning that is enough to ramble.
  **Refinement of the E7 story:** "outside the head at 0.2×top-1" was too
  loose a definition of harmful; on AIME24 the safe zone is roughly
  α ≲ 0.15–0.2 (p(x) ≳ 0.8–0.85 × top-1).
- **Statistical caution.** Means are dominated by 2–5 looping runs of
  32k tokens; medians are within ±10% of strict for every arm except
  tok_lt 0.8; even excluding loops the relaxed arms are +8% to +44% longer
  than strict on typical problems (tok_lt 0.15: +8%, tok 0.15: +25%).
  Loop counts of 0–5 out of 30 are not separable statistically (tok 0.15's
  5 vs strict's 2 is p≈0.2), and plain tok at α=0.15 inflated here (1.51×)
  where the campaign's fresh-server run had 1.00× — warm-server confound,
  different hardware numerics, or just loop noise; cannot tell at n=30.
- Decision rule as written (support = tok_lt exceeds tok's max l̄ with
  len ≤ 1.05): **not met** — the clean point is at the low end. The
  *useful* result is narrower and still valuable: a lossless-tail head
  rule at α≈0.15 gives ~+0.3 accepted tokens/round over strict on AIME24
  with no inflation and no accuracy loss, i.e. the "free" ~1.1× the
  campaign found for tok, with a bit more acceptance.

Consequences for the plan: E6's head widths must be small (0.15/0.35, not
0.5/0.8); add E1F, a fine low-α sweep (0.05–0.25) with 3 seeds to map
exactly where inflation begins with enough power to see it.

- **E1F-aime24 submitted** (job 21804913, persistent, 12 h limit): tok_lt
  and tok at α ∈ {0.05, 0.1, 0.15, 0.2, 0.25} plus strict, seeds 0/1/2 →
  33 warm servers × 30 problems = 990 runs. At the quick look's ~17 min
  per arm, expect ~9–10 h. Outputs: `campaign/{results,tables,graphs}/
  aime24_fine.*`. Decision rule: with 90 runs per point, does tok_lt at
  0.15–0.20 keep length ≤ 1.05× strict and a loop rate ≤ strict's? If yes
  → a real, safe ~1.1× with a quotable head-width rule; if inflation
  appears by 0.10 → no safe zone on AIME24, the rule's value is confined
  to short tasks.

## 2026-09-13 — E1F-aime24: fine low-α sweep, 3 seeds (job 21804913, 8 h 13 m)

990 runs: tok_lt and tok at α ∈ {0.05, 0.1, 0.15, 0.2, 0.25} × 30 problems
× seeds 0/1/2, plus strict × 3 seeds. Paired per (problem, seed). Files
`campaign/*/aime24_fine.*`; `cascade/results/speed_ignoring_accuracy.md`
(dataset `aime24_fine`; the script now pairs by (case, seed)).

Strict: l̄ 2.20, mean 9703 / median 7182 tokens, 6 loops of 90 (2/1/3 by
seed), acc 0.733.

| arm | α | l̄ | mean len / strict | no-loop mean / strict | loops /90 (by seed) | rounds speedup | acc |
|---|---:|---:|---:|---:|---|---:|---:|
| tok | 0.05 / 0.1 / 0.15 / 0.2 / 0.25 | 2.32 / 2.35 / 2.38 / 2.38 / 2.41 | 1.10 / 1.00 / 1.26 / 1.23 / 1.02 | 1.06 / 0.93 / 1.17 / 1.15 / 0.93 | 8 / 9 / 11 / 9 / 10 | 0.96 / 1.05 / 0.84 / 0.87 / 1.05 | 0.73 / 0.77 / 0.77 / 0.77 / 0.77 |
| tok_lt | 0.05 / 0.1 / 0.15 / 0.2 / 0.25 | 2.45 / 2.44 / 2.48 / 2.49 / 2.50 | 1.03 / 1.08 / 1.01 / 1.04 / 1.07 | 0.99 / 1.10 / 0.98 / 0.97 / 0.98 | 9 / 8 / 6 (0/3/3) / 6 (0/2/4) / 11 | 1.06 / 1.01 / 1.08 / 1.06 / 1.01 | 0.70 / 0.70 / 0.73 / 0.70 / 0.63 |

Read-out (what survives 90 runs per point):
- **Acceptance gain is real and stable across seeds**: tok_lt +11–14%
  accepted tokens/round over strict at every setting; tok +5–10%. The
  lossless tail does what it was built to do.
- **Neither head-restricted rule produces the big inflation of the other
  rules** at α ≤ 0.25: worst mean ratio 1.26 (tok 0.15) vs opt's 2.13 /
  cactus 1.86 in the campaign; typical (non-looping) answers are within
  ±10% of strict for tok_lt at every setting; loop rates 7–12% vs strict's 7%.
- **The end-to-end prize on AIME24 is small: ~1.05–1.08× fewer verifier
  rounds** for tok_lt at α 0.15–0.2 (length 1.01–1.04×, loops = strict's
  6/90, accuracy = strict's 0.73). Consistent with the quick look's 1.08×,
  now with 3 seeds. On gsm8k the same rule gave ~1.2×.
- **The quick look's "cliff at α=0.35" was partly noise.** Loop counts of
  6–11/90 do not separate by α within 0.05–0.25, and the earlier 0.35+
  loop rates (3–5 of 30) are the same ~10–17% band as tok here at 0.15.
  What is monotone is nothing; what is flat is typical-answer length for
  tok_lt. The honest summary: within this range the rule is safe and the
  gain is modest; the E1-aime24 quick-look table above overstated both
  the sweet spot and the cliff.
- **tok_lt inflates less than tok at the same α** on the two settings
  where tok inflated (0.15, 0.2: tok's non-loop mean 1.15–1.17× vs
  tok_lt's 0.97–0.98×; 9–11 loops vs 6) even though tok_lt accepts
  *more* drafted tokens. The two rules differ off the head in exactly one
  more place besides the accept test: tok resamples rejections from its
  blended pi_rej (mass proportional to p on the whole head regardless of
  q), tok_lt from the lossless residual (p−q)+. Suggestive (tok's
  per-point numbers are non-monotone in α, so this is 2 points out of 5),
  but it is the first hint that *what replaces a rejected token* matters
  as much as the accept rule — worth a dedicated look before building on it.
- Accuracy: tok_lt 0.70–0.73 vs strict 0.73 (tok 0.73–0.77); tok_lt at
  0.25 drops to 0.63 (57 vs 66 correct of 90) — the loosest setting is
  where quality starts to go, consistent with the acceptance/loop trend.

Consequence: tok_lt α≈0.15–0.2 is a real but small win (~1.05–1.08× on hard
reasoning, ~1.2× on short math, accuracy intact). The bigger prize, if it
exists, is opt's much larger acceptance gain (+23–54% l̄ in the campaign)
with a narrow head — **E6-aime24 with β ∈ {0.15, 0.35}** is the next run.

- **E6-aime24 submitted** (job 21848564, persistent, seed 0): `spec_casc_opt_head`
  at β ∈ {0.15, 0.35} × α ∈ {−0.3, −0.1, −0.02, 0.05}, 30 problems, 8 warm
  servers (~2.5 h). Report → `campaign/*/aime24_e6.*` (opt_head arms keyed
  `spec_casc_opt_head_beta<b>`, plus tok_lt/tok fine points and strict for
  context). Compare against the campaign's opt (same alphas, fresh servers,
  seed 0): l̄ 2.71→3.38, length 1.33→2.48×, budget hits up to 43%. Decision
  rule: at β=0.15, does opt_head keep ≥ half of opt's l̄ gain over strict
  with length ≤ 1.1× and loops ≈ strict's? Yes → head restriction transfers
  to a looser trigger (the 1.2–1.3× prize); no → opt's damage is in its
  trigger, not only in out-of-head commits.
- **E6-aime24 done** (job 21848564, 1 h 56 m, seed 0, 30 problems, warm
  servers). Files `campaign/*/aime24_e6.*`. `spec_casc_opt_head` = opt's
  trigger AND the drafted token within β of the verifier's top choice.
  Strict seed 0: l̄ 2.22, 2 loops, acc 0.73.

  | β | α | l̄ (/strict) | mean len | median len | loops /30 | passes speedup | acc |
  |---:|---:|---:|---:|---:|---:|---:|---:|
  | 0.15 | −0.3 / −0.1 / −0.02 / 0.05 | 2.45–2.48 (1.10–1.12) | 1.09 / 1.13 / 1.30 / 1.19 | 0.80 / 0.67 / 0.91 / 1.00 | 1 / 3 / 2 / 1 | 1.01 / 0.95 / 0.84 / 0.91 | 0.73 / 0.73 / 0.83 / 0.80 |
  | 0.35 | −0.3 / −0.1 / −0.02 / 0.05 | 2.47–2.53 (1.11–1.14) | 1.03 / 1.26 / 1.12 / 1.27 | 0.95 / 0.93 / 0.85 / 0.72 | 1 / 5 / 2 / 5 | 1.07 / 0.86 / 1.00 / 0.87 | 0.80 / 0.63 / 0.80 / 0.67 |

  For comparison, plain opt (campaign, fresh servers, seed 0): α −0.3 → l̄
  2.71 (1.23×), len 1.33×, 3 loops, passes 0.89, acc 0.80; α 0.05 → l̄ 3.38
  (1.54×), len 2.48×, 13 loops, passes 0.59, acc 0.37.

  Read-out:
  - **The narrow head removes opt's rambling** — no 2.5× blow-ups, loops
    1–5/30 instead of 13, mean length ≤ 1.30× instead of 2.48×. Third
    confirmation of the mechanism (after E7 and E1F).
  - **It also removes opt's acceptance gain.** With the head in place, l̄
    is 2.45–2.53 whatever opt's α is — identical to tok_lt (2.44–2.50) —
    versus opt's 2.71–3.38. Once a free pass requires the drafted token to
    be near the verifier's top choice, the drafter-confidence trigger is
    almost always satisfied there anyway; the head width alone sets the
    acceptance. opt_head *is* tok_lt with a redundant extra condition.
  - **End-to-end: 0.84–1.07×, i.e. no better than tok_lt's 1.01–1.08×**,
    with noisier lengths (single seed; two arms have long non-looping
    tails, no-loop mean 1.27–1.28×). β=0.35 costs accuracy at two
    settings (0.63, 0.67), as tok_lt did at α=0.25.
  - **Conclusion: there is no bigger prize in this family.** The
    acceptance gain of a head-restricted rule is bounded by how often the
    drafter proposes a near-top token that lossless would have rejected
    (~10–14% with this drafter on AIME24); opening the head to get more
    brings the rambling back (opt, cactus, tok at α ≥ 0.35). One quantity
    — how far below the verifier's own top choice a committed token may
    sit — governs both the gain and the damage, and on long reasoning the
    safe zone is worth ≈1.05–1.1×. That, plus ~1.2× on short math, is the
    ceiling for training-free relaxation with this drafter, and the paper
    can say so with a mechanism attached.

  Stopping the GPU experiments here unless the group wants seeds on E6
  (would only tighten error bars on "no gain") or the residual-sampling
  hint from E1F pursued (a different question).
## 2026-09-14 — E1P: the AIME24 protocol on the other five benchmarks (staged)

Bill asked for the "proper" run (tok_lt and tok at α 0.15/0.20/0.25, 3
seeds, strict × 3) on gsm8k, humaneval, mtbench, livecodebench and
longbench_v2. Sized from the campaign's own per-answer wall times (mean:
gsm8k 2.2 s, humaneval 6.5 s, mtbench 8.8 s, livecodebench 25 s,
longbench_v2 73 s) with 21 warm servers per dataset: gsm8k 150 problems
≈ 4 h, humaneval 150 ≈ 7 h, mtbench 80 ≈ 6 h, livecodebench 90 ≈ 15 h,
longbench_v2 at 150 would be ≈ 66 h so it runs at 30 problems (AIME24's
90-runs-per-point power) ≈ 15 h. Added `E1P-<ds>` to `run.sh` (reports to
`campaign/*/<ds>_proper.*`) and `SBATCH_EXTRA` so the five jobs chain with
`--dependency=afterany` on one GPU (~47 h total sequential; ~15 h if run in
parallel on five GPUs). Dry-runs validated for all five.

- **Submitted 2026-09-14**, chained with `afterany` on one GPU: gsm8k
  21910960 → humaneval 21910961 → mtbench 21910962 → livecodebench 21910964
  → longbench_v2 21910965. Outputs `campaign/{results,tables,graphs}/<ds>_proper.*`
  on Nibi; job logs `casc-<jobid>.out` in the repo dir.
  **Re-wired the same day into two lanes (Bill's call, two GPUs):**
  GPU 1: gsm8k 21910960 → humaneval 21910961 → livecodebench 21910964
  (~26 h); GPU 2: mtbench 21910962 → longbench_v2 21910965 (~21 h). Done
  with `scontrol update jobid=… dependency=…`, no resubmission. Nibi has
  no per-user GPU cap under QOS `normal`; the constraint is fair-share
  (group score fell 0.49 → 0.32 after ~30 GPU-h this weekend).
- **2026-09-15: all five failed after 20–80 min — my mistake.** Every job
  shares `.venv-vllm`, and every arm switches the installed patch in it
  (the patches are mutually exclusive on one file). One job at a time is
  safe (that is why E0 and SAMPLE were chained `afterok`); two lanes
  rewrote the sampler under each other: `apply.sh` self-tests found the
  other job's patch (`no attribute _SPEC_CASC_TOK_ALPHA … did you mean
  _SPEC_CASC_TOK_LT_ALPHA`), servers died when Triton re-read a changed
  file (`@jit functions should be defined in a Python file`), requests
  then got `Connection refused`. Completed `run.json`s are sound (a
  request only succeeds against a healthy server; a mismatched patch
  crashes rather than runs) and are reused by skip-if-done.
  **Fix:** one repo + venv copy per lane (`lossy-token-eff-lane2/`,
  11 GB), lanes pinned to disjoint H100 nodes (`--exclude=g[15-28]` /
  `--exclude=g[1-14]`) because the `/tmp` knob files are per node, not per
  job. Rule for the future: **concurrent jobs must never share a venv.**
  Resubmitted 2026-09-15: lane 1 (main dir, g1–g14) gsm8k 21986969 →
  humaneval 21986970 → livecodebench 21986971; lane 2 (`lossy-token-eff-lane2`,
  `REPO_DIR` exported, g15–g28) mtbench 21987918 → longbench_v2 21987919.
  The 11 GB venv copy took ~50 min on project storage. Lane-2 outputs live
  in the lane-2 directory (`campaign/*/{mtbench,longbench_v2}_proper.*`).
  Lane 2's first submission (21987918/21987919) died in 5 min: the copy
  had used *unanchored* `--exclude runs/ --exclude logs/`, which rsync
  applies at every depth, so `openai/types/beta/threads/runs` (and every
  other `runs`/`logs` dir inside site-packages) was missing →
  `ModuleNotFoundError`. Re-synced with anchored `/runs/` `/logs/`,
  verified imports + no missing dirs, resubmitted: mtbench 21988492 →
  longbench_v2 21988496. (Lesson: anchor rsync excludes with a leading
  slash when copying a venv.)

## 2026-09-15 — E1P-gsm8k done (job 21986969, 150 problems × 3 seeds = 450 runs per point)

Lossless: l̄ 2.59, mean 326 tokens, 7 of 450 runs hit the 2,048-token
budget, acc 0.96. Files `campaign/*/gsm8k_proper.*`; scored as
`gsm8k_proper` in `cascade/results/speed_ignoring_accuracy.md`.

| rule | α | accepted per pass | mean len | median len | budget hits /450 | passes speedup | acc |
|---|---:|---:|---:|---:|---:|---:|---:|
| tok | 0.15 / 0.20 / 0.25 | 1.05 / 1.04 / 1.06 | 0.97 / 0.94 / 0.94 | 0.93 / 0.90 / 0.87 | 7 / 7 / 10 | 1.06 / 1.10 / 1.11 | 0.96 / 0.95 / 0.95 |
| tok_lt | 0.15 / 0.20 / 0.25 | 1.12 / 1.12 / 1.13 | 1.02 / 1.04 / 1.03 | 0.98 / 0.98 / 0.94 | 8 / 10 / 11 | 1.07 / 1.04 / 1.07 | 0.95 / 0.95 / 0.96 |

Read-out: same shape as AIME24. tok_lt accepts 12–13% more per pass than
lossless (tok 4–6%), answers stay at lossless length, accuracy unchanged,
end-to-end **~1.05–1.10× for both rules** — the quick look's 1.27× at
α=0.8 (30 runs) was optimistic. Per-seed speedups swing 0.95–1.21 even at
150 problems because the handful of 2,048-token budget hits carry ~10–15%
of all tokens; gsm8k length statistics are loop-dominated too, just at a
smaller scale. tok's slightly shorter answers (0.94–0.97×) cancel tok_lt's
larger acceptance gain, so on this benchmark the two rules tie.

## 2026-09-16 — E1P: humaneval, livecodebench, mtbench done; longbench_v2 refilling

- humaneval 21986970 (3 h 33 m), livecodebench 21986971 (5 h 11 m — the
  15 h estimate was 3× too pessimistic; generation on the H100 SXM is much
  faster than the old box's PCIe), mtbench 21988492 (3 h 15 m): all clean.
  Tables in `RESULTS.md` §2.3b. Pattern identical to AIME24/gsm8k: tok_lt
  +9–13% accepted/pass, length ≈ lossless, accuracy unchanged, end-to-end
  1.06–1.10× at the best α; tok +2–6% and ~1.00–1.04×.
- **Two data-hygiene problems found and fixed.** (1) humaneval's tok_lt
  α=0.15 arm had 227 *failed* placeholder `run.json`s (status != ok) from
  the 2026-09-14 collision; skip-if-done treats any run.json as done, so
  they were never redone. Removed them; the arm is re-running (job
  22068663, lane 1). Rule: after any failed job, delete non-ok run.jsons
  before resubmitting. (2) longbench_v2 21988496 died at 11/21 arms with
  `OSError: Address already in use` — `remote/stop_server.sh` waits for
  the GPU to free, not for the API server's socket, so the next arm's
  server could bind before the previous one closed. Added a port-free
  wait (≤90 s) to `fresh_server_replay.start_server`; resubmitted as
  22068664 (lane 2); it reuses the 330 completed longbench runs.
- Scan of both lane dirs: the humaneval arm was the only place with
  non-ok records.
- **Both gap-fills done**: humaneval 22068663 (30 min; tok_lt α=0.15 now
  450/450: accepted 1.10, len 1.00, 0 budget hits, passes 1.08, acc 95%),
  longbench_v2 22068664 (59 min, port-wait fix held).
- **Report bug found and fixed:** `campaign_report.grade_accuracy` keyed
  verdicts by (method, params, case) — no seed — so for multi-seed runs
  the last-graded seed's verdict stood in for all three. Fixed to key by
  seed, verified identical on single-seed old_runs, all multi-seed reports
  regenerated on Nibi and re-pulled. Corrected lossless accuracies: AIME24
  78% (was 73%), livecodebench 89% (was 85.5%), longbench_v2 60% (was
  63%); gsm8k/humaneval unchanged. RESULTS.md updated throughout.
- **longbench_v2 (30 × 3 seeds)**: lossless l̄ 1.97, 1,382 tokens, 0 budget
  hits, 60% (17/18/19 of 30 by seed). tok_lt: accepted 1.11–1.13, len
  1.09/0.99/1.27, passes 1.00/1.09/0.88, acc 56/53/56%; tok: 1.08–1.11,
  len 1.10/1.23/0.99, passes 0.95/0.87/1.09, acc 56/57/52%. No consistent
  speedup (per-seed 0.63–1.40) and every arm 3–8 points below lossless —
  the one benchmark where the head-restricted rules are not free, in line
  with the campaign's 150-problem tok result (−3/−4 points).
- **E1P complete on all five benchmarks.** Five-benchmark picture: tok_lt
  1.06–1.10× at unchanged accuracy on gsm8k/humaneval/livecodebench/
  mtbench/AIME24; nothing on longbench_v2. Total GPU time this week ≈ 60 h.
  Read-out per dataset: pull the `_proper` files (tables under a distinct
  local name), rerun `speed_ignoring_accuracy.py`, compare tok_lt/tok at
  0.15/0.2/0.25 vs strict with the same table as AIME24's.

- Nibi facts learned: the multiplexed SSH master dies after ~10 min of
  inactivity server-side (each new round needs one Duo tap; batch work
  per login); `pkill -f` on the login node matches your own ssh command
  line; login nodes are separate hosts (l3/l4), so `pgrep` cannot see a
  build started on another one — use the shared log file.
- **Verification pass found two real gaps in the pipeline, both fixed:**
  (1) `campaign_report.py` built `results/*.csv` and graphs from the fixed
  five-method list, so any new variant would have been silently absent
  from accuracy and graphs — now any calibrated method is included, and
  uncalibrated arms (two-knob `alpha<a>_beta<b>` dirs, guard arms) get
  their own rows keyed `<method>_<extra>`; grey fallback graph styles.
  Verified end-to-end on `old_runs/aime24`. (2) `campaign_run.py`
  overwrote `campaign/calibration/<dataset>.json` with only the methods it
  ran, so `E1-gsm8k` would have erased the paper's other methods from the
  next report — now merged; new methods are matched to the targets
  already on file (`--retarget` opts out). Refactor reproduces all 8
  recorded calibrations exactly. Also cleaned an ugly expectation override
  in `test_spec_casc_diff.py`.

## 2026-09-17 — final results PDF

`cascade/analysis/results_pdf.py` → `cascade/results/final_results.pdf` (8 pages): summary table of the best tok_lt
point per benchmark, then one page per benchmark (lossless / tok α 0.15, 0.25 / tok_lt α 0.15, 0.20, 0.25; accepted per
pass, answer length, budget hits, verifier passes, accuracy — all ÷ lossless, paired per problem and seed — plus the two
graphs), then notes and caveats. Regenerate after any result change with `python3 cascade/analysis/results_pdf.py`.
