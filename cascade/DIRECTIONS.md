# Directions for the speculative-cascade thread

**Runnable form of this list: `EXPERIMENTS.md` (ids E0–E8) and `bash
cascade/run.sh <id>`.** Mapping: D1 -> E1, D2 -> E7 (done), D3 -> E2, D4 ->
E3, D5 -> E5 (Diff/Chow) + E6 (opt_head; entropy-gated head not built),
D6 -> E4, D7 -> not built (needs Chiatzen's split), D8 -> E8, D9 -> not
built.

**Status 2026-09-17:** D1 (E1/E1F/E1P), D2 (E7) and D5's opt_head (E6) are
done — results in `RESULTS.md`; D3 (opt_ent), D4 (timing), D5's Diff/Chow,
D6 (draft length) are built and unrun; D7–D9 not built.

Ranked by (information per GPU-hour) for a single H100. Each entry: the
hypothesis, the concrete run, what each outcome would mean, and a rough
cost using the campaign's own timings (~90-100 s fixed server overhead per
fresh-server measurement plus generation; gsm8k cases are seconds, AIME24
cases are minutes). Status tags: `ready` = can run today on the old box or
Nibi once login works; `needs-X` = blocked on X.

Constraints agreed in the 2026-09 meeting: acceptance-rule work only (no
"LLM tricks" on the one-layer drafter — HaoChen's group owns drafter
training); guards on top of tok were already explored at length in
`analysis/semantic_guard/` with no token-efficiency gain, so do not redo
them; Chiatzen owns the reasoning-vs-answer length split and the MT-Bench
category breakdown — coordinate, do not duplicate.

## D1. Mechanism test: `spec_casc_tok_lt` vs `spec_casc_tok` vs strict  — `ready`

**Hypothesis.** Length inflation comes from committing draft tokens that
are low-probability under the verifier (outside its head), not from
relaxation per se. `spec_casc_tok` never does that; every inflating method
does. `spec_casc_tok_lt` keeps tok's head-only free pass but drops the
out-of-head `eta*p` penalty (lossless there instead).

**Run.** GPT-OSS-20B. `campaign_run.py --dataset gsm8k --methods
spec_casc_tok_lt spec_casc_tok --full-cases 30`, then the same on
`humaneval` and `aime24` (aime24 is where inflation is worst: 30 cases,
32k budget — budget ~6-8 GPU-h for both methods; gsm8k+humaneval ~2 GPU-h).
The calibration stage places tok_lt's l̄ band automatically; report with
`campaign_report.py` and `cascade/analysis/speed_ignoring_accuracy.py`.

**Read-out.**
- l̄ up vs tok *and* completion length flat (len_ratio within ~1.05 of
  strict) -> hypothesis supported; the design principle becomes "relax as
  much as you like inside the verifier's head, never outside". Then D5.
- l̄ up and length inflates -> the `eta` penalty was doing the work; tok's
  no-inflation property comes from being *stricter* than lossless off the
  head, which is a much less useful principle. Still a result.
- l̄ barely moves -> out-of-head accepts are rare under this drafter
  anyway; tok's narrow band is a property of the drafter, not the rule
  (ties to D6).

## D2. Trace-level test of the same hypothesis on existing runs  — `done 2026-09-11` (E7)

**Done.** `old_runs/` turned out to hold 1,226 git-tracked traces;
`analysis/trace_rank_analysis.py` ran on them. Result and caveats:
`EXPERIMENTS.md` E7 and `results/trace_rank_analysis.md`. The original plan
follows for the record; the "loop onset" part was replaced by a simpler
stop-vs-budget-hit split, which showed per-case rates do not predict loops.

`patches/relaxation_trace.py` already records, per proposal, the drafted
token's **rank under the verifier**, `p(x)`, `q(x)`, both entropies, TV,
whether strict would have accepted, and whether the lossy rule did. For
every campaign run that has `proposals.jsonl`, classify each *lossy-only*
accept (lossy accepted, strict would not have) by verifier rank, and
measure: fraction of lossy-only accepts with rank > k per method/alpha;
whether the first budget-exhausting loop in a run is preceded by a burst of
low-rank accepts (the `analysis/semantic_guard/` scripts already locate
loop onsets); completion length regressed on the count of rank>k accepts.
No new generation. Blocked only on access to `runs/` (gitignored, lives on
the old box — copy the `proposals.jsonl` files, they are small) or on
re-running a subset with tracing on Nibi. This is the cheapest strong
evidence available and should be done before D1's results are
interpreted.

## D3. `spec_casc_opt_ent` vs `spec_casc_opt`  — `ready`

**Hypothesis.** opt's rambling is partly a proxy problem: its deferral
compares two argmax probabilities and is blind to hedging positions where
the verifier's mass is spread. The paper's own entropy plug-in (App. C.2)
compares whole-distribution sharpness.

**Run.** `campaign_run.py --dataset aime24 --methods spec_casc_opt_ent
--full-cases 30` (opt already has its full sweep; compare at matched l̄).
The grid `[-2, -0.5, 0, 0.5]` is a guess; look at the calibration JSON
before trusting the chosen alphas. ~3-4 GPU-h.

**Read-out.** If opt_ent inflates less than opt at the same l̄, the
confidence proxy matters and a hybrid (D5) is the next step. If it inflates
the same, the problem is the wholesale trust, not the trigger — which
again points at head-restriction as the fix.

## D4. Real wall-clock speedup, measured, including drafter cost  — `ready`, quick

The paper draft has no measured throughput; Xia et al. found vLLM's own
spec-dec overhead (`c_rel` 0.85 vs an ideal 0.27) dominates realisable
gains. On one H100: time `strict` vs `spec_casc_tok` (a=0.8) vs baseline
(no drafter) on gsm8k and aime24 with `wall_time_seconds` from the existing
runner, plus tokens/s from vLLM `/metrics`. Fresh server per measurement,
same cases. ~1 GPU-h. This turns "1.21x rounds" into a number a reader can
believe, and it measures `c_rel` for this stack, which every speedup
formula in the paper needs.

## D5. Rule variants that follow from D1/D3  — `after D1`

All are one-line mask changes in the opt-shaped patch (recipe in
README.md section 5), each ~30 min to add:

- **opt with a head check** (two knobs): opt's deferral AND `p(x) >=
  (1-beta) max p`. Tests whether opt's acceptance gain survives once its
  out-of-head commits are removed.
- **Diff and Chow deferral** from the source paper (Eq. 5: `max q < max p
  - alpha`; Eq. 2: `max q < 1 - alpha`): the baselines the paper's OPT
  rule was measured against. Cheap completeness for the paper's method
  table.
- **entropy-gated head width**: `alpha` shrinks as `H(p)` grows, so the
  free pass narrows exactly at hedging positions. Direction of the effect
  is an open question (Medusa's typical acceptance loosens at high
  entropy; the loop analysis suggests the opposite is right here).

## D6. Draft length (`NUM_SPEC`) sweep for strict and tok  — `ready`, quick

Xia et al. Finding 2: tuning `N_draft` under *strict* verification gives
gains comparable to relaxation at zero accuracy risk. The whole campaign
used `NUM_SPEC=6`. Sweep 3/4/6/8/10 for `strict` and `spec_casc_tok` (a=0.8)
on gsm8k (fast) and aime24 (long); `rounds` and wall time per case. ~2
GPU-h. If strict at N=4 beats tok at N=6, that reframes the paper's
"cascades are the exception" as "nothing beats tuning the draft length".

## D7. Reasoning-only vs answer-only relaxation  — `after Chiatzen's split`

Chiatzen is measuring *where* inflation happens (analysis vs final channel
on GPT-OSS; the `run.json` fields `analysis_chars`/`final_chars` already
split it). If it is all in the reasoning channel, a rule that runs the
relaxed test only after the final channel opens is the obvious
accuracy-safe variant; if it is in the answer, the opposite. The patch
needs the channel boundary, which `spec_casc_tok_force_commit`'s patch
already knows how to read from the emitted history.

## D8. Port the variants (and fix the V2 gap) for Qwen3-8B  — `needs-old-box`

Qwen3 routes through vLLM's V2 runner. The consolidated V2 file with all
five methods exists **only on the old H100 box** (no patch file in the
repo; `patches/HASHES.txt` V2 section). Before any Qwen3 work on Nibi:
copy `.venv-vllm/lib/python3.12/site-packages/vllm/v1/worker/gpu/spec_decode/rejection_sampler_utils.py`
from the box, diff it against the pristine v0.26.0 file, and commit it as
`patches/vllm-0.26.0-v2-consolidated.patch` with its hash. Note for the
paper: that V2 port is accept-test-only for cactus and spec_casc_tok
(residual on raw `p`), so the Qwen3 tables use slightly different rules
than the GPT-OSS tables for those two methods. Worth a footnote at least;
worth re-running if the reviewers are careful.

## D9. MT-Bench judge  — `low priority`

MT-Bench has no accuracy grader (needs an LLM judge). Cheap to add with
any API model, but the campaign's MT-Bench inflation is the mildest of any
dataset, so it is the least informative place to spend time.

## Not directions

- Guards/breakers on top of tok: done (`analysis/semantic_guard/`), no
  token-efficiency win; the judge/nudge and hsr-guard lines each found
  real bugs late. Do not reopen without a new mechanism.
- Drafter-side changes: HaoChen's rollout-aligned drafter training.
  Provide him the acceptance-rule findings; take his drafters when ready
  and re-run D1 with them (Xia Finding 6: stronger drafters make relaxed
  rules nearly lossless — the question is whether that holds for
  head-restricted rules specifically).
