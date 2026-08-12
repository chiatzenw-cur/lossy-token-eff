# semantic_guard: concise summary

Full narrative/methodology in `README.md`. This is the hard-data digest.

## 1. Hesitation-word baseline (wait/hmm/let's/actually/but)

AIME24 (n=30) + HumanEval (n=164), full completion text.

| arm | AIME24 total | HumanEval total | % relaxed-only (AIME24) |
|---|---:|---:|---:|
| strict | 4,455 | 2,001 | 0% |
| spec_casc_tok (α=0.3) | 4,172 | 1,981 | 3.76% |
| mentored_dec (α=0.37) | 5,913 | 1,969 | 11.08% |
| spec_casc_opt (α=0.05) | 16,620 | 4,570 | 12.38% |
| cactus (α=0.25) | 15,911 | 4,700 | 24.47% |
| r_fuzzy (α=0.3) | 18,052 | 6,245 | 26.19% |

`spec_casc_tok` and `strict` = lowest hesitation, highest accuracy (86.7%/76.7% AIME24, 95.7%/95.1% HumanEval).

## 2. `r_fuzzy_semantic_guard`: strict at hesitation tokens, full scale

| | r_fuzzy | +guard |
|---|---:|---:|
| AIME24 accuracy | 43.3% | 36.7% (-6.7pp) |
| HumanEval accuracy | 56.7% | 52.4% (-4.3pp) |
| AIME24 length | 19,506 | 16,942 (-13.1%) |
| HumanEval length | 1,787 | 1,525 (-14.7%) |

Cuts length, costs accuracy, on both benchmarks independently. (Original mechanism-check number, 0.01% relaxed-only, was a tracer bug — see §7.)

## 3. `spec_casc_tok_semantic_guard` (override-to-strict): full scale

| | AIME24 | HumanEval | Combined |
|---|---:|---:|---:|
| accuracy | 86.7%→73.3% (-13.4pp) | 95.7%→97.0% (+1.3pp) | 94.3%→93.3% (-1.0pp) |
| length | 9,440→10,397 (+10.1%) | 918.8→850.6 (-7.4%) | 2,236→2,327 (+4.0%) |
| rounds | +13.1% | -6.8% | +6.4% |
| l̄ (accepted length) | -0.9% | -0.4% | -0.5% |
| relaxed-only hesitation | 157→0 | 92→0 | 249→0 |

Benchmark-dependent: net loss on long chain-of-thought (AIME24), net win on short completions (HumanEval). l̄ barely moves — effect is round-count, not per-round acceptance rate.

## 4. `spec_casc_tok_semantic_guard_and` (AND-combination): full AIME24

Built to close a loophole in §3 (see §5) — accept iff both lossless AND `spec_casc_tok` agree, instead of overriding to pure strict.

| metric | baseline | override-guard | AND-guard |
|---|---:|---:|---:|
| accuracy | 26/30 | 22/30 | 22/30 |
| length | 9,440 | 10,397 (+10.1%) | 10,964 (+16.1%) |
| rounds | 2,896 | 3,276 (+13.1%) | 3,465 (+19.6%) |
| wall-time | 1,078.2s | 1,269.6s (+17.8%) | 1,345.3s (+24.8%) |
| hesitation words | 4,173 | 4,949 (+18.6%) | 4,822 (+15.6%) |

Same accuracy as override, worse on every efficiency axis. Failures are a lateral trade (fixes case_023/030, breaks case_011/019 instead), not a reduction — closing the loophole did not fix the underlying cost.

## 4b. `spec_casc_tok_semantic_guard_future_guard` (K-token window after a marker): full AIME24, K=4

Third design: leaves the marker's own accept decision untouched, forces strict on the K tokens *after* it instead. K chosen from pilot testing (K=4, K=8 both piloted; K=8 also run full-scale, see below).

| metric | lossless (strict) | baseline | override-guard | AND-guard | future-guard K=4 |
|---|---:|---:|---:|---:|---:|
| accuracy | 23/30 | 26/30 | 22/30 | 22/30 | 22/30 |
| length | 10,043 | 9,440 | 10,397 (+10.1%) | 10,964 (+16.1%) | 10,397 (+10.1%) |
| accepted length (l̄) | 2.2046 | 2.4210 | 2.3999 (-0.9%) | 2.3906 (-1.3%) | 2.3447 (-3.2%) |
| rounds | 100,605 total | 86,874 total | ~98,280 (+13.1%) | ~103,890 (+19.6%) | 97,779 (+12.6%) |
| wall-time | 1,234.8s | 1,078.2s | 1,269.6s (+17.8%) | 1,345.3s (+24.8%) | 1,266.3s (+17.4%) |
| hesitation words | 4,456 | 4,173 | 4,949 (+18.6%) | 4,822 (+15.6%) | 4,869 (+16.7%) |
| hesitation words, relaxed-only | 0 | 157 (3.8%) | 0 | 0 | 199 (4.1%) |

Same 22/30 accuracy as both other guards, and length/rounds/wall-time land almost on top of the override-guard's numbers (mean length 10,397 both) despite gating a disjoint set of tokens. Only design with nonzero relaxed-only hesitation words (4.1%) — by construction it never forces strict on the marker itself. Verdict changes: +1 (case_006), -5 (case_003, 014, 023, 026, 029) — case_002 is **not** rescued at K=4, unlike both other guards (stays stuck at the 32,768 cap); case_030 stays correct here but regresses under override.

## 4c. `spec_casc_tok_semantic_guard_future_guard`, K=8: the best result in this investigation so far

| metric | lossless (strict) | baseline | override-guard | AND-guard | future-guard K=4 | future-guard K=8 |
|---|---:|---:|---:|---:|---:|---:|
| accuracy | 23/30 | 26/30 | 22/30 | 22/30 | 22/30 | **25/30** |
| length | 10,043 | 9,440 | 10,397 (+10.1%) | 10,964 (+16.1%) | 10,397 (+10.1%) | **9,303 (-1.4%)** |
| accepted length (l̄) | 2.2046 | 2.4210 | 2.3999 (-0.9%) | 2.3906 (-1.3%) | 2.3447 (-3.2%) | **2.3950 (-1.1%)** |
| rounds | 100,605 total | 86,874 total | ~98,280 (+13.1%) | ~103,890 (+19.6%) | 97,779 (+12.6%) | **87,607 (+0.8%)** |
| wall-time | 1,234.8s | 1,078.2s | 1,269.6s (+17.8%) | 1,345.3s (+24.8%) | 1,266.3s (+17.4%) | **1,137.2s (+5.5%)** |
| hesitation words | 4,456 | 4,173 | 4,949 (+18.6%) | 4,822 (+15.6%) | 4,869 (+16.7%) | **3,952 (-5.3%)** |
| hesitation words, relaxed-only | 0 | 157 (3.8%) | 0 | 0 | 199 (4.1%) | 139 (3.5%) |

K=8 gives back the least accepted-length throughput of any guard variant (-1.1% off baseline, still +8.6% above lossless's own l̄) while being the only variant to sit *below* baseline on length/rounds/hesitation-words simultaneously — every other guard trades efficiency for a partial accuracy recovery; K=8 doesn't make that trade.

Widening the window from K=4 to K=8 doesn't just extend the K=4 effect, it **reverses it**: length and hesitation-word count flip from clearly worse than baseline (+10.1%/+16.7%) to clearly better (-1.4%/-5.3%), while the accuracy cost shrinks from -13.4pp to -3.4pp. First guard variant in this investigation to beat plain `spec_casc_tok` on efficiency without a comparably large accuracy cost. Verdict changes: +2 (case_002 rescued — stuck at 32,768-cap → correct in 11,506 tokens, exactly matching the K=8 pilot's own run token-for-token; case_006 wrong→correct), -3 (case_003, 014, 026 correct→no_answer) — fewer regressions than K=4 (5) or override (6); case_023/029 stay correct at K=8 (they regress at K=4). Reading: a short forced-strict window (K=4) is long enough to trigger a further hesitation cascade right after the marker but too short to ride it out; K=8 covers enough of the subsequent instability for the trajectory to settle before control reverts to the relaxed rule — consistent with §5's mechanism theory below. Natural next step: K=12/16, not yet run.

## 4d-full. `future-guard-AND` at full scale: matches lossless's own accuracy, but costs more than future-guard-strict

| metric | lossless | baseline | future-guard-strict K=8 | future-guard-AND K=8 |
|---|---:|---:|---:|---:|
| accuracy | 23/30 | 26/30 | 25/30 | **23/30** |
| length | 10,043 | 9,440 | 9,303 (-1.4%) | 10,460 (+10.8%) |
| l̄ | 2.2046 | 2.4210 | 2.3950 (-1.1%) | 2.3724 (-2.0%) |
| rounds | 100,605 | 86,874 | 87,607 (+0.8%) | 99,463 (+14.5%) |
| wall-time | 1,234.8s | 1,078.2s | 1,137.2s (+5.5%) | 1,288.2s (+19.5%) |
| hesitation words | 4,456 | 4,173 | 3,952 (-5.3%) | 4,461 (+6.9%) |

23/30 exactly matches lossless's own accuracy — worse than future-guard-strict on every efficiency axis (AND's extra conservatism has real overhead outside guarded positions too), and 5 regressions (most of any future-guard variant) vs. 3 for the strict window. +2 (case_002, case_006 rescued), -5 (case_003, 005, 014, 019, 026).

## 4e. Relaxing `spec_casc_tok`'s own alpha (0.3→0.5): pilot signal REVERSED at full scale

**Pilot (n=8):** accuracy baseline α=0.3→α=0.5: 7/8→5/8; guard α=0.3→α=0.5: 7/8→**6/8** — guard appeared to *beat* its own baseline at α=0.5 (first such case in this investigation). 2 rescues (case_003, case_005) vs 1 regression (case_011).

**Full 30-case sweep — does NOT replicate:**

| metric | baseline α=0.3 | baseline α=0.5 | future-guard K=8 α=0.3 | future-guard K=8 α=0.5 |
|---|---:|---:|---:|---:|
| accuracy | 26/30 | 22/30 | 25/30 | **20/30** |
| length | 9,440 | 10,495 | 9,303 | 10,555 (+0.6% vs α=0.5 baseline) |
| rounds | 86,874 | 96,402 | 87,607 | 97,984 (+1.6%) |
| wall-time | 1,078.2s | 1,212.9s | 1,137.2s | 1,273.6s (+5.0%) |
| relaxed-only | 3.8% | 5.0% | 3.5% | 5.5% |

At full scale the guard is **worse** than its own α=0.5 baseline (20/30 vs 22/30) — the opposite of the pilot. The pilot's own two rescues (case_003, case_005) reproduce exactly, but 4 new regressions outside the 8-case sample (case_006, 009, 011, 019) flip the net sign (-2 instead of +1). Same pattern as the `r-fuzzy-semantic-guard` pilot-vs-full-scale reversal earlier in this document, on a different axis.

**Pushed further to α=0.7 — reverses AGAIN.** Full 30-case sweep: baseline 22/30, guard **25/30** — a clean +3-case win with **zero regressions** (3 improved: case_002, 003, 005; 0 regressed). But not free this time: length +18.4%, rounds +20.3%, wall-time +23.8% over the α=0.7 baseline (vs. future-guard-strict K=8 being *cheaper* than baseline at α=0.3).

| α | baseline acc | guard acc | guard vs baseline | guard length vs baseline |
|---:|---:|---:|---|---:|
| 0.3 | 26/30 | 25/30 | -1 case, but cheaper | -1.4% |
| 0.5 | 22/30 | 20/30 | **-2 cases, more expensive** | +0.6% |
| 0.7 | 22/30 | 25/30 | **+3 cases, zero regressions** | +18.4% |

**Non-monotonic — not a single trend.** Alpha appears to have multiple regimes with different guard/baseline dynamics, not a smooth curve. The α=0.3 conclusion (future-guard-strict K=8 is the best cost/accuracy trade in this investigation) still stands — α=0.7 buys the same accuracy tier at real extra cost, not for free the way α=0.3 does.

**A 4th combination rule — future-guard-AND (K=8, α=0.3), pilot n=8:** crosses future-guard's trigger (gate the K tokens after an accepted marker) with the AND-guard's rule (`min(pi_rej,p)` inside the window instead of pure strict, provably never more lenient than future-guard-strict).

| metric | baseline | override | AND | future-guard-strict K=8 | future-guard-AND K=8 |
|---|---:|---:|---:|---:|---:|
| accuracy | 7/8 | 7/8 | 6/8 | 7/8 | 6/8 |
| length | 118,947 | 85,716 (-27.9%) | 91,358 (-23.2%) | 95,424 (-19.8%) | 97,541 (-18.0%) |
| hesitation words | 1,891 | 1,333 (-29.5%) | 1,419 (-24.9%) | 1,508 (-20.3%) | **1,396 (-26.2%)** |
| relaxed-only | 67 | 0 | 0 | 49 (3.3%) | 47 (3.4%) |

Same accuracy tier as the marker-level AND-guard (6/8, not future-guard-strict's 7/8), but the best hesitation-word reduction of any guard pilot so far (-26.2%). Verdict: +1 rescue (case_002, but at 23,811 tokens — 2x future-guard-strict's own more efficient rescue), -2 regressions (case_003, same case every guard loses; case_005, new). case_011 shrinks 27,669→4,427 (**-84.0%**, largest single-case reduction across all four guard pilots), staying correct throughout. **Full 30-case sweep: 23/30 (76.7%), exactly matching lossless — worse than future-guard-strict on every efficiency axis (length +10.8%, rounds +14.5%, wall-time +19.5%), 5 regressions (most of any future-guard variant). See §4d-full above.**

## 4f. `spec_casc_tok_semantic_guard_v2` (wide marker set, override mechanism): isolating whether SET WIDTH explains future-guard's edge

Every future-guard variant uses the wide 35-id/14-word marker set; override/AND both still use the narrow 18-id/5-word set. v2 tests the wide set on the plain override (marker-level, not future-guard) mechanism to isolate width from window-placement.

| metric | baseline | override (narrow) | AND (narrow) | future-guard-strict K=8 | future-guard-AND K=8 | v2 (wide, override) |
|---|---:|---:|---:|---:|---:|---:|
| accuracy | 7/8 | 7/8 | 6/8 | 7/8 | 6/8 | **7/8** |
| length | 118,947 | 85,716 (-27.9%) | 91,358 (-23.2%) | 95,424 (-19.8%) | 97,541 (-18.0%) | 109,027 (-8.3%) |
| hesitation words | 1,891 | 1,333 (-29.5%) | 1,419 (-24.9%) | 1,508 (-20.3%) | 1,396 (-26.2%) | 1,489 (-21.3%) |
| relaxed-only | 67 (3.5%) | 0 | 0 | 49 (3.3%) | 47 (3.4%) | **0 (0.0%)** |

**Marker-set width alone does not explain future-guard's edge.** v2 ties baseline accuracy with a perfectly clean mechanism check (0.0% relaxed-only, same as narrow override — v2 still gates the marker itself, so it doesn't have future-guard's structural leak), but its efficiency gains (-8.3% length) are smaller than narrow override's own (-27.9%) or future-guard-strict's (-19.8%). Verdict: net 0 (case_002 rescued, case_011 newly regresses — the only guard variant to lose case_011).

**Full 30-case sweep: 25/30 (83.3%)** — exactly matches future-guard-strict K=8's accuracy, via a completely different mechanism (wide-set override at the marker, not a trailing window). Full numbers: length 9,440→10,599 (+12.3%), l̄ 2.4210→2.3986 (-0.9%), rounds 86,874→97,540 (+12.3%), wall-time 1,078.2s→1,274.3s (+18.2%), hesitation words 4,173→4,313 (+3.4%), relaxed-only 0.0%. Verdict: +2 (case_002, case_006), -3 (case_011, case_014, case_018). case_011's pilot regression reproduces at full scale — real, not noise.

## 5a. Final AIME24 conclusion: eight variants, one table

| variant | accuracy | length | l̄ | rounds | wall-time | hesitation words | relaxed-only |
|---|---:|---:|---:|---:|---:|---:|---:|
| lossless (strict) | 23/30 (76.7%) | 10,043 | 2.2046 | 100,605 | 1,234.8s | 4,456 | 0.0% |
| **baseline (spec_casc_tok)** | **26/30 (86.7%)** | **9,440** | **2.4210** | **86,874** | **1,078.2s** | **4,173** | 3.8% |
| override (narrow) | 22/30 (73.3%) | 10,397 | 2.3999 | 98,277 | 1,269.6s | 4,949 | 0.0% |
| AND (narrow) | 22/30 (73.3%) | 10,964 | 2.3906 | 103,942 | 1,345.3s | 4,822 | 0.0% |
| v2 (wide, override) | 25/30 (83.3%) | 10,599 | 2.3986 | 97,540 | 1,274.3s | 4,313 | 0.0% |
| future-guard-strict K=4 | 22/30 (73.3%) | 10,397 | 2.3447 | 97,779 | 1,266.3s | 4,869 | 4.1% |
| **future-guard-strict K=8** | **25/30 (83.3%)** | **9,303** | **2.3950** | **87,607** | **1,137.2s** | **3,952** | 3.5% |
| future-guard-AND K=8 | 23/30 (76.7%) | 10,460 | 2.3724 | 99,463 | 1,288.2s | 4,461 | 4.0% |
| baseline, α=0.5 | 22/30 (73.3%) | 10,495 | 2.4929 | 96,402 | 1,212.9s | 4,532 | 5.0% |
| future-guard-strict K=8, α=0.5 | 20/30 (66.7%) | 10,555 | 2.4484 | 97,984 | 1,273.6s | 4,662 | 5.5% |
| baseline, α=0.7 | 22/30 (73.3%) | 10,337 | 2.6565 | 90,948 | 1,147.4s | -- | -- |
| **future-guard-strict K=8, α=0.7** | **25/30 (83.3%)** | 12,239 | 2.5365 | 109,433 | 1,419.9s | 5,699 | 6.9% |

Relaxing alpha is **non-monotonic** for the guard — see §4e for the full 0.3/0.5/0.7 story. At α=0.5 the guard loses to its own baseline (reversing an 8-case pilot's wrong signal); at α=0.7 it wins clearly again (25/30 vs 22/30, zero regressions) but at real extra cost (+18.4% length). Every guard/alpha combination tested still loses to unguarded `spec_casc_tok` **at α=0.3** — the practical recommendation from §5a stands; the α=0.7 win doesn't change it, since it costs more than α=0.3's baseline to reach the same accuracy tier.

**No guard beats vanilla `spec_casc_tok`'s 86.7%** — it remains the single best-accuracy AND cheapest arm tested. The seven guards split into two clusters regardless of mechanism: **high-accuracy (25/30)** = v2 and future-guard-strict K=8, tied on accuracy but future-guard-strict K=8 is strictly better on efficiency (-1.4% length vs. v2's +12.3%) — **future-guard-strict K=8 dominates** unless a provably-clean mechanism (v2's 0.0% relaxed-only vs. future-guard's inherent 3.5%) matters independent of cost. **Low-accuracy (22-23/30)** = override, AND, future-guard K=4, future-guard-AND — all four cost accuracy AND efficiency, a clean net loss, regardless of narrow/wide set or marker-level/window mechanism.

**Recommendation**: use unguarded `spec_casc_tok` for AIME24 if accuracy is the only goal. If cutting hesitation-language volume matters independently, `future-guard-strict K=8` is the only guard that's cheaper than baseline while keeping 83.3% accuracy — every other guard buys its accuracy at a real cost.

## 5. Mechanism: why does forcing strict on hesitation tokens make AIME24 longer?

**Direction A — guard forces strict, `spec_casc_tok` would have rejected** (override-guard trace, n=4,830 guarded positions):
- 35.4% rejected by the forced strict test; 10.6% (510) are where the guard itself changed the outcome vs plain `spec_casc_tok`; 3.95% (191) produce a visibly different word.
- 100% of those 191 are provably outside `spec_casc_tok`'s trusted top set (its own rule always accepts in-set tokens unconditionally — could never disagree with strict in this direction otherwise).
- Root cause: hesitation markers land outside the trusted set ~3x more than typical tokens (6.60% of guarded positions vs. 2.22% background rate).

**Direction B — plain `spec_casc_tok` itself rejects a hesitation token lossless would keep** (no guard installed, n=217 events, `spec_casc_tok0p3` baseline, all 30 AIME24 cases):

| | count | % |
|---|---:|---:|
| total events | 217 | 100% |
| → substituted with **another hesitation marker** | 78 | 35.9% |
| → substituted with something else | 139 | 64.1% |

By marker: `but` 98, `let's` 47, `wait` 35, `actually` 35, `hmm` 2.

Top transitions: `But`→`So` (22), `Actually`→`Wait` (13), `Let's`→`But` (11), `But`→`Let's` (9), `Wait`→`Actually` (8), `But`→`Wait` (6), `Wait`→`Let's` (6), `Actually`→`But` (6). Dominated by hesitation-marker-to-hesitation-marker swaps, not elimination — the model was already committed to hedging; rejection mostly just redirects *which* word.

Downstream effect (30-token window after the event): hesitation rate 2.65% after marker→marker swaps vs. 2.37% after marker→other (10.6% relative gap); entropy 0.994 vs. 0.957 (3.8% gap). Direction consistent with "marker→other reduces further hedging slightly," but weak — not confirmed, no causal test run.

**Correlation**: per-case guard-intervention rate vs. length growth, r=0.592 (n=30) — real but imperfect; guard can also rescue an already-unstable baseline (case_002: 32,768-cap → correct answer).

**Cross-run methodology caveat**: this system is deterministic given a fixed patch (two independent same-arm runs are 100% token-identical). But baseline and guard are different patches/kernels, and diverge completely within the first 100-900 tokens of the first real disagreement. So cross-run "what happened after this one intervention" comparisons are invalid; only within-run comparisons are sound. Within-run (guard-fired-no-change vs. guard-fired-changed, same trajectory): hesitation-rate 1.83x elevated after genuine changes (real); entropy 1.03x (flat — corrects an earlier invalid cross-run claim of 1.64x).

## 6. Hidden-state recurrence / loop investigation

- Token-level onset detectors (window-entropy, hidden-state S_k) against `r_fuzzy`: low precision as real-time detectors (1/7 longest streaks; onset positions not enriched for `lossy_only_accepted`, ~20% either way).
- Macro-loop pattern (reach `final`, abandon it, restart `analysis`): found once (`r_fuzzy` case_028). Recurrence strong at the restart itself (99.4th percentile) but does not predict the abandoned span while being written (13th percentile) — marks the boundary, not the waste.
- Single-event counterfactual (flip one lossy-only-accept to strict, resume): 1/3 tested onsets shows strong reproducible ignition (case_028: cap-out → <350 tokens, 2/2 seeds); other 2 partial/seed-inconsistent.
- Strict (true lossless), same 8 cases, hidden-state capture: only 1/8 fails to converge (case_002 — same case fails under plain `spec_casc_tok` too, not a relaxed-verification artifact). Zero macro-loop restarts under strict. Recurrence labeling (24 candidates): all 3 genuine `reasoning_loop` labels from the one failing case; 20/24 elsewhere `benign`; 1 `no_progress`. 100% precision on the failing case, 0% false positives on the 7 successful ones.

## 7. Bugs found and fixed

1. **Tracer tautology**: merged (not base-only) defer_mask passed to tracer made `lossy_would_accept` collapse to `strict_would_accept` at guarded positions by construction. Found in window-entropy-guard first, retrofitted into `r_fuzzy_semantic_guard`(+v2).
2. **Wrong model runner**: hidden-state capture first patched dead-code V2 (`gpu/model_runner.py`) instead of active V1 (`gpu_model_runner.py`) — caught via 0-byte output.
3. **Recurrence-score matrix bug**: `S1==S4==S8==S16` from an indexing error, caught via hand-computed reference mismatch.
4. **proposals.jsonl drops the true first token** on short completions-endpoint probes — caught via cross-check against `response.json`.
5. **Alpha-file aliasing** (`spec_casc_tok_semantic_guard_and`): first draft fell back to plain `spec_casc_tok`'s alpha file instead of its own — caught and fixed before any run.

## 8. Reference: methods explained + complete data matrix

**`spec_casc_tok`** (base method): `pi_rej(v) = q(v)+eta*p(v)` for `v` in trusted set `A = {u: p(u) >= (1-alpha)*max(p)}`, else `eta*p(v)`; `eta = 1 - sum_{A} q(v)`. Higher alpha = more relaxed (bigger `A`). Strict limit is `alpha=-inf`, NOT 0. Provably: in-`A` tokens always accept; out-of-`A` tokens are *more conservative than lossless* (`pi_rej < p`) — hesitation markers are disproportionately out-of-`A` (6.6% vs 2.2% background), which is why plain `spec_casc_tok` already beats lossless without any guard.

**Five guards, all leaving unguarded positions untouched:**
- **override** (narrow, 5-word set): force `A` empty at the marker — exactly `alpha=-inf` at that token.
- **AND** (narrow): accept iff BOTH lossless AND `spec_casc_tok`'s own test agree (`min(p,pi_rej)`) — closes override's loophole (override can accept what `spec_casc_tok` itself would reject).
- **v2** (wide, 14-word set): same mechanism as override, wider set — isolates whether set width alone (not window placement) explains future-guard's edge.
- **future-guard-strict** (wide, param K): doesn't gate the marker itself — arms a trailing K-token raw-strict window the moment a marker is *accepted*. Cross-round persistent state (first patch in this repo with that).
- **future-guard-AND** (wide, param K): same trailing window, AND-combined inside it instead of pure strict.

Mechanism check (`relaxed-only %`) is always exactly 0% for override/AND/v2 (they gate every marker occurrence), never 0% for the two future-guard variants (they never touch the marker's own decision).

**Complete data, full 30-case AIME24:**

| method | α | K | accuracy | length | l̄ | rounds | wall-time | hesitation words | relaxed-only |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| lossless | — | — | 23/30 | 10,043 | 2.2046 | 100,605 | 1,234.8s | 4,456 | 0.0% |
| **baseline** | 0.3 | — | **26/30** | **9,440** | **2.4210** | **86,874** | **1,078.2s** | **4,173** | 3.8% |
| override | 0.3 | — | 22/30 | 10,397 | 2.3999 | 98,277 | 1,269.6s | 4,949 | 0.0% |
| AND | 0.3 | — | 22/30 | 10,964 | 2.3906 | 103,942 | 1,345.3s | 4,822 | 0.0% |
| v2 | 0.3 | — | 25/30 | 10,599 | 2.3986 | 97,540 | 1,274.3s | 4,313 | 0.0% |
| future-guard-strict | 0.3 | 4 | 22/30 | 10,397 | 2.3447 | 97,779 | 1,266.3s | 4,869 | 4.1% |
| **future-guard-strict** | 0.3 | 8 | **25/30** | **9,303** | 2.3950 | **87,607** | **1,137.2s** | **3,952** | 3.5% |
| future-guard-AND | 0.3 | 8 | 23/30 | 10,460 | 2.3724 | 99,463 | 1,288.2s | 4,461 | 4.0% |
| baseline | 0.5 | — | 22/30 | 10,495 | 2.4929 | 96,402 | 1,212.9s | 4,532 | 5.0% |
| future-guard-strict | 0.5 | 8 | 20/30 | 10,555 | 2.4484 | 97,984 | 1,273.6s | 4,662 | 5.5% |
| baseline | 0.7 | — | 22/30 | 10,337 | 2.6565 | 90,948 | 1,147.4s | 4,895 | 7.3% |
| **future-guard-strict** | 0.7 | 8 | **25/30** | 12,239 | 2.5365 | 109,433 | 1,419.9s | 5,699 | 6.9% |

Not run: override/AND/v2 at α=0.5/0.7, K=4 at α≠0.3, finer alpha steps (0.4/0.6) to characterize the 0.5-dip/0.7-recovery transition.
