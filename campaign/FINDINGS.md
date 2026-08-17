# Findings: per-method behaviour across the l̄-matched sweep

Cross-dataset observations about how each method's alpha actually behaves,
as opposed to `campaign/PLAN.md`'s a-priori design. Updated as datasets
land; current basis is the 3 finished datasets (**gsm8k, aime24,
humaneval**) plus whatever calibration data exists for the in-progress one.
Not a substitute for the graphs/results CSVs -- this is the narrative of
*why* they look the way they do.

## Headline: cactus and spec_casc_tok jointly define the shared comparison band, on every dataset so far

`campaign_run.py`'s target-selection rule intersects every method's
achievable l̄ range: `[max of per-method minimums, min of per-method
maximums]`. On all 3 finished datasets, that intersection has been set by
the *same two methods* both times:

| dataset | band floor (= max of mins) | band ceiling (= min of maxs) |
|---|---|---|
| gsm8k | **cactus** @ 3.50 | **spec_casc_tok** @ 3.26 |
| aime24 | **cactus** @ 3.07 | **spec_casc_tok** @ 2.62 |
| humaneval | **cactus** @ 3.04 | **spec_casc_tok** @ 2.63 |

(Floor > ceiling before the code's own fallback-to-global-span kicks in --
see `pick_targets_and_alphas()` -- so the *effective* targets end up
spanning the global min/max instead, but the mechanism is the same: these
two methods are always the ones setting the boundary, on every dataset run
so far.) Concretely: `cactus`'s *weakest* relaxation (lowest alpha tried)
already produces a higher l̄ than any other method can reach at its own
lowest alpha, and `spec_casc_tok`'s *strongest* relaxation (highest alpha
tried) still can't reach as high an l̄ as any other method's highest alpha.
`mentored_dec`, `spec_casc_opt`, and `r_fuzzy` have always had slack on
both ends -- their ranges sit inside the cactus/spec_casc_tok envelope, not
past it, on every dataset so far.

## Per-method achievable l̄ range (4-point calibration grid, 3 probe cases)

| method | gsm8k | aime24 | humaneval | monotonic in alpha? |
|---|---|---|---|---|
| `mentored_dec` | [3.20, 3.88] span 0.68 | [2.42, 3.23] span 0.81 | [2.20, 3.25] span 1.05 | yes, all 3 |
| `cactus` | [3.50, 4.18] span 0.68 | [3.07, 4.40] span 1.33 | [3.04, 4.15] span 1.11 | yes, all 3 |
| `spec_casc_opt` | [3.24, 4.07] span 0.83 | [2.66, 3.32] span 0.66 | [2.45, 3.21] span 0.76 | yes, all 3 |
| `r_fuzzy` | [2.90, 4.07] span **1.17** | [2.21, 3.67] span **1.45** | [2.33, 3.51] span **1.18** | yes, all 3 -- widest range every time |
| `spec_casc_tok` | [2.82, 3.26] span **0.44** | [2.42, 2.62] span **0.20** | [2.22, 2.63] span **0.41** | **no** (gsm8k, humaneval) |

`spec_casc_tok` is the narrowest-range method on every dataset by a wide
margin (span 0.2-0.44 vs. everyone else's 0.66-1.45), and non-monotonic on
2 of 3: its grid l̄ actually *drops* at the second alpha before recovering
(gsm8k: 3.14 -> 2.82 -> 2.83 -> 3.26; humaneval: 2.30 -> 2.33 -> 2.22 ->
2.63). Alpha isn't cleanly "more relaxed = higher l̄" for this method the
way it is for the other four -- consistent with the mechanism note already
in `analysis/semantic_guard/README.md` (`spec_casc_tok`'s out-of-trusted-set
tokens are *more conservative than lossless*, not a smooth knob).

## Consequence: chosen-alpha collapse (fewer than 3 comparison points)

Because `pick_targets_and_alphas()` dedupes when 2 targets both land on the
same nearest grid point, a method with a narrow range regularly contributes
only 2 comparison points instead of 3 (visibly fewer dots/markers on that
method's line in the graph):

| method | gsm8k | aime24 | humaneval |
|---|---|---|---|
| `spec_casc_tok` | 2/3 | 2/3 | 2/3 |
| `spec_casc_opt` | 3/3 | 2/3 | 2/3 |
| `cactus` | 3/3 | 3/3 | 2/3 |
| `mentored_dec`, `r_fuzzy` | 3/3 | 3/3 | 3/3 |

`spec_casc_tok` has collapsed on every dataset so far. `spec_casc_opt`
started clean on gsm8k but has collapsed on both harder datasets since.
`mentored_dec` and `r_fuzzy` have never collapsed -- consistent with them
never being the band's floor or ceiling either (see above).

## Statistical backing for the headline (2026-08-16, for the survey paper)

The headline claim above is about *means* (12-case averages per point).
Those means are cleanly separated, but individual cases are noisy (l̄
std ≈ 0.2-0.5 per point, comparable in size to the gaps between methods'
means) -- so a mean-vs-mean comparison alone doesn't establish that cactus
genuinely runs "ahead" of the other methods case-by-case, only that it does
so on average. Fixed with a **paired per-case sign test**: the same 12
prompts (`case_001..012`) were run under every method/alpha, so for each
case the l̄ from method A's extreme alpha can be compared directly against
method B's, cancelling out the (large) per-prompt variance that dominates
the raw std. Exact two-sided binomial test against p=0.5 (n=12 per
dataset x method-pair).

**Floor claim** -- cactus's *lowest* tested alpha vs. every other method's
own lowest tested alpha, same 12 cases, paired:

| dataset | vs. mentored_dec | vs. spec_casc_opt | vs. r_fuzzy | vs. spec_casc_tok |
|---|---|---|---|---|
| gsm8k | 10/12, p=.039 | 9/12, p=.146 | 10/12, p=.039 | 11/12, p=.006 |
| aime24 | 12/12, p<.001 | 12/12, p<.001 | 12/12, p<.001 | 12/12, p<.001 |
| humaneval | 11/12, p=.006 | 9/12, p=.146 | 12/12, p<.001 | 11/12, p=.006 |

**Pooled: cactus wins 131/144 (91.0%) of all paired case comparisons.**
Direction is unanimous (never a losing majority in any single
dataset x method-pair cell); the 2 non-significant cells at n=12
(gsm8k/humaneval vs. `spec_casc_opt`, both 9/12) are the one method whose
own floor sits closest to cactus's -- consistent with `spec_casc_opt`
having the 2nd-highest floor in the range table above, not a contradiction
of the ranking.

**Ceiling claim** -- every other method's *highest* tested alpha vs.
spec_casc_tok's own highest tested alpha, same 12 cases, paired (positive
= the other method beats spec_casc_tok, as claimed):

| dataset | mentored_dec | cactus | spec_casc_opt | r_fuzzy |
|---|---|---|---|---|
| gsm8k | 10/12, p=.039 | 11/12, p=.006 | 12/12, p<.001 | 11/12, p=.006 |
| aime24 | 12/12, p<.001 | 12/12, p<.001 | 12/12, p<.001 | 12/12, p<.001 |
| humaneval | 12/12, p<.001 | 12/12, p<.001 | 11/12, p=.006 | 12/12, p<.001 |

**Pooled: the other 4 methods win 139/144 (96.5%) of all paired case
comparisons against spec_casc_tok at its own most-relaxed setting.** Every
one of the 12 dataset x method cells is individually significant at
p<.05, most at p<.001.

**Reproduce**: per-case l̄ values are in `campaign/tables/<dataset>.csv`
(`method`, `params`=`alpha<value>`, `case`, `l_bar` columns); the exact
(method, alpha) pairs compared above are each method's min/max
`mean_l_bar` row in `campaign/results/<dataset>.csv`. No new data
collection needed -- this reuses runs already in the sweep.

**Caveat for the paper**: n=12 cases/dataset, 3 datasets so far (6 planned)
-- strong within what's been run, but state it as "3 of 6 planned
datasets" rather than implying the full benchmark suite. `spec_casc_opt`'s
2 non-significant floor cells above should be reported alongside the
131/144 pooled figure, not folded into "always significant."

## Weaker, single-instance observation (watch for repeats)

`cactus` on gsm8k: completion length is *not* monotonic in l̄ across its 3
chosen alphas -- alpha 0.18 (l̄ 4.35) produces a **longer** mean completion
(786.8 tokens) than alpha 0.35 (l̄ 4.45, 569.6 tokens), despite the higher
alpha also giving the higher l̄. Only seen once so far (aime24/humaneval's
`cactus` chosen-alpha sets don't overlap enough to compare the same way);
flagging so it's not missed if the same non-monotonic-length pattern shows
up again on livecodebench/mtbench/longbench_v2.

## Lossless (`strict`) reference, where it exists yet

Only `humaneval` has it so far (added mid-campaign, gsm8k/aime24 backfill
still pending -- see `campaign/JOURNAL.md`): l̄ 2.50, completion length
674.2 tokens. Sits *below* every lossy method's low-end l̄ on humaneval
except `spec_casc_tok` (2.22) and `mentored_dec` (2.20) -- i.e. even the
"gentlest" relaxation tested for most methods already accepts more than
lossless verification does, which is the expected direction (relaxation
exists to raise acceptance) but useful as a sanity check that the grids
are calibrated on the correct side of strict.

## Caveat

3 of 6 datasets. `gsm8k`/`aime24` are both math-reasoning-flavoured;
`humaneval` is the first code dataset and already shows `cactus` collapsing
for the first time -- worth checking whether `livecodebench` (also code)
repeats that, or whether it's humaneval-specific.
