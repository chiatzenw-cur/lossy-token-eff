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
