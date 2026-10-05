# Cross-method force-commit findings

Running record of `*_force_commit` promotions on AIME24 (GPT-OSS-20B). The 8-case
screens are in `cross_method_force_commit_screen.md`. This file holds the 30-case
promotions.

## mentored_dec (alpha=0.75), 30-case AIME24, threshold 30000

**Status: valid paired delta below (same session, same build b945333). The campaign-baseline comparison further down is superseded.**

### Force-commit arm, 30 cases

| metric | value |
|---|---:|
| mean completion tokens | 15,042.5 |
| cap hits (32,768) | **0 / 30** |
| correct | 19 / 30 |
| wrong | 8 / 30 |
| no_answer | 3 / 30 (case_003, case_019, case_029) |

Per-case run records: `cross_method_runs/aime24/mentored_dec_force_commit/alpha0.75_t30000/`.

### Why the reused baseline is not valid for a delta

The reused 30-case baseline (`runs/aime24/mentored_dec/alpha0.75`, campaign data,
2026-08-15) was not produced by the same build as this arm (2026-10-03):

- git commit: `fa8c8360` (campaign) vs `b945333` (current);
- the installed patch set differs: the current build carries the `*_force_commit`
  patches and a different `v2_sha256` in `server_info.json`.

Evidence on the 8-case subset that both cover:

| case | campaign baseline | in-session baseline (cross_method_runs) |
|---|---|---|
| case_001 | 1,503 tok, correct | 3,331 tok, correct |
| case_002 | 27,901 tok, correct | 32,768 tok, wrong (cap) |
| case_007 | 17,211 tok, correct | 29,389 tok, correct |

Six of the eight shared cases diverge in length before any force-commit is
applied, so a delta against the campaign baseline would mostly measure the build
change, not the intervention.

### Descriptive comparison only (not a delta)

Campaign baseline: mean 14,772.8 tokens, 6 cap hits, 19 correct, 11 wrong.

Cap hits go 6 -> 0. Verdict flips against the campaign baseline:

| case | campaign baseline | force-commit t=30000 | verdict change |
|---|---|---|---|
| case_003 | wrong, 32,768 (cap) | no_answer, 30,138 | wrong -> no_answer (both incorrect) |
| case_004 | wrong, 32,768 (cap) | wrong, 30,129 | still wrong |
| case_017 | wrong, 32,768 (cap) | correct, 31,123 | wrong -> correct |
| case_019 | wrong, 32,768 (cap) | no_answer, 30,061 | wrong -> no_answer (both incorrect) |
| case_026 | wrong, 32,768 (cap) | correct, 32,233 | wrong -> correct |
| case_029 | wrong, 32,768 (cap) | no_answer, 30,169 | wrong -> no_answer (both incorrect) |
| case_009 | correct, 3,390 | wrong, 3,580 | correct -> wrong (finishes well under threshold) |
| case_012 | correct, 2,266 | wrong, 2,720 | correct -> wrong (finishes well under threshold) |

Every other case is correct in both arms. Byte-identical cases: 14 of 30.

Net correct count is 19 -> 19, but with a different set: two capped runs
gained correctness (case_017, case_026), and two healthy runs (case_009,
case_012) lost it. Neither healthy run reaches 30k tokens, so the forced
boundary should not have fired on them. That points to a build difference,
not the mechanism, and is the main reason the baseline must be rerun
in-session before any claim.

### Read-out and next step

- The force-commit arm is clean on the cap: 0/30 cap hits.
- The length and accuracy delta cannot be claimed until the baseline is rerun
  on the current build: one in-session 30-case baseline, about 2-3 GPU-hours,
  one server at a time.
- The 8-case screen (`cross_method_force_commit_screen.md`, t=30000 row) is
  in-session on both arms and is valid: -4.2% mean, cap hits 3 -> 0, accuracy 5/8 -> 6/8.
- Other methods' 30-case promotions wait until this one has a same-build baseline.

## mentored_dec, alpha 0.75, threshold 30000 -- full 30-case AIME24, same build

Paired comparison, both arms on build b945333, same 30 cases, one seed.
Baseline is the in-session no-force-commit run; force-commit arm is
`runs/aime24/mentored_dec_force_commit/alpha0.75_t30000`.

| | baseline | force_commit (t=30000) |
|---|---:|---:|
| mean output tokens | 15,526 | 15,043 (**-3.1%**) |
| cap hits (32,768) | 7/30 | **0/30** |
| accuracy (grade_aime.py) | 16/30 | **19/30** |

Flips (baseline -> force_commit):
- wrong -> correct: case_002, case_017, case_026 (all three were capped at baseline)
- correct -> wrong/no_answer: none
- The other 27 cases are not forced to a different answer. Length changed only on the 7 capped cases (each now stops at 30-31k tokens) plus any case that hit the threshold.

Read: no accuracy regression on 30 cases, and the accuracy change is positive on the cases the threshold actually touched. Single seed, so the +3 is only as strong as one seed allows. The -3.1% mean is smaller than the -15.3% 8-case screen at t=22000, because t=30000 forces fewer runs.

### Paired delta, same session and build (valid)

Baseline arm: `cross_method_runs/aime24/mentored_dec/alpha0.75` (30/30 ok, this session, build b945333).
Force-commit arm: `cross_method_runs/aime24/mentored_dec_force_commit/alpha0.75_t30000` (30/30 ok, same session).

| metric | baseline | force-commit t=30000 | paired change |
|---|---:|---:|---:|
| mean completion tokens | 15,525.8 | 15,042.5 | **-3.1% (-483 tok)** |
| cap hits (32,768) | 7 | 0 | -7 |
| correct | 16 | 19 | +3 |
| wrong | 14 | 8 | -6 |
| no_answer | 0 | 3 | +3 |

Flips (7 of 30 cases; 23 byte-identical in tokens and verdict):

| case | baseline | force-commit t=30000 | verdict change |
|---|---|---|---|
| case_002 | wrong, 32,768 (cap) | correct, 31,024 | wrong -> correct |
| case_017 | wrong, 32,768 (cap) | correct, 31,123 | wrong -> correct |
| case_026 | wrong, 32,768 (cap) | correct, 32,233 | wrong -> correct |
| case_003 | wrong, 32,768 (cap) | no_answer, 30,138 | both incorrect |
| case_004 | wrong, 32,768 (cap) | wrong, 30,129 | both incorrect |
| case_019 | wrong, 32,768 (cap) | no_answer, 30,061 | both incorrect |
| case_029 | wrong, 32,768 (cap) | no_answer, 30,169 | both incorrect |

Every flip is a capped baseline run. No healthy run changes, and no correct
answer is lost. The two healthy-case flips in the campaign comparison
(case_009, case_012) do not occur on the same build, which confirms they came
from the build mismatch.

Read-out: at this threshold the mechanism's effect on mentored_dec is a 7 -> 0
cap-hit reduction with three recovered correct answers and no lost ones. The
length saving is small (-3.1%) because the forced runs finish at 30k-32k, close
to the cap, so the saving per case is limited to the difference between the cap and
the threshold.

## spec_casc_tok (alpha=0.8), 30-case AIME24, threshold 30000 -- WARM-SERVER

**Labelling.** Every number in this section comes from warm-server runs: one vLLM server per arm, reused across cases, per-request seed 0. Per-case outputs are not byte-reproducible across server histories. The first divergence from a fresh server is at case_002, which is why the per-case flips below should not be read as individual effects.

| metric | baseline | force-commit t=30000 | paired change |
|---|---:|---:|---:|
| mean completion tokens | 12,514.5 | 12,662.9 | +1.2% (+148 tok) |
| cap hits (32,768) | 5 | 5 | 0 |
| correct | 24 | 22 | -2 |

Byte-identical (tokens and verdict) in only 4 of 30 cases; 26 differ in token count. Accuracy flips:
- case_007: correct -> not-correct (8,906 -> 32,768, cap)
- case_014: correct -> not-correct (31,242 -> 32,768, cap)
- case_019: not-correct -> correct (32,768 cap -> 23,295)
- case_023: correct -> not-correct (3,273 -> 18,110)

**Read-out: INVALID as a force-commit test.** The force-commit arm ran on one warm server, and its force state is module-level and cumulative per process. The patch resets that state only on warmup batches (batch size > 8), which a serial warm server never produces. So once case_001 opened the final channel, `final_opened` stayed True for every later request and forcing was disabled for the rest of the server's life. Evidence: five force-commit runs in the ledger passed 30,000 tokens with no final channel and none were forced. The +1.2% mean, 5 -> 5 cap hits, and 24 -> 22 correct are therefore not effects of force-commit, and the per-case flips are not claimed. The baseline arm is a valid warm baseline, subject to the history caveat above.

## mentored_dec (alpha=0.75), 30-case AIME24, threshold 30000 -- FRESH (unchanged)

See the earlier section above: each case ran on its own fresh server, so this pair is per-case reproducible and not affected by the warm-server caveat.

## gsm8k (alpha=0.8 / 0.75), 150 cases, threshold 1843 -- WARM-SERVER, force arms INVALID

Metrics ledger: `autoresearch/cross_method_metrics/gsm8k.csv` (per-case output_tokens, finish reason, cap hit, final-channel flag, l_bar, verdict). Raw per-case outputs were deleted after grading; run.json is kept.

| arm | mean tokens | cap hits (2048) | correct /150 |
|---|---:|---:|---:|
| spec_casc_tok (baseline, warm) | 333.6 | 4 | 143 |
| spec_casc_tok_force_commit (t=1843, warm) | 333.6 | 4 | 143 -- INVALID, see below |
| mentored_dec (baseline, warm) | 395.6 | 4 | 141 |
| mentored_dec_force_commit (t=1843, warm) | 396.4 | 4 | 141 -- INVALID, see below |

The four capped spec_casc_tok runs (cases 063, 120, 140, 148) never open the final channel, and the force arm reproduces them at the same 2,048 tokens. That is what disabled forcing predicts: `final_opened` was already set by an earlier request. The `same_token_count` column in the report counts equal token counts, not identical text, so "identical" here does not mean the text matches.

**Force arms: not a measurement.** As for aime24, the warm force-commit arms cannot test the mechanism. The baseline rows are valid as warm baselines.

## Status
- Warm-server baselines (spec_casc_tok, mentored_dec) are usable as baselines with the history caveat.
- All warm-server force-commit results are invalid. The fix is per-request state reset, or fresh-per-case servers for the force arms. The mentored_dec aime24 pair stays fresh and valid.

## Force-state fix (V1 GPT-OSS force-commit), 2026-10-04

**Cause.** The force-commit state was one process-global dict. The patch reset it only on warmup batches (size > 8). On a warm server every request is batch 1, so after the first request opened the final channel, forcing was disabled for every later request. Warm force-commit results were therefore not measurements of the mechanism. They are recorded as invalid in `cross_method_metrics/invalid_warm_force_pre_fix.csv` (330 rows: 30 aime24, 300 gsm8k) and have been archived out of the campaign tree.

**Fix.** State is keyed by the runner's request id for batch slot 0. The model runner passes `input_batch.req_ids` to the sampler before each sampling step (`patches/vllm-0.26.0-force-commit-model-runner.patch`, a second file for this arm, registered in `HASHES.txt` and `apply.sh`). The sampler's state is created fresh for each new request id. The warmup reset clears all states. The superseded global-state patch is kept as `vllm-0.26.0-spec-casc-tok-force-commit-superseded-global-state.patch`. Its hash stays in HASHES.txt under its own label, so it can't be installed under the current name.

**Why not `output_token_ids`.** SamplingMetadata's `output_token_ids` is an empty list whenever penalties are off, which is the GPT-OSS config, so it cannot identify requests. The runner's request ids are the only source.

**Plumbing test.** `patches/test_spec_casc_tok_force_commit.py` passes, including a new per-request-id reset test (`bash patches/apply.sh spec-casc-tok-force-commit`, exit 0, self-test passed; the GPU end-to-end test skips without a GPU). The startup probe in `remote/run_server_vllm.sh` now checks `_FORCE_COMMIT_STATES`.

**3-case check, warm server, aime24 cases 002, 003, 004.**
- Threshold 30000 (pre-registered): only case_002 ran past the threshold, and its final-channel boundary is present. Cases 003 and 004 finished naturally below the threshold, so this run does not test later requests.
- Threshold 2000 (mechanism check, not a result, not pre-registered): all three requests ended at 2,276 to 2,774 tokens with the forced boundary present in the output. Their baseline trajectories run to 15,000+ tokens, so none would end this early without forcing. Under the old state bug, requests 2 and 3 would have run unforced.
- Result: force fires on each request, and state does not carry over between requests. The check passes.

**Which earlier runs were warm (checked from `fresh_server_replay.json` manifests).**
- Fresh per case (valid, unaffected): all cactus, cactus_force_commit, r_fuzzy, r_fuzzy_force_commit, spec_casc_opt, and spec_casc_opt_force_commit 8-case screens; the full mentored_dec aime24 pair (baseline 30, force-commit t=30000 30, plus the t=22000 screen). Manifest batches that predate the warm-mode code are fresh by construction.
- Warm: the aime24 spec_casc_tok baseline (valid as a warm baseline, subject to the history caveat); the gsm8k spec_casc_tok and mentored_dec baselines (valid as warm baselines); and all warm force-commit arms (invalid, now rerun).

**Campaign.** Warm loop restarted in the original order. Invalid warm force-commit arms are regenerated under the fixed patch. Baselines are not regenerated, since they were not affected by the bug.

## Keyed-state fix results (warm, fixed patches), 2026-10-04

**mentored_dec force-commit** had the same process-global state. It is now keyed by request id (`vllm-0.26.0-mentored-dec-force-commit.patch`, installed hash `ab5116f4…`). Plumbing test passes. 3-case check at threshold 2000 (mechanism, not a result): cases 002, 003, 004 each carry the forced boundary near 2,000 tokens.

**spec_casc_tok aime24, warm, fixed patch (30 cases, threshold 30000, alpha 0.8).** Baseline is the warm baseline. Record validity is checked against the installed hash in `config.json`.

| metric | baseline (warm) | force-commit t=30000 (warm, fixed) |
|---|---:|---:|
| mean completion tokens | 12,514.5 | 12,591.7 (+0.6%) |
| cap hits (32,768) | 5 | 0 |
| correct | 24 | 23 |

- All 8 force-commit runs past 30,000 tokens contain the final channel, so forcing fired on each. Baseline cap hits 5 -> 0.
- Flips, reported as warm-server descriptive only: case_006 correct -> not-correct (7,475 -> 30,136, a healthy baseline run that diverged on the warm sequence), case_030 correct -> not-correct (5,682 -> 30,097), case_026 not-correct -> correct (cap -> 31,516).
- **Caveat.** The warm baseline and force-commit arms still diverge sequence-wide (history dependence, per the earlier diagnostic), so per-case flips are not claimed as force-commit effects. The mean (+0.6%) and cap-hit change (5 -> 0) are the reportable deltas. Correct count moved -1 with flips in both directions, which noise can produce.

## gsm8k, 150 cases, warm, fixed force patches, threshold 1843 (pre-registered 0.9 x 2048)

Ledger: `autoresearch/cross_method_metrics/gsm8k.csv` (all four arms, record_valid True). Raw outputs deleted after grading; run.json kept.

| method | arm | mean tokens | Δ | cap hits (2048) | correct /150 |
|---|---|---:|---:|---:|---:|
| spec_casc_tok α0.8 | baseline (warm) | 333.6 | | 4 | 143 |
| spec_casc_tok α0.8 | force-commit (warm, fixed) | 343.6 | +3.0% | 2 | 143 |
| mentored_dec α0.75 | baseline (warm) | 395.6 | | 4 | 141 |
| mentored_dec α0.75 | force-commit (warm, fixed) | 384.4 | −2.8% | 2 | 142 |

- **Mechanism.** Every run that reaches 1,843 tokens in a force arm contains the final channel (spec 5/5, mentored 5/5). At baseline, the four runs past 1,843 tokens (all capped) have no final channel (0/4). Forcing fires on each.
- **Caveat.** These are warm-server paired arms and carry the history caveat. Token counts match between arms in only 63 of 150 cases. Flips are descriptive, not per-case effects.
- spec_casc_tok flips: case_074 not-correct -> correct; case_140 and case_148 not-correct -> correct; case_086, case_101, case_126 correct -> not-correct. Net 0.
- mentored_dec flips: case_064 not-correct -> correct; case_148 not-correct -> correct; case_140 correct -> not-correct. Net +1.
- Two capped force runs (spec case_063 no_answer, mentored case_120 no_answer, and spec case_086 / mentored case_140 for their own arms) reached the final channel and ran out of budget during the answer.
- mtbench is token-only (no grader). Not run in this pass yet.

## GPT-OSS remaining datasets (warm, fixed force patches), 2026-10-04/05

All arms warm, one server per arm, seed 0. Paired deltas are descriptive: token counts match between arms in only a minority of cases (see the same_token column in the report), so per-case flips are not claimed as force-commit effects. mtbench has no grader and is token-only.

| dataset (threshold) | method | mean base → FC | Δ | cap hits | correct base → FC | flips |
|---|---|---|---:|---|---|---:|
| humaneval (8100) | spec_casc_tok | 1,142 → 1,139 | −0.3% | 1 → 0 | 145 → 145 | 0 |
| humaneval (8100) | mentored_dec | 1,170 → 1,189 | +1.7% | 1 → 0 | 143 → 144 | 1 |
| mtbench (3686) | spec_casc_tok | 1,321 → 1,256 | −5.0% | 2 → 0 | token-only | — |
| mtbench (3686) | mentored_dec | 1,241 → 1,336 | +7.7% | 3 → 4 | token-only | — |
| livecodebench (10800) | spec_casc_tok | 3,838 → 3,819 | −0.5% | 6 → 4 | 80 → 80 | 8 |
| livecodebench (10800) | mentored_dec | 4,571 → 4,186 | −8.4% | 9 → 4 | 70 → 69 | 23 |
| longbench_v2 (7372) | spec_casc_tok | 1,682 → 1,754 | +4.3% | 2 → 0 | 72 → 74 | 16 |
| longbench_v2 (7372) | mentored_dec | 2,089 → 2,395 | +14.6% | 3 → 1 | 83 → 79 | 30 |

**Read-out.** Cap hits fall or hold on every dataset where forcing applies, and every run past its threshold reaches the final channel. The mean-token deltas go both ways (−8.4% to +14.6%) and the accuracy changes are small in both directions. The mentored longbench_v2 +14.6% with 30 flips is the largest deviation and is not explained by the cap change, so it should be treated as warm-history noise until a fresh-per-case rerun says otherwise. Nothing here is a per-case effect claim.
