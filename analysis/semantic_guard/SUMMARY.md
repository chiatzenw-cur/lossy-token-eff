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
