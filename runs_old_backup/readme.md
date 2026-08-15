# Semantic-guard variants: definitions and full-scale AIME24 results

All guards below are built on `spec_casc_tok` (Narasimhan et al. 2025 /
Xia et al. 2026 Eq. 15): `pi_rej(v) = q(v)+eta*p(v)` for `v` in the trusted
top set `A = {u : p(u) >= (1-alpha)*max(p)}`, else `eta*p(v)`, with
`eta = 1 - sum_{u in A} q(u)`. `alpha -> -inf` is the strict limit (`A`
empty, `pi_rej = p`), not `alpha = 0`. Each guard below is a rule for
forcing `A` empty (or otherwise falling back toward strict) at specific
positions, on top of this base method. `lossless (strict)` is plain
speculative decoding (`p(x)/q(x) >= u`), `spec_casc_tok` is the unguarded
base method at a given alpha -- both are reference rows, not guards.

## Definitions

**`spec_casc_tok_semantic_guard`** ("override", narrow marker set): forces
`A` empty at the drafted position whenever the drafted token is one of an
18-id/5-word hesitation/self-correction set (`wait, hmm, let's, actually,
but`). Stateless, one round, one position at a time.

**`spec_casc_tok_semantic_guard_v2`** ("v2", wide marker set): identical
mechanism to the override guard, but a wider 35-id/14-word marker set
(adds `thus, we, so, now, let, compute, similarly, define, from` and
variants).

**`spec_casc_tok_semantic_guard_and`** ("AND", narrow marker set):
same narrow marker set as the override guard, but instead of overriding to
pure strict at a marker, accepts iff BOTH the lossless test AND
`spec_casc_tok`'s own relaxed test would accept (`min(p, pi_rej)` as the
effective target) -- provably never more lenient than the override guard
at any guarded position.

**`spec_casc_tok_semantic_guard_future_guard`** ("future-guard-strict",
parameter `K`): different trigger shape -- instead of gating the marker
token itself, arms a `K`-token trailing strict window the moment
`spec_casc_tok`'s own test *accepts* a marker (wide 35-id set). For the
next `K` verified positions, the accept test uses the raw lossless ratio
`p(x)/q(x) >= u` instead of `spec_casc_tok`'s blend. Cross-round state
(remaining-window count) is carried via a small per-batch-slot tensor
threaded through the Triton accept kernel itself.

**`spec_casc_tok_semantic_guard_future_guard_and`** ("future-guard-AND",
parameter `K`): same trigger shape as future-guard-strict, but AND-combined
inside the window instead of pure strict (same combination rule as the AND
guard, applied to the `K`-window instead of the marker position alone).

**`spec_casc_tok_hsr_guard`** ("hsr-guard", parameters `window`, `budget`,
`percentile`, `actuator_k`): non-lexical trigger, no token-identity check
at all. Computes S_32 (fixed 128-dim random projection of
`target_hidden_states` -- already produced every round for EAGLE3's own
drafting, so this reads data that's free -- trailing-32-mean cosine
similarity against the best match >=32 committed tokens back) for every
newly-committed real token. Self-calibrates a `percentile` threshold from
its own trailing `window`-token score history (per-generation, not one
fixed global cutoff); `budget` threshold-crossings within that window arm
a trailing `actuator_k`-token strict-verification window (`A` forced
empty, same mechanism as the override guard, just position-derived instead
of token-identity-derived). Round-granular Python/`/tmp`-file state, not
carried through the kernel. Defaults: `window=600, budget=25,
percentile=99.9, actuator_k=8`.

## Results, AIME24, alpha = 0.3

30-case full sweep, `spec_casc_tok`-family guards with a `K` parameter set
to 8 (future-guard variants) or the defaults above (hsr-guard):

| variant | accuracy | mean length | l̄ | total rounds | mean s/round | wall-time | hesitation words | mechanism check |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lossless (strict) | 23/30 (76.7%) | 10,043 | 2.2046 | 100,605 | 0.01227 | 1,234.8s | 4,455 | -- |
| **spec_casc_tok (baseline)** | **26/30 (86.7%)** | **9,440** | **2.4210** | **86,874** | 0.01241 | **1,078.2s** | **4,172** | 3.8% |
| + override (narrow) | 22/30 (73.3%) | 10,397 | 2.3999 | 98,277 | 0.01292 | 1,269.6s | 4,949 | 0.0% |
| + AND (narrow) | 22/30 (73.3%) | 10,964 | 2.3906 | 103,942 | 0.01294 | 1,345.3s | 4,821 | 0.0% |
| + v2 (wide, override) | 25/30 (83.3%) | 10,599 | 2.3986 | 97,540 | 0.01306 | 1,274.3s | 4,312 | 0.0% |
| + future-guard-strict K=4 | 22/30 (73.3%) | 10,397 | 2.3447 | 97,779 | 0.01295 | 1,266.3s | 4,869 | 4.1% |
| **+ future-guard-strict K=8** | **25/30 (83.3%)** | **9,303** | 2.3950 | **87,607** | 0.01298 | **1,137.2s** | **3,952** | 3.5% |
| + future-guard-AND K=8 | 23/30 (76.7%) | 10,460 | 2.3724 | 99,463 | 0.01295 | 1,288.2s | 4,460 | 4.0% |
| **+ hsr-guard** (budget=25, pct=99.9) | **26/30 (86.7%)** | **9,032** | 2.4040 | **85,177** | 0.02242¹ | 1,910.2s¹ | 4,108 | 5.00%² |

¹ hsr-guard's own wall-time/s-per-round was measured in a later session
than every other row in this table; a same-session, same-arm comparison
(baseline vs hsr-guard, both run back-to-back on the 16 overlapping cases)
showed 0.02228 vs 0.02242 s/round -- effectively no difference -- so the
0.01241-vs-0.02242 gap above is machine-load variance between sessions,
not a real property of the guard. Round-count and length are the reliable
cross-session metrics (deterministic given a fixed seed); wall-time is not.

² hsr-guard's mechanism check is defined differently from every guard
above it: fraction of ALL verified positions with the guard active
(position-based), not fraction of hesitation-marker words specifically
accepted via relaxation. Not directly comparable to the marker guards'
own "mechanism check" column, listed here for completeness only.

## Results, AIME24, alpha = 0.5

| variant | accuracy | mean length | l̄ | total rounds | mean s/round | wall-time | hesitation words | mechanism check |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_tok (baseline) | 22/30 (73.3%) | 10,495 | 2.4929 | 96,402 | 0.01258 | 1,212.9s | 4,532 | 5.0% |
| + future-guard-strict K=8 | 20/30 (66.7%) | 10,555 | 2.4484 | 97,984 | 0.01300 | 1,273.6s | 4,662 | 5.5% |

## Results, AIME24, alpha = 0.7

| variant | accuracy | mean length | l̄ | total rounds | mean s/round | wall-time | hesitation words | mechanism check |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| spec_casc_tok (baseline) | 22/30 (73.3%) | 10,337 | 2.6565 | 90,948 | 0.01262 | 1,147.4s | 4,894 | 7.3% |
| **+ future-guard-strict K=8** | **25/30 (83.3%)** | 12,239 | 2.5365 | 109,433 | 0.01297 | 1,419.9s | 5,699 | 6.9% |

Not run at alpha=0.5/0.7: override/AND/v2, future-guard-AND, hsr-guard,
future-guard-strict K=4.
