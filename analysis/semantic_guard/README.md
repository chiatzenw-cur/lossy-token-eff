# semantic_guard: hesitation-marker word counts

A lexical proxy for the "rambling/self-correction" failure mode the
top-level README infers indirectly from completion length and verifier
rounds. Here it's measured directly in the text: count occurrences of five
hesitation/self-correction markers —

    wait, hmm, let's, actually, but

— in each archived run's full completion text (`output.txt`: analysis +
final channel together, exactly as produced), grouped by case and by arm.
Matching is whole-word/whole-phrase, case-insensitive (`\bwait\b`, `\bhmm+\b`,
`\blet's\b`, `\bactually\b`, `\bbut\b`).

Source data: `runs/aime24_fresh` (180 runs, 30 cases × 6 arms) and
`runs/humaneval_fresh` (984 runs, 164 cases × 6 arms) — the same runs the
top-level README's tables are built from, read the same way
`scripts/summarize_arms.py` reads them.

Reproduce:

```
python3 analysis/semantic_guard/count_hesitation.py \
    --runs-root runs/aime24_fresh --out-prefix analysis/semantic_guard/results/aime24
python3 analysis/semantic_guard/count_hesitation.py \
    --runs-root runs/humaneval_fresh --out-prefix analysis/semantic_guard/results/humaneval
```

## Per-case comparison

One row per case, one column per arm, cell = total marker count for that
`(case, arm)` run — the full 30×6 and 164×6 breakdowns:

- [`results/aime24_case_by_arm.md`](results/aime24_case_by_arm.md) /
  [`.csv`](results/aime24_case_by_arm.csv) (per-marker columns in the CSV)
- [`results/humaneval_case_by_arm.md`](results/humaneval_case_by_arm.md) /
  [`.csv`](results/humaneval_case_by_arm.csv)

## Total comparison by method

### AIME24 (30 cases × 6 arms, 180 runs)

| arm | runs | wait | hmm | let's | actually | but | total | mean/run | per 1k completion tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| r_fuzzy (α=0.3) | 30 | 4170 | 115 | 3773 | 3345 | 6646 | **18049** | 601.6 | 30.8 |
| spec_casc_opt (α=0.05) | 30 | 4973 | 74 | 3155 | 2698 | 5718 | **16618** | 553.9 | 25.9 |
| cactus (α=0.25) | 30 | 3105 | 107 | 3283 | 2438 | 6976 | **15909** | 530.3 | 28.4 |
| mentored_dec (α=0.37) | 30 | 1108 | 35 | 1675 | 699 | 2396 | **5913** | 197.1 | 16.0 |
| strict | 30 | 835 | 25 | 1250 | 538 | 1807 | **4455** | 148.5 | 14.8 |
| spec_casc_tok (α=0.3) | 30 | 708 | 12 | 1224 | 385 | 1843 | **4172** | 139.1 | 14.7 |

### HumanEval (164 cases × 6 arms, 984 runs)

| arm | runs | wait | hmm | let's | actually | but | total | mean/run | per 1k completion tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| r_fuzzy (α=0.3) | 164 | 1042 | 39 | 1286 | 767 | 3107 | **6241** | 38.1 | 21.3 |
| cactus (α=0.25) | 164 | 505 | 32 | 937 | 507 | 2719 | **4700** | 28.7 | 19.1 |
| spec_casc_opt (α=0.05) | 164 | 771 | 22 | 893 | 581 | 2303 | **4570** | 27.9 | 18.0 |
| strict | 164 | 150 | 9 | 498 | 142 | 1202 | **2001** | 12.2 | 12.8 |
| spec_casc_tok (α=0.3) | 164 | 139 | 3 | 450 | 115 | 1274 | **1981** | 12.1 | 13.1 |
| mentored_dec (α=0.37) | 164 | 153 | 4 | 487 | 122 | 1202 | **1968** | 12.0 | 12.6 |

### Combined (both benchmarks, 194 runs/arm)

| arm | runs | wait | hmm | let's | actually | but | total | mean/run | per 1k completion tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| r_fuzzy (α=0.3) | 194 | 5212 | 154 | 5059 | 4112 | 9753 | **24290** | 125.2 | 27.7 |
| spec_casc_opt (α=0.05) | 194 | 5744 | 96 | 4048 | 3279 | 8021 | **21188** | 109.2 | 23.7 |
| cactus (α=0.25) | 194 | 3610 | 139 | 4220 | 2945 | 9695 | **20609** | 106.2 | 25.5 |
| mentored_dec (α=0.37) | 194 | 1261 | 39 | 2162 | 821 | 3598 | **7881** | 40.6 | 15.0 |
| strict | 194 | 985 | 34 | 1748 | 680 | 3009 | **6456** | 33.3 | 14.1 |
| spec_casc_tok (α=0.3) | 194 | 847 | 15 | 1674 | 500 | 3117 | **6153** | 31.7 | 14.2 |

Full breakdown incl. per-run rows: [`results/*_totals_by_arm.csv`](results/),
[`results/*_all_rows.json`](results/).

## Total comparison by method, normalized by length

The tables above conflate two effects: bad arms produce more hesitation
words *and* longer completions, so raw totals partly just reflect
`mean_completion_length` (already in the top-level README). Dividing out
completion length — hesitation words per 1,000 completion tokens — isolates
the rate:

### AIME24 (ascending by rate)

| arm | total words | total completion tokens | hesitation words / 1k completion tok |
|---|---:|---:|---:|
| spec_casc_tok (α=0.3) | 4,172 | 283,193 | **14.73** |
| strict | 4,455 | 301,299 | **14.79** |
| mentored_dec (α=0.37) | 5,913 | 369,539 | **16.00** |
| spec_casc_opt (α=0.05) | 16,618 | 642,316 | **25.87** |
| cactus (α=0.25) | 15,909 | 560,354 | **28.39** |
| r_fuzzy (α=0.3) | 18,049 | 585,171 | **30.84** |

### HumanEval (ascending by rate)

| arm | total words | total completion tokens | hesitation words / 1k completion tok |
|---|---:|---:|---:|
| mentored_dec (α=0.37) | 1,968 | 156,464 | **12.58** |
| strict | 2,001 | 156,892 | **12.75** |
| spec_casc_tok (α=0.3) | 1,981 | 150,681 | **13.15** |
| spec_casc_opt (α=0.05) | 4,570 | 253,579 | **18.02** |
| cactus (α=0.25) | 4,700 | 246,499 | **19.07** |
| r_fuzzy (α=0.3) | 6,241 | 293,005 | **21.30** |

The rate alone reproduces the same two-cluster split as the raw totals,
on both benchmarks, with an *identical arm ordering inside each cluster*
between AIME24 and HumanEval (`spec_casc_tok`/`strict`/`mentored_dec`
low, `spec_casc_opt`/`cactus`/`r_fuzzy` high — only the two low-cluster
arms and two high-cluster arms swap places between benchmarks, `r_fuzzy`
stays highest on both). So the length effect is real (raw totals move a lot
more than rates do) but it isn't the whole story — the *rate* of hesitation
language is itself roughly 1.3–1.9× higher in the bad cluster on both
benchmarks, not just the volume.

Files: [`results/aime24_normalized_by_arm.md`](results/aime24_normalized_by_arm.md) /
[`.csv`](results/aime24_normalized_by_arm.csv),
[`results/humaneval_normalized_by_arm.md`](results/humaneval_normalized_by_arm.md) /
[`.csv`](results/humaneval_normalized_by_arm.csv).

## How many of these were accepted only because of the relaxed verifier

Every relaxed patch's trace already carries the counterfactual needed to
answer this precisely: `patches/relaxation_trace.py` computes
`lossy_only_accepted` on every `accepted_draft` row in `proposals.jsonl` --
`true` exactly when the relaxed rule accepted a draft token that the
strict rule (`p/q >= u`, the same `p`, `q`, `u` the relaxed rule used) would
have rejected. It's computable from a single relaxed run because strict
acceptance is a deterministic function of quantities the relaxed rule
already evaluated -- see that module's docstring for the per-method
counterfactual shapes. `recovered`/`bonus` rows never carry it: rejection
recovery and the per-round bonus token use the same mechanism regardless of
which rule is in force.

`analysis/semantic_guard/count_relaxed_only_hesitation.py` maps that flag
onto text: it reconstructs each run's emitted-token stream in order from
`proposals.jsonl`, decodes it token-by-token with the same o200k_harmony
encoding the model was served with (buffering across tokens when a
multi-byte character's bytes split across two adjacent tokens, so every
token gets an exact character span), re-runs `count_hesitation.py`'s same
five marker regexes over the reconstructed text, and for each match checks
whether any token spanning it has `lossy_only_accepted: true`. `strict` runs
score 0/0 by construction (`lossy_would_accept == strict_would_accept`
there always) and are kept in the table rather than dropped, so the
comparison stays uniform across all six arms.

**Correction (found during the `r-fuzzy-semantic-guard` pilot below, fixed
in the current script):** the original version of `reconstruct()` buffered
tokens across a suspected multi-byte UTF-8 split with no cap on how long it
would keep accumulating. A UTF-8 character never needs more than 3
continuation bytes, so a genuine split always resolves within a handful of
extra tokens -- but on rare, genuinely anomalous single-token emissions (one
confirmed by hand: token id 35353, an orphaned lead byte with no matching
continuation token following it, unlike its normal pairing) the buffer would
never resolve and silently swallowed the *rest of the document* into one
merged span, whose `lossy_only_accepted` flag was the OR of every token in
it -- overcounting relaxed-only hits for any hesitation word that happened
to fall inside that span. Caught on one pilot run where it produced 1,965
spans for a 5,029-token completion (average >2.5 raw tokens per "token").
Fixed by capping the buffer at 4 tokens and falling back to a lossy
per-token decode beyond that, attributing only that one token's own flag.
The tables below are the corrected numbers; on HumanEval (much shorter
completions) they're unchanged from the original run -- the anomaly never
triggered there. On AIME24 only `r_fuzzy` and `cactus` moved, by 1-2
percentage points, not a qualitative change (numbers below vs. superseded
first-pass numbers: r_fuzzy 27.5%→26.2%, cactus 26.6%→24.5%; spec_casc_opt,
mentored_dec, spec_casc_tok, strict were exactly unchanged, meaning that
anomaly never triggered in their runs either).

### AIME24 (sorted by % of hesitation words that are relaxed-only)

| arm | hesitation words | relaxed-only | % of hesitation words | % of *all* tokens (baseline) | enrichment |
|---|---:|---:|---:|---:|---:|
| r_fuzzy (α=0.3) | 18,052 | 4,728 | **26.2%** | 20.49% | 1.28× |
| cactus (α=0.25) | 15,911 | 3,893 | **24.5%** | 21.96% | 1.11× |
| spec_casc_opt (α=0.05) | 16,620 | 2,058 | **12.4%** | 12.47% | 0.99× |
| mentored_dec (α=0.37) | 5,913 | 655 | **11.1%** | 5.26% | 2.11× |
| spec_casc_tok (α=0.3) | 4,173 | 157 | **3.8%** | 2.60% | 1.45× |
| strict | 4,456 | 0 | 0.0% | 0.00% | — |

### HumanEval (unaffected by the correction above)

| arm | hesitation words | relaxed-only | % of hesitation words | % of *all* tokens (baseline) | enrichment |
|---|---:|---:|---:|---:|---:|
| r_fuzzy (α=0.3) | 6,245 | 1,541 | **24.7%** | 17.60% | 1.4× |
| cactus (α=0.25) | 4,700 | 1,154 | **24.6%** | 17.55% | 1.4× |
| spec_casc_opt (α=0.05) | 4,571 | 587 | **12.8%** | 11.07% | 1.2× |
| mentored_dec (α=0.37) | 1,969 | 209 | **10.6%** | 4.88% | 2.2× |
| spec_casc_tok (α=0.3) | 1,981 | 92 | **4.6%** | 2.59% | 1.8× |
| strict | 2,003 | 0 | 0.0% | 0.00% | — |

### Combined (both benchmarks)

| arm | hesitation words | relaxed-only | % of hesitation words | % of *all* tokens (baseline) | enrichment |
|---|---:|---:|---:|---:|---:|
| r_fuzzy (α=0.3) | 24,297 | 6,269 | **25.8%** | 19.52% | 1.32× |
| cactus (α=0.25) | 20,611 | 5,047 | **24.5%** | 20.61% | 1.19× |
| spec_casc_opt (α=0.05) | 21,191 | 2,645 | **12.5%** | 12.07% | 1.03× |
| mentored_dec (α=0.37) | 7,882 | 864 | **11.0%** | 5.15% | 2.13× |
| spec_casc_tok (α=0.3) | 6,154 | 249 | **4.1%** | 2.60% | 1.56× |
| strict | 6,459 | 0 | 0.0% | 0.00% | — |

"% of all tokens" is the same `lossy_only_accepted` rate computed over
*every* emitted token in the run, not just hesitation-marker words --
included as a baseline so "X% of hesitation words are relaxed-only" can be
read against "Y% of an average word is relaxed-only" rather than in
isolation. "Enrichment" is just the ratio of the two.

**Reading this**: about a quarter of the hesitation words on `r_fuzzy` and
`cactus` — the two worst-accuracy arms on AIME24 — would very likely not be
in the completion at all had strict verification run instead; on
`spec_casc_tok`, the one arm that beats strict on both benchmarks, that's
under 5%. And hesitation words are consistently *enriched* for relaxed-only
acceptance relative to the average token (0.99–2.2× across every relaxed
arm on both benchmarks, essentially never below 1.0×, `spec_casc_opt` on
AIME24 the only case that dips fractionally under) — so it's not just that
bad arms accept more tokens via relaxation overall (true, and already
visible in the "% of all tokens" baseline column tracking the same bad/good
split as everything else in this analysis); the relaxed verifier is mostly
*somewhat* more likely to be the reason a hesitation word exists than the
reason an arbitrary token exists, on nearly every relaxed arm measured.

Files: [`results/*_relaxed_only_case_by_arm.csv`](results/) (per-run,
per-marker detail), [`results/*_relaxed_only_totals_by_arm.csv`](results/),
[`results/*_relaxed_only_all_rows.json`](results/),
[`results/combined_relaxed_only_totals_by_arm.csv`](results/combined_relaxed_only_totals_by_arm.csv).

Reproduce (after `count_hesitation.py`, requires the `.venv-vllm`
environment for `openai-harmony`):

```
source .venv-vllm/bin/activate
python3 analysis/semantic_guard/count_relaxed_only_hesitation.py \
    --runs-root runs/aime24_fresh --out-prefix analysis/semantic_guard/results/aime24
python3 analysis/semantic_guard/count_relaxed_only_hesitation.py \
    --runs-root runs/humaneval_fresh --out-prefix analysis/semantic_guard/results/humaneval
```

## Reading these

- **Both benchmarks split into the same two clean clusters, independent of
  the accuracy numbers used to define them.** `{spec_casc_tok, strict,
  mentored_dec}` sit at 1,968–2,001 hesitation words on HumanEval and
  4,172–5,913 on AIME24; `{cactus, spec_casc_opt, r_fuzzy}` sit at
  4,570–6,241 and 15,909–18,049 respectively — a 2.3–3.6× gap between
  clusters on both benchmarks, with no overlap. This is exactly the
  three-good-arms/three-bad-arms split the top-level README's accuracy
  table shows, recovered here from word counts in the text alone, not from
  correctness or length.
- **The gap survives length-normalization.** Raw totals are partly just
  "bad arms produce longer completions" (also true, and already reported as
  `mean_completion_length` in the top-level README) — but `per 1k
  completion tok` shows the *rate* is elevated too, not only the volume:
  ~14–15 hesitation words per 1k tokens for the good cluster vs ~18–31 for
  the bad cluster, roughly a 1.3–2× rate difference on top of the length
  difference.
- **Within a cluster, hesitation-word rank doesn't reproduce the accuracy
  rank exactly.** `spec_casc_tok` is the best-scoring arm on both
  benchmarks and is the lowest-hesitation arm on AIME24 (4,172, vs strict's
  4,455 and mentored_dec's 5,913) — but on HumanEval `mentored_dec` edges it
  out slightly (1,968 vs 1,981, and 12.0 vs 12.1 mean/run), with `strict`
  a close third (2,001). Small margins within the low cluster, not a
  contradiction of the cluster split above.
- **`but` dominates every arm's count** (the largest single column
  everywhere) and is the least specific of the five markers — it's ordinary
  prose as often as it's a self-correction. It's reported broken out by
  marker for exactly this reason: so its high base rate doesn't drown the
  sharper, lower-volume signal from `wait`/`hmm`/`let's`/`actually`, which
  individually show the same two-cluster split (e.g. AIME24 `wait`: 3,105–4,973
  for the bad cluster vs 708–1,108 for the good one).

## Methodology notes / limitations

- This is a **lexical proxy, not a semantic classifier**: it counts words,
  not verified instances of hesitation or self-correction. `but` in
  particular over-counts (see above). No attempt is made to disambiguate
  e.g. `wait` used mid-arithmetic ("wait 24 minutes") from `wait` used as a
  hesitation marker — both are rare enough in this domain (AIME word
  problems, HumanEval docstrings) not to move the totals much, but it's
  worth naming as a source of noise rather than leaving implicit.
- Counts are taken over the **whole completion** (`output.txt`, analysis +
  final channel together), not restricted to the `analysis` channel where
  most hesitation language actually lives. Restricting to `analysis` only
  would very likely sharpen the signal further, since the `final` channel is
  comparatively terse; not done here to keep the script's one read of
  `output.txt` as the single source of truth rather than re-parsing channel
  boundaries `grade_aime.py`/`grade_humaneval.py` already parse for a
  different purpose.
- The five-word list itself is not derived from anything in this repo — it's
  the markers named for this analysis, not a validated instrument. Treat the
  clustering above as a real, reproducible pattern in this specific word
  list against this specific data, not as a calibrated "hesitation score."

## Pilot experiment: `r-fuzzy-semantic-guard`

Tests a hypothesis directly rather than just observing it: if hesitation
words are disproportionately relaxed-only-accepted, and relaxed-only
acceptance seeds trajectory corruption, does forcing *strict* verification
specifically at hesitation-marker token ids (leaving every other token's
acceptance rule untouched) reduce rambling? Implemented as a real vLLM
patch, not a simulation -- see `patches/vllm-0.26.0-r-fuzzy-semantic-guard.patch`
and its module comment for the mechanism (an unconditional OR of a
hesitation-marker token-id check into r-fuzzy's own `defer_mask`, computed
in plain PyTorch before the kernel launch; the kernel itself is
byte-identical to plain r-fuzzy's) and `patches/README.md`'s "A sixth,
experimental variant" section for how it's wired into the repo as a proper
6th arm.

**Design**: `r_fuzzy` vs. `r_fuzzy_semantic_guard`, both α=0.3, 8 AIME24
cases, one fresh server per run (16 runs total), collected in the same
batch back-to-back for a clean A/B -- re-running the `r_fuzzy` baseline
rather than reusing `runs/aime24_fresh`'s existing data, since this repo's
own tooling documents real run-to-run GPU nondeterminism even at a fixed
seed (`remote/run_server_vllm.sh`'s comment: three fresh servers, same
prompt+seed, gave 1686/1505/1640 tokens). Cases were **not** randomly
sampled: chosen as the 8 AIME24 cases where plain `r_fuzzy` showed the most
relaxed-only-accepted hesitation words in the full 30-case dataset above
(case_005, 028, 002, 020, 021, 015, 011, 003) -- deliberately the arm's
worst/most-rambling cases, to maximize sensitivity for a small pilot. This
means the pilot is **not a representative sample**; effect sizes here
should not be extrapolated to the full 30-case average without a broader
follow-up run.

**Mechanism check passes cleanly.** Re-running this section's own
instrumentation on the pilot traces:

| arm | hesitation words | relaxed-only | % relaxed-only |
|---|---:|---:|---:|
| r_fuzzy (α=0.3) | 8,522 | 2,376 | 27.9% |
| r_fuzzy_semantic_guard (α=0.3) | 4,242 | **0** | **0.0%** |

Zero, exactly -- every hesitation-marker token in all 8 guarded runs went
through strict verification, with no exceptions. (The guard's own
`_semantic_guard_mask` only covers the *leading-space* single-token form of
each marker, documented explicitly in the patch as a known gap; 0/4,242
across this pilot says that gap didn't bite here, not that it's provably
airtight in general.)

**Effect on length/rounds is large and consistent.** Aggregate:
`mean_completion_len` 31,863 → 21,673 tokens (**-32%**), `mean_verifier_rounds`
6,369 → 4,492 (**-29%**). Per case (`output_tokens`, `r_fuzzy` →
`r_fuzzy_semantic_guard`):

| case | r_fuzzy | +guard | change | verdict change |
|---|---:|---:|---:|---|
| case_011 | 27,824 | 5,027 | **-82%** | correct → correct |
| case_015 | 31,476 | 14,562 | -54% | wrong → wrong |
| case_020 | 31,809 | 15,481 | -51% | wrong → wrong |
| case_003 | 32,768 (cap) | 16,785 | -49% | no_answer → wrong |
| case_005 | 32,768 (cap) | 23,223 | -29% | no_answer → wrong |
| case_002 | 32,768 (cap) | 32,768 (cap) | 0% | no_answer → no_answer |
| case_028 | 32,768 (cap) | 32,768 (cap) | 0% | wrong → no_answer |
| case_021 | 32,722 | 32,768 (cap) | +0.1% | **correct → no_answer** |

**Does the guard's own per-round check cost hidden wall-time not visible in
round counts?** Round counts and `l_bar` are event-count metrics -- they
capture the *decision* effect (a guarded position forced to the strict test
can end a round earlier than it otherwise would have), but not the raw GPU
time the guard's own check (`torch.isin` + a `defer_mask` OR, run every
round regardless of whether it fires) adds per round. Checked directly with
`analysis/semantic_guard/check_round_throughput.py`, using `run.json`'s own
`wall_time_seconds` (pure generation time, excludes the ~80-100s fresh-
server startup that's in the outer per-run time reported elsewhere) divided
by round count:

| | r_fuzzy | +guard | change |
|---|---:|---:|---:|
| mean s/round | 0.01249 | 0.01275 | **+2.1%** |
| total generation wall-time (8 cases) | 636.2s | 458.1s | **-28.0%** |

The overhead is real and consistent (every one of the 8 cases shows it,
non-overlapping ranges: guard 0.0126-0.0129 s/round vs. r_fuzzy's
0.0124-0.0126) -- but it's ~2% per round against a 29% reduction in total
round *count*, so the round-count savings dominate by more than an order of
magnitude and the net effect on measured generation wall-time is still a
solid -28%, not eaten by it. Re-check at full-sweep scale (n=30/n=164)
before trusting the exact percentage, since this is 8 cases: `python3
analysis/semantic_guard/check_round_throughput.py --runs-root
runs/aime24_fresh --tags rFuzzy0p3 rFuzzySemanticGuard0p3` (swap
`--runs-root`/tags for HumanEval).

Six of eight cases got shorter, several dramatically (case_011 finished in
a fifth of the tokens and stayed correct). Two cases that previously
rambled all the way to the 32,768-token cap without ever reaching a
`\boxed{}` answer (case_003, case_005) now terminate properly, well under
the cap -- the exact failure mode this intervention targets, fixed in both
instances, even though the answer they land on is wrong rather than right.

**Accuracy on this 8-case adversarial subset moved from 2/8 to 1/8** --
case_021 is the one regression (a case `r_fuzzy` got *correct* now hits the
token cap instead), and no case flipped into newly-correct. At n=8 this is
one case's worth of noise, not a resolved verdict either way: the length
effect is large enough to trust from 8 cases, the accuracy effect is not.
What the case-by-case table shows that the headline 2/8→1/8 doesn't is that
the failures aren't uniform -- two genuinely regressed-in-status cases
became *better-behaved* failures (finishing instead of rambling to the
cap), against one genuine regression (correct → no_answer).

**Open questions this pilot left, and their status:**
1. ~~Does the length/round reduction hold on a *random* (not
   worst-case-selected) sample, and at the full 30-case scale where the
   accuracy comparison has enough cases to be more than one flip's worth of
   noise?~~ **Answered below ("Full-scale results")**: yes on
   length/rounds (smaller effect than the pilot suggested), and the
   accuracy cost is real too, not noise.
2. Is case_021's regression characteristic (the guard forcing a strict
   re-verification that happens to derail an otherwise-converging
   trajectory) or a fluke -- worth reading that run's trace directly rather
   than only its summary stats. **Still open** -- with -9 cases combined
   at full scale, worth doing now more than when this was one flip out of 8.
3. Does the same intervention help the *other* two bad-cluster arms
   (`cactus`, `spec_casc_opt`), which would need their own kernel-tensor
   version of the guard (see the parent conversation's design discussion --
   their relaxation knob is a scalar baked into the Triton kernel, not a
   pre-computed Python-side mask like r-fuzzy's, so guarding them costs a
   real kernel change, not a one-line addition). **Still open**, and less
   motivated now that v1's full-scale result on `r_fuzzy` is a net accuracy
   cost rather than a win to extend.

Reproduce:

```
source .venv-vllm/bin/activate
python3 patches/apply.sh r-fuzzy-semantic-guard   # if not already installed
python3 scripts/fresh_server_replay.py \
    --arms r_fuzzy r_fuzzy_semantic_guard \
    --cases case_005 case_028 case_002 case_020 case_021 case_015 case_011 case_003 \
    --r-fuzzy-alpha 0.3 --r-fuzzy-semantic-guard-alpha 0.3 \
    --prompt-root prompts/aime24 --runs-root runs/semantic_guard_pilot/aime24 \
    --log-root logs/semantic_guard_pilot/aime24 --max-new-tokens 32768
python3 scripts/summarize_arms.py --runs-root runs/semantic_guard_pilot/aime24 --prompt-root prompts/aime24
python3 analysis/semantic_guard/count_relaxed_only_hesitation.py \
    --runs-root runs/semantic_guard_pilot/aime24 --out-prefix analysis/semantic_guard/results/pilot_aime24
```

Full per-run detail: [`runs/semantic_guard_pilot/aime24/summary.json`](../../runs/semantic_guard_pilot/aime24/summary.json),
[`results/pilot_aime24_relaxed_only_totals_by_arm.csv`](results/pilot_aime24_relaxed_only_totals_by_arm.csv).

## Full-scale results: `r_fuzzy` vs. `r_fuzzy_semantic_guard`, all cases

Answers open question 1 above. `r_fuzzy_semantic_guard` run across all 30
AIME24 cases and all 164 HumanEval cases (194 fresh-server runs, into
`runs/aime24_fresh`/`runs/humaneval_fresh` alongside the other six arms, not
a separate pilot directory) and compared against the existing `r_fuzzy`
baseline already collected there -- not re-run fresh this time, unlike the
8-case pilot: at n=30/n=164 the run-to-run GPU nondeterminism that justified
a paired fresh baseline for 8 cases averages out enough that reusing the
existing baseline is the better time/signal trade-off (~6h saved against a
few bit-level-different runs' worth of noise in an aggregate this large).

| | AIME24 (n=30) | HumanEval (n=164) | Combined (n=194) |
|---|---|---|---|
| accuracy: **strict (lossless)** | **23/30 (76.7%)** | **156/164 (95.1%)** | **179/194 (92.3%)** |
| accuracy: r_fuzzy | 13/30 (43.3%) | 93/164 (56.7%) | 106/194 (54.6%) |
| accuracy: +guard | **11/30 (36.7%)** | **86/164 (52.4%)** | **97/194 (50.0%)** |
| accuracy change | -2 cases (-6.7pp) | -7 cases (-4.3pp) | -9 cases (-4.6pp) |
| mean completion length: **strict** | **10,043** | **957** | **2,362** |
| mean completion length: r_fuzzy → +guard | 19,506 → 16,942 | 1,787 → 1,525 | 4,527 → 3,909 |
| length change | -13.1% | -14.7% | -13.6% |
| mean verifier rounds: **strict** | **3,355** | **290.0** | **764.0** |
| mean verifier rounds: r_fuzzy → +guard | 3,831 → 3,457 | 343.1 → 303.8 | 882.4 → 791.4 |
| rounds change | -9.7% | -11.5% | -10.3% |
| mean l_bar: **strict** | **2.21** | **2.52** | -- |
| mean l_bar: r_fuzzy → +guard | 4.129 → 3.957 | 4.205 → 4.057 | -4.2% / -3.5% |
| hesitation words: **strict** | **4,455** | **2,001** | **6,456** |
| hesitation words: r_fuzzy → +guard | 18,052 → 11,984 | 6,245 → 3,947 | 24,297 → 15,936 |
| hesitation words, % relaxed-only | strict: **0%** (no relaxed accepts by construction); r_fuzzy 26.2% → **0.01%** | strict: **0%**; r_fuzzy 24.7% → **0.03%** | strict: **0%**; r_fuzzy 25.8% → **0.01%** |
| mean s/round: **strict** | **0.01227** | **0.01305** | **0.01252** |
| mean s/round (throughput tax): r_fuzzy → +guard | 0.01241 → 0.01273 (+2.6%) | 0.01304 → 0.01353 (+3.8%) | 0.01261 → 0.01299 (+3.0%) |
| total generation wall-time: **strict** | **1,234.8s** | **618.7s** | **1,853.5s** |
| total generation wall-time: r_fuzzy → +guard | 1,425s → 1,320s (-7.4%) | 731.5s → 671.7s (-8.2%) | 2,157s → 1,992s (-7.6%) |

`strict` rows are the already-published n=30/n=164 baseline from the
top-level README (accuracy, l_bar, completion length, rounds) plus two
rows computed fresh here (hesitation words via `count_hesitation.py`'s
existing per-arm totals; throughput/wall-time via
`check_round_throughput.py --tags strict rFuzzy0p3 rFuzzySemanticGuard0p3`,
cross-checked: `total_tokens / runs` from that script reproduces the
published mean completion length exactly, e.g. AIME24 301,303/30=10,043.4).
**Puts the guard's savings in context**: strict is already ~1.9x shorter
than the guard on AIME24 (10,043 vs 16,942) and ~1.6x shorter on HumanEval
(957 vs 1,525), while scoring far higher (76.7%/95.1% vs the guard's
36.7%/52.4%) -- the guard recovers part of the length gap `r_fuzzy` opened
against strict, but at a further accuracy cost stacked on top of what
`r_fuzzy` had already paid, not a step toward strict on quality.

**The mechanism check still holds essentially perfectly at full scale** --
0.01%/0.03% relaxed-only, i.e. 2 leftover hesitation-word matches out of
15,936 across all 194 runs (the same known coverage gap discussed above:
bare no-leading-space forms this guard's fixed id list doesn't cover).

**But the pilot's efficiency numbers were inflated by its case selection,
and the accuracy cost is real, not pilot noise.** The 8-case pilot (chosen
as `r_fuzzy`'s *most* rambling cases) showed -28% to -32% on
length/rounds/wall-time; the full, representative sample shows -7% to
-15% on the same metrics -- a real, consistent, positive effect, just far
smaller than the pilot implied once averaged over ordinary cases rather
than worst-case ones. The accuracy question the pilot left open (2/8→1/8,
"one case's worth of noise, not resolved either way") is answered now:
**both benchmarks lose accuracy under the guard, independently and in the
same direction** (-6.7pp AIME24, -4.3pp HumanEval) -- two separate
benchmarks agreeing is a real signal, not the same flip counted twice.

**Verdict**: this specific intervention -- forcing strict verification at
five hesitation-marker tokens on top of `r_fuzzy` -- reliably does exactly
what it's mechanistically built to do (eliminate relaxed-only acceptance at
those tokens, cut length/rounds/hesitation-word volume by a real but modest
amount, at a real but small per-round throughput cost) and reliably fails
to do what motivated building it (make `r_fuzzy` more accurate by
suppressing corruption seeded at those specific tokens). At the scale
tested, it trades a consistent ~4-7pp of accuracy for a ~7-15% cut in
length/rounds -- not a free efficiency win, and not a fix for the
underlying accuracy gap between `r_fuzzy` and `strict`/`spec_casc_tok`
this whole analysis started from.

Reproduce:

```
source .venv-vllm/bin/activate
python3 scripts/fresh_server_replay.py \
    --arms r_fuzzy_semantic_guard --cases $(ls prompts/aime24 | grep '^case_') \
    --r-fuzzy-semantic-guard-alpha 0.3 --prompt-root prompts/aime24 \
    --runs-root runs/aime24_fresh --log-root logs/aime24_fresh --max-new-tokens 32768
python3 scripts/fresh_server_replay.py \
    --arms r_fuzzy_semantic_guard --cases $(ls prompts/humaneval | grep '^case_') \
    --r-fuzzy-semantic-guard-alpha 0.3 --prompt-root prompts/humaneval \
    --runs-root runs/humaneval_fresh --log-root logs/humaneval_fresh --max-new-tokens 9000
python3 scripts/summarize_arms.py --runs-root runs/aime24_fresh --prompt-root prompts/aime24
python3 scripts/summarize_arms.py --runs-root runs/humaneval_fresh --prompt-root prompts/humaneval
python3 analysis/semantic_guard/count_relaxed_only_hesitation.py --runs-root runs/aime24_fresh --out-prefix analysis/semantic_guard/results/aime24_full7
python3 analysis/semantic_guard/count_relaxed_only_hesitation.py --runs-root runs/humaneval_fresh --out-prefix analysis/semantic_guard/results/humaneval_full7
python3 analysis/semantic_guard/check_round_throughput.py --runs-root runs/aime24_fresh --tags rFuzzy0p3 rFuzzySemanticGuard0p3
python3 analysis/semantic_guard/check_round_throughput.py --runs-root runs/humaneval_fresh --tags rFuzzy0p3 rFuzzySemanticGuard0p3
```

## `r-fuzzy-semantic-guard-v2`: a wider marker set, not yet run

Built (patch, tests, full registry wiring -- see `patches/README.md`'s "A
seventh, wider variant" section) but not yet evaluated: v1's 5 hesitation
markers plus 9 generic reasoning-transition words (`Thus`, `We`, `So`,
`Now`, `Let`, `Compute`, `Similarly`, `Define`, `From`), added at the
user's request from a frequency count of AIME24 sentence-initial tokens.
Given v1's full-scale result above -- a real accuracy cost, not just a
pilot artifact -- v2's much broader intervention (guarding words that open
*correct* reasoning as often as corrupted reasoning, per the patch's own
module-comment caveat) is not obviously going the right direction either;
it's queued as a pilot-scale run (same 8 adversarial AIME24 cases as v1's
pilot) to check before considering anything larger.

## `r-fuzzy-window-entropy-guard`: a distributional sibling, pilot only

Gates on the *shape* of a rolling entropy window instead of token identity
(see `patches/README.md`'s "An eighth variant" section for the full
mechanism): strict verification only while mean(w64) < mean(w32) <
mean(w16) < mean(w8) holds for BOTH target and draft entropy jointly over
the trailing committed tokens -- deliberately unquantified, no calibrated
threshold, a pure shape check. Pilot only so far (same 8 AIME24 cases as
v1's pilot, directly comparable) -- see the data tables below for numbers.

A tracer bug was found and fixed mid-experiment: the trace's
`lossy_would_accept` field was being computed from the *merged* defer mask
(JSD OR the guard's own contribution), which makes it trivially equal
`strict_would_accept` at every guarded position regardless of what the
guard actually changed -- a tautology, not a finding. Fixed by keeping the
base method's own (JSD-only) decision separate and passing *that* to the
tracer; `relaxation_trace.py` now carries an explicit warning comment
against this mistake for future guards. The pilot's headline metrics
(accuracy/length/rounds) are unaffected -- those come from real generation,
not this field -- but the pilot has not yet been re-run with the fix, so
there's no corrected "did the guard change anything vs plain r_fuzzy"
number yet.

**Offline validation, independent of the guard itself**: ran the exact same
trigger condition against *plain, unguarded* `r_fuzzy` traces (same 8
cases) to check whether it actually marks loop onsets, deliberately without
the guard's own intervention confounding the answer. 5,737 onset events
found and saved *before* any judgment call
(`results/window_entropy_ramp_onsets.jsonl`, each carrying the full
at-onset distributional profile -- p, q, u, rank, entropy, KL, TV,
accept-rule flags -- joined straight from the trace). Streak lengths are
heavily fragmented (mode 1, max 19 across the whole set) -- manually
reading the 7 longest-streak (most sustained, best-case-for-the-hypothesis)
onsets gave **1 clear hit, 2 borderline, 4 clear false positives** (three
of which were coherent, even well-self-correcting reasoning that happened
to trigger the shape condition). Full annotated read:
`results/window_entropy_ramp_onsets_manual_read.md`. Reading: even at its
most sustained, this condition is noisy and low-precision as a standalone
per-token detector -- consistent with the pilot showing a real accuracy
cost rather than a clean win.

## Complete data tables (raw values, not just deltas)

Everything measured so far, as absolute numbers. Deltas/percentages
elsewhere in this document are derived from these; if the two ever
disagree, these are the source of truth (backed directly by
`runs/*/summary.json`, `analysis/semantic_guard/results/*_full7*.csv`, and
`analysis/semantic_guard/results/window_entropy_ramp_onsets.jsonl`).

### Semantic guard v1 -- pilot (8 AIME24 cases)

| metric | r_fuzzy | +semantic guard |
|---|---:|---:|
| accuracy | 2/8 (0.250) | 1/8 (0.125) |
| mean l_bar | 4.0086 | 3.8291 |
| mean completion length (tokens) | 31,862.88 | 21,672.75 |
| mean verifier rounds | 6,368.88 | 4,492.38 |
| errored/no-answer | 3 | 3 |

### Semantic guard v1 -- full sweep

**AIME24 (n=30 each)**

| metric | r_fuzzy | +semantic guard |
|---|---:|---:|
| accuracy | 13/30 (0.4333) | 11/30 (0.3667) |
| mean l_bar | 4.1287 | 3.9566 |
| mean completion length | 19,505.53 | 16,941.50 |
| mean verifier rounds | 3,830.63 | 3,457.27 |
| errored/no-answer | 5 | 6 |
| total hesitation words | 18,052 | 11,985 |
| hesitation words, relaxed-only | 4,728 (26.19%) | 1 (0.01%)* |
| total tokens (all positions) | 583,898 | 507,016 |
| all-token relaxed-only | 119,651 (20.49%) | 95,981 (18.93%) |
| total gen wall-time (s) | 1,425.4 | 1,320.4 |
| total verify rounds (throughput denom.) | 114,889 | 103,689 |
| mean s/round | 0.01241 | 0.01273 |

**HumanEval (n=164 each)**

| metric | r_fuzzy | +semantic guard |
|---|---:|---:|
| accuracy | 93/164 (0.5671) | 86/164 (0.5244) |
| mean l_bar | 4.2053 | 4.0566 |
| mean completion length | 1,786.63 | 1,524.74 |
| mean verifier rounds | 343.07 | 303.77 |
| errored/no-answer | 6 | 4 |
| total hesitation words | 6,245 | 3,951 |
| hesitation words, relaxed-only | 1,541 (24.68%) | 1 (0.03%)* |
| total tokens (all positions) | 293,655 | 250,812 |
| all-token relaxed-only | 51,686 (17.60%) | 41,855 (16.69%) |
| total gen wall-time (s) | 731.5 | 671.7 |
| total verify rounds | 56,100 | 49,654 |
| mean s/round | 0.01304 | 0.01353 |

**Combined (n=194 each)**

| metric | r_fuzzy | +semantic guard |
|---|---:|---:|
| accuracy | 106/194 (0.5464) | 97/194 (0.5000) |
| mean completion length | 4,526.7 | 3,908.8 |
| mean verifier rounds | 882.4 | 791.4 |

\* Tautological under the tracer bug described above -- fixed for the
window-entropy guard, not retroactively re-run for v1. Every other row in
these three tables is unaffected (real generation, not this field).

### Window-entropy guard -- pilot (8 AIME24 cases, all three arms)

| metric | r_fuzzy | +semantic guard | +window-entropy guard |
|---|---:|---:|---:|
| accuracy | 2/8 (0.250) | 1/8 (0.125) | 1/8 (0.125) |
| mean l_bar | 4.0086 | 3.8291 | 3.6528 |
| mean completion length | 31,862.88 | 21,672.75 | 28,229.88 |
| mean verifier rounds | 6,368.88 | 4,492.38 | 6,098.12 |
| errored/no-answer | 3 | 3 | 3 |
| rounds_offset_anomaly | 0 | 0 | 2 |
| total gen wall-time (s) | 636.2 | -- | 629.9 |
| total verify rounds | 50,943 | -- | 48,779 |
| total tokens | 254,903 | -- | 225,839 |
| mean s/round | 0.01249 | -- | 0.01291 |
| window guard fired (of all rows) | -- | -- | 15,874 / 225,876 (7.03%) |
| strict-decoding baseline rate (same joint condition) | -- | -- | 34,484 / 427,569 (8.065%) |

### Onset-detection offline check (plain, unguarded r_fuzzy, same 8 cases)

| | value |
|---|---:|
| total onset events found | 5,737 |
| streak length: mode | 1 |
| streak length: max | 19 |
| onsets with streak >=5 | 1,439 |
| onsets with streak >=10 | 210 |
| onsets with streak >=20 | 0 |
| top-7 longest streaks, manual read | 1 clear hit / 2 borderline / 4 false-positive |

## Single-event counterfactual: is the "loop" caused by one earlier accept, or by the visible onset itself?

Both detectors above (window-entropy ramp, hidden-state recurrence) mark
*where a loop is visibly under way*, and both turned out to be
low-precision **and** not locally enriched for `lossy_only_accepted` right
at the onset (~20% either way, essentially the population rate) -- i.e.
whatever happens at the visible onset isn't itself an unusually
lossy-influenced decision. The reframing that motivated this section: the
onset is plausibly *loop maintenance*, not *ignition* -- the actual bad
decision, if there is one, happened earlier, and a per-token guard reacting
at the onset is reacting too late by construction.

**Design.** For each of 3 manually-confirmed onsets, walk backward to the
nearest preceding token where `lossy_only_accepted=True` (strict would have
rejected the draft; the relaxed test accepted it anyway) and replay a
counterfactual: reconstruct the exact text prefix up to (not including)
that token, run it through a fresh server under **strict** verification
with a 1-token probe to get the token strict *actually* would have
committed there, splice that one token onto the prefix, and resume
generation normally under `r_fuzzy` (the arm the original loop occurred
under). Compare against the original run's own factual continuation from
that point (free -- already have it) as the "did nothing" control. 2 seeds
per case for robustness against generation stochasticity (no exact-replay
seeding is done anywhere in this repo's fresh-server protocol, so this is
a real independent resample each time, not a controlled replay of the same
draws).

**A real bug found while building this, disclosed rather than fixed
silently**: for short completions-endpoint probe requests, `proposals.jsonl`
consistently **drops the true first generated token** -- confirmed by
tokenizing `response.json`'s `text` field (authoritative -- it's what the
API actually returned) and finding one more token than the trace logged,
with the extra leading token accounting for the whole mismatch every time.
The single spliced token in this experiment is always taken from
`response.json`, never from the trace's row 0. Root cause not
investigated (out of scope here); flagged for anyone using
`proposals.jsonl` from a fresh, very-short completions request elsewhere in
this repo.

**A null result also found and disclosed**: case_020's nearest-preceding
`lossy_only_accepted` before onset 3673 (t=3669, original token `" +"`)
probed as a **non-divergent counterfactual** -- strict's independent
resample reproduced the exact same 5 tokens (`" + y ζ - "`) as the factual
run, token-for-token. Spliced back, this would just be a stochasticity
control, not a test of anything. Substituted for the next-nearest
lossy-only-accept before it (t=3659, original `"7"` -> strict `"2"`,
confirmed genuinely divergent) instead, and that substitution is used
throughout below.

**Results** (`analysis/semantic_guard/results/counterfactual_continuation_manifest.json`,
runs under `runs/counterfactual_continuation/`):

| case | intervention (orig -> counterfactual) | seed | outcome | tokens to resolve | original's own tokens-to-resolve from same point |
|---|---|---:|---|---:|---:|
| case_028, onset 31322 | t=31318: `"array"` -> `"aligned"` | 0 | **resolved**, boxed `707` | 343 | never (original hit the 32,768 cap, `finish=length`, no boxed answer at all) |
| | | 1 | **resolved**, boxed `17` | 214 | never |
| case_020, onset 3673 | t=3659: `"7"` -> `"2"` | 0 | **resolved**, boxed `1` | 3,239 | 28,150 (original's own run continues to L=31,809, `finish=stop`, from this point) |
| | | 1 | **not resolved** even at 8,192-token budget (4x seed 0's resolution length) | -- (capped) | 28,150 |
| case_020, onset 28786 | t=28770: `"312"` -> `" "` (space) | 0 | **resolved**, boxed `507`-equivalent, reached final channel | 1,646 | 3,039 (original continues to L=31,809 from this point) |
| | | 1 | **resolved**, boxed `507` | 4,813 | 3,039 |

**Reading the actual text, not just the stop reason**, matters here:

- **case_028 is the cleanest positive result.** The original's own
  continuation from the SAME point, read in the first ~300 tokens, already
  shows the failure mode in miniature: it reaches a tentative
  `\boxed{5}`, then immediately emits `<|end|><|start|>assistant<|channel|>analysis<|message|>`
  and restarts the entire derivation from scratch -- i.e. the pathology
  driving this run to the 32,768 cap looks like repeated
  *solve -> tentative answer -> full restart* macro-cycles, not simple
  token-level repetition. Both counterfactual seeds instead reach a boxed
  answer and stop cleanly, with no restart cycle, in under 350 tokens.
- **case_020 onset 3673 is a genuine mixed result, not a clean win.** Seed
  0 does eventually resolve (3,239 tokens -- ~8.7x fewer than the original
  needs from the same point) but resolves by giving up on the algebra
  ("Time is running... I think answer may be 1 (for product modulo 1000).
  Let's deliver.") rather than a rigorous derivation -- so "resolved" here
  means "stopped and boxed an answer," not "the reasoning got better."
  Seed 1 shows no such luck: still mid-derivation, still exploring
  resultant/polynomial-recurrence approaches, unresolved at 8,192 tokens.
  Both seeds' *content* is dense abstract-algebra hedging (`"Wait"`,
  `"Eh"`, `"Not."`) throughout, not obviously different in kind from the
  original's own continuation from this point -- distinct-trigram ratios
  are comparable, not dramatically higher for the counterfactual. This
  intervention point was already a second-choice substitution (see the
  null result above); plausibly it still isn't the true causal token.
- **case_020 onset 28786 resolves in both seeds, but the efficiency gain is
  smaller and inconsistent.** Seed 0 resolves faster than the original
  (1,646 vs 3,039 tokens). Seed 1 resolves *slower* than the original would
  from this point (4,813 vs 3,039), via a visibly messier path (extended
  hand-wavy arithmetic, a first wrong boxed guess (`511??`) before
  correcting to the right one) before landing on the same final answer
  (507) the original also reaches on its own. Not evidence against the
  hypothesis, but not a clean win either -- more like "this specific
  decision wasn't the load-bearing one, or wasn't the only one."

**Honest overall read**: this is n=3 onsets (6 base runs + 3 extended-budget
reruns = 9 total counterfactual generations), not a statistically powered
result -- treat every number above as a single data point, not a rate.
With that caveat: **one of three onsets (case_028) shows a strong, clean,
reproducible (2/2 seeds) ignition effect** -- flipping one earlier
relaxed-only-accept to what strict would have chosen prevented the
restart-loop pathology entirely, converting a 32,768-token unresolved
runaway into a <350-token clean resolution. **The other two (both from
case_020, the same underlying run)** show real but partial and
seed-inconsistent effects -- faster resolution in some seeds, no
improvement or even a slower path in others -- consistent with case_020's
loop not hinging on a single token the way case_028's apparently did, or
with the chosen intervention points not being the true causal ones (both
were derived from a heuristic -- "nearest preceding lossy-only-accept" --
not a search over all candidates). Doesn't generalize into a guard design
on its own (three onsets, one clean hit), but it does support the original
reframing that motivated this experiment: at least sometimes, the
actionable signal is an earlier acceptance decision, not the point where a
loop becomes visible -- exactly the kind of signal a per-token,
onset-reactive guard structurally cannot use.

Scripts: `analysis/semantic_guard/prepare_counterfactual_probe.py` (phase
A: prefix reconstruction + strict probe prompts),
`build_counterfactual_continuation.py` (phase B: single-token splice +
continuation prompts), `compare_counterfactual_continuation.py` (phase C:
side-by-side read-out against the factual control).

## Do macro-loops show hidden-state recurrence too?

The case_028 counterfactual read-out above noticed a *second* failure
shape distinct from the token-level repetition loops the recurrence
detector was built for: reading the original run's own continuation, the
model reaches `<|channel|>final<|message|>` (a real attempt at committing
to an answer), abandons it, and reopens
`<|end|><|start|>assistant<|channel|>analysis<|message|>` -- a full
re-derivation from scratch, in mostly *different* surface words each time.
A token-identity or entropy detector has no structural reason to fire on
this (the tokens genuinely differ across cycles); hidden-state recurrence,
which compares latent representations rather than token ids, might catch
it precisely because it doesn't care that the words changed.

**Finding the pattern exactly**: detected on raw committed token ids (not
decoded text, for exactness) as the 6-token sequence `<|end|> <|start|>
"assistant" <|channel|> "analysis" <|message|>` --
`find_macro_loop_restarts.py`. A real bug caught while building this: the
first version dropped the first hit per run, wrongly assuming it was the
model's own initial turn-open -- but this repo's rendered prompts already
end in the harmony `<|start|>assistant` marker (confirmed by inspecting
`rendered_prompt.txt` directly), so the model never generates that opening
sequence itself, and the drop was silently zeroing out case_028's only
hit. Fixed by not dropping anything.

**Across the 8 hidden-state-captured `r_fuzzy` AIME24 runs, exactly one
macro-loop restart exists**: case_028, at output_position 31478, following
an abandoned `final`-channel attempt opened at 30953. (The other cases
either reach `final` once and finish cleanly from there, e.g. case_020's
*this* independent draw -- L=31,809, `finish=stop`, no restart -- or never
reach `final` at all within the 32,768 cap, e.g. case_002/003/005: a third,
distinct failure shape, "never commits," not analyzed further here.) n=1
restart event -- everything below is a single case study, not a rate.

**Test 1 -- generic windowed recurrence (`S_k`, same score the earlier
per-token onset detector used), at the restart position, ranked against
this run's own score distribution:**

| k | S_k at restart | this run's percentile |
|---:|---:|---:|
| 8 | 0.898 | 91.3th |
| 16 | 0.858 | 94.9th |
| 32 | 0.825 | 98.0th |
| 64 | 0.802 | **99.4th** |

Genuinely elevated, and more so at longer windows -- unlike the per-token
onset check earlier in this document (where `lossy_only_accepted` rate at
the visible onset was ~flat against baseline), the *hidden-state signal
itself* here really is in the tail of the run's own distribution.

**Test 2 -- targeted: does the restart specifically resemble the abandoned
attempt it's replacing**, not just "some" earlier state:

- `cos(final-channel-open @ 30953, restart @ 31478) = 0.882`
- Ranked against the restart's similarity to all 28,709 earlier positions
  (mean 0.537, max 0.887): the abandoned-attempt point sits at the
  **100.0th percentile** -- essentially the single best match in the
  model's entire generation history up to that point.
- The actual single best match (0.887) is output_position 31413 -- not
  30953 itself, but only 65 tokens earlier and still inside the same
  abandoned `final`-channel attempt (which ran 30953 -> 31478). So the
  restart isn't returning to the exact *first* token of the previous
  attempt so much as to the *region* of latent space that whole abandoned
  attempt occupied.

**Read**: on this one confirmed example, hidden-state recurrence catches
the macro-loop cleanly by both measures -- generic windowed S_k already
lands in the 98-99th percentile without any bespoke tuning, and the
targeted attempt-to-attempt test is about as clean a positive as this kind
of check produces (100th percentile, best match in the whole run).
This is the flip side of the earlier disappointing precision numbers
against *token-repetition* loops (1 clear hit / 7 longest streaks):
hidden-state recurrence was always motivated by catching *semantic*
recurrence that survives a change of words, and a macro-loop -- same
underlying state, different derivation each time -- is exactly the shape
it should be suited for, whereas token-repetition loops (identical or
near-identical phrasing) are arguably closer to what a much cheaper
token/n-gram check could already catch. n=1 is not enough to act on
(a guard reacting to this pattern would need either a real population of
confirmed restarts to calibrate against, or the same "ignition, not
maintenance" caveat the token-loop work ran into -- this only shows the
signal exists AT the restart, not that it existed early enough to
prevent it). Gathering more macro-loop examples (more AIME24 cases with
hidden-state capture, screened via `find_macro_loop_restarts.py`) would be
the natural next step to turn this into more than a single case study.

Scripts: `find_macro_loop_restarts.py` (detection),
`check_macro_loop_hidden_recurrence.py` (both tests above).

## Does recurrence predict "unproductive" generation in general? (correction to the section above)

The macro-loop check above only looked at the restart TOKEN itself. This
scans every scored position across all 8 hidden-state-captured runs
(233,156 positions, `S32`, min_gap=32) against four "unproductive" proxies,
to check whether recurrence is a general early-warning signal or only
fires at that one specific boundary moment.

| proxy | comparison | result |
|---|---|---|
| hesitation markers (wait/hmm/let's/actually/but) | hesitation vs. other | 0.7821 vs. 0.7818 -- flat |
| `lossy_only_accepted` | lossy-only vs. other | 0.7833 vs. 0.7813 -- ~flat |
| target_entropy | pearson r | +0.12 (weak) |
| draft_entropy | pearson r | +0.10 (weak) |
| target_top1_shortfall | pearson r | -0.004 -- none |
| **case_028's own abandoned final-channel span (ground truth, not a proxy)** | inside vs. outside | **0.767 vs. 0.779 -- LOWER, 13th percentile against random same-length windows** |

The first three proxies show no practically meaningful relationship
(pooled correlations this weak, at n=233k, are not something to build a
detector on). The last row is the important one, because it's the one
place in this dataset "unproductive" is known rather than inferred: the
488 tokens that were later discarded outright (30953-31478, the abandoned
final-channel attempt) do **not** show elevated recurrence while they're
being generated -- if anything, slightly below-typical.

**This corrects, not confirms, the section above.** What that section
found was real -- the single RESTART token's hidden state strongly
resembles the abandoned attempt's own opening (98-99th percentile
windowed, ~100th percentile targeted) -- but it is a boundary-crossing
signature at the moment of loop-back, not a property that pervades the
"wasted" content leading up to it. A detector watching this signal
continuously would not have flagged the doomed final-answer attempt while
it was being written; it only spikes at the instant the model abandons it
and jumps back. Same ignition-vs-maintenance shape the token-level loop
work kept running into, now confirmed for a different signal too: knowing
*that* a loop-back happened is available at the restart; knowing *that
this content is heading nowhere* while it's still being generated is not,
at least not from this signal.

Full per-position data:
`analysis/semantic_guard/results/recurrence_vs_unproductive.jsonl`.
Script: `scan_recurrence_predicts_unproductive.py`.

## `spec-casc-tok-semantic-guard`: porting the token-marker guard to the arm that actually wins

Everything above tests the semantic-guard idea on `r_fuzzy` -- the
arm this whole investigation started from because it's `r_fuzzy` that
rambles. But `spec_casc_tok` is the one arm in the top-level README that
beats `strict` outright on both benchmarks (86.7% vs 76.7% AIME24, 95.7% vs
95.1% HumanEval, *and* shorter completions). The question here is
different: does the same intervention help an arm that's already good, or
is there nothing left to fix?

**A real bug found and fixed building this, disclosed before results
below**: while porting the guard, re-reading `r_fuzzy_semantic_guard`'s own
patch turned up the exact tracer tautology bug
`r_fuzzy_window_entropy_guard` had already hit and fixed once (passing the
MERGED defer_mask, JSD-test OR the guard, to the tracer instead of the JSD
test alone) -- meaning `r_fuzzy_semantic_guard`'s published "0.0%/0.01%
relaxed-only, mechanism check passes cleanly" numbers (pilot AND the
full 194-run sweep) are a construction artifact: `lossy_would_accept`
collapsed to `strict_would_accept` at every guarded position by
definition, not because the guard was observed to be airtight. Retrofitted
both `r_fuzzy_semantic_guard` and (never-run) `r_fuzzy_semantic_guard_v2`
to the same jsd-mask/merged-mask split `r_fuzzy_window_entropy_guard`
already used, verified by the usual pristine-round-trip diff and each
patch's own test suite (all passing). The accuracy/length/rounds numbers
in this document's earlier sections are NOT affected (ground truth from
actual generation, never derived from this trace field) -- only the
`% relaxed-only` mechanism-check claim is. `spec_casc_tok_semantic_guard`,
below, was built correctly from the start using the fixed convention, so
its own mechanism-check number is trustworthy without a caveat.
`patches/HASHES.txt` documents both the old (superseded) and new hashes.

**Mechanism (see `patches/vllm-0.26.0-spec-casc-tok-semantic-guard.patch`'s
own module comment for the full derivation)**: `spec_casc_tok` is a genuine
full-vocab blend, not a wholesale q/p switch like `r_fuzzy`, so there's no
`defer_mask` to OR a guard into. Instead, "force strict at this token" means
forcing the trusted top set A empty for that row -- which the base method's
own module comment already proves is *exactly* its alpha=-inf strict limit
(A={} => eta=1 => pi_rej=p), not an approximation. Enforced in two places
that have to agree with each other (Python's full-vocab `in_top_set`, used
for recovery, and the kernel's own from-scratch recheck of the drafted
token's membership, used for the accept test) -- both take the same
`semantic_guard_mask`. Same 18-token hesitation-marker id list as
`r_fuzzy_semantic_guard`. Full test suite:
`patches/test_spec_casc_tok_semantic_guard.py` (alpha plumbing, guard-id
set, the guard-forces-strict-limit-at-any-alpha property, a GPU kernel test,
and a GPU recovery test) -- all passing, including on a real end-to-end
smoke-test run.

**Pilot design**: same 8 AIME24 cases as the `r_fuzzy_semantic_guard`
pilot (case_005, 028, 002, 020, 021, 015, 011, 003, chosen there for
`r_fuzzy`'s worst rambling, kept here for cross-guard comparability rather
than re-deriving a `spec_casc_tok`-specific "worst" ranking), both arms run
fresh and paired (not reusing the existing 30-case `spec_casc_tok` data,
same nondeterminism discipline as the `r_fuzzy` pilot), α=0.3 for both, full
32,768-token budget. 16 runs.

**Mechanism check passes cleanly, genuinely this time**: 67 relaxed-only
hesitation words under plain `spec_casc_tok` -> **0** under the guard,
`lossy_would_accept` computed from the unguarded base alpha throughout (see
above), so this is a real measurement, not a construction artifact.

**Results, per case** (`output_tokens`, `spec_casc_tok` -> `+guard`):

| case | spec_casc_tok | +guard | change | verdict change |
|---|---:|---:|---:|---|
| case_002 | 32,768 (cap) | 9,718 | **-70%** | **no_answer -> correct** |
| case_003 | 22,175 | 32,768 (cap) | **+48%** | **correct -> no_answer** |
| case_005 | 7,038 | 5,614 | -20% | correct -> correct |
| case_011 | 27,669 | 15,131 | -45% | correct -> correct |
| case_015 | 6,823 | 5,190 | -24% | correct -> correct |
| case_020 | 3,439 | 4,249 | +24% | correct -> correct |
| case_021 | 5,066 | 8,917 | +76% | correct -> correct |
| case_028 | 13,969 | 4,129 | -70% | correct -> correct |

Aggregate: mean completion length 14,868 -> 10,715 (**-27.9%**), mean
verifier rounds 4,715 -> 3,398 (same -27.9%, `l_bar` essentially flat:
2.362 -> 2.373). Throughput (`check_round_throughput.py`): mean s/round
0.01249 -> 0.01306 (**+4.6%**, the guard's own per-round check cost, same
order as `r_fuzzy_semantic_guard`'s +2-4%), total generation wall-time
471.2s -> 355.0s (**-24.7%**, round-count savings still dominate).

**Accuracy: 7/8 both arms -- identical on the scoreboard, but NOT the same
case.** The guard fixes case_002 (was stuck at the 32,768 cap with no
answer at all; now resolves cleanly to the correct answer in under a third
of the tokens) and breaks case_003 (was correct at 22,175 tokens; now runs
to the cap with no answer). This is a genuinely different shape than
`r_fuzzy_semantic_guard`'s pilot, which only ever cost accuracy (2/8->1/8,
no case flipped into newly-correct). Here the guard demonstrably CAN
rescue a case from the exact failure mode it targets (rambling to the
token cap without ever committing to an answer) -- it just isn't free,
and at n=8 "swapped one no_answer for a different one" is not yet
distinguishable from "net neutral, occasionally flips whichever case
was already closest to the edge." The two regressions in the OTHER
direction (case_020 +24%, case_021 +76%, both stayed correct) show the
guard doesn't uniformly help even where it doesn't break anything --
consistent with the broader theme in this document: forcing strict at a
lexical marker is a blunt instrument, sometimes load-bearing for the
run's own recovery, sometimes not.

**Honest read**: on an arm that already beats strict, this guard is a much
closer call than it was on `r_fuzzy`. Aggregate length savings are real and
similar in size to the `r_fuzzy` pilot (-27.9% vs -28% to -32%), the
mechanism check is genuinely clean this time, and -- unlike every other
guard variant tried in this document -- it produced at least one clear
per-case rescue, not only regressions. But n=8 with a 1-for-1 case swap is
not enough to call this a net win; the natural next step is the same one
`r_fuzzy_semantic_guard` took: a full 30-case AIME24 (+ 164-case HumanEval)
sweep, to see whether case_002-style rescues or case_003-style regressions
dominate at scale, not run here without checking in first (this pilot alone
was ~27 minutes of GPU time; the full sweep is the multi-hour-scale
commitment the `r_fuzzy` full-scale section above describes).

Reproduce:

```
source .venv-vllm/bin/activate
python3 scripts/fresh_server_replay.py \
    --arms spec_casc_tok spec_casc_tok_semantic_guard \
    --spec-casc-tok-alpha 0.3 --spec-casc-tok-semantic-guard-alpha 0.3 \
    --cases case_005 case_028 case_002 case_020 case_021 case_015 case_011 case_003 \
    --prompt-root prompts/aime24 \
    --runs-root runs/spec_casc_tok_semantic_guard_pilot/aime24 \
    --log-root logs/spec_casc_tok_semantic_guard_pilot/aime24 --max-new-tokens 32768
python3 scripts/grade_aime.py --runs-root runs/spec_casc_tok_semantic_guard_pilot/aime24 --prompt-root prompts/aime24
python3 analysis/semantic_guard/count_relaxed_only_hesitation.py --runs-root runs/spec_casc_tok_semantic_guard_pilot/aime24 --out-prefix analysis/semantic_guard/results/spec_casc_tok_guard_pilot
python3 analysis/semantic_guard/check_round_throughput.py --runs-root runs/spec_casc_tok_semantic_guard_pilot/aime24 --tags specCascTok0p3 specCascTokSemanticGuard0p3
```

## Full-scale AIME24 results: the pilot's picture reverses completely

`spec_casc_tok_semantic_guard` run across all 30 AIME24 cases (fresh, into
`runs/aime24_fresh` alongside the other arms, same convention as
`r_fuzzy_semantic_guard`'s full-scale section above -- existing
`spec_casc_tok` baseline reused, not re-run). HumanEval (164 cases) was
launched in the same sweep and is reported separately once it finishes;
this section is AIME24 only.

| metric | spec_casc_tok | +guard | change |
|---|---:|---:|---:|
| accuracy | 26/30 (86.7%) | 22/30 (73.3%) | **-13.4pp** |
| mean l̄ (accepted length) | 2.421 | 2.400 | -0.9% |
| mean completion length | 9,440 | 10,397 | **+10.1%** |
| mean verifier rounds | 2,896 | 3,276 | **+13.1%** |
| mean s/round (throughput tax) | 0.01241 | 0.01292 | +4.1% |
| total generation wall-time | 1,078.2s | 1,269.6s | **+17.8%** |
| hesitation words, relaxed-only | 157 | **0** | mechanism check still clean |

**This is the opposite of the 8-case pilot's result, on every axis.** The
pilot (accuracy flat at 7/8 both arms, -27.9% aggregate length, -24.7%
wall-time) used the same 8 cases as `r_fuzzy_semantic_guard`'s own pilot --
chosen there for *`r_fuzzy`'s* worst rambling, never re-derived for
`spec_casc_tok` specifically. At full scale the guard makes `spec_casc_tok`
worse on every measured axis: longer completions, more rounds, more
wall-time, AND a real 13.4-point accuracy cost -- not a partial, mixed
picture, a clear net loss.

**Verdict changes** (26 -> 22, net -4): 2 cases improved (case_002: stuck
at the 32,768-token cap with no answer -> correct in under a third of the
tokens; case_006: wrong -> correct) but **6 regressed** (case_003,
case_014, case_026: correct -> no_answer/cap; case_023, case_029, case_030:
correct -> wrong). Both of the pilot's own flip cases (case_002's rescue,
case_003's regression) reproduce exactly at full scale -- those two are
real. What the pilot missed is everything else: its other 6 cases were all
mild-to-moderate length wins that happened not to cost accuracy, and none
of them were the 6 cases (014, 023, 026, 029, 030, plus 003) where the
guard actually does damage. An 8-case pilot built for a DIFFERENT arm's
failure mode was never a reliable predictor here -- worth remembering
before trusting any small pilot's sign, not just its magnitude, as
representative of a different arm.

This AIME24-only verdict is superseded below once HumanEval's half of the
same sweep finished -- the two benchmarks turned out to disagree with each
other, not just with the pilot.

## Full-scale HumanEval results, and the combined picture: the two benchmarks disagree

Same sweep, same run (`spec_casc_tok_semantic_guard` fresh across all 164
HumanEval cases, into `runs/humaneval_fresh`, existing `spec_casc_tok`
baseline reused), finished after AIME24. Where AIME24 showed a clear net
loss on every axis, HumanEval shows the opposite:

| metric | spec_casc_tok | +guard | change |
|---|---:|---:|---:|
| pass@1 | 157/164 (95.7%) | **159/164 (97.0%)** | **+1.3pp** |
| mean l̄ (accepted length) | 2.604 | 2.593 | -0.4% |
| mean completion length | 918.8 | 850.6 | **-7.4%** |
| mean verifier rounds | 267.5 | 249.4 | **-6.8%** |
| mean s/round (throughput tax) | 0.01322 | 0.01429 | +8.1% |
| total generation wall-time | 580.0s | 584.2s | +0.7% (round-count savings roughly cancel the per-round tax here) |
| hesitation words, relaxed-only | 92 | **0** | mechanism check still clean |

**Verdict changes** (157 -> 159, net +2): 4 cases improved (case_076,
case_117, case_161, case_164: failed -> passed) against 2 regressions
(case_048, case_094: passed -> failed) -- a real net win, not a wash
dressed up as one, and the opposite shape from AIME24 (which had 2
improvements against 6 regressions).

**Combined across both benchmarks (n=194)**:

| metric | spec_casc_tok | +guard | change |
|---|---:|---:|---:|
| accuracy (both graded pass/fail) | 183/194 (94.3%) | 181/194 (93.3%) | -1.0pp |
| mean l̄ (accepted length), run-count-weighted | 2.576 | 2.563 | -0.5% |
| mean completion length | 2,236 | 2,327 | +4.0% |
| mean verifier rounds | 674.0 | 717.4 | +6.4% |
| mean s/round | 0.01268 | 0.01332 | +5.0% |
| total generation wall-time | 1,658.2s | 1,853.8s | +11.8% |
| hesitation words, relaxed-only | 249 | **0** | clean |

**l̄ (mean accepted length) barely moves in either benchmark** (-0.9%
AIME24, -0.4% HumanEval, both far smaller than the length/rounds swings
above) -- a clarifying detail about the mechanism, not just another metric.
The guard doesn't make an average verifier round accept meaningfully fewer
tokens; it changes how many rounds the WHOLE generation needs (rounds moves
in lockstep with completion length, in opposite directions per benchmark,
while l̄ stays close to flat throughout). Whatever is driving the
benchmark-level split above, it's downstream of "does the run as a whole
converge faster or slower," not a change in per-round acceptance
generosity.

**Honest read: this is not one verdict, it's two, and they point opposite
directions.** On AIME24 -- long, multi-thousand-token chain-of-thought
completions where a single early wrong turn compounds for tens of
thousands of tokens -- forcing strict at hesitation markers is a net
loss: worse accuracy, longer completions, more wall-time. On HumanEval --
short, mostly-single-shot completions -- the same intervention is a real
net win: better accuracy AND shorter completions, at only a marginal
wall-time cost. Pooling the two into one "combined" number (as the table
above does, and as this document's `r_fuzzy_semantic_guard` section also
did) obscures this: the pooled numbers are dominated by AIME24's much
longer completions (2,236 vs ~919 mean tokens), so the combined row reads
as a mild net loss even though HumanEval genuinely improved. **The
benchmark-level breakdown is the finding here, not the pooled row.**

This also reframes the `r_fuzzy_semantic_guard` comparison: that guard
cost accuracy on BOTH benchmarks, in the same direction, independently --
real evidence the intervention itself was the problem there.
`spec_casc_tok_semantic_guard` splitting by benchmark instead suggests the
underlying effect is more like "forcing strict at hesitation markers helps
short-completion domains and hurts long-chain-of-thought domains where
those tokens are more often load-bearing for recovering from an earlier
mistake" -- a hypothesis this data supports but a 2-benchmark, 1-guard
sample can't confirm on its own.

Reproduce (HumanEval half):

```
python3 scripts/fresh_server_replay.py \
    --arms spec_casc_tok_semantic_guard --spec-casc-tok-semantic-guard-alpha 0.3 \
    --cases $(ls prompts/humaneval | grep '^case_') \
    --prompt-root prompts/humaneval --runs-root runs/humaneval_fresh \
    --log-root logs/humaneval_fresh --max-new-tokens 9000
python3 scripts/grade_humaneval.py --runs-root runs/humaneval_fresh --prompt-root prompts/humaneval --tags specCascTok0p3 specCascTokSemanticGuard0p3
python3 analysis/semantic_guard/count_relaxed_only_hesitation.py --runs-root runs/humaneval_fresh --out-prefix analysis/semantic_guard/results/humaneval_spec_casc_tok_guard_full
python3 analysis/semantic_guard/check_round_throughput.py --runs-root runs/humaneval_fresh --tags specCascTok0p3 specCascTokSemanticGuard0p3
```

## Does hidden-state recurrence fire under the TRUE lossless baseline, and is it a real reasoning loop when it does?

Every recurrence check so far in this document ran against a RELAXED
method (`r_fuzzy`, and implicitly `spec_casc_tok` via the trace but never
its own hidden states). That leaves the causal question this whole
investigation keeps circling back to unanswered: is "reasoning loop"
something relaxed verification induces or amplifies, or is it a property
of the base model's own reasoning that shows up regardless of how
verification runs? This section runs the recurrence detector against
`strict` itself -- lossless, no relaxation of any kind -- to find out, and
labels each flagged event into a 3-way taxonomy (`reasoning_loop` /
`no_progress` / `benign`) rather than the earlier binary loop-or-not, since
"the hidden state recurred" turns out to have several real causes, not one.

**Setup**: `strict` with hidden-state capture, same 8 AIME24 cases as the
earlier `r_fuzzy` hidden-state pilot (case_005, 028, 002, 020, 021, 015,
011, 003), full 32,768-token budget. 8 fresh-server runs.

**Only one of 8 cases failed to converge under strict**: case_002 hit the
full 32,768-token cap with no final answer (`finish=length`,
`final_ch=False`) -- the SAME case that also failed under plain
`spec_casc_tok` (also `no_answer`, also the cap) in the guard experiment
above. This on its own is informative: whatever makes case_002 hard is not
an artifact of relaxed verification, since the lossless control has the
identical failure. The other 7 cases all resolved cleanly (3,342-28,934
tokens, `finish=stop`, reached `final`).

**Macro-loop restarts (the `<|end|><|start|>assistant<|channel|>analysis`
pattern from earlier)**: zero, across all 8 strict runs, including
case_002 (which never even opens a `final` channel to abandon -- it just
never stops exploring in `analysis`). That specific failure shape --
reaching a real answer and then discarding it to restart -- was found
exactly once in this whole document, in `r_fuzzy`'s case_028. It does not
reproduce in strict's case_028 (3,680 tokens, clean finish) or anywhere
else here. Consistent with that pattern being something relaxed
verification enables rather than a base-model behavior.

**Recurrence events**: `find_hidden_state_recurrence_onsets.py`, same
per-run P99 empirical threshold as before, found 309 onset events across
the 8 runs (dominated by case_002's 90 and case_003's 112 -- the two
longest runs, more opportunity to cross a per-run threshold). Top 3
longest-streak events per case (24 total, `results/strict_hidden_state_recurrence_labels.jsonl`)
read manually and labeled:

| case | outcome | reasoning_loop | no_progress | benign |
|---|---|---:|---:|---:|
| case_002 (never converged) | cap, no answer | **3** | 0 | 0 |
| case_003 | correct | 0 | 0 | 3 |
| case_005 | correct | 0 | 0 | 3 |
| case_011 | correct | 0 | 0 | 3 |
| case_015 | correct | 0 | 1 | 2 |
| case_020 | correct | 0 | 0 | 3 |
| case_021 | correct | 0 | 0 | 3 |
| case_028 | correct | 0 | 0 | 3 |
| **total** | | **3** | **1** | **20** |

**This is a genuinely clean, informative split.** All 3 `reasoning_loop`
labels come from the ONE case that actually failed (case_002) -- and
they're the same persistent episode, not three independent ones: all three
top-streak candidates (positions 27,882 / 28,334 / 28,957, spanning over
1,000 tokens) are the model stuck re-deriving whether
`354,375/3388 = 50,625/484` after finding a numeric contradiction, never
resolving it. The other 20 of 24 candidates, across all 7 cases that
resolved correctly, are `benign`: legitimate structurally-repetitive
computation (per-case number-theory iteration in case_005, a deliberate
bounded brute-force enumeration in case_021, group-theory case tracking in
case_003) that *looks* similar to a recurrence detector precisely because
the underlying algorithm legitimately repeats a procedure across inputs --
not because the model is stuck. One `no_progress` case (case_015, pos=154):
the model briefly flip-flops on whether rhombus diagonals are perpendicular
"only if it's a square" (they always are, for every rhombus) without
resolving it within the flagged span -- real circular questioning, but
brief and local, and the case still reaches the correct final answer.

**What this adds to the picture**: hidden-state recurrence is NOT a
false-positive-prone artifact of relaxed verification specifically --
under the true lossless baseline it fires exactly where a real problem
exists (100% of case_002's flagged events are genuine loops) and is
correctly quiet elsewhere (0 of 63 flagged events in the 7 successful
cases are loops). This is a much cleaner precision result than the earlier
`r_fuzzy` check (1 clear hit / 7 longest streaks) -- though not a
contradiction: that check was reading a RELAXED run's trajectory, where a
guard's own on-top intervention and a noisier acceptance process both add
confounds a lossless run doesn't have. It also directly answers this
section's opening question: at least in this 8-case sample, the one real
reasoning loop found occurs under **strict**, with no relaxed verification
involved at all -- reasoning loops are not solely an artifact of lossy
methods, they can and do happen in the base model's own lossless
generation. What relaxed verification (specifically `r_fuzzy`, per the
macro-loop section above) adds is a DIFFERENT failure shape -- abandoning a
real answer to restart -- that this strict sample shows zero instances of.

Reproduce:

```
python3 scripts/fresh_server_replay.py \
    --arms strict --cases case_005 case_028 case_002 case_020 case_021 case_015 case_011 case_003 \
    --prompt-root prompts/aime24 --runs-root runs/hidden_state_strict_pilot/aime24 \
    --log-root logs/hidden_state_strict_pilot/aime24 --max-new-tokens 32768 --capture-hidden-states
python3 analysis/semantic_guard/find_hidden_state_recurrence_onsets.py \
    --runs-root runs/hidden_state_strict_pilot/aime24 --tag strict --k 8 --percentile 99 --min-gap 32 \
    --out analysis/semantic_guard/results/strict_hidden_state_recurrence_onsets.jsonl
python3 analysis/semantic_guard/find_macro_loop_restarts.py \
    --runs-root runs/hidden_state_strict_pilot/aime24 --tag strict \
    --out analysis/semantic_guard/results/strict_macro_loop_restarts.jsonl
```

## `spec_casc_tok_semantic_guard_future_guard`: a third combination rule, gating what comes AFTER a marker instead of the marker itself

Different trigger shape from the other two: instead of gating the hesitation-marker token, this arms a K-token strict window the moment `spec_casc_tok`'s own test *accepts* one (wider marker set: the 35-id/14-word list from `r_fuzzy_semantic_guard_v2`, reused verbatim). For the next K verified positions, the accept test uses the raw lossless ratio instead of `spec_casc_tok`'s blend. First patch in this repo with cross-round persistent state (the remaining-window count carries across verification rounds via a small kernel-level counter) -- see the patch's own module comment for the single-real-sequence-per-process scoping this relies on. K=8 by default (matches the k=8 window already used elsewhere in this investigation for hidden-state recurrence).

**Pilot** (same 8 AIME24 cases, paired fresh baseline, α=0.3, K=8):

| metric | baseline | override-guard | AND-guard | future-guard-strict (K=8) | future-guard-AND (K=8) |
|---|---:|---:|---:|---:|---:|
| accuracy | 7/8 | 7/8 | 6/8 | **7/8** | 6/8 |
| aggregate length | 118,947 | 85,716 (-27.9%) | 91,358 (-23.2%) | 95,424 (-19.8%) | 97,541 (**-18.0%**) |
| hesitation words (n=8) | 1,891 | 1,333 (-29.5%) | 1,419 (-24.9%) | 1,508 (-20.3%) | 1,396 (**-26.2%**) |
| mechanism check (relaxed-only) | 67 | 0 | 0 | 49 (3.25%) | **47 (3.37%)** |
| total wall-time | 471.9s | 355.0s (-24.7%) | 376.4s (-19.8%) | 396.0s (-16.1%) | 415.9s (**-13.0%**) |
| s/round tax | — | +4.6% | +3.6% | +3.4% | +3.9% |

Mechanism check is NOT zero for either future-guard design, correctly -- neither touches the marker token's own accept decision (that still runs plain `spec_casc_tok`, unguarded), only the K positions after it, so a marker can still be relaxed-only-accepted itself; the two future-guard variants' mechanism-check rates land almost on top of each other (3.25% vs 3.37%), as expected since they share the identical trigger/arming logic and differ only in what happens *inside* an already-armed window.

**future-guard-AND is a fourth combination rule, crossing future-guard's trigger shape with the AND-guard's combination rule**: inside the K-window, accept iff BOTH the lossless test AND `spec_casc_tok`'s own relaxed test would accept (`min(pi_rej, p)`), instead of future-guard-strict's raw-strict-only window -- provably never more lenient than future-guard-strict at any guarded position (same identity the standalone AND-guard uses). At this pilot scale it lands closer to the AND-guard's overall shape than to future-guard-strict's: same 6/8 accuracy as the marker-level AND-guard (not future-guard-strict's 7/8), but with **the best length/hesitation-word reduction of any guard variant so far on this pilot** (-18.0% length is close to future-guard-strict's -19.8%, but -26.2% hesitation words beats every other variant including the two marker-level guards).

**Verdict changes** (7/8 -> 6/8, net -1): 1 rescue (case_002: cap/no_answer -> correct, though at 23,811 tokens -- more than double future-guard-strict's own case_002 rescue at 11,506, a real but much less efficient fix) against 2 regressions (case_003: correct -> cap/no_answer, the same case every other guard variant also loses; case_005: correct -> wrong, 110 -> 134 -- a NEW regression not seen in any of the other three guards' pilots). case_011 stands out on the positive side: 27,669 -> 4,427 tokens (**-84.0%**), the single largest length reduction of any case across all four guard pilots, while staying correct throughout.

Reproduce (K is a real CLI flag, not baked into the patch):

```
python3 scripts/fresh_server_replay.py \
    --arms spec_casc_tok spec_casc_tok_semantic_guard_future_guard \
    --spec-casc-tok-alpha 0.3 --spec-casc-tok-semantic-guard-future-guard-alpha 0.3 \
    --spec-casc-tok-semantic-guard-future-guard-k 8 \
    --cases case_005 case_028 case_002 case_020 case_021 case_015 case_011 case_003 \
    --prompt-root prompts/aime24 --runs-root runs/spec_casc_tok_semantic_guard_future_guard_pilot/aime24 \
    --log-root logs/spec_casc_tok_semantic_guard_future_guard_pilot/aime24 --max-new-tokens 32768
```

future-guard-AND reproduce:

```
python3 scripts/fresh_server_replay.py \
    --arms spec_casc_tok spec_casc_tok_semantic_guard_future_guard_and \
    --spec-casc-tok-alpha 0.3 --spec-casc-tok-semantic-guard-future-guard-and-alpha 0.3 \
    --spec-casc-tok-semantic-guard-future-guard-and-k 8 \
    --cases case_005 case_028 case_002 case_020 case_021 case_015 case_011 case_003 \
    --prompt-root prompts/aime24 --runs-root runs/spec_casc_tok_semantic_guard_future_guard_and_pilot/aime24 \
    --log-root logs/spec_casc_tok_semantic_guard_future_guard_and_pilot/aime24 --max-new-tokens 32768
```

Full 30-case AIME24 sweeps for future-guard-strict at K=4 and K=8 are done (see
below). future-guard-AND has only been piloted so far, not run at full scale.

## Full-scale AIME24 results, K=4: matches the other two guards almost exactly

`spec_casc_tok_semantic_guard_future_guard` run across all 30 AIME24 cases at
K=4 (existing `spec_casc_tok` baseline reused, same convention as the other
two guards' full-scale sections). Mechanism-check numbers below are the
K=4-only slice (the raw `count_relaxed_only_hesitation.py` output groups by
arm label, not by K, so it briefly mixed in one in-flight K=8 run while the
K=8 sweep was starting -- filtered back out here by `tag`).

| metric | **lossless (strict)** | baseline (spec_casc_tok) | override-guard | AND-guard | future-guard K=4 |
|---|---:|---:|---:|---:|---:|
| accuracy | 23/30 (76.7%) | 26/30 (86.7%) | 22/30 (73.3%) | 22/30 (73.3%) | **22/30 (73.3%)** |
| mean completion length | 10,043 | 9,440 | 10,397 (+10.1%) | 10,964 (+16.1%) | 10,397 (**+10.1%**) |
| mean accepted length (l̄) | 2.2046 | 2.4210 | 2.3999 (-0.9%) | 2.3906 (-1.3%) | 2.3447 (**-3.2%**) |
| total verifier rounds | 100,605 | 86,874 | ~98,280 (+13.1%) | ~103,890 (+19.6%) | 97,779 (**+12.6%**) |
| mean s/round (throughput tax) | 0.01227 | 0.01241 | 0.01292 (+4.1%) | -- | 0.01295 (**+4.4%**) |
| total generation wall-time | 1,234.8s | 1,078.2s | 1,269.6s (+17.8%) | 1,345.3s (+24.8%) | 1,266.3s (**+17.4%**) |
| hesitation words | 4,456 | 4,173 | 4,949 (+18.6%) | 4,822 (+15.6%) | 4,869 (**+16.7%**) |
| hesitation words, relaxed-only | 0 | 157 (3.8%) | 0 | 0 | **199 (4.1%)** |

`l̄` (mean accepted length per verifier round -- higher is better speculative-decoding throughput) is included because it's the metric all these relaxation methods exist to improve on top of lossless: `spec_casc_tok` baseline already beats strict here (2.4210 vs 2.2046, +9.8%), and every guard variant gives some of that back by forcing extra strict-only rounds -- K=4 gives back the most (2.3447, -3.2% off baseline, though still +6.3% above lossless), the override- and AND-guards give back the least (~-1%, still +8.6%/+8.4% above lossless). Percentages in the `baseline (spec_casc_tok)` comparisons above are relative to that baseline column, not to lossless -- lossless is included as the zero-relaxation reference point, not as the thing the guards are trying to move toward.

Three structurally different combination rules (override the marker to pure
strict; AND the marker's own decision with lossless; leave the marker alone
but force strict on the K tokens *after* it) land within a few points of
each other on every axis, and all three land on the exact same accuracy:
**22/30**. Length/rounds/wall-time for future-guard K=4 are close enough to the
override-guard's numbers that the two are barely distinguishable (10,397
mean length both; wall-time +17.4% vs +17.8%) -- despite gating a
completely different set of tokens (the marker itself for override; up to 4
tokens *after* it, and never the marker, for future-guard). The AND-guard is
the outlier, costing more on every efficiency axis for the same accuracy.
The mechanism check is the one real structural difference: future-guard is the
only one of the three with nonzero relaxed-only hesitation words (199, 4.1%)
by design, since it never touches the marker token's own accept decision.

**Verdict changes** (26 -> 22, net -4): 1 case improved (case_006: wrong ->
correct, same as the other two guards) but 5 regressed (case_003, case_014,
case_026: correct -> no_answer/cap; case_023, case_029: correct -> wrong).
Notably **case_002 is *not* rescued at K=4** -- unlike the override- and
AND-guards, which both flip it from stuck-at-cap to correct, K=4's window
is short enough that this run stays stuck at the 32,768-token cap either
way (`no_answer -> no_answer`, unchanged length: 32,768 both arms). K=4's
regression set (003, 014, 023, 026, 029) is a subset of the override-guard's
six (003, 014, 023, 026, 029, 030) minus case_030, which stays correct
under future-guard K=4 (8,684 -> 8,083 tokens) but flips to wrong under
override. Case_028 is a genuine outlier here too: length *grows* under
future-guard K=4 (13,969 -> 16,605, +18.9%) while it *shrinks* under both other
guards (see the pilot table above) -- the opposite direction from every
other guard design on this specific case, still `correct -> correct`
throughout.

## Full-scale AIME24 results, K=8: a genuinely different, better outcome than K=4

Same protocol as K=4 above, K=8 instead (existing `spec_casc_tok` baseline
reused; mechanism-check numbers filtered by `tag` the same way, since both
K=4 and K=8 traces now coexist under `runs/aime24_fresh` and share the same
underlying arm label).

| metric | **lossless (strict)** | baseline (spec_casc_tok) | override-guard | AND-guard | future-guard K=4 | future-guard K=8 |
|---|---:|---:|---:|---:|---:|---:|
| accuracy | 23/30 (76.7%) | 26/30 (86.7%) | 22/30 (73.3%) | 22/30 (73.3%) | 22/30 (73.3%) | **25/30 (83.3%)** |
| mean completion length | 10,043 | 9,440 | 10,397 (+10.1%) | 10,964 (+16.1%) | 10,397 (+10.1%) | **9,303 (-1.4%)** |
| mean accepted length (l̄) | 2.2046 | 2.4210 | 2.3999 (-0.9%) | 2.3906 (-1.3%) | 2.3447 (-3.2%) | **2.3950 (-1.1%)** |
| total verifier rounds | 100,605 | 86,874 | ~98,280 (+13.1%) | ~103,890 (+19.6%) | 97,779 (+12.6%) | **87,607 (+0.8%)** |
| mean s/round (throughput tax) | 0.01227 | 0.01241 | 0.01292 (+4.1%) | -- | 0.01295 (+4.4%) | 0.01298 (+4.6%) |
| total generation wall-time | 1,234.8s | 1,078.2s | 1,269.6s (+17.8%) | 1,345.3s (+24.8%) | 1,266.3s (+17.4%) | **1,137.2s (+5.5%)** |
| hesitation words | 4,456 | 4,173 | 4,949 (+18.6%) | 4,822 (+15.6%) | 4,869 (+16.7%) | **3,952 (-5.3%)** |
| hesitation words, relaxed-only | 0 | 157 (3.8%) | 0 | 0 | 199 (4.1%) | 139 (**3.5%**) |

**K=8's accepted-length cost is the smallest of the three guard families** (-1.1% off `spec_casc_tok` baseline, vs. -3.2% for K=4 and -0.9%/-1.3% for override/AND) while still landing at +8.6% above lossless's own l̄ (2.3950 vs 2.2046) -- it gives back only a sliver of the speculative-decoding throughput gain `spec_casc_tok` has over strict, which is consistent with the s/round tax also being the smallest relative cost once weighed against K=8's round-count reduction (unlike K=4, whose extra rounds compound with the tax instead of offsetting it). Put together with the completion-length and hesitation-word numbers: K=8 is the only guard variant tested that sits *closer to lossless on accuracy* (83.3% vs strict's 76.7% -- still above it) while *also* sitting closer to (in fact below) the `spec_casc_tok` baseline on length, rounds, and hesitation words -- every other variant, including K=4, moves away from `spec_casc_tok` on efficiency to only partially claw back toward lossless on accuracy.

**K=8 is a materially better design point, not just a bigger K.** It's the
only variant of the four that beats baseline `spec_casc_tok` on length,
rounds, and hesitation-word count simultaneously, while giving up less
accuracy than either K=4 or the other two combination rules (-3.4pp vs.
-13.4pp). The direction flip between K=4 and K=8 on length/hesitation-words
(+10.1%/+16.7% at K=4 vs. -1.4%/-5.3% at K=8) is the interesting result:
a longer forced-strict window doesn't just extend the K=4 effect, it
reverses it. Consistent with §5's mechanism theory elsewhere in this
document (forcing strict at a hesitation marker can itself seed a *further*
hesitation cascade in the immediately following tokens) -- a short K=4
window is long enough to trigger that cascade but too short to ride it out,
while K=8 covers enough of the subsequent instability to let the trajectory
settle before control reverts to the relaxed rule.

**Verdict changes** (26 -> 25, net -1): 2 cases improved -- **case_002 is
rescued** (stuck at the 32,768-token cap with no answer -> correct in
11,506 tokens, exactly matching the K=8 pilot's own case_002 run
token-for-token, L=11,506 both times -- the determinism finding from
earlier in this investigation holding again here) and case_006 (wrong ->
correct, same flip as every other guard variant). Only 3 regressed
(case_003, case_014, case_026: correct -> no_answer/cap) -- fewer than
either K=4 (5) or the override-guard (6), and neither case_023 nor
case_029 regress at K=8 (both stay correct, unlike K=4 where they flip to
wrong). Case_028's length also flips back to *shrinking* at K=8 (13,969 ->
6,084, -56.4%) -- the opposite of K=4's growth on this same case, and now
the single largest length reduction of any case in the K=8 sweep.

**Reading across all four combination-rule variants together**: the
override-guard, AND-guard, and future-guard-K=4 all land on the exact same
22/30 accuracy through different mechanisms and different regression sets,
suggesting -13.4pp is close to a floor for "force strict somewhere near a
hesitation marker, narrowly" at this alpha. FutureGuard-K=8 breaks that floor
by widening the window, which both argues against the marker-token identity
being the load-bearing choice (window *position/width* matters more than
*which* combination rule gates the marker itself) and is the first result
in this whole investigation where a hesitation-marker-triggered guard is a
net win over plain `spec_casc_tok` on efficiency without a comparably large
accuracy cost -- worth treating as the most promising design point found so
far, and a natural next step (K=12, K=16, ...) rather than a stopping point.

## Relaxing `spec_casc_tok`'s own alpha (0.3 -> 0.5): an 8-case pilot signal that did NOT survive full scale (see correction below)

A different axis from K: instead of widening the guard's own window, relax
`spec_casc_tok`'s underlying alpha itself (recall: alpha controls the
trusted-set threshold `(1-alpha)*max(p)` -- 0.5 roughly doubles how much of
the vocabulary near the verifier's top token is unconditionally trusted,
compared to 0.3). Same 8-case pilot protocol as every guard pilot above
(paired fresh baseline, K=8), alpha=0.5 instead of 0.3, vanilla
`spec_casc_tok` vs `spec_casc_tok_semantic_guard_future_guard`:

| metric | baseline α=0.3 | +future-guard K=8 α=0.3 | baseline α=0.5 | +future-guard K=8 α=0.5 |
|---|---:|---:|---:|---:|
| accuracy | 7/8 (87.5%) | 7/8 (87.5%) | **5/8 (62.5%)** | **6/8 (75.0%)** |
| aggregate length | 118,947 | 95,424 (-19.8%) | 114,046 | 88,926 (**-22.0%**) |
| total verifier rounds | -- | -- | 35,537 | 28,041 (-21.1%) |
| hesitation words (n=8) | 1,891 | 1,508 (-20.3%) | 1,732 | 1,465 (**-15.4%**) |
| hesitation words, relaxed-only | 67 | 49 (3.3%) | 80 | 88 (**6.0%**) |
| total wall-time | 471.9s | 396.0s (-16.1%) | 446.2s | 365.3s (**-18.1%**) |

**Relaxing alpha further costs `spec_casc_tok` itself real accuracy on this
hard 8-case subset** (7/8 -> 5/8) -- a much bigger hit than anything the
semantic guard has cost at alpha=0.3 anywhere in this document. **But the
guard's relative value grows to compensate**: at alpha=0.3 the guard and
its baseline tie (7/8 both); at alpha=0.5 the guard actually *beats* its
own baseline (6/8 vs 5/8), the first time in this whole investigation a
hesitation-marker-triggered guard shows a net accuracy *gain* over its own
unguarded baseline, not just a smaller loss. Verdict changes at alpha=0.5:
2 rescues (case_003: cap/no_answer -> correct in 16,523 tokens; case_005:
wrong -> correct) against 1 regression (case_011: correct -> wrong,
104 -> 106) -- net +1. Length/rounds/wall-time savings are also all
somewhat larger in relative terms at alpha=0.5 than alpha=0.3 (-22.0% vs
-19.8% length, -18.1% vs -16.1% wall-time). The one number that moves the
"wrong" direction is the mechanism check: relaxed-only hesitation words
nearly doubles as a share (3.3% -> 6.0%) -- expected, since a more relaxed
base alpha pushes more of the relaxed-only acceptance onto the marker
token itself (which this guard design never gates), so a larger share
leaks past an unchanged K-window mechanism.

**Reading (superseded -- see the full-scale correction immediately below):
this was n=8, one pilot, not a sweep**, and its own headline claim (the
guard beating its own baseline) turned out not to survive full scale.
Recorded here rather than deleted, per this document's own standing
practice of disclosing when a pilot misleads rather than quietly replacing
it -- see the `r-fuzzy-semantic-guard` pilot-vs-full-scale section earlier
in this document for the prior instance of exactly this pattern.

Reproduce:

```
python3 scripts/fresh_server_replay.py \
    --arms spec_casc_tok spec_casc_tok_semantic_guard_future_guard \
    --spec-casc-tok-alpha 0.5 --spec-casc-tok-semantic-guard-future-guard-alpha 0.5 \
    --spec-casc-tok-semantic-guard-future-guard-k 8 \
    --cases case_005 case_028 case_002 case_020 case_021 case_015 case_011 case_003 \
    --prompt-root prompts/aime24 --runs-root runs/spec_casc_tok_alpha0p5_pilot/aime24 \
    --log-root logs/spec_casc_tok_alpha0p5_pilot/aime24 --max-new-tokens 32768
```

## Correction: full-scale alpha=0.5 results -- the pilot's headline claim reverses

Full 30-case AIME24 sweep, existing `strict`/`spec_casc_tok0p3` baselines
reused for reference, fresh `spec_casc_tok` and `spec_casc_tok_semantic_guard_future_guard`
runs at α=0.5:

| metric | lossless | baseline α=0.3 | baseline α=0.5 | future-guard K=8 α=0.5 |
|---|---:|---:|---:|---:|
| accuracy | 23/30 (76.7%) | 26/30 (86.7%) | **22/30 (73.3%)** | **20/30 (66.7%)** |
| mean completion length | 10,043 | 9,440 | 10,495 | 10,555 (+0.6%) |
| mean accepted length (l̄) | 2.2046 | 2.4210 | 2.4929 | 2.4484 (-1.8%) |
| total verifier rounds | 100,605 | 86,874 | 96,402 | 97,984 (+1.6%) |
| mean s/round | 0.01227 | 0.01241 | 0.01258 | 0.01300 (+3.3%) |
| total generation wall-time | 1,234.8s | 1,078.2s | 1,212.9s | 1,273.6s (+5.0%) |
| hesitation words | 4,456 | 4,173 | 4,532 | 4,662 (+2.9%) |
| hesitation words, relaxed-only | 0 | 157 (3.8%) | 228 (5.0%) | 258 (5.5%) |

**The 8-case pilot's headline result does not survive full scale --
future-guard does NOT beat its own baseline at alpha=0.5.** At full scale,
relaxing alpha from 0.3 to 0.5 costs the *baseline* real accuracy (26/30 ->
22/30, roughly matching the pilot's own direction) but the guard costs
*more*, not less (22/30 -> 20/30) -- the opposite of the pilot's 5/8 -> 6/8
result. Both numbers move length/rounds/wall-time in the SAME direction
too (guard now costs MORE than baseline on every axis, +0.6% length, +1.6%
rounds, +5.0% wall-time, +2.9% hesitation words) -- at alpha=0.3 the guard
reliably cuts these relative to baseline; at alpha=0.5 it no longer does,
on any of them.

**Verdict changes, guard vs. its own alpha=0.5 baseline** (22 -> 20, net
-2): 2 improved (case_003: no_answer -> correct; case_005: wrong ->
correct -- the SAME two cases the pilot's own rescue involved, both
reproducing) against 4 regressed (case_006, case_009, case_011: correct ->
wrong; case_019: correct -> no_answer) plus 2 lateral moves among already-
wrong cases (case_002, case_004: wrong -> no_answer). The pilot's own two
positive flips are real and reproduce exactly -- what the pilot missed is
everything else: 4 new regressions outside its own 8-case sample, enough
to flip the net sign.

**Reading**: this is exactly the `r-fuzzy-semantic-guard` pilot-vs-full-
scale pattern repeating on a different axis (relaxing alpha instead of
choosing adversarial cases) -- a small, non-random 8-case sample showed a
real effect (the two rescues genuinely reproduce) that did not generalize
once measured on all 30 cases. At alpha=0.5 specifically, relaxing
`spec_casc_tok`'s alpha does not create a regime where this guard wins --
it makes both the guard and its baseline worse, and the guard consistently
worse than its own more-relaxed baseline, matching the pattern already
established at alpha=0.3 (no guard variant beats vanilla `spec_casc_tok`)
rather than breaking it. **This does NOT hold at alpha=0.7 -- see
immediately below.**

## Pushing further: alpha=0.7 -- the guard reverses AGAIN, cleanly beats its own baseline

Requested directly: does the guard's disadvantage at alpha=0.5 grow, shrink,
or reverse again as `spec_casc_tok` relaxes even further? Full 30-case
sweep at alpha=0.7 (existing lossless/α=0.3 baselines reused for
reference):

| metric | lossless | baseline α=0.3 | baseline α=0.7 | future-guard K=8 α=0.7 |
|---|---:|---:|---:|---:|
| accuracy | 23/30 (76.7%) | 26/30 (86.7%) | 22/30 (73.3%) | **25/30 (83.3%)** |
| mean completion length | 10,043 | 9,440 | 10,337 | 12,239 (+18.4%) |
| mean accepted length (l̄) | 2.2046 | 2.4210 | 2.6565 | 2.5365 (-4.5%) |
| total verifier rounds | 100,605 | 86,874 | 90,948 | 109,433 (+20.3%) |
| mean s/round | 0.01227 | 0.01241 | 0.01262 | 0.01297 (+2.8%) |
| total generation wall-time | 1,234.8s | 1,078.2s | 1,147.4s | 1,419.9s (+23.8%) |
| hesitation words | 4,456 | 4,173 | 5,699 (α=0.7 guard) | -- |
| hesitation words, relaxed-only | 0 | 157 (3.8%) | 395 (6.9%, guard) | -- |

**Non-monotonic: the guard's relationship to its own baseline is not a
straight line as alpha increases.** At alpha=0.3 the guard wins narrowly
(25/30 vs 26/30, -1 case but cheaper); at alpha=0.5 it loses clearly (20/30
vs 22/30, worse on every axis); at alpha=0.7 it wins clearly again --
**25/30 vs. baseline's own 22/30, a real +3-case advantage**, and this time
with **zero regressions**: 3 improved (case_002, case_003: no_answer ->
correct; case_005: wrong -> correct), 0 regressed, 1 lateral move among
already-wrong cases (case_004: no_answer -> wrong). This is the first
guard-vs-baseline comparison anywhere in this investigation with a
completely clean win column -- every case that changed, changed for the
better.

**The cost is real and grows with alpha, though**: length is now +18.4%
over the α=0.7 baseline (vs. +0.6% at α=0.5, and future-guard-strict K=8
actually being CHEAPER than baseline at α=0.3), rounds +20.3%, wall-time
+23.8% -- the guard is winning on accuracy at alpha=0.7 by spending a lot
more compute, not by being efficient the way it was at alpha=0.3. Whatever
is happening here isn't "the guard gets uniformly better as alpha
increases" (the alpha=0.5 dip disproves that) -- it looks more like alpha
has multiple regimes with different guard/baseline dynamics, and 0.3/0.5/
0.7 land in three different ones. A finer alpha sweep (0.4, 0.6) would be
needed to characterize the transition rather than just its endpoints; not
run here.

## Full-scale AIME24 results: `future-guard-AND`, K=8 -- lands on lossless's own accuracy

`spec_casc_tok_semantic_guard_future_guard_and` run across all 30 AIME24
cases (existing `spec_casc_tok` baseline reused). Reference columns from
here on always include both **lossless (strict)** and **vanilla `spec_casc_tok`**,
per the standing convention this document now follows for every comparison.

| metric | lossless (strict) | baseline (spec_casc_tok) | future-guard-strict K=8 | future-guard-AND K=8 |
|---|---:|---:|---:|---:|
| accuracy | 23/30 (76.7%) | 26/30 (86.7%) | **25/30 (83.3%)** | **23/30 (76.7%)** |
| mean completion length | 10,043 | 9,440 | 9,303 (-1.4%) | **10,460 (+10.8%)** |
| mean accepted length (l̄) | 2.2046 | 2.4210 | 2.3950 (-1.1%) | **2.3724 (-2.0%)** |
| total verifier rounds | 100,605 | 86,874 | 87,607 (+0.8%) | **99,463 (+14.5%)** |
| mean s/round | 0.01227 | 0.01241 | 0.01298 (+4.6%) | 0.01295 (+4.4%) |
| total generation wall-time | 1,234.8s | 1,078.2s | 1,137.2s (+5.5%) | **1,288.2s (+19.5%)** |
| hesitation words | 4,456 | 4,173 | 3,952 (-5.3%) | **4,461 (+6.9%)** |
| hesitation words, relaxed-only | 0 | 157 (3.8%) | 139 (3.5%) | 177 (**4.0%**) |

**future-guard-AND's full-scale accuracy lands exactly on lossless's own
(23/30)** -- a genuinely different outcome from the K=8 pilot's picture
(where it undershot both baseline and future-guard-strict at 6/8). At full
scale it's worse than future-guard-strict on every efficiency axis (longer
completions, more rounds, more wall-time, more hesitation words -- the
AND-combination's extra conservatism costs real overhead here, not just at
guarded positions) while landing on the SAME accuracy lossless itself gets,
not a coincidence worth over-reading (different cases can and do compose to
the same total) but a real data point: this is the first guard variant
whose accuracy is statistically indistinguishable from doing no relaxation
at all, at a real efficiency cost relative to the unguarded baseline.

**Verdict changes** (26 -> 23, net -3): 2 improved (case_002: cap/no_answer
-> correct, matching every other guard's rescue of this case; case_006:
wrong -> correct, the flip every guard variant reproduces) against 5
regressions (case_003, case_014, case_026: correct -> no_answer/cap;
case_005, case_019: correct -> wrong) plus one lateral move among already-
wrong cases (case_004: no_answer -> wrong, no effect on the correct count).
Five real regressions is the most of any future-guard variant (vs. 3 for
future-guard-strict K=8), consistent with AND being provably more
conservative than strict alone at every guarded position and therefore
having more surface area to go wrong on, not less.

Reproduce:

```
python3 scripts/fresh_server_replay.py \
    --arms spec_casc_tok_semantic_guard_future_guard_and \
    --spec-casc-tok-semantic-guard-future-guard-and-alpha 0.3 \
    --spec-casc-tok-semantic-guard-future-guard-and-k 8 \
    --cases $(ls prompts/aime24 | grep '^case_') \
    --prompt-root prompts/aime24 --runs-root runs/aime24_fresh \
    --log-root logs/aime24_fresh --max-new-tokens 32768
```

## `spec_casc_tok_semantic_guard_v2`: does marker-set WIDTH alone explain any of future-guard's edge?

Every future-guard variant uses the wider 35-id/14-word marker set; the
marker-level override- and AND-guards both still use the original 18-id/
5-word set. Confounded axis: nobody has tested the wide set on the
marker-level (non-future-guard) mechanism, so it's not yet known whether
future-guard's better full-scale accuracy comes from *where* it gates
(after the marker, not at it) or just from *which* markers it's watching.
`spec_casc_tok_semantic_guard_v2` isolates this: identical override-to-
strict mechanism as plain `spec_casc_tok_semantic_guard`, wide set instead
of narrow. See `patches/vllm-0.26.0-spec-casc-tok-semantic-guard-v2.patch`
and `analysis/semantic_guard/README.md`'s reproduce block below.

**Pilot** (α=0.3, same 8 AIME24 cases, paired fresh baseline):

| metric | lossless (strict) | baseline | override (narrow) | AND (narrow) | future-guard-strict K=8 | future-guard-AND K=8 | **v2 (wide, override)** |
|---|---:|---:|---:|---:|---:|---:|---:|
| accuracy | n/a at pilot scale | 7/8 | 7/8 | 6/8 | 7/8 | 6/8 | **7/8** |
| aggregate length | n/a | 118,947 | 85,716 (-27.9%) | 91,358 (-23.2%) | 95,424 (-19.8%) | 97,541 (-18.0%) | **109,027 (-8.3%)** |
| total verifier rounds | n/a | 37,721 | -- | -- | 31,590 (-16.3%) | -- | **33,967 (-9.9%)** |
| mean s/round | n/a | 0.01256 | -- | -- | 0.01316 | -- | **0.01293 (+2.9%)** |
| total wall-time | n/a | 473.7s | 355.0s (-24.7%) | 376.4s (-19.8%) | 415.9s (-12.2%) | -- | **439.0s (-7.3%)** |
| hesitation words | n/a | 1,891 | 1,333 (-29.5%) | 1,419 (-24.9%) | 1,508 (-20.3%) | 1,396 (-26.2%) | **1,489 (-21.3%)** |
| hesitation words, relaxed-only | n/a | 67 (3.5%) | 0 | 0 | 49 (3.3%) | 47 (3.4%) | **0 (0.0%)** |

**Marker-set width alone is NOT what makes future-guard better than the
marker-level guards.** v2 (wide set, but still gating the marker itself,
not a trailing window) ties baseline's accuracy (7/8, matching narrow-set
override and future-guard-strict, better than narrow-set AND and
future-guard-AND) with a genuinely CLEAN mechanism check (0.0%
relaxed-only, same as narrow override -- the wider set doesn't introduce
the leak future-guard structurally has, since v2 still gates every marker
occurrence itself). Efficiency gains are real (-8.3% length, -9.9% rounds,
-21.3% hesitation words) but smaller than either narrow-set marker guard
(override: -27.9%/-24.7% length/wall-time) or future-guard-strict
(-19.8% length) -- widening the set trades some of override's own
aggression away without future-guard's structural advantage of gating
*downstream* of the marker instead of at it.

**Verdict changes** (7/8 -> 7/8, net 0): 1 rescue (case_002: cap/no_answer
-> correct in 20,966 tokens, the same case every other guard variant
rescues, though at roughly double future-guard-strict's own token cost for
this case) against 1 new regression (case_011: correct -> cap/no_answer --
a case NONE of the narrow-set guards or future-guard-strict lose, only
future-guard-AND touches it and there it stays correct, shrinking to
4,427 tokens). Net wash on accuracy, real efficiency win, structurally
clean mechanism -- the strongest pilot result of any marker-level
(non-future-guard) guard so far, but future-guard-strict K=8's full-scale
83.3% accuracy (vs. this variant's untested-at-scale pilot tie) remains
the benchmark to beat.

Reproduce:

```
python3 scripts/fresh_server_replay.py \
    --arms spec_casc_tok spec_casc_tok_semantic_guard_v2 \
    --spec-casc-tok-alpha 0.3 --spec-casc-tok-semantic-guard-v2-alpha 0.3 \
    --cases case_005 case_028 case_002 case_020 case_021 case_015 case_011 case_003 \
    --prompt-root prompts/aime24 --runs-root runs/spec_casc_tok_semantic_guard_v2_pilot/aime24 \
    --log-root logs/spec_casc_tok_semantic_guard_v2_pilot/aime24 --max-new-tokens 32768
```

**Full 30-case AIME24 sweep** (existing baseline reused):

| metric | lossless (strict) | baseline | v2 (wide, override) |
|---|---:|---:|---:|
| accuracy | 23/30 (76.7%) | 26/30 (86.7%) | **25/30 (83.3%)** |
| mean completion length | 10,043 | 9,440 | 10,599 (+12.3%) |
| mean accepted length (l̄) | 2.2046 | 2.4210 | 2.3986 (-0.9%) |
| total verifier rounds | 100,605 | 86,874 | 97,540 (+12.3%) |
| mean s/round | 0.01227 | 0.01241 | 0.01306 (+5.2%) |
| total generation wall-time | 1,234.8s | 1,078.2s | 1,274.3s (+18.2%) |
| hesitation words | 4,456 | 4,173 | 4,313 (+3.4%) |
| hesitation words, relaxed-only | 0 | 157 (3.8%) | 0 (**0.0%**) |

**v2 matches future-guard-strict K=8's exact full-scale accuracy (25/30,
83.3%) via a completely different mechanism** -- gating the marker itself
with a wider set, not a trailing window after it. This confirms the pilot's
signal held at scale: widening the marker set on the plain override
mechanism recovers real accuracy (22/30 with the narrow set -> 25/30 wide)
without needing future-guard's window machinery at all. But the efficiency
picture is the opposite of future-guard-strict K=8's: v2 costs +12.3% length
and rounds, +18.2% wall-time relative to baseline (vs. future-guard-strict
K=8's -1.4% length, +0.8% rounds, +5.5% wall-time) -- v2 buys its accuracy
recovery by being MORE aggressive across more tokens (35 ids instead of 18,
every occurrence gated, not just a K-window after some of them), while
future-guard-strict K=8 buys the same accuracy more cheaply by being
*narrower in trigger but wider in scope per trigger* (fewer trigger points,
but each one gates K downstream positions, and only fires on markers
`spec_casc_tok` itself already accepted, which any override guard also
touches for free). Mechanism check is exactly clean (0.0%), as expected for
any override-family guard -- the leak future-guard structurally has doesn't
exist here.

**Verdict changes** (26 -> 25, net -1): 2 improved (case_002, case_006 --
the same two rescues every guard variant makes) against 3 regressed
(case_011, case_014: correct -> no_answer/cap; case_018: correct -> wrong),
plus one lateral move among already-wrong cases (case_004: no_answer ->
wrong). case_011 is the interesting one: the pilot already flagged it as
v2's one distinctive regression (no other guard variant loses it), and it
regresses again here at full scale -- a real, reproducible cost specific to
this variant, not pilot noise.

## Overall AIME24 conclusion: eight variants compared at full 30-case scale

Everything in this document's `spec_casc_tok`-family investigation, one
table. All rows are full 30-case AIME24 sweeps (no pilot-only numbers),
same baseline (`spec_casc_tok`, α=0.3) and same lossless (`strict`)
reference reused throughout:

| variant | accuracy | mean length | l̄ | total rounds | wall-time | hesitation words | relaxed-only |
|---|---:|---:|---:|---:|---:|---:|---:|
| **lossless (strict)** | 23/30 (76.7%) | 10,043 | 2.2046 | 100,605 | 1,234.8s | 4,456 | 0.0% |
| **baseline (spec_casc_tok)** | **26/30 (86.7%)** | **9,440** | **2.4210** | **86,874** | **1,078.2s** | **4,173** | 3.8% |
| override (narrow, marker-level) | 22/30 (73.3%) | 10,397 | 2.3999 | 98,277 | 1,269.6s | 4,949 | 0.0% |
| AND (narrow, marker-level) | 22/30 (73.3%) | 10,964 | 2.3906 | 103,942 | 1,345.3s | 4,822 | 0.0% |
| v2 (wide, override, marker-level) | 25/30 (83.3%) | 10,599 | 2.3986 | 97,540 | 1,274.3s | 4,313 | 0.0% |
| future-guard-strict K=4 | 22/30 (73.3%) | 10,397 | 2.3447 | 97,779 | 1,266.3s | 4,869 | 4.1% |
| **future-guard-strict K=8** | **25/30 (83.3%)** | **9,303** | **2.3950** | **87,607** | **1,137.2s** | **3,952** | 3.5% |
| future-guard-AND K=8 | 23/30 (76.7%) | 10,460 | 2.3724 | 99,463 | 1,288.2s | 4,461 | 4.0% |
| baseline (spec_casc_tok), α=0.5 | 22/30 (73.3%) | 10,495 | 2.4929 | 96,402 | 1,212.9s | 4,532 | 5.0% |
| future-guard-strict K=8, α=0.5 | 20/30 (66.7%) | 10,555 | 2.4484 | 97,984 | 1,273.6s | 4,662 | 5.5% |
| baseline (spec_casc_tok), α=0.7 | 22/30 (73.3%) | 10,337 | 2.6565 | 90,948 | 1,147.4s | -- | -- |
| **future-guard-strict K=8, α=0.7** | **25/30 (83.3%)** | 12,239 | 2.5365 | 109,433 | 1,419.9s | 5,699 | 6.9% |

**No guard variant beats vanilla `spec_casc_tok`'s own 86.7%.** Across
seven guard designs (two marker sets x {override, AND} plus a K-sweep and
an AND-combination of the window mechanism), the unguarded baseline remains
the single best-accuracy arm on AIME24 -- and it's already the cheapest
(shortest completions, fewest rounds, least hesitation language) of every
`spec_casc_tok`-family arm tested. Forcing extra strict verification at
hesitation markers, in every combination tried, costs accuracy relative to
just running `spec_casc_tok` unguarded.

**The seven guards split into two clean clusters, independent of which
axis (marker gating shape, marker set width, combination rule) varies:**

- **High-accuracy cluster (25/30, 83.3%): v2 and future-guard-strict K=8.**
  Two structurally different mechanisms (gate-the-marker-itself-with-a-wide-
  set vs. gate-a-trailing-window-after-a-narrow-trigger) land on the exact
  same accuracy, tied. What actually distinguishes them is efficiency:
  future-guard-strict K=8 is the ONLY guard variant in this whole
  investigation that improves on baseline efficiency (-1.4% length, +0.8%
  rounds -- essentially free) while v2 costs +12.3% length/rounds for the
  same accuracy. If a real choice has to be made between them,
  **future-guard-strict K=8 dominates** -- same accuracy, real efficiency
  win instead of a real efficiency cost. v2's one advantage is a
  structurally clean mechanism check (0.0% relaxed-only, vs.
  future-guard's inherent 3.5% leak at the marker token itself) -- relevant
  only if a provably-airtight guard matters independent of the efficiency
  cost.
- **Low-accuracy cluster (22-23/30, 73.3-76.7%): override, AND,
  future-guard-strict K=4, future-guard-AND K=8.** All four cost BOTH
  accuracy and length/rounds/wall-time relative to baseline -- a clean net
  loss on every axis, not a trade-off. Notably this cluster includes both
  narrow-set marker-level guards (override, AND) AND two future-guard
  variants (K=4, AND-combined) -- neither "narrow marker set" nor "gate the
  marker itself" is what determines cluster membership on its own; K=4's
  window is too short to pay off, and AND's extra conservatism (whether at
  the marker or in a window) consistently costs more than it recovers.
- **Relaxing `spec_casc_tok`'s own alpha is NOT monotonic for the guard.**
  0.3: guard wins narrowly and cheaply (25/30 vs. 26/30, but shorter than
  baseline). 0.5: guard loses clearly (20/30 vs. 22/30, worse on every
  axis -- an 8-case pilot had wrongly suggested a win here, corrected in
  detail above). 0.7: guard wins clearly again (25/30 vs. 22/30, zero
  regressions), but now by spending real extra compute (+18.4% length,
  +23.8% wall-time over the α=0.7 baseline) rather than for free. Three
  alpha values, three different guard/baseline relationships -- this
  doesn't look like a single trend that generalizes cleanly across alpha;
  it looks like alpha has multiple regimes. See "Correction: full-scale
  alpha=0.5 results" and "Pushing further: alpha=0.7" above for the full
  writeups. **None of this changes the alpha=0.3 conclusion above** --
  future-guard-strict K=8 at α=0.3 remains the best cost/accuracy trade
  found in this investigation; α=0.7 buys the same accuracy at meaningfully
  higher cost.

**Practical recommendation for AIME24 with this model/draft pair:** run
`spec_casc_tok` unguarded (α=0.3) if accuracy is the only goal -- no
semantic guard tested here recovers or exceeds its 86.7%. If cutting
hesitation-language volume and completion length is independently valuable
(e.g. for downstream cost, not just accuracy), `spec_casc_tok_semantic_guard_future_guard`
at K=8 is the best available trade: -3.4pp accuracy for a guard that is
*cheaper* than the unguarded baseline, not more expensive -- a genuinely
different profile from every other guard variant tried, all of which buy
whatever accuracy they keep at a real efficiency cost.

## Reference: every `spec_casc_tok`-family method explained, and every full-scale AIME24 result in one place

Everything above this section built up incrementally; this section is the
flat reference -- what each method actually does, and the complete data
matrix (every variant, every alpha tested), independent of the narrative
order they were discovered in.

### The base method: `spec_casc_tok` (Speculative Cascades [Tok])

Narasimhan et al. 2025 appendix ("Faster Cascades via Speculative
Decoding"), as unified into Xia et al. 2026's taxonomy (arXiv:2607.08690
Appendix B, Eq. 15). At each drafted token `x`, instead of the lossless
accept test `p(x)/q(x) >= u`, `spec_casc_tok` accepts against a blended
target:

```
pi_rej(v) = q(v) + eta*p(v)     if v in A   (v is in the "trusted top set")
          = eta*p(v)             otherwise
A   = { u : p(u) >= (1-alpha) * max_w p(w) }     (trusted top set)
eta = 1 - sum_{u in A} q(u)                      (drafter mass NOT already covering A)
```

`p` = target (verifier) distribution, `q` = draft distribution, `alpha` is
the one tunable knob. `A` is the set of tokens the verifier considers
"plausible enough" (within `alpha` of its own top choice); for tokens
inside `A`, the drafter's own probability is trusted outright and topped up
with a rescaled verifier correction; for tokens outside `A`, only the
rescaled correction applies. **Two provable properties this whole
investigation leans on:**
- For `v` in `A`: `pi_rej(v)/q(v) >= 1` always (regardless of `u` -- an
  unconditional accept).
- For `v` outside `A`: `pi_rej(v) = eta*p(v) < p(v)` (since `eta < 1`) --
  i.e. `spec_casc_tok` is **provably more conservative than lossless** for
  out-of-trusted-set tokens. This is the mechanism behind everything in
  this document's earlier "mechanism" section: hesitation markers are
  disproportionately outside `A` (6.6% vs. 2.2% background rate), so
  `spec_casc_tok`'s own unmodified behavior already rejects them more than
  lossless would -- no guard needed to explain part of why it beats
  lossless on accuracy.
- `alpha -> -inf` is the actual strict/lossless limit (`A` empties, `eta`
  -> 1, `pi_rej` -> `p` exactly) -- **not** `alpha=0`, unlike every other
  method in this repo. `alpha=0` still gives `A = {argmax p}` only, a real
  (if narrow) trusted set.
- **Higher alpha = more relaxed**: the threshold `(1-alpha)*max(p)` drops
  as alpha rises, admitting more of the vocabulary into the unconditionally
  -trusted set `A`. 0.3 (this repo's default) is mild; 0.5 and 0.7 (tested
  in the "Pushing further" sections above) are progressively more
  permissive.

### The five hesitation-marker guards, explained

All five guard variants leave `spec_casc_tok`'s formula completely
untouched at unguarded positions; they differ only in what happens at (or
after) a hesitation/discourse marker.

**Marker sets used**: "narrow" = 18 token ids / 5 words (`wait`, `hmm`,
`actually`, `but`, `let's`). "wide" = 35 token ids / 14 words (narrow set
plus `thus`, `we`, `so`, `now`, `let`, `compute`, `similarly`, `define`,
`from`) -- the wide set trades marker specificity for coverage (most of the
additions are generic discourse connectives that open correct reasoning as
often as corrupted reasoning, not hesitation markers specifically).

1. **override** (`spec_casc_tok_semantic_guard`, narrow set) -- at a guarded
   position, force the trusted top set `A` empty for that row. Provably
   identical to running `alpha=-inf` (exact lossless) at that one position,
   not an approximation.
2. **AND** (`spec_casc_tok_semantic_guard_and`, narrow set) -- at a guarded
   position, accept iff BOTH the lossless test AND `spec_casc_tok`'s own
   test would accept (`min(p, pi_rej)` as the effective target). Closes a
   loophole override has: override can *accept* a marker `spec_casc_tok`'s
   own rule would have rejected (whenever `pi_rej(x) > p(x)`, i.e. `x`
   inside the trusted set), which override's own "force to strict" doesn't
   prevent since strict itself might be laxer at that specific token than
   `spec_casc_tok`'s blend was. AND is provably never more lenient than
   either test alone.
3. **v2** (`spec_casc_tok_semantic_guard_v2`, wide set) -- identical
   mechanism to override, wide set instead of narrow. Built to isolate
   whether marker-set *width* alone (independent of window-vs-marker
   gating) explains any of future-guard's edge. Answer: partially --
   width alone recovers real accuracy (22/30 narrow -> 25/30 wide) but not
   future-guard's efficiency.
4. **future-guard-strict** (`spec_casc_tok_semantic_guard_future_guard`,
   wide set, parameter K) -- does NOT gate the marker token itself (that
   still runs plain, unguarded `spec_casc_tok`). Instead, the moment a
   marker is *accepted* (by whichever rule was in force), it arms a
   trailing K-token strict window: for the next K verified positions
   (bonus tokens don't count), the accept test is the raw lossless ratio,
   bypassing `spec_casc_tok`'s blend entirely. First patch in this repo
   with cross-round persistent state (the remaining-window count survives
   across verification rounds via a small kernel-level counter, scoped to
   one real sequence per server process). K=4 and K=8 both tested; K=8 is
   the standout result of this whole investigation (see below).
5. **future-guard-AND** (`spec_casc_tok_semantic_guard_future_guard_and`,
   wide set, parameter K) -- same trailing-window trigger as future-guard-
   strict, but AND-combined inside the window (`min(pi_rej, p)`) instead of
   pure strict -- provably never more lenient than future-guard-strict's
   window at any guarded position, same identity the marker-level AND-guard
   uses.

Mechanism-check column below (`hesitation words, relaxed-only`) is the
direct empirical confirmation: override/AND/v2 are always exactly 0%
(they gate every marker occurrence itself, so nothing marker-shaped can
ever be relaxed-only-accepted); future-guard-strict/AND are never 0% (they
never touch the marker's own accept decision, only what comes after it).

### Complete data: every variant, every alpha tested, full 30-case AIME24

| method | α | K | accuracy | completion length (mean) | accepted length l̄ (mean) | verifier rounds (total) | mean s/round | wall-time (total) | hesitation words | relaxed-only |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| lossless (strict) | n/a | n/a | 23/30 (76.7%) | 10,043 | 2.2046 | 100,605 | 0.01227 | 1,234.8s | 4,456 | 0.0% |
| **baseline** | 0.3 | -- | **26/30 (86.7%)** | **9,440** | **2.4210** | **86,874** | **0.01241** | **1,078.2s** | **4,173** | 3.8% |
| override (narrow) | 0.3 | -- | 22/30 (73.3%) | 10,397 | 2.3999 | 98,277 | 0.01292 | 1,269.6s | 4,949 | 0.0% |
| AND (narrow) | 0.3 | -- | 22/30 (73.3%) | 10,964 | 2.3906 | 103,942 | 0.01294 | 1,345.3s | 4,822 | 0.0% |
| v2 (wide, override) | 0.3 | -- | 25/30 (83.3%) | 10,599 | 2.3986 | 97,540 | 0.01306 | 1,274.3s | 4,313 | 0.0% |
| future-guard-strict | 0.3 | 4 | 22/30 (73.3%) | 10,397 | 2.3447 | 97,779 | 0.01295 | 1,266.3s | 4,869 | 4.1% |
| **future-guard-strict** | 0.3 | 8 | **25/30 (83.3%)** | **9,303** | 2.3950 | **87,607** | 0.01298 | **1,137.2s** | **3,952** | 3.5% |
| future-guard-AND | 0.3 | 8 | 23/30 (76.7%) | 10,460 | 2.3724 | 99,463 | 0.01295 | 1,288.2s | 4,461 | 4.0% |
| baseline | 0.5 | -- | 22/30 (73.3%) | 10,495 | 2.4929 | 96,402 | 0.01258 | 1,212.9s | 4,532 | 5.0% |
| future-guard-strict | 0.5 | 8 | 20/30 (66.7%) | 10,555 | 2.4484 | 97,984 | 0.01300 | 1,273.6s | 4,662 | 5.5% |
| baseline | 0.7 | -- | 22/30 (73.3%) | 10,337 | 2.6565 | 90,948 | 0.01262 | 1,147.4s | 4,895 | 7.3% |
| **future-guard-strict** | 0.7 | 8 | **25/30 (83.3%)** | 12,239 | 2.5365 | 109,433 | 0.01297 | 1,419.9s | 5,699 | 6.9% |

Bolded rows are the accuracy-tier winners at each alpha value tested
(baseline at α=0.3 overall; future-guard-strict K=8 tied with it at three
different alphas, via three different cost profiles -- free at 0.3,
expensive at 0.7, and simply worse at 0.5). Not run: override/AND/v2 at
α=0.5 or 0.7 (queued but not executed -- the autonomous relaxation chain
was stopped after α=0.7 per explicit instruction, before reaching this
phase), K=4 at α=0.5/0.7, and any alpha between the three tested points
(0.4, 0.6 would be needed to characterize the 0.5 dip / 0.7 recovery
transition rather than just its endpoints).

Full narrative, mechanism analysis, and reproduce commands for every row
above are in the sections preceding this one.
