# autoguard — autonomous research loop

You are running an autonomous experiment loop in the style of
`karpathy/autoresearch`. Your job: discover a **guard** that stops the
lossy relaxed-verification method `spec_casc_tok` from inflating the
completion length on hard reasoning problems, **without losing accuracy**.

You edit exactly **one file**: `patches/autoguard.py`. Everything else —
the vLLM kernel, the patch that calls your guard, the replay harness, the
grader, this file — is frozen. Do not edit it.

---

## Background (read once)

`spec_casc_tok` is a training-free relaxed speculative-decoding verifier.
At `alpha > 0` it accepts drafted tokens its trusted-top-set test allows,
which is faster but lets the drafter pull the trajectory into
rambling / self-correction / restart loops. On AIME24 the worst lossy
methods roughly double the mean completion length versus lossless
decoding; `spec_casc_tok` at `alpha=0.3` is milder but still drifts on
some cases. `analysis/semantic_guard/` is the prior manual investigation of
this exact failure — read `analysis/semantic_guard/SUMMARY.md` for what has
already been tried (hesitation-marker token guards, K-token future
windows, hidden-state-recurrence triggers, entropy-window shape checks).
The recurring result there: forcing lossless verification at well-chosen
positions cuts length, but naive choices also cost accuracy. Beating that
trade-off is the point.

A guard here is a per-verification-round boolean mask over the drafted
positions: `True` => verify that position **losslessly** this round
(provably identical to `spec_casc_tok`'s own `alpha=-inf` limit at that
row); `False` => leave `spec_casc_tok` untouched. An all-`False` mask is
the baseline; an all-`True` mask is full lossless `strict`. You want a
**sparse, well-targeted** mask.

---

## The file you edit: `patches/autoguard.py`

It defines one function:

```python
def decide(*, round_index, committed_token_ids, draft_token_ids,
           draft_probs, target_probs, num_draft_tokens, vocab_size) -> torch.Tensor
```

Called once per verification round, on the GPU, before that round's
accept/reject kernel. Returns a `[num_tokens]` bool tensor. The full
contract (argument shapes/meanings, safety behaviour, performance rules)
is the module docstring in that file — read it before your first edit.
Three un-tuned reference strategies are in comments at the bottom.

Key facts:
- A raised exception / wrong-shape / non-tensor return degrades to an
  all-`False` mask (logged once). It will not crash the server — but a
  `decide()` that fails `apply.sh` (syntax error, import error, failing
  plumbing test) makes the whole eval a FAILURE, so check it compiles.
- `committed_token_ids` is the generated text so far as token ids
  (request 0, oldest-first, capped at 40000). This repo serves one
  request per server, so module-level state in `patches/autoguard.py` is
  safe across rounds if you need history beyond what's passed in.
- Keep it cheap: it is on the hot path every round. Vectorised torch over
  the `[num_tokens, vocab]` tensors is fine; a Python loop over the vocab
  is not. No file I/O, no new imports beyond torch/stdlib.

---

## Setup (once, before the loop)

1. `git checkout -b autoguard-run` (work on a branch, accumulate commits).
2. Read `patches/autoguard.py` and `analysis/semantic_guard/SUMMARY.md`.
3. Confirm the eval plan: `.venv-vllm/bin/python autoresearch/evaluate.py --dry-run`
4. Collect the baseline **once** (this runs 8 fresh vLLM servers, ~30–45
   min on the single GPU — there is no parallelism here, it is inherently
   serial): `.venv-vllm/bin/python autoresearch/evaluate.py --baseline`
   This writes `autoresearch/baseline.json`. Do not delete it.
5. Initialise the log if it has only a header:
   `autoresearch/results.tsv` (see "Logging" below).

You may not install dependencies. VRAM is a soft constraint — a guard that
somehow blows it up is unacceptable. The single GPU is a hard serial
bottleneck: one eval ≈ 30–60 min. Budget accordingly; do not start more
than one eval at a time.

---

## The experiment loop

Repeat until you stop finding improvements (or the user stops you):

1. **Hypothesis.** State, in one sentence, what failure shape you are
   targeting and why this `decide()` change should shorten completions
   without breaking correctness.
2. **Edit** `patches/autoguard.py` — `decide()` only (plus module-level
   helpers/state in that same file if you need them).
3. **Sanity check** it imports:
   `.venv-vllm/bin/python -c "import ast; ast.parse(open('patches/autoguard.py').read())"`
   and ideally `bash patches/apply.sh spec-casc-tok-autoguard` (runs the
   plumbing test, no GPU).
4. **Evaluate:** `.venv-vllm/bin/python autoresearch/evaluate.py`
   Reads `autoresearch/metrics.json` when done.
5. **Decide:**
   - `failure: true` → **revert**: `git checkout patches/autoguard.py`.
   - `improved_vs_baseline: true` **and** not a failure → **keep**:
     `git add patches/autoguard.py autoresearch/results.tsv && git commit`
     with a message stating the hypothesis and the score.
     Then treat this new score as the bar to beat (update your running
     "best" — the objective is still measured against the fixed
     `baseline.json`, but only commit changes that also beat your current
     best).
   - Neither improved nor failed → revert, try a different idea.
6. **Log** one row to `autoresearch/results.tsv` **every** iteration,
   kept or not (see below).
7. Go to 1.

Do not pause to ask for confirmation once the loop is running. Do not
edit `autoresearch/evaluate.py`, the grader, the prompts, the patch, or
the kernel to make numbers look better — that is the one way to invalidate
the whole run.

---

## Metric (authoritative: `autoresearch/evaluate.py`)

- **score** = mean completion length (output tokens) over the 8 fixed
  AIME24 cases, for the `spec_casc_tok_autoguard` arm. **Lower is better.**
- **Hard accuracy floor:** `accuracy >= baseline_accuracy - 1/8`. An eval
  below the floor is a **failure**, not a candidate, no matter how short.
- Also a failure: any eval run errors, `apply.sh` rejects your
  `autoguard.py`, or the eval exceeds `--max-eval-seconds` (default 3600).
- `metrics.json` also reports `delta_completion_tokens`,
  `delta_accuracy_cases`, `mean_l_bar`, `guard_fire_rate` (fraction of
  drafted tokens the guard forced strict on) and per-case verdicts — use
  these to reason about *why* a guard helped or hurt, not just whether.

A good result: a clear cut in mean completion length (say ≥8%) at
`delta_accuracy_cases >= 0`, with a `guard_fire_rate` well under 1.0 (a
guard that fires everywhere is just `strict` and defeats the purpose).

---

## Output format

Each iteration, before editing, print:

```
## iteration N
hypothesis: <one sentence>
change: <what in decide() / autoguard.py>
```

After `evaluate.py`, print the `[IMPROVED] / [no improvement] / [FAILURE]`
line it emits plus your keep/revert decision and the reason.

---

## Logging results

`autoresearch/results.tsv` — append one tab-separated row per iteration.
Header (already in the file):

```
iteration	timestamp	git_sha	score	baseline_score	delta_tok	acc_cases	baseline_acc_cases	delta_acc	guard_fire_rate	failure	kept	note
```

- `git_sha`: `git rev-parse --short HEAD` (of the commit this iteration is
  built on, before any keep-commit).
- `score` / `delta_tok` / `acc_cases` / `guard_fire_rate`: straight from
  `metrics.json`. Use `NA` for a failed eval with no score.
- `kept`: `yes` if you committed it, `no` otherwise.
- `note`: your one-line hypothesis, trimmed.
