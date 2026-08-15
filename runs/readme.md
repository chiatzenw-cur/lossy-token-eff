# AIME24 results: every arm, by method family and parameter

All numbers below are freshly recomputed from `runs/aime24/<method>/<params>/<case>/seed_0/`
(`scripts/grade_aime.py`, `scripts/summarize_arms.py`,
`analysis/semantic_guard/count_hesitation.py`,
`analysis/semantic_guard/count_relaxed_only_hesitation.py`), restricted to the
standard 30-case set (`case_001`..`case_030`) -- diagnostic/probe case
variants (`case_NNN_onsetXXXXX`, `_forced_recovery`, etc.) and single-case
diagnostic captures are excluded from the tables and footnoted instead.

## Definitions

### `spec_casc_tok` family

Base method (Narasimhan et al. 2025 / Xia et al. 2026 Table 2, Eq. 15):
`pi_rej(v) = q(v) + eta*p(v)` for `v` in the trusted top set
`A = {u : p(u) >= (1-alpha)*max(p)}`, else `eta*p(v)`, with
`eta = 1 - sum_{u in A} q(u)`. `alpha -> -inf` is the strict limit (`A`
empty, `pi_rej = p`), **not** `alpha = 0`. `lossless (strict)` is plain
speculative decoding (`p(x)/q(x) >= u`) and `spec_casc_tok` is this
unguarded base method at a given alpha -- both are reference rows, not
guards. Every guard below is a rule for forcing `A` empty (or otherwise
overriding toward strict/a fixed pattern) at specific positions, layered on
top of this same base formula.

- **`spec_casc_tok_semantic_guard`** ("override", narrow marker set):
  forces `A` empty at the drafted position whenever the drafted token is
  one of an 18-id/5-word hesitation/self-correction set (`wait, hmm, let's,
  actually, but`). Stateless, one round, one position at a time.

- **`spec_casc_tok_semantic_guard_v2`** ("v2", wide marker set): identical
  mechanism to the override guard, but a wider 35-id/14-word marker set
  (adds `thus, we, so, now, let, compute, similarly, define, from` and
  variants).

- **`spec_casc_tok_semantic_guard_and`** ("AND", narrow marker set): same
  narrow marker set as the override guard, but instead of overriding to
  pure strict at a marker, accepts iff BOTH the lossless test AND
  `spec_casc_tok`'s own relaxed test would accept (`min(p, pi_rej)` as the
  effective target) -- provably never more lenient than the override guard
  at any guarded position.

- **`spec_casc_tok_semantic_guard_future_guard`** ("future-guard-strict",
  parameter `K`): different trigger shape -- instead of gating the marker
  token itself, arms a `K`-token trailing strict window the moment
  `spec_casc_tok`'s own test *accepts* a marker (wide 35-id set). For the
  next `K` verified positions, the accept test uses the raw lossless ratio
  `p(x)/q(x) >= u` instead of `spec_casc_tok`'s blend. Cross-round state
  (remaining-window count) is carried via a small per-batch-slot tensor
  threaded through the Triton accept kernel itself -- this kernel-carried
  counter has a confirmed rare bug (a marker accepted while a window is
  already active silently fails to re-arm it); see
  `analysis/semantic_guard/README.md`.

- **`spec_casc_tok_semantic_guard_future_guard_and`** ("future-guard-AND",
  parameter `K`): same trigger shape as future-guard-strict, but AND-combined
  inside the window instead of pure strict (same combination rule as the AND
  guard, applied to the `K`-window instead of the marker position alone).

- **`spec_casc_tok_hsr_guard`** ("hsr-guard", parameters `window`, `budget`,
  `percentile`, `actuator_k`): non-lexical trigger, no token-identity check
  at all. Computes S_32 (fixed 128-dim random projection of
  `target_hidden_states` -- already produced every round for EAGLE3's own
  drafting, so this reads data that's free -- trailing-32-mean cosine
  similarity against the best match >=32 committed tokens back) for every
  newly-committed real token. Self-calibrates a `percentile` threshold from
  its own trailing `window`-token score history (per-generation, not one
  fixed global cutoff); `budget` threshold-crossings within that window arm
  a trailing `actuator_k`-token strict-verification window (`A` forced
  empty, same mechanism as the override guard, just position-derived
  instead of token-identity-derived). Round-granular Python/`/tmp`-file
  state, not carried through the kernel. Defaults:
  `window=600, budget=25, percentile=99.9, actuator_k=8`.

- **`spec_casc_tok_antiloop`** (reactive repetition breaker): the moment a
  drafted continuation would complete a genuine periodic repeat (period `k`
  in `[1,12]`, 3rd consecutive occurrence), that specific `(position,
  token)` gets zeroed out of `target_probs` and the row renormalized,
  before `spec_casc_tok`'s own eta/pi_rej math runs -- a banned token
  automatically gets `pi_rej=0` (guaranteed rejection) regardless of alpha.
  No kernel changes.

- **`spec_casc_tok_force_commit`** (parameter `t`, cumulative-token
  threshold): targets the "never commits to a final-channel answer"
  failure shape (distinct from antiloop's literal-repetition target). Once
  cumulative real emitted tokens cross `t` without the model having
  naturally opened a harmony `final`-channel message, one-hot
  `target_probs` onto the next token of the fixed 6-token
  `<|end|><|start|>assistant<|channel|>final<|message|>` boundary at the
  first drafted position each round, until the boundary completes.

- **`spec_casc_tok_self_check`** (parameter `i`, token interval): every `i`
  real emitted tokens, force-inject a fixed self-assessment question
  (one-hot `target_probs`, same mechanism as antiloop/force-commit), let
  the next few tokens generate unconstrained, and read back whether the
  model's own answer starts with "yes" or "no". "No" resumes unchanged;
  "yes" force-injects a pivot phrase (or force-commit's final-channel push
  if budget is nearly exhausted). Outsources the "is this unproductive?"
  judgment to the model's own self-report.

- **`spec_casc_tok_free_judgment`**: appends a fixed criterion-question
  sequence after the real drafted tokens each round, exploiting that EAGLE
  verification is already one parallel forward pass over the whole drafted
  block -- the target's same pass computes a judgment (`p_yes - p_no`) at
  marginal FLOPs cost. The criterion tokens are always force-rejected (ban
  + renormalize at the first criterion position, not a whole-row zero) so
  they never cost real generation budget. v1 here is observation-only
  (traced, not yet acted on beyond an optional reject-and-resample probe).

All ten `spec_casc_tok*` rows share one `alpha` knob controlling the base
trusted-top-set threshold above; `K`/`t`/`i`/`window,budget,percentile,
actuator_k` are each guard's own extra knob(s) layered on top.

### Other lossy-method families (own `alpha` semantics -- not the same axis)

These do not share `spec_casc_tok`'s formula or alpha meaning, so they are
**not** grouped into the per-alpha tables below; see the separate table at
the end. (Xia et al. 2026 = arXiv:2607.08690, Table 2.)

- **`cactus`** (Hao & Mou 2026, Xia et al. Eq. 6-7): accept iff
  `gamma_x/q(x) >= u`, `gamma_x = min(p(x) + sqrt(2*alpha*p(x)*(1-p(x))), 1)`.
  `alpha` bounds a KL divergence, domain `[0, inf)`, strict at `alpha=0`.

- **`mentored_dec`** (Tran-Thien 2023 beta=1, Xia et al. Eq. 9): accept iff
  `p(x)/((1-alpha)*q(x)) >= u`, i.e. rejection-sampling against `lam*q`
  with `lam=1-alpha`. Domain `[0,1)`, strict at `alpha=0`.

- **`r_fuzzy`** (fuzzy speculative decoding, Holsman et al. 2025, Xia et
  al. Eq. 10): accept unconditionally (residual `pi_rej=q`) iff
  `JSD(p,q) < alpha`, else fall back to the strict `p/q` test. `alpha` is a
  Jensen-Shannon-divergence threshold; strict at `alpha=-inf`.

- **`r_fuzzy_semantic_guard`**: same `JSD(p,q) < alpha` test as `r_fuzzy`,
  ANDed with "drafted token is not a hesitation marker" (always-on
  token-id override forcing strict at marker ids, independent of alpha).

- **`r_fuzzy_window_entropy_guard`**: `JSD(p,q) < alpha` AND rolling-32
  mean target+draft entropy over committed tokens below its
  strict-calibrated Q90 (else strict), a distributional/entropy sibling of
  the token-marker guards.

- **`spec_casc_opt`** (speculative cascades [OPT], Narasimhan et al. 2025,
  Xia et al. Eq. 12): defer to the strict `p/q` test iff
  `max_u q(u) < max_u p(u) - alpha*TV(p,q)`, else accept unconditionally.
  `alpha` scales a total-variation-distance margin; strict at `alpha=-inf`.

## Results, AIME24, alpha = 0.3

`spec_casc_tok`-family guards, `K=8` where applicable (hsr-guard at its
own defaults above). `n` is out of 30 standard cases; guards below 30 are
partial pilots, not full sweeps -- shown as-is, not extrapolated.

| variant | n | accuracy | mean length | l̄ | total rounds | hesitation words | mechanism check |
|---|---:|---:|---:|---:|---:|---:|---:|
| lossless (strict) | 30 | 23/30 (76.7%) | 10,043 | 2.2046 | 100,635 | 4,455 | -- |
| **spec_casc_tok (baseline)** | 30 | **26/30 (86.7%)** | **9,440** | **2.4210** | **86,903** | **4,172** | 3.8% |
| + override (narrow) | 30 | 22/30 (73.3%) | 10,397 | 2.4000 | 98,306 | 4,949 | 0.0% |
| + AND (narrow) | 30 | 22/30 (73.3%) | 10,964 | 2.3906 | 103,972 | 4,821 | 0.0% |
| + v2 (wide, override) | 30 | 25/30 (83.3%) | 10,599 | 2.3987 | 97,570 | 4,312 | 0.0% |
| + future-guard-strict K=4 | 30 | 22/30 (73.3%) | 10,397 | 2.3447 | 97,807 | 4,869 | 4.1% |
| **+ future-guard-strict K=8** | 30 | **25/30 (83.3%)** | **9,303** | 2.3949 | **87,637** | **3,952** | 3.5% |
| + future-guard-AND K=8 | 30 | 23/30 (76.7%) | 10,460 | 2.3723 | 99,492 | 4,460 | 4.0% |
| **+ hsr-guard** (budget=25, pct=99.9, K=8) | 30 | **26/30 (86.7%)** | **9,032** | 2.4042 | **85,207** | 4,108 | 5.0%¹ |
| + antiloop | 8 | 7/8 (87.5%) | 13,638 | 2.4093 | 33,492 | 1,515 | 3.3% |
| + force-commit t=28000 | 7 | 6/7 (85.7%) | 15,279 | 2.3081 | 32,798 | 1,607 | 4.1% |
| + self-check i=3000 | 2 | 1/2 (50.0%) | 3,020 | 2.3392 | 1,815 | 73 | 2.7% |
| + free-judgment | 6 | 2/6 (33.3%) | 17,962 | 2.1972 | 35,724 | 1,703 | 3.2% |

¹ hsr-guard's mechanism check is defined differently from every marker
guard above it: fraction of ALL verified positions with the guard active
(position-based), not fraction of hesitation-marker words specifically
accepted only via relaxation. Not directly comparable to the other rows'
"mechanism check" column, listed here for completeness only.

## Results, AIME24, alpha = 0.5

| variant | n | accuracy | mean length | l̄ | total rounds | hesitation words | mechanism check |
|---|---:|---:|---:|---:|---:|---:|---:|
| lossless (strict) | 30 | 23/30 (76.7%) | 10,043 | 2.2046 | 100,635 | 4,455 | -- |
| spec_casc_tok (baseline) | 30 | 22/30 (73.3%) | 10,495 | 2.4930 | 96,430 | 4,532 | 5.0% |
| + future-guard-strict K=8 | 30 | 20/30 (66.7%) | 10,555 | 2.4484 | 98,012 | 4,662 | 5.5% |

## Results, AIME24, alpha = 0.7

| variant | n | accuracy | mean length | l̄ | total rounds | hesitation words | mechanism check |
|---|---:|---:|---:|---:|---:|---:|---:|
| lossless (strict) | 30 | 23/30 (76.7%) | 10,043 | 2.2046 | 100,635 | 4,455 | -- |
| spec_casc_tok (baseline) | 30 | 22/30 (73.3%) | 10,337 | 2.6565 | 90,977 | 4,894 | 7.3% |
| **+ future-guard-strict K=8** | 30 | **25/30 (83.3%)** | 12,239 | 2.5364 | 109,462 | 5,699 | 6.9% |

Not run at alpha=0.5/0.7: override/AND/v2, future-guard-AND, hsr-guard,
future-guard-strict K=4, antiloop, force-commit, self-check, free-judgment
(all piloted at alpha=0.3 only), except one single-case antiloop probe at
alpha=0.7 -- footnoted below, not tabulated (n=1).

## Results, AIME24, other lossy-method families (own alpha, own axis)

Full 30-case sweeps, each method's own single alpha (not comparable to the
`spec_casc_tok` tables above -- see Definitions).

| variant | n | accuracy | mean length | l̄ | total rounds | hesitation words | mechanism check |
|---|---:|---:|---:|---:|---:|---:|---:|
| lossless (strict) | 30 | 23/30 (76.7%) | 10,043 | 2.2046 | 100,635 | 4,455 | -- |
| cactus (α=0.25) | 30 | 14/30 (46.7%) | 18,679 | 4.1678 | 108,521 | 15,909 | 24.5% |
| mentored_dec (α=0.37) | 30 | 21/30 (70.0%) | 12,318 | 2.6727 | 106,326 | 5,913 | 11.1% |
| spec_casc_opt (α=0.05) | 30 | 11/30 (36.7%) | 21,410 | 3.4122 | 148,208 | 16,618 | 12.4% |
| r_fuzzy (α=0.3) | 30 | 13/30 (43.3%) | 19,506 | 4.1287 | 114,919 | 18,049 | 26.2% |
| r_fuzzy_semantic_guard (α=0.3) | 30 | 11/30 (36.7%) | 16,942 | 3.9566 | 103,718 | 11,984 | 0.0% |
| r_fuzzy_window_entropy_guard (α=0.3) | 8 | 1/8 (12.5%) | 28,230 | 3.6528 | 48,785 | 7,285 | 24.9% |

## Excluded from all tables above (diagnostic/probe-only, not systematic-sweep data)

- `spec_casc_tok/alpha0.3_hscapture`, `case_004`, n=1: hidden-state capture
  of the known "|"-repeat-loop case at a non-canonical 14,000-token budget
  (vs. 32,768 everywhere else) -- kept on disk to support
  `spec_casc_tok_hsr_guard`'s own reproduce commands, not a comparable data
  point (0/1, but at the wrong token budget for a fair read).
- `spec_casc_tok/alpha1`, `case_001`, n=1: single exploratory run at the
  domain's near-degenerate extreme (0/1).
- `spec_casc_tok_antiloop/alpha0.7`, `case_004`, n=1: single targeted probe
  against the known-looping case (0/1, hit the 32,768-token cap) -- not
  part of the 8-case alpha=0.3 pilot above.
- 6 `case_NNN_onsetXXXXX` / `_forced_recovery` / `_alt####` directories
  under `strict` and `r_fuzzy` (counterfactual-continuation splices from a
  specific token offset, used for the future-guard/antiloop root-cause
  investigations): excluded from every case count and mean above.

Wall-time / s-per-round are omitted from every table: a same-session,
same-arm comparison (baseline vs. hsr-guard, both run back-to-back on 16
overlapping cases) showed 0.02228 vs. 0.02242 s/round -- no real
difference -- while naive cross-session numbers disagreed by >20%, i.e.
machine-load variance between sessions, not a property of any method. See
`analysis/semantic_guard/README.md` for the full writeup.
