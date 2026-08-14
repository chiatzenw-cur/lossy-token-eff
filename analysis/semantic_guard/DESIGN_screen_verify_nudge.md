# Design: verify → nudge (screen dropped, see amendment)

Status: design doc, written before implementation, THEN corrected after
an empirical finding invalidated the "screen" stage. Original 3-stage
design (screen → verify → nudge) is kept below for the record, followed
by the amendment that supersedes it. Every claim cites the specific
finding it rests on; none of this is aspirational.

## AMENDMENT: the screen stage doesn't work, cost is paid unconditionally

**Empirical test, not just code-reading**: free-judgment's own
`gpu_model_runner.py` overwrite was made conditional (fire 1/20 rounds,
`num_speculative_tokens` left at the same fixed 29). Result: **0.02807
s/round — statistically identical to the always-forced-content baseline
(0.02799 s/round)**, nowhere near the genuinely-narrow baseline (0.01250
s/round). Making 19/20 rounds' *content* idle saved nothing, because
`num_speculative_tokens` is a static, server-startup-fixed config value —
the *scheduler*, not our patch, decides how many tokens get verified each
round, and it schedules the full configured width regardless of what our
patch puts in those columns. There is no live per-round lever to make
some rounds cheap and others expensive within this repo's established
patch scope (`gpu_model_runner.py`'s content-overwrite hook +
`rejection_sampler.py`).

**Decision (explicit, made by the user after this finding): accept the
cost.** RV's own blend was already priced at ~150%/round unconditionally
from the start — that was never contingent on screening working. Drop
the screen stage entirely; run the judge every round (same structural
cost free-judgment always paid), and gate NUDGE on the judge's own
per-round confirmation, same as free-judgment's original reject-and-
resample trigger shape, but with the two most validated pieces from this
whole investigation swapped in: the best-performing judge phrase (TRUE/
FALSE + completion scaffold, tested against 48 ground-truth points, best
of six phrasings), and RV's ephemeral blend as the actuator (instead of
plain reject-and-resample, which the case_010 causal trace showed
doesn't work: resampling from an *unmodified* target barely moves a
stuck state).

The rest of this document (signal handling, state machine, build plan)
is updated to the 2-stage design below. The original screen-based cost
model section is left in place afterward, struck through in spirit if
not in markdown, as a record of what didn't work and why.

## Why this design, not another judge-every-round mechanism

Two facts, both established on real data, drive this:

1. **Widening the verification span costs real time regardless of what's
   in it.** A width-only control (`spec_casc_tok`, `num_spec` 6→29, zero
   forced tokens) cost **+123.9% wall-time/round**. free-judgment's own
   criterion append cost +150%. This tax is paid *every round the span is
   widened*, independent of phrasing quality — a better prompt does not
   reduce it.
2. **A per-round judge, however phrased, is thin evidence.** Five
   structurally different criterion phrasings (compound-question,
   unambiguous+anchored, repetition-focused, TRUE/FALSE, TRUE/FALSE with
   completion scaffold) were tested against 48 points with **real
   ground-truth labels** (24 hand-labeled recurrence events + 9 confirmed
   literal-repeat points + 15 regular clean samples). Only the last
   (TRUE/FALSE + "the answer is:" scaffold) showed a positive-direction
   gap, and it's built on n=3 confirmed reasoning-loop examples. Real, but
   thin — not something to trust unconditionally every round forever.

So: **don't pay the width tax every round.** Screen first, cheaply, using
a signal that doesn't need a widened span at all. Only pay for the judge
when the screen is suspicious. Only act (and only gently) when the judge
confirms.

## The signals, and what happens with each

### 0. Screen: hidden-state recurrence — DROPPED, kept for the record

Everything below this subsection describes the screen as originally
designed. **It is not built.** See the amendment at the top: there is no
live lever to make some rounds cheap and others expensive within this
repo's patch scope, so a screen that only saves cost when it *doesn't*
fire has nothing to save. The hidden-state-recurrence precision findings
themselves (case_002, case_004) remain real and could still motivate a
*different* use (e.g. an offline diagnostic, or a future design that
finds an actual cost lever) — just not this one.

### 1. Screen: hidden-state recurrence (cheap, every round) [dropped, see above]

**What it is.** `target_hidden_states` — the concatenated EAGLE3
aux-hidden-state layers — is already computed every round in
`gpu_model_runner.py`, immediately before `self.drafter.propose(...)`
(this is the exact tensor `hidden_state_trace.py` captures). It costs
nothing extra to *read*; the only new cost is a cheap projection +
cosine-similarity comparison against a rolling history buffer, both pure
tensor ops on an already-materialized tensor.

**Validated precision, not just plausibility.** Two independent real
cases:
- case_002 (strict decoding, the one case that hit the cap unresolved):
  hand-labeled top-3-longest-streak candidates split **3/3 real
  `reasoning_loop`** in the failing case vs **0/63 in the 7 successful
  cases** — a real precision result on retrospective event flagging.
- case_004 (rambling probe, no_answer at the capture's own 14k-token
  budget): 13 flagged recurrence events, **11 of which cluster into one
  confirmed genuine stuck-recomputation episode** (repeatedly re-deriving
  `f(0.284)`, `f(0.2845)`, ... by hand without converging).

**Known gap, disclosed not hidden.** Both validations are *retrospective*
(computed after the fact from a saved capture) and used the *last row of
`target_hidden_states`* as a proxy for "this round's real committed
state" — which is only exactly correct when the whole round's real
positions get accepted (same caveat free-judgment's own criterion-read
already carries and discloses; not a new corner cut). Never tested live,
never tested under our own induced failures (case_010/014/026 — which
can't be tested this way regardless, since they only fail *because of*
our own intervention, not natively).

**What happens with the signal:** self-calibrated per-run threshold
(same convention as `find_hidden_state_recurrence_onsets.py`: top
percentile of *this run's own* S_k distribution so far, gated on a
minimum reading count before the percentile is trusted — mirrors
`MIN_READINGS` from every earlier trend-based design in this repo, for
the same reason: an immature baseline reads as spuriously "diverged"
against the very next value). Crossing it **arms VERIFY for the next
round only.** It does not itself touch `target_probs` or cost any width.

### 2. Judge: the TRUE/FALSE criterion (expensive, every round — accepted)

**What it is.** Same "extended verification span" trick as
free-judgment/RV: append the criterion after the real draft, read the
target's own judgment from the same forward pass, at marginal FLOPs cost
— except now gated, not unconditional.

**Phrase**, the best-performing of six tested, exact text validated last
turn:

    \n\nThe last few tokens are unproductively repetitive. Answer TRUE or FLASE: the answer is:

(Yes, "FLASE" — literally what was tested and validated; the model reads
past the typo fine, and re-spelling it is untested, not "the same,
presumably".)

**What happens with the signal:** `score = p_true - p_false` at the
judgment position, read every round. If `score > JUDGE_THRESHOLD` (own
knob, starting point TBD from a live calibration pass, analogous to
free-judgment's own 0.08): **arms NUDGE for the next `NUDGE_WINDOW`
rounds.** If not: stays in JUDGE mode, reads again next round — no
forced action, no persisted state beyond the threshold check itself.

**Honest gap.** n=3 reasoning-loop examples. This is real signal (best of
six phrasings, by a clear margin, and specifically strongest on the
category that matters), not a coin flip — but three is three.

### 3. Nudge: RV-style ephemeral logit blend (bounded window, only on confirmation)

**What it is.** Already built and mechanically verified this session
(`patches/vllm-0.26.0-rv-model-runner.patch` +
`patches/vllm-0.26.0-spec-casc-tok-rv.patch`): duplicate the real draft
tokens after a fixed "keep going, don't restart" reflection prompt,
blend `z_mix = (1-alpha)*z0 + alpha*z_reflect` at the **logit** level
into `target_probs` at the real positions, feeding both the accept test
and the recovery/residual draw. Never committed to persistent context —
closes the exact gap that broke plain reject-and-resample (proven via
the case_010 causal trace: resampling from an *unmodified* target
distribution barely moves a stuck state; a rejected token there needs to
be resampled from a distribution that's already nudged, not the same one
that produced the bad draft).

**What happens with the signal.** Runs unconditionally for
`NUDGE_WINDOW` rounds (fixed small integer, e.g. 3-5 — a bounded window,
not another judgment call, deliberately: this investigation has shown
every attempt to *decide when to stop* nudging via a threshold hits the
same wall as everything else. A fixed window sidesteps that specific
failure mode, at the cost of not adapting duration to need). After the
window, mode returns to IDLE unconditionally, regardless of whether the
judge would now say TRUE or FALSE — no re-verification, no early exit.

**Honest gap.** RV's own blend has *never been run live* — mechanically
verified (real imports, real-kernel adversarial test showing the blend
changes acceptance), never tested for whether it actually helps a real
generation. This design bets on it; that bet is untested.

## State machine (2-stage, post-amendment)

```
JUDGE (every round) --score > threshold--> NUDGE (fixed N rounds) --window ends--> JUDGE
JUDGE (every round) --score <= threshold--> JUDGE (stays)
```

Two states. `JUDGE` is now the default and active every round (no more
free "IDLE" — the screen that would have made JUDGE cheap doesn't work,
see amendment above). Both states pay the same order of width cost;
`NUM_SPEC` (server config) = `max(REAL_DRAFT_LEN + JUDGE_LEN,
2*REAL_DRAFT_LEN + RV_PROMPT_LEN)` = `max(27, 30)` = **30**, so JUDGE
rounds pay for slightly more width than they strictly need (their own
pattern is only 27 wide) — an accepted, minor inefficiency rather than
building a second knob to avoid it.

## Where each piece of state actually lives

Consistent with this repo's established discipline (`apply()` functions
are pure reads that only ARM something; `update()` functions, gated on
real committed history, are the only place mode transitions happen) —
and with the "patches are self-contained, no cross-patch imports"
convention (constants duplicated literally in both halves, never
imported):

- **Judge state** (reading `p_true`/`p_false`, deciding `NUDGE` vs
  staying in `JUDGE`) lives entirely in `rejection_sampler.py` — it only
  needs `target_probs` at the judgment row, which only exists there.
- **The one genuine cross-file dependency**: `rejection_sampler.py`'s own
  judge decision (arm NUDGE for N rounds, or not) has to reach
  `gpu_model_runner.py`, which decides what to *append* to the next
  round's draft. Bridged via a small file-based signal (same `/tmp`
  knob-file convention used everywhere else in this repo for
  cross-process config, extended here to a per-round runtime signal
  rather than static config): `rejection_sampler.py` writes the
  remaining nudge-round-count after each round; `gpu_model_runner.py`
  reads it before deciding NUDGE vs JUDGE for the upcoming round.

## What gpu_model_runner.py appends, round to round (post-amendment)

```
if nudge_rounds_remaining > 0:
    append RV pattern (reflection prompt + duplicate draft)   # NUDGE
else:
    append TRUE/FALSE judge criterion                          # JUDGE (every round, no gate)
```

No IDLE branch anymore. `nudge_rounds_remaining` is the one piece of
cross-round, cross-file state (written by `rejection_sampler.py` after
reading the judge's score, read by `gpu_model_runner.py` before deciding
what to append) — same file-based bridge described in the original
design, still needed for exactly the reason described there (the judge's
own score only exists in `rejection_sampler.py`, which sees
`target_probs`; `gpu_model_runner.py` doesn't).

## Cost model (post-amendment: accepted, not avoided)

Every round pays the wide-verification tax, JUDGE or NUDGE, no
exceptions — measured directly at ~+150%/round for a comparable width in
free-judgment's own case_008 run (0.08493 s/round vs 0.01250 s/round
narrow baseline). `NUM_SPEC=30` for this mechanism (see state-machine
section). This is the accepted price of having the capability at all;
nothing in this design reduces it. The only variable cost left is
*how often NUDGE fires* — NUDGE's own pattern is only marginally wider
than JUDGE's (30 vs 27), so switching modes doesn't meaningfully change
per-round cost either. Total run cost is dominated by 2-3x fewer rounds
completing in the same wall-clock time, same as free-judgment's own
6-case rollout showed.

## Build plan

1. New patch pair, own name (`spec-casc-tok-judge-nudge`), built on
   spec-casc-tok base — not layered on free-judgment or RV (both
   superseded by this for live-trigger purposes; free-judgment remains
   valid as an *observation-only* patch, untouched; RV's own files remain
   as the standalone always-on-blend alternative, untouched).
2. `gpu_model_runner.py` half: 2-way mode dispatch (append RV pattern if
   `nudge_rounds_remaining > 0`, else append TRUE/FALSE judge criterion).
   No hidden-state buffer, no screen.
3. `rejection_sampler.py` half: judge criterion read + TRUE/FALSE scoring
   (reuse validated logic), RV blend (reuse existing RV logic verbatim),
   mode-transition write-back (`nudge_rounds_remaining`) to the shared
   signal file, gated on real committed history per this repo's own
   state-mutation discipline.
4. Unit tests mirroring established patterns: knob plumbing, apply()
   no-ops correctly per mode, real-kernel adversarial tests for both the
   judge-criterion ban and the RV blend (already-proven patterns, reused
   verbatim where possible).
5. **Before any multi-case rollout**: a single-case smoke test (case_004,
   the case with the most existing evidence — real hidden-state capture,
   real reasoning-loop-shaped stuck behavior) to confirm the pipeline
   doesn't crash, NUDGE fires a sane number of times, and the mechanics
   hold under a real generation — same discipline used for every patch
   this session before committing to a real rollout.
6. Only then: a real multi-case rollout, graded against the same known
   baselines used throughout this investigation (case_003/004/008/010/
   014/026).

## What would falsify this design

- JUDGE essentially never says TRUE across a real run (the n=3 finding
  was noise, not signal) — would show up immediately in the smoke test's
  own trace.
- NUDGE's fixed window helps some cases and actively hurts others the
  way every other acted-on mechanism this session did (reject-and-
  resample: 3 hurt / 1 helped / 2 held, on the same 6 cases) — the real
  multi-case rollout is what actually answers this; nothing here proves
  it in advance.
- Per-round cost comes in meaningfully worse than the ~150% already
  measured for a comparable width (should not happen — same order of
  width as free-judgment's own criterion — but not yet measured for
  *this* mechanism specifically).
