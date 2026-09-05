# autoguard autoresearch loop — findings (2026-09-02/03)

Full narrative below; the one-line summary: **the loop ran 11 iterations,
found a guard that cut mean completion length 21.2% on its 8-case tuning
set, and that guard turned out to be a pure overfitting artifact — it
makes the full 30-case AIME24 set 11.8% *longer*.** No guard config from
this run should be adopted. See `autoresearch/results.tsv` for the raw
per-iteration log and `git log` on this branch for full commit-message
detail on every iteration.

## 1. Setup

`autoresearch/evaluate.py` scores `patches/autoguard.py::decide()` — a
per-verification-round boolean mask (`True` = force lossless verification
at that drafted position) — against a fixed 8-case AIME24 subset (cases
001–008), objective = minimise mean completion tokens subject to
`accuracy >= baseline_accuracy - 1/8`. Baseline (`spec_casc_tok`, α=0.3,
these 8 cases): **6/8 correct, mean 13,364 tokens**. Two of the eight
(case_003, case_004) hard-cap at 32,768 tokens without ever opening their
harmony `final` channel — together they're 65.5k of the 106.9k token
total, so from the start the biggest lever was "make the runaway cases
terminate," not "shave a little off every case."

## 2. The 11-iteration loop (tuning set: cases 1–8)

| iter | change | score | acc | kept |
|---|---|---:|---:|---|
| 1 | future-guard K=8 (force strict on the 8 drafted positions after an accepted hesitation/discourse marker; wide 38-id marker set) | 13,056 | 6/8 | ✅ |
| 2 | + gate the window to only arm past 6,000 committed tokens | 13,496 | 6/8 | ✗ — killed case_002's beneficial *early* window |
| 3 | narrow the marker set to 18 genuine-hesitation ids (drop discourse connectives) | 10,397 | **4/8** | ✗ FAILURE — the connectives are load-bearing inside two spirals |
| 4 | iter1 + a full-strict "stuck-run" backstop (>24,000 committed tokens with no `final` channel open → force the whole block strict; provably lossless) | 12,626 | 6/8 | ✅ |
| 5 | widen the window to K=12 | 15,117 | 5/8 | ✗ — rescued case_003 to a *correct* answer for the only time in the whole run, but broke two healthy cases |
| 6 | pull the backstop threshold in to 14,000 | 12,062 | 6/8 | ✅ |
| 7 | **cluster-gate the window trigger**: a marker only (re)arms a window when ≥2 markers fall within the last 32 tokens | **10,534** | **6/8** | ✅ **best-on-8-cases** |
| 8 | iter7 + K=12 | 7,829 | 5/8 | ✗ — sits exactly on the accuracy floor, one case flipped |
| 9 | iter7 + K=12 + a stricter cluster gate (≥3/32) | 16,023 | 4/8 | ✗ FAILURE — K=12 is uncontrollable at any gate threshold |
| 10 | backstop threshold →12,000 | 12,969 | 6/8 | ✗ — earlier full-strict *locks* the stuck cases into non-termination instead of fixing them |
| 11 | backstop disabled entirely | 10,702 | 6/8 | ✗ — 168 tokens worse than iter7 (noise-level), at less than half the fire rate |

iter7 was confirmed to reproduce bit-identically on a clean-install rerun
(fresh-server determinism holds in this repo).

### Mechanistic takeaways from the loop itself

- The **wide discourse-connective set is load-bearing** inside the
  spiraling cases — narrowing it to "genuine" hesitation words breaks
  accuracy on cases that were fine before (iter3).
- **K=8 windows are controllable; K=12 is not.** The same window mechanism
  that behaves predictably at K=8 becomes chaotic at K=12 — it can rescue
  a stuck case (iter5 got case_003 to a correct answer, the only time
  this happened anywhere in the investigation) but destabilises healthy
  trajectories unpredictably, and no cluster-gate threshold tames it
  (iter8/iter9).
- **Forcing full strict does not reliably shorten a non-converging run —
  it can lock it further into non-termination** (iter10: pulling the
  backstop earlier made two terminating cases re-cap). The thing that
  actually got stuck cases moving was window *perturbation* (iter5, iter7
  as a side effect), not verification strictness per se.
- The full-strict backstop's net contribution is marginal: iter7 (backstop
  at 14,000) vs iter11 (backstop off) differ by only 168 tokens (noise on
  n=8) while more than doubling the fire rate (0.358 vs 0.154).

## 3. Full 30-case AIME24 validation — iter7 does not generalize

| | baseline `spec_casc_tok` | iter7 guard | Δ |
|---|---:|---:|---:|
| mean completion tokens (30 cases) | 9,270 | **10,363** | **+11.8% (longer)** |
| held-out cases 9–30 only | 7,781 | 10,301 | **+32.4% (longer)** |
| accuracy | 22/30 | 23/30 | +1 (noise at this n) |

The −21.2% headline was an 8-case artifact. On held-out cases the guard
mostly *inflates* length — the exact failure it was built to fix:

- case_019: 10,752 → 25,062 (+14,310)
- case_029: 14,862 → 31,961 (+17,099)
- case_026: 16,996 (terminated) → 32,768 (cap) — the guard turned a
  terminating-but-wrong run into a non-terminating one
- case_021 +4,735, case_018 +5,820, case_022 +3,219
- Only two held-out cases improved meaningfully: case_017 −4,046,
  case_027 −3,156
- One accuracy flip in the guard's favour: case_013 wrong → correct

This reproduces, independently, `analysis/semantic_guard/`'s own standing
conclusion (reached by hand, on a different — though overlapping —
set of guard designs): **no guard beats vanilla `spec_casc_tok` at
α=0.3** on accuracy-preserving grounds.

## 4. Side experiment: periodic self-check + pivot (not the autoguard loop)

Prompted by "periodically remind the model of its subgoal" — `decide()`
cannot inject tokens (mask-only contract), so this was tested via the
existing, separately-frozen `spec_casc_tok_self_check` arm instead
(periodic forced injection of *"Wait, let me pause and check: am I going
in circles here, making no real progress? Answer yes or no:"*, reading
the model's own unconstrained answer, pivoting to *"Yes -- I am going in
circles. Let me abandon this approach and restart with a cleaner, more
direct method."* on "yes"). 8-case tuning set, α=0.3:

| interval (real tokens between checks) | mean tokens | Δ | accuracy |
|---:|---:|---:|---:|
| 3,000 | 9,181 | −31.3% | **4/8** FAILURE |
| 6,000 | 11,472 | −14.2% | 5/8 |
| 10,000 | 11,838 | −11.4% | 6/8 (clean) |

Shorter interval = more length cut, more spurious pivots away from
*productive* reasoning — case_002 (correct at baseline, 20,070 tokens)
is the persistent casualty at intervals 3,000 and 6,000. Even at the one
interval where accuracy survives, the length cut is roughly half of
iter7's (and iter7 itself didn't generalize). Not adopted. This confirms,
independently, the `self_check` patch's own module-comment warning that
asking the model "am I stuck?" doesn't reliably separate productive from
unproductive generation — the same conclusion the manual investigation
reached testing five *other* structural signals (entropy ramp, confidence
dip, hesitation density, hidden-state recurrence, canonical-template
periodicity).

## 5. Why this genre of guard is probably close to a dead end

Three independent lines of evidence now point the same way:

1. **The metric is dominated by a few outlier cases.** AIME24 completion
   length has enormous case-to-case variance — a single case flipping
   between "terminates at 17k" and "caps at 32,768" moves an 8-case mean
   by 2,000 tokens and a 30-case mean by 500+. Any adaptive search against
   an 8-case mean (11 iterations of hill-climbing, in this run) will find
   configurations that fit that specific sample's noise, not a real
   effect — which is exactly what happened.
2. **The mechanism doesn't support the intervention.** Forcing strict
   verification at a hesitation marker doesn't suppress hedging, it
   redirects *which* hedge word appears (documented in
   `analysis/semantic_guard/SUMMARY.md` sec. 5); the length blow-up is a
   round-count effect, not a per-round acceptance-rate effect (l̄ barely
   moves under any guard tried); and outcomes are chaotically sensitive to
   small parameter changes (K=8→12) even on cases the change wasn't aimed
   at. A local per-token accept/reject rule is trying to steer a global,
   semantic property (does this trajectory converge) that it structurally
   can't see.
3. **Two independent search processes reached the same wall** — the
   manual `analysis/semantic_guard/` investigation (many hand-designed
   guards, full 30-case sweeps) and this autonomous loop (11 adaptive
   iterations, validated post-hoc) both conclude that no strict/relaxed
   masking guard beats vanilla `spec_casc_tok` at α=0.3 without a real
   accuracy cost.

## 6. Recommended next steps (not yet run)

**A. Fix the measurement before searching over masks again**, if that
path is worth continuing at all:
- Tune against the full 30 cases from the start (not an 8-case proxy with
  a post-hoc check) — ~5x eval cost per iteration, but the 8-case number
  has just been shown to carry no signal.
- Score on a statistic robust to the 1–3 cap-hitting outliers — trimmed
  mean, median, or mean of per-case log-ratios — instead of the raw mean,
  which a single case-level cap/no-cap flip can dominate.
- If the harness supports multiple seeds per case, average 2–3 to reduce
  per-trajectory noise before trusting any delta.

**B. Switch intervention class instead of searching harder in the same
one.** The single biggest lever in every run so far is the handful of
cases that hit the 32,768 cap without ever opening a final-channel
answer (case_003, 004, 014, 026, 029 across the two sweeps here) — they
are wrong either way, so fixing them is free on accuracy, and they're
each worth 1,000+ tokens on any mean. This is a "never commits" failure,
not an acceptance-rule failure, and the repo already has a
purpose-built, frozen mechanism for exactly this:
**`spec_casc_tok_force_commit`** (force-injects the harmony
`final`-channel-open boundary once a token budget is crossed without one
occurring naturally). It should be near-surgical — a no-op on the ~25
healthy cases, active only on the pathological few — which is the shape
of intervention likeliest to survive a full 30-case check, unlike a
marker-based guard that reshapes every trajectory it touches.
`decide()` cannot express this (no token injection in its contract), so
testing it means running the existing `spec_casc_tok_force_commit` arm
directly via `scripts/fresh_server_replay.py`, not editing
`patches/autoguard.py`.

This is the next thing tried — see the `force_commit` section appended
below (or the corresponding `results.tsv` / git history) once it lands.
