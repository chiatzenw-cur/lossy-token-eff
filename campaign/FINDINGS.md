# Findings: per-method behaviour across the l̄-matched sweep

Cross-dataset observations about how each method's alpha actually behaves,
as opposed to `campaign/PLAN.md`'s a-priori design. Not a substitute for
the graphs/results CSVs -- this is the narrative of *why* they look the
way they do.

**Basis (rewritten 2026-08-22)**: all 6 GPT-OSS-20B datasets, complete.
This replaces an earlier version of this section written mid-campaign on
3 of 6 datasets (gsm8k, aime24, humaneval) and never re-audited against
the final run -- every table and statistic below was recomputed directly
from `campaign/calibration/*.json`, `campaign/results/*.csv`, and
`campaign/tables/*.csv` as they stand now, not carried forward from the
earlier draft. Two things changed on re-verification, noted where they
occur below: the "weaker, single-instance" cactus observation turned out
to recur on 4 of 6 datasets, and the floor sign-test has a real gap
(`spec_casc_opt` contributes zero comparisons -- its own calibration-grid
floor alpha was never among its chosen full-sweep alphas on any of the 6
datasets, not just the 3 originally checked).

## Headline: cactus and spec_casc_tok jointly define the shared comparison band, on every one of the 6 datasets

`campaign_run.py`'s target-selection rule intersects every method's
achievable l̄ range: `[max of per-method minimums, min of per-method
maximums]`. On all 6 finished datasets, that intersection is set by the
*same two methods*, no exceptions:

| dataset | band floor (= max of mins) | band ceiling (= min of maxs) |
|---|---|---|
| gsm8k | **cactus** @ 3.50 | **spec_casc_tok** @ 3.26 |
| aime24 | **cactus** @ 3.07 | **spec_casc_tok** @ 2.62 |
| humaneval | **cactus** @ 3.04 | **spec_casc_tok** @ 2.63 |
| livecodebench | **cactus** @ 3.08 | **spec_casc_tok** @ 2.80 |
| mtbench | **cactus** @ 4.25 | **spec_casc_tok** @ 2.03 |
| longbench_v2 | **cactus** @ 3.87 | **spec_casc_tok** @ 2.12 |

(Floor > ceiling in every row before the code's own fallback-to-global-span
kicks in -- see `pick_targets_and_alphas()` -- so the *effective* targets
end up spanning the global min/max instead, but the mechanism is the same:
these two methods are always the ones setting the boundary, on all 6
datasets now, not just the 3 this was originally checked against.)
Concretely: `cactus`'s *weakest* relaxation (lowest alpha tried) already
produces a higher l̄ than any other method can reach at its own lowest
alpha, and `spec_casc_tok`'s *strongest* relaxation (highest alpha tried)
still can't reach as high an l̄ as any other method's highest alpha.
`mentored_dec`, `spec_casc_opt`, and `r_fuzzy` always have slack on both
ends -- their ranges sit inside the cactus/spec_casc_tok envelope, not
past it, on every dataset.

## Per-method achievable l̄ range (4-point calibration grid, 3 probe cases)

| method | gsm8k | aime24 | humaneval | livecodebench | mtbench | longbench_v2 |
|---|---|---|---|---|---|---|
| `mentored_dec` | [3.20,3.88] 0.68 | [2.42,3.23] 0.81 | [2.20,3.25] 1.05 | [2.35,3.39] 1.04 | [2.29,4.19] 1.90 | [1.76,3.00] 1.24 |
| `cactus` | [3.50,4.18] 0.68 | [3.07,4.40] 1.33 | [3.04,4.15] 1.11 | [3.08,4.32] 1.24 | [4.25,5.48] 1.23 | [3.87,5.24] 1.36 |
| `spec_casc_opt` | [3.24,4.07] 0.83 | [2.66,3.32] 0.66 | [2.45,3.21] 0.76 | [2.77,3.34] 0.57 | [2.54,3.51] 0.97 | [2.08,2.61] 0.53 |
| `r_fuzzy` | [2.90,4.07] **1.17** | [2.21,3.67] **1.45** | [2.33,3.51] **1.18** | [2.32,3.67] **1.35** | [2.05,4.69] **2.64** | [1.59,3.44] **1.85** |
| `spec_casc_tok` | [2.82,3.26] **0.44** | [2.42,2.62] **0.20** | [2.22,2.63] **0.41** | [2.38,2.80] **0.42** | [1.70,2.03] **0.33** | [1.64,2.12] **0.49** |

(`[min,max] span` per cell.) `spec_casc_tok` is the narrowest-range method
on all 6 datasets, by a wide margin every time (span 0.2-0.49 vs.
everyone else's 0.53-2.64); `r_fuzzy` has the widest range on all 6, also
without exception. `spec_casc_tok`'s grid is non-monotonic in alpha on 2
of 6 (gsm8k, humaneval -- l̄ dips at the second alpha before recovering,
e.g. gsm8k: 3.14 -> 2.82 -> 2.83 -> 3.26) -- consistent with the mechanism
note already in `analysis/semantic_guard/README.md` (`spec_casc_tok`'s
out-of-trusted-set tokens are *more conservative than lossless*, not a
smooth knob).

## Consequence: chosen-alpha collapse (fewer than 3 comparison points)

Because `pick_targets_and_alphas()` dedupes when 2 targets both land on
the same nearest grid point, a method with a narrow range regularly
contributes only 2 comparison points instead of 3 (visibly fewer
dots/markers on that method's line in the graph):

| method | gsm8k | aime24 | humaneval | livecodebench | mtbench | longbench_v2 |
|---|---|---|---|---|---|---|
| `spec_casc_tok` | 2/3 | 2/3 | 2/3 | 2/3 | 2/3 | 2/3 |
| `spec_casc_opt` | 3/3 | 2/3 | 2/3 | 2/3 | 2/3 | 3/3 |
| `cactus` | 3/3 | 3/3 | 2/3 | 3/3 | 3/3 | 3/3 |
| `mentored_dec`, `r_fuzzy` | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |

`spec_casc_tok` collapses to 2/3 on **all 6** datasets, no exceptions --
this is now a settled property of the method on this model, not an early
pattern. `spec_casc_opt` collapses on 4 of 6 (every dataset except gsm8k
and longbench_v2). `mentored_dec` and `r_fuzzy` have never collapsed on
any dataset -- consistent with them never being the band's floor or
ceiling either.

## Statistical backing for the headline

The headline claim above is about *means* (12-case averages per point).
Those means are cleanly separated, but individual cases are noisy (l̄
std ≈ 0.2-0.5 per point, comparable in size to the gaps between methods'
means) -- so a mean-vs-mean comparison alone doesn't establish that cactus
genuinely runs "ahead" of the other methods case-by-case, only that it
does so on average. Fixed with a **paired per-case sign test**: the same
12 prompts (`case_001..012`) were run under every method/alpha, so for
each case the l̄ from method A's extreme alpha can be compared directly
against method B's, cancelling out the (large) per-prompt variance that
dominates the raw std. Exact two-sided binomial test against p=0.5.

**Floor claim** -- cactus's *lowest* tested alpha vs every other method's
own lowest tested alpha, same 12 cases, paired. `spec_casc_opt` is absent
from every row: its own lowest calibration-grid alpha was never among its
chosen full-sweep alphas on any of the 6 datasets (see the collapse table
above -- it only ever gets 2-3 of its 4 grid points fully run), so there's
no 12-case data to pair it against:

| dataset | vs. mentored_dec | vs. r_fuzzy | vs. spec_casc_tok |
|---|---|---|---|
| gsm8k | 10/12, p=.039 | 2/3, p=1.000 | 3/3, p=.250 |
| aime24 | 12/12, p<.001 | 12/12, p<.001 | 12/12, p<.001 |
| humaneval | 11/12, p=.006 | 12/12, p<.001 | 3/3, p=.250 |
| livecodebench | 12/12, p<.001 | 12/12, p<.001 | 12/12, p<.001 |
| mtbench | 10/12, p=.039 | 3/3, p=.250 | 12/12, p<.001 |
| longbench_v2 | 12/12, p<.001 | 3/3, p=.250 | 11/12, p=.006 |

**Pooled: cactus wins 164/171 (95.9%) of all paired case comparisons it
has data for.** Direction is unanimous everywhere (never a losing majority
in any cell); several cells only have n=3 because that dataset's own
comparison method also collapsed to 2 chosen alphas and the *particular*
low alpha being compared only ran its 3 probe cases, not the full 12 --
those cells are individually weak (p=.25 at n=3 can't reach significance)
but every one still points the same direction as the significant ones.

**Ceiling claim** -- every other method's *highest* tested alpha vs.
spec_casc_tok's own highest tested alpha, same 12 cases, paired (positive
= the other method beats spec_casc_tok, as claimed):

| dataset | mentored_dec | cactus | spec_casc_opt | r_fuzzy |
|---|---|---|---|---|
| gsm8k | 10/12, p=.039 | 11/12, p=.006 | 12/12, p<.001 | 11/12, p=.006 |
| aime24 | 12/12, p<.001 | 3/3, p=.250 | 12/12, p<.001 | 12/12, p<.001 |
| humaneval | 12/12, p<.001 | 12/12, p<.001 | 11/12, p=.006 | 12/12, p<.001 |
| livecodebench | 12/12, p<.001 | 3/3, p=.250 | 12/12, p<.001 | 12/12, p<.001 |
| mtbench | 12/12, p<.001 | 12/12, p<.001 | 11/12, p=.006 | 12/12, p<.001 |
| longbench_v2 | 11/12, p=.006 | 12/12, p<.001 | 11/12, p=.006 | 12/12, p<.001 |

**Pooled: the other 4 methods win 262/270 (97.0%) of all paired case
comparisons against spec_casc_tok at its own most-relaxed setting.**
Direction is unanimous everywhere; the two n=3 cells (`cactus` vs.
aime24/livecodebench, where cactus's own highest alpha wasn't in the
chosen set on those two datasets) don't reach significance alone but
agree with the direction every other cell already establishes.

**Reproduce**: per-case l̄ values are in `campaign/tables/<dataset>.csv`
(`method`, `params`=`alpha<value>`, `case`, `l_bar` columns); the exact
(method, alpha) pairs compared above are each method's min/max
`mean_l_bar` row in `campaign/calibration/<dataset>.json`'s `grid_results`.
No new data collection needed -- this reuses runs already in the sweep.

**Caveat for the paper**: n=12 cases/dataset where the full sweep ran,
n=3 for cells where the comparison alpha only got probe-stage data (see
above) -- report the pooled figures with that split noted, not as if
every cell were independently significant.

## Cactus's completion length is not monotonic in l̄ -- a real, recurring pattern, not a fluke

An earlier draft of this section flagged one instance of this on gsm8k and
called it "watch for repeats." Rechecked directly against all 6 datasets:
it recurs on **4 of 6** (gsm8k, aime24, mtbench, longbench_v2) -- only
humaneval and livecodebench are cleanly monotonic. Example (longbench_v2):
alpha 0.18 (l̄ 4.46) produces a *shorter* mean completion (1862 tokens)
than alpha 0.03 (l̄ 3.51, 2197 tokens), despite the higher alpha giving the
higher l̄; gsm8k shows the same shape in the other direction (0.18 longer
than 0.35 despite lower l̄). This is now a real property of `cactus`
worth explaining, not noise: higher l̄ (more tokens accepted per
verification round) doesn't reliably predict shorter completions, because
completion length is also downstream of what the model chooses to say
once relaxation changes which tokens land -- the two are correlated but
not causally identical the way "more accepted per round -> fewer rounds
-> shorter wall time" often gets assumed.

## Lossless (`strict`) reference, all 6 datasets

| dataset | l̄ | completion length | accuracy |
|---|---|---|---|
| gsm8k | 2.69 | 273 | 1.000 |
| aime24 | 2.22 | 9090 | 0.750 |
| humaneval | 2.50 | 674 | 1.000 |
| livecodebench | 2.19 | 3747 | 0.083 |
| mtbench | 2.30 | 1689 | n/a (ungraded, no LLM-judge infra) |
| longbench_v2 | 1.81 | 1470 | 0.750 |

Strict's own l̄ sits below every lossy method's low-end l̄ on every dataset
except `spec_casc_tok` and (on some datasets) `mentored_dec` -- i.e. even
the "gentlest" relaxation tested for most methods already accepts more
than lossless verification does, which is the expected direction
(relaxation exists to raise acceptance) and holds as a sanity check that
the grids are calibrated on the correct side of strict, on all 6.
`livecodebench`'s accuracy floor (0.083, 1/12) is the one dataset where
even the lossless baseline struggles -- a real property of the benchmark
at this scale, not something the lossy methods introduce (see the
Qwen3-8B section below for the same benchmark showing the identical
pattern on a different model).

*(Note added 2026-08-22: both this section and the Qwen3-8B section below
are now current against their respective complete 6-dataset runs.)*

## Qwen3-8B + drafter: full 6-dataset campaign, real per-method behaviour (2026-08-22)

Supersedes two earlier, both-wrong attempts at this section: the first
(retracted 2026-08-19, see `campaign/JOURNAL.md`) was a silent sampling-
config bug (Qwen3's own `generation_config.json` overriding this
campaign's actual temperature/top_p); the second never got written up
before the run underneath it turned out to need a further architectural
fix (all five methods' patches only ever touched vLLM's "V1" rejection
sampler, but Qwen3-8B routes speculative-decoding verification through the
newer "V2" GPU model runner path exclusively -- see `campaign/JOURNAL.md`'s
2026-08-20/21/22 entries for the full port and the three further patch-
switching bugs it took to make it reliable across a real unattended run,
plus a fourth, unrelated CUDA crash bug on `longbench_v2_qwen3`'s longest
cases, fixed 2026-08-22). This section is grounded in the run that finally
landed clean: all 6 datasets, `campaign_report.py`'s own scoring
cross-checked against each dataset's independent grader where one exists.

**Headline: which methods actually preserve accuracy, not just which are
fastest.** For each dataset, call a (method, alpha) point a **free win** if
its accuracy is at or above `strict`'s own -- i.e. it costs nothing to
adopt. Counting free wins across the 5 accuracy-graded datasets (mtbench
has no grader, see below):

| method | free wins (of 5) | where |
|---|---|---|
| `mentored_dec` | **4/5** | gsm8k, aime24, humaneval, longbench_v2 (all at its own highest tested alpha, 0.75) |
| `spec_casc_tok` | **4/5** | gsm8k, aime24, humaneval, longbench_v2 (all at its own highest tested alpha, 0.8) |
| `spec_casc_opt` | 3/5 | gsm8k, aime24, humaneval (all at its own gentlest/most-conservative alpha) |
| `r_fuzzy` | 3/5 | aime24, humaneval, longbench_v2 (all at its own gentlest alpha) |
| `cactus` | 1/5 | humaneval only |

`mentored_dec` and `spec_casc_tok` are the two methods that reliably don't
cost accuracy on this model/drafter pair -- and notably, both do so at
their *most* relaxed tested alpha, not a timid one: 1.04x-1.21x l̄ speedup
"for free" wherever they land a win. `cactus` is the opposite profile: it
wins on only 1 of 5 graded datasets, but see below for why it's still the
right choice when speed, not accuracy-matching, is the actual goal.

**`cactus` has by far the largest speed ceiling of any method, if accuracy
parity isn't required.** Best l̄ speedup at any tested alpha, per method,
per dataset (mtbench included since this doesn't need accuracy grading):

| method | gsm8k | aime24 | humaneval | livecodebench | mtbench | longbench_v2 |
|---|---|---|---|---|---|---|
| `mentored_dec` | 1.14x | 1.21x | 1.14x | 1.19x | 1.29x | 1.15x |
| `cactus` | 1.21x | **3.46x** | 1.20x | **2.26x** | **2.65x** | **4.96x** |
| `spec_casc_opt` | 1.42x | 1.72x | 1.79x | 1.31x | 1.48x | 1.90x |
| `r_fuzzy` | 1.36x | 1.16x | 1.46x | 1.37x | 1.64x | 1.27x |
| `spec_casc_tok` | 1.04x | 1.12x | 1.07x | 1.09x | 1.12x | 1.11x |

`cactus` is the only method that ever breaks 2x, and it does so on 4 of 6
datasets (aime24, livecodebench, mtbench, longbench_v2) -- everyone else
tops out under 1.9x everywhere. This tracks its own alpha semantics
(`gamma_x = p(x) + sqrt(2*alpha*p(x)*(1-p(x)))`, a variance-scaled
widening of the accept band with no upper clamp until saturation) against
the other four methods' bounded threshold tests. The cost: `cactus`'s
speed and its accuracy loss both scale together with alpha (e.g.
longbench_v2: 1.68x/66.7% -> 2.98x/58.3% -> 4.96x/50.0% across its own
3-point grid) -- there is no free lunch at the high end, `cactus` genuinely
trades accuracy for l̄ the whole way up, unlike `mentored_dec`/
`spec_casc_tok` whose best alpha for speed and best alpha for accuracy
frequently coincide.

**`livecodebench_qwen3`: no method gets a free win, on any dataset-method
pair.** `strict` itself only reaches 2/12 (16.7%) on this benchmark --
investigated directly (independent grader cross-check, per-case failure
tracing) and confirmed genuine: LiveCodeBench is hard enough at this model
scale and 12000-token budget that several cases never finish reasoning in
budget, and several more produce code that runs but is simply wrong. Every
lossy method's own accuracy sits at or below `strict`'s already-low floor
-- there's no "safe" alpha to recommend here, on any method, at this
budget. Worth revisiting with a larger token budget before concluding the
methods themselves are the problem.

**`mtbench_qwen3` has no accuracy grader** (needs an LLM-judge; no
infrastructure for one exists yet, a known, documented gap -- see
`scripts/campaign_report.py`'s own `GRADERS` dict comment). Only the l̄/
speed columns above are available for it; treat any claim about mtbench
quality as unverified until a judge exists.

**Caveat**: same alpha grids as GPT-OSS-20B's own `campaign/PLAN.md`
(reused as-is, by design, per `campaign/JOURNAL.md`'s 2026-08-17 entry),
n=12 cases/dataset, 5 of 6 datasets graded. `cactus`'s free-win count
(1/5) reflects this specific grid's 4 tested alphas, not necessarily
every alpha in its space -- a gentler grid point below its own tested
floor might recover more free wins at the cost of a smaller speed ceiling;
not tested here.

**Reproduce**: `campaign/results/<dataset>_qwen3.csv` has one row per
(method, alpha) with `mean_l_bar`/`mean_completion_length`/`accuracy`
columns; `strict`'s own row in the same file is the baseline every
comparison above is against.
