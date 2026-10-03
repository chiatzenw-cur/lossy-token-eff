# Cross-method force-commit screen (AIME24, cases 001-008)

Force-commit (see `patches/HASHES.txt`'s 2026-10-03 entry) mechanically
ported onto cactus/mentored-dec/r-fuzzy/spec-casc-opt, tested the same way
the original `spec_casc_tok_force_commit` candidate was first screened:
8-case AIME24 tuning set, each method's own aggressive alpha (the value
used throughout `campaign/`'s own AIME24 sweep -- see `campaign/results/
aime24.csv`), threshold=28000 (reusing `spec_casc_tok_force_commit`'s own
validated default, not yet tuned per method). Both arms run fresh via
`scripts/fresh_server_replay.py` in the same session for a clean
comparison -- historical `runs/aime24/<method>/` data from the earlier
`campaign/` sweep (a different harness, `run_experiment_vllm.py`) is NOT
reused here: a spot check (cactus case_001) found it diverges from a fresh
rerun at the same alpha (2767 vs 5103 tokens) despite matching seed/patch
hash, consistent with this repo's own documented GPU-kernel nondeterminism
caveat -- so only same-session, same-methodology comparisons are trusted.

## cactus (alpha=0.18)

| | baseline | cactus_force_commit (t=28000) |
|---|---:|---:|
| mean completion tokens | 21,342.75 | **19,961.5 (-6.5%)** |
| accuracy | 4/8 | 4/8 (±0) |
| cap hits (32,768) | 3/8 | **0/8** |
| wrong | 4 | 1 |
| no_answer | 0 | 3 |

Per-case:

| case | baseline | force_commit | verdict (base/fc) |
|---|---:|---:|---|
| case_001 | 5,103 (stop) | 5,103 (stop) | correct/correct -- byte-identical |
| case_002 | 32,768 (cap) | 28,072 (stop) | wrong/no_answer |
| case_003 | 32,768 (cap) | 28,108 (stop) | wrong/no_answer |
| case_004 | 16,311 (stop) | 16,311 (stop) | wrong/wrong -- byte-identical |
| case_005 | 25,812 (stop) | 25,812 (stop) | correct/correct -- byte-identical |
| case_006 | 32,768 (cap) | 31,074 (stop) | wrong/no_answer |
| case_007 | 17,245 (stop) | 17,245 (stop) | correct/correct -- byte-identical |
| case_008 | 7,967 (stop) | 7,967 (stop) | correct/correct -- byte-identical |

**Clean win, same shape as the original spec_casc_tok result**: byte-identical
on the 5/8 healthy cases, all 3 cap-hits now terminate (one, case_006, lands
close to the cap at 31,074 -- the threshold leaves little slack there and is
a candidate to tune down later, same as spec_casc_tok's own threshold
sweep). Zero accuracy cost (wrong-with-a-spuriously-extracted-wrong-digit
becomes a clean no_answer, not a flip to correct or a newly-broken case).
cactus shows a MUCH higher baseline cap-hit rate on this 8-case set (3/8,
37.5%) than spec_casc_tok ever did (3/30, 10%) -- consistent with
`reasoning_vs_output_all_datasets.md`'s own finding that cactus pushes
non-termination far harder than spec_casc_tok at comparable "aggressive"
settings (aime24: 2->7 of 30 cases, strict->cactus@0.18).

**Caveat before promoting to full-30**: cactus never reaches a "free win"
accuracy point on AIME24 at any tested alpha (`campaign/FINDINGS.md`'s own
0.6/0.633/0.533/0.6 numbers across its 4-point grid, all below strict's
0.767) -- so this result demonstrates force-commit is a real, surgical,
*accuracy-neutral-relative-to-cactus-itself* backstop, not that cactus+
force-commit becomes a method worth deploying over spec_casc_tok. The
value of this result is for the cross-method generalization claim (force-
commit's mechanism isn't spec_casc_tok-specific), not a recommendation to
use cactus.

## r_fuzzy (alpha=0.25) -- complete 8-case screen, clean win

| | baseline | r_fuzzy_force_commit (t=28000) |
|---|---:|---:|
| mean completion tokens | 24,048.5 | **21,905.4 (-8.9%)** |
| accuracy | 2/8 | 2/8 (identical correct set) |
| cap hits (32,768) | 4/8 | **0/8** |
| wrong / no_answer | 6 / 0 | 3 / 3 |

Per-case: case_001, case_004, case_005, case_008 byte-identical. case_002
32,768 (cap, wrong) -> 29,233 (stop); case_003 32,768 (cap) -> 28,361
(no_answer); case_006 32,768 -> 28,058 (no_answer); case_007 32,768 ->
28,275 (no_answer). Every capped run now terminates. Same win shape as
cactus, on a switch-based (defer_mask) accept rule.

The first attempt was interrupted at case_003 by host disk exhaustion
(unrelated to the patch); cases 001-002 from that attempt were kept
(complete, valid), 003-008 rerun fresh. Disk has since been freed.

## spec-casc-opt (alpha=0.05) -- complete 8-case screen, clears the bar

| | baseline | spec_casc_opt_force_commit (t=28000) |
|---|---:|---:|
| mean completion tokens | 27,139.4 | **24,611.0 (-9.3%)** |
| accuracy | 2/8 | 2/8 (identical correct set: 001, 008) |
| cap hits (32,768) | 6/8 | **1/8** |
| wrong / no_answer | 6 / 0 | 4 / 2 |

Per-case: case_001, case_008 byte-identical. Five capped runs (002, 004,
005, 006, 007) now terminate at 28-30k tokens. case_003 stays capped at
32,768 with only 3 final-channel tokens -- it still does not commit, so the
forcing did not rescue it. Same threshold-vs-noise caveat as cactus's
case_006: landing close to the threshold means the forced boundary is doing
the work.

Note on the defer_mask OR: spec_casc_opt's own alpha is a TV-based switch.
The real-kernel aggressive-alpha test (0.05, 0.999-confident draft) passed
on GPU, so the OR-in is confirmed load-bearing in that regime.

## mentored_dec -- pending

