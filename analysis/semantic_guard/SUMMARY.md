# semantic_guard: concise summary

Full narrative/methodology in `README.md`. This is the hard-data digest.

## 1. Hesitation-word baseline (wait/hmm/let's/actually/but)

AIME24 (n=30) + HumanEval (n=164), counted over full completion text.

| arm | AIME24 total | HumanEval total | % relaxed-only (AIME24) |
|---|---:|---:|---:|
| strict | 4,455 | 2,001 | 0% (by construction) |
| spec_casc_tok (α=0.3) | 4,172 | 1,981 | 3.76% |
| mentored_dec (α=0.37) | 5,913 | 1,969 | 11.08% |
| spec_casc_opt (α=0.05) | 16,620 | 4,570 | 12.38% |
| cactus (α=0.25) | 15,911 | 4,700 | 24.47% |
| r_fuzzy (α=0.3) | 18,052 | 6,245 | 26.19% |

`spec_casc_tok` and `strict` are the two low-hesitation arms; also the two highest-accuracy arms (86.7%/76.7% AIME24, 95.7%/95.1% HumanEval).

## 2. `r_fuzzy_semantic_guard`: force strict at hesitation-marker tokens, full 30+164 scale

| | r_fuzzy | +guard | Δ |
|---|---:|---:|---:|
| AIME24 accuracy | 43.3% (13/30) | 36.7% (11/30) | -6.7pp |
| HumanEval accuracy | 56.7% (93/164) | 52.4% (86/164) | -4.3pp |
| AIME24 mean completion length | 19,506 | 16,942 | -13.1% |
| HumanEval mean completion length | 1,787 | 1,525 | -14.7% |
| hesitation words, % relaxed-only (AIME24) | 26.2% | 0.01%* | — |

*\*Bug found and fixed 2026-08-11: original v1 patch passed the merged (not JSD-only) defer_mask to the tracer, making `lossy_would_accept` collapse to `strict_would_accept` at every guarded position by construction. The 0.01% number above predates the fix and is a construction artifact — retrofitted (jsd_defer_mask vs merged_defer_mask split), not re-run at scale.*

**Verdict**: cuts length at a real, consistent accuracy cost on both benchmarks independently.

## 3. `spec_casc_tok_semantic_guard` (override-to-strict): full 30+164 scale

| | AIME24 | HumanEval | Combined (n=194) |
|---|---:|---:|---:|
| accuracy | 86.7%→73.3% (**-13.4pp**) | 95.7%→**97.0%** (+1.3pp) | 94.3%→93.3% (-1.0pp) |
| mean completion length | 9,440→10,397 (**+10.1%**) | 918.8→**850.6** (-7.4%) | 2,236→2,327 (+4.0%) |
| mean verifier rounds | 2,896→3,277 (+13.1%) | 267.5→249.4 (-6.8%) | 674.0→717.4 (+6.4%) |
| mean l̄ (accepted length) | 2.421→2.400 (-0.9%) | 2.604→2.593 (-0.4%) | 2.576→2.563 (-0.5%) |
| total wall-time | 1,078.2s→1,269.6s (+17.8%) | 580.0s→584.2s (+0.7%) | 1,658.2s→1,853.8s (+11.8%) |
| hesitation words, relaxed-only | 157→**0** | 92→**0** | 249→**0** |

**Verdict**: benchmark-dependent. Net loss on AIME24 (long chain-of-thought), net win on HumanEval (short completions). l̄ barely moves either way — effect is in round-count, not per-round acceptance generosity.

## 4. `spec_casc_tok_semantic_guard_and` (AND-combination, closes a loophole in #3): pilot (n=8) + full AIME24 (n=30)

Mechanism found: `spec_casc_tok`'s own formula is strictly *more conservative* than lossless for drafts outside its trusted top set (η<1 discount), so overriding to pure strict at guarded positions can *accept* a hesitation-marker token `spec_casc_tok` itself would reject — the opposite of the guard's intent. AND-variant instead accepts iff both tests agree (`min(p, pi_rej)`), provably never more lenient than either alone.

| metric | baseline | override-guard | AND-guard |
|---|---:|---:|---:|
| accuracy (n=30) | 26/30 (86.7%) | 22/30 (73.3%) | 22/30 (73.3%) |
| mean completion length | 9,440 | 10,397 (+10.1%) | 10,964 (**+16.1%**) |
| mean verifier rounds | 2,896 | 3,276 (+13.1%) | 3,465 (**+19.6%**) |
| total wall-time | 1,078.2s | 1,269.6s (+17.8%) | 1,345.3s (**+24.8%**) |
| hesitation words | 4,173 | 4,949 (+18.6%) | 4,822 (+15.6%) |
| mechanism check (relaxed-only) | 157 | 0 | 0 |

**Verdict**: same accuracy as override (22/30), but worse on every efficiency axis. Failures are a lateral trade, not a reduction — AND fixes 2 of override's regressions (case_023, case_030) but introduces 2 new ones (case_011, case_019); 4 regressions shared by both. Closing the mathematical loophole did not fix the underlying accuracy/length cost — that cost is not explained by the loophole.

## 5. Why does forcing strict at hesitation markers increase length on AIME24?

- **Mechanism**: `spec_casc_tok` rejects hesitation-marker drafts more than lossless for tokens outside its trusted top set (empirically: 6.60% of guarded positions vs 2.22% background rate — hesitation markers land outside the trusted set ~3x more than typical tokens).
- **Full funnel** (AIME24, override-guard, n=4,830 guarded positions): 35.4% rejected by the forced strict test; of those, only 10.6% (510) are positions where the guard itself changed the outcome vs plain `spec_casc_tok`; of those, only 3.95% (191) produce a visibly different word.
- **The 191 visible substitutions**: 100% are provably outside `spec_casc_tok`'s trusted top set (its own rule always accepts in-set tokens unconditionally, so it could never disagree with strict there in this direction).
- **Reverse direction, checked separately**: 217 events where plain `spec_casc_tok` itself rejects a hesitation marker that lossless would keep — 35.9% substituted with *another* hesitation marker (`But`→`So`, `Actually`↔`Wait`, `Let's`↔`But` dominate), 64.1% with something else. Downstream (30-token window) hesitation rate is slightly lower after "something else" substitutions (2.37%) than after marker-to-marker swaps (2.65%) — weak evidence (~10%, not confirmed) that these substitutions reduce continued hedging.
- **Correlation**: per-case guard-intervention rate (changes per 1k tokens) vs. length growth, r=0.592 (n=30) — real but not perfect; exceptions exist where the guard rescues an already-unstable baseline trajectory.
- **Cross-run comparison caveat (important, found via user pushback)**: this system is fully deterministic given a fixed patch (two independent fresh-server runs of the same arm are 100% token-identical). But baseline and guard runs are *different patches* — different kernel code paths — and diverge completely within the first 100-900 tokens once the first `strict_would_accept != lossy_would_accept` event occurs. This means **cross-run "what happened after this specific intervention" comparisons are invalid** for isolating a single event's causal effect; only within-run comparisons (e.g. guard-fired-no-change vs guard-fired-changed, both from the same trajectory) are methodologically sound. Within-run: hesitation-rate 1.83x elevated after genuine changes (real), entropy 1.03x (flat — not a real effect, corrects an earlier invalid cross-run claim of 1.64x).

## 6. Hidden-state recurrence / loop investigation

- **Token-level onset detection** (window-entropy ramp, hidden-state S_k recurrence) against `r_fuzzy` trajectories: low precision as a real-time detector (1 clear hit / 7 longest streaks for window-entropy; onset positions not enriched for `lossy_only_accepted`, ~20% either way).
- **Macro-loop pattern** (reach `final` channel, abandon it, restart `analysis`): found once in `r_fuzzy` (case_028). Hidden-state recurrence at the restart itself is strong (99.4th percentile windowed, ~100th percentile targeted-match) — but does NOT predict the abandoned span while it's being generated (13th percentile, i.e. below-typical) — recurrence marks the boundary-crossing moment, not the unproductive content leading into it.
- **Single-event counterfactual** (flip one earlier lossy-only-accept to strict, resume under r_fuzzy): 1 of 3 tested onsets shows a strong, reproducible ignition effect (case_028: 32,768-token cap-out → <350 tokens, 2/2 seeds); the other 2 (same underlying case_020 run) show partial, seed-inconsistent effects.
- **Strict (true lossless) baseline, same 8 cases, with hidden-state capture**: only 1/8 cases fails to converge (case_002 — same case that also fails under plain `spec_casc_tok`, confirming this is not a relaxed-verification artifact). Zero macro-loop restarts under strict — that specific failure shape appears to be relaxed-verification-specific. Recurrence-onset labeling (24 candidates, top-3-streak per case): all 3 genuine `reasoning_loop` labels come from the one case that failed; 20/24 candidates elsewhere are `benign` (legitimate repetitive-structure computation); 1 `no_progress`. Recurrence signal has real precision here (100% of the failing case's flagged events are genuine loops, 0% false positives in the 7 successful cases).

## 7. Real bugs found and fixed this investigation

1. **Tracer tautology** (`r_fuzzy_semantic_guard`, `r_fuzzy_window_entropy_guard` originally): passing the merged (base ∪ guard) defer_mask to the tracer instead of the base-only mask makes `lossy_would_accept` collapse to `strict_would_accept` at every guarded position by construction. Window-entropy-guard caught and fixed first; `r_fuzzy_semantic_guard` (and unused v2) retrofitted after.
2. **Wrong model runner** (hidden-state capture): first attempt patched `vllm/v1/worker/gpu/model_runner.py` (V2, dead code in this config) instead of the flat `gpu_model_runner.py` (V1, active) — caught via a 0-byte output file.
3. **Recurrence-score matrix bug**: `S1==S4==S8==S16` for every row from an indexing error (`k_sim[r:,r:] += sims[r:,r:]` instead of `sims[:n-r,:n-r]`) — caught via hand-computed reference mismatch.
4. **proposals.jsonl drops the true first token** on short completions-endpoint probe requests — caught by cross-checking against `response.json`.
5. **Own-alpha-file aliasing bug** (`spec_casc_tok_semantic_guard_and`, caught before any run): first draft read the plain `spec_casc_tok` alpha file as a fallback instead of its own file, violating the "never alias" convention every other patch in this repo follows. Fixed before the patch was ever applied.
