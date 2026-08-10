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
| accuracy: r_fuzzy | 13/30 (43.3%) | 93/164 (56.7%) | 106/194 (54.6%) |
| accuracy: +guard | **11/30 (36.7%)** | **86/164 (52.4%)** | **97/194 (50.0%)** |
| accuracy change | -2 cases (-6.7pp) | -7 cases (-4.3pp) | -9 cases (-4.6pp) |
| mean completion length | 19,506 → 16,942 | 1,787 → 1,525 | 4,527 → 3,909 |
| length change | -13.1% | -14.7% | -13.6% |
| mean verifier rounds | 3,831 → 3,457 | 343.1 → 303.8 | 882.4 → 791.4 |
| rounds change | -9.7% | -11.5% | -10.3% |
| mean l_bar | 4.129 → 3.957 | 4.205 → 4.057 | -4.2% / -3.5% |
| hesitation words | 18,052 → 11,984 | 6,245 → 3,947 | 24,297 → 15,936 |
| hesitation words, % relaxed-only | 26.2% → **0.01%** | 24.7% → **0.03%** | 25.8% → **0.01%** |
| mean s/round (throughput tax) | 0.01241 → 0.01273 (+2.6%) | 0.01304 → 0.01353 (+3.8%) | 0.01261 → 0.01299 (+3.0%) |
| total generation wall-time | 1,425s → 1,320s (-7.4%) | 731.5s → 671.7s (-8.2%) | 2,157s → 1,992s (-7.6%) |

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
