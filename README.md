# lossy-token-eff

Practical evaluation of training-free relaxed speculative decoding methods
(Xia et al. 2026, arXiv:2607.08690) against vLLM 0.26.0 on GPT-OSS-20B +
EAGLE3, following on from `lossy-spec-decode-repetition`'s methodology (see
`patches/README.md` for what's ported vs new, and `remote/ENVIRONMENT.md`
for the environment).

Five relaxed methods (`patches/`) benchmarked against a lossless (`strict`)
control, one fresh server per `(case, arm)` measurement (see
`remote/ENVIRONMENT.md`'s "Fresh server per measurement" section for why
that discipline is load-bearing, not caution for its own sake), seed fixed
at 0, temperature 1.0, top-p 1.0, probabilistic draft sampling.

## Results

### AIME24 (30 cases × 6 arms, 180/180 runs, zero request failures)

| arm | correct | mean accepted length (l̄) | mean completion length | mean verifier rounds | errors/no-answer |
|---|---:|---:|---:|---:|---:|
| strict | 0.767 (23/30) | 2.21 | 10,043 | 3,355 | 3 |
| mentored_dec (α=0.37) | 0.700 (21/30) | 2.67 | 12,318 | 3,544 | 1 |
| cactus (α=0.25) | 0.467 (14/30) | 4.17 | 18,679 | 3,617 | 8 |
| spec_casc_opt (α=0.05) | 0.367 (11/30) | 3.41 | 21,410 | 4,940 | 14 |
| **spec_casc_tok (α=0.3)** | **0.867 (26/30)** | 2.42 | **9,440** | **2,897** | **2** |
| r_fuzzy (α=0.3) | 0.433 (13/30) | 4.13 | 19,506 | 3,831 | 5 |

Full per-run detail: [`runs/aime24_fresh/summary.json`](runs/aime24_fresh/summary.json)

### HumanEval (164 cases × 6 arms, 984/984 runs, 1 transient request failure — backfilled)

| arm | pass@1 | passed | mean accepted length (l̄) | mean completion length | mean verifier rounds |
|---|---:|---:|---:|---:|---:|
| strict | 0.951 | 156/164 | 2.52 | 957 | 290.0 |
| mentored_dec (α=0.37) | 0.951 | 156/164 | 2.99 | 954 | 248.4 |
| cactus (α=0.25) | 0.909 | 149/164 | 4.23 | 1,503 | 289.5 |
| spec_casc_opt (α=0.05) | 0.799 | 131/164 | 3.56 | 1,546 | 344.4 |
| **spec_casc_tok (α=0.3)** | **0.957** | **157/164** | 2.60 | 919 | 268.5 |
| r_fuzzy (α=0.3) | 0.567 | 93/164 | 4.21 | 1,787 | 343.1 |

Full per-run detail: [`runs/humaneval_fresh/summary.json`](runs/humaneval_fresh/summary.json)

### Reading these

- **`spec_casc_tok` is the one clean win, not just a wash.** Beats strict on
  *both* benchmarks — higher accuracy, shorter completions, fewer verifier
  rounds — most pronounced on AIME (0.867 vs strict's 0.767, and the fewest
  errors of any arm including strict). Every other lossy method costs
  accuracy for extra acceptance somewhere.
- **`spec_casc_opt` is the clear loser**, worse on AIME (0.367, 14/30
  runs failing to produce a scorable answer, ~4,940 rounds vs strict's
  ~3,355) than HumanEval (0.799) — AIME's long free-form reasoning chains
  give the rambling/repetition failure mode this line of work studies much
  more room than HumanEval's short code completions do.
- **`cactus` and `r_fuzzy` land in a similar worse-than-strict band on
  AIME** (0.467, 0.433) despite `cactus` tracking closer to strict on
  HumanEval (0.909) — accepting more per round (l̄ 4.1–4.2 vs strict's
  ~2.2–2.5) without a matching accuracy return, the same pathology in a
  milder form.
- **`mentored_dec`** is consistent but unremarkable on both: close to
  strict, never clearly better, never dramatically worse.

## Metrics

- **mean accepted length (l̄)**: mean accepted *draft* tokens per
  verification round (excludes the always-kept bonus token), from vLLM's
  own `/metrics` counters, differenced around each request.
- **mean completion length**: mean output tokens per run (`usage.completion_tokens`).
- **mean verifier rounds**: mean number of draft-then-verify cycles per run,
  counted from each run's `proposals.jsonl` trace (`max(round) + 1`) —
  see below for why this needed a small correction.
- **score**: HumanEval — pass@1, candidate code executed against the
  problem's hidden unit tests in an isolated subprocess
  (`scripts/grade_humaneval.py`). AIME24 — exact match against the
  reference integer, extracted from the last `\boxed{...}` in the model's
  `final` channel (`scripts/grade_aime.py`).

Reproduce: `python3 scripts/summarize_arms.py --runs-root runs/<benchmark>_fresh --prompt-root prompts/<benchmark>`.

## The trace/metrics round-count anomaly

`mean verifier rounds` is computed two independent ways per run: from the
trace (`proposals.jsonl`'s own `round` field) and from vLLM's `/metrics`
counters (already recorded per-run as `draft_rounds` in `run.json`, via an
unrelated code path). Cross-checking one against the other turned up a
real, small, still not-fully-explained discrepancy, worth recording plainly
rather than quietly averaging over it.

**What's true:**

- In **1,120 of 1,204 runs (93%)** — every single run that ended by reaching
  EOS (`finish_reason: "stop"`), no exceptions — `trace_rounds` is exactly
  `metrics_draft_rounds + 1`.
- In **37 of the 44 runs that hit the token cap** (`finish_reason: "length"`)
  the same `+1` holds.
- In the remaining **7 of 1,204 runs (0.6%)** — all of them cap-terminated —
  `trace_rounds` equals `metrics_draft_rounds` exactly (no offset).

**What I ruled out:** a first pass at explaining this assumed the split was
clean — `+1` for EOS-terminated runs, `+0` for cap-terminated ones — based
on an initial sample that happened to contain only cap-terminated
exceptions. That rule is *wrong*: it's contradicted by the 37 cap-terminated
runs that still show `+1`. The real pattern is that termination-by-cap is
*necessary* for the exception (never occurs on an EOS-terminated run) but
not *sufficient* (most cap-terminated runs behave normally anyway).

I also checked the 7 exceptions against the tracer's own `trace_anomaly`
flag (the zero-probability-emission edge case documented below) — no
overlap, all 7 show zero flagged rows — and against the composition of each
run's final round (single-token vs. full 7-token round, ending in
`accepted_draft`/`recovered`/`bonus`) — no distinguishing pattern there
either; both the 7 exceptions and a same-sized sample of normal cap-terminated
runs cover the same range of final-round shapes.

**Best working theory, not confirmed**: after the round that emits EOS,
vLLM likely launches one further speculative round before the stop
condition is detected, whose result is then discarded — this tracer's hook
fires unconditionally on every `rejection_sample()` call (by design: Phase 1
is meant to observe everything, see `patches/relaxation_trace.py`), so it
still records that discarded round, while `/metrics`' counter only tallies
rounds whose output was actually committed to the response. That explains
the universal `+1` on EOS-terminated runs cleanly. It does *not* explain why
a small minority of cap-terminated runs — which have no EOS round to
discard — pattern-match the `+1` case anyway rather than the `+0` one; that
part would need tracing through vLLM's own scheduler/output-processor code
around max-tokens truncation to actually pin down, which I haven't done.
Flagged as an open question rather than guessed at further.

**Why this doesn't undermine the results above**: the affected 7 runs are
off by exactly 1 round each, against per-run means in the hundreds
(HumanEval) to low thousands (AIME) — under 0.1% of any individual run's
count, and `scripts/summarize_arms.py` reports it via a `rounds_offset_anomaly`
column precisely so it stays visible rather than silently smoothed into the
mean. None of the accuracy, completion-length, or accepted-length numbers
are affected at all — those come from entirely separate fields.

## A related, already-fixed issue: the tracer's own crash

Separately from the round-count question, `patches/relaxation_trace.py` had
a hard `assert` that could crash the entire vLLM engine on a rare condition
(an emitted token reading back a target probability of exactly `0.0` in
fp32) — hit twice in a row on `case_033/spec_casc_opt` during the HumanEval
sweep before being traced to the tracer itself, not the patch under test.
Phase 1 tracing is meant to be observation-only and must never be able to
take down generation just by watching it, so this was softened to a
non-fatal `trace_anomaly` flag recorded on the affected row instead of a
crash — confirmed to reproduce again safely on retry (1 flagged row out of
5,599 in the backfilled run) rather than failing the request. All
previously-completed runs were unaffected: a hard crash fails visibly
(HTTP 500, no successful `run.json`), it can't silently corrupt data, and
this was the only failure in either full sweep.
