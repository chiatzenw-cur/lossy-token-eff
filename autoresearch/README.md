# autoresearch/ — autonomous guard search

An autonomous experiment loop, in the style of
[`karpathy/autoresearch`](https://github.com/karpathy/autoresearch),
pointed at this repo's own research question: **can a guard stop the lossy
relaxed verifier `spec_casc_tok` from inflating completion length on hard
reasoning problems without costing accuracy?**

An AI coding agent (Claude Code or similar) is pointed at `program.md`,
which tells it to edit one file in a loop, run a frozen evaluator, keep
changes that improve a single scalar, and commit as it goes.

## The mapping to karpathy/autoresearch

| autoresearch | here |
|---|---|
| `prepare.py` (frozen data + eval harness) | `autoresearch/evaluate.py` + `scripts/fresh_server_replay.py` + `scripts/grade_aime.py` + `prompts/aime24/` + the vLLM kernel |
| `train.py` (the one file the agent edits) | **`patches/autoguard.py`** — specifically `decide()` |
| `program.md` (human-written directions) | `autoresearch/program.md` |
| metric `val_bpb`, lower is better | **mean completion length** (output tokens) over 8 fixed AIME24 cases, lower is better |
| fixed 5-minute training budget | fixed 8-case fresh-server replay, ~30–60 min (one H100, serial — no parallelism) |
| ">10 min run = failure" | eval that breaks the accuracy floor, errors, or exceeds `--max-eval-seconds` = failure |
| accumulates git commits on a branch | same |

## What a "guard" is

`spec_casc_tok` (Narasimhan et al. 2025 "Tok" variant) accepts a drafted
token when the verifier's probability keeps it in a trusted top set — fast,
but at `alpha>0` it lets the drafter steer into rambling / self-correction
/ restart loops that inflate the output (see `analysis/semantic_guard/` for
the standing manual investigation of exactly this).

A guard is a per-verification-round boolean mask over the drafted
positions. `True` at a position forces **lossless** verification there this
round — provably identical to running `spec_casc_tok`'s own `alpha=-inf`
limit at that one row (trusted top set forced empty ⇒ `eta=1` ⇒
`pi_rej=p`). `False` leaves `spec_casc_tok` untouched.

- all-`False` mask  ≡  plain `spec_casc_tok`  (the baseline)
- all-`True` mask   ≡  lossless `strict`

The search is for a **sparse, well-targeted** mask that recovers most of
`strict`'s brevity for a fraction of its cost.

## Architecture

```
patches/autoguard.py                     <- THE ONLY FILE THE LOOP EDITS
    decide(*, round_index, committed_token_ids, draft_token_ids,
           draft_probs, target_probs, num_draft_tokens, vocab_size)
        -> torch.Tensor[bool]  shape [num_tokens]   (True = force strict here)

patches/vllm-0.26.0-spec-casc-tok-autoguard.patch   <- FROZEN
    a verbatim copy of the spec-casc-tok-semantic-guard patch with the
    hard-coded hesitation-marker id list swapped for a call into
    autoguard.decide(). Same stateless in-kernel top-set-forcing
    mechanism. Adds a post-kernel _autoguard_observe() that maintains the
    round counter + a rolling committed-token history for decide().
    Hash-pinned in patches/HASHES.txt as `spec-casc-tok-autoguard`.
    A broken decide() degrades to an all-False mask, never a crash.

autoresearch/evaluate.py                  <- FROZEN
    installs the current patches/autoguard.py (apply.sh, runs the plumbing
    test), clears + replays the 8-case guard arm, grades it, compares to
    autoresearch/baseline.json, writes autoresearch/metrics.json with a
    single `score` + a `failure` flag.

autoresearch/program.md                   <- the agent's instructions
autoresearch/results.tsv                  <- durable per-iteration log (tracked)
autoresearch/runs/, logs/, metrics.json, baseline.json   <- scratch (gitignored)
```

Everything the agent must not touch: `evaluate.py`, the `.patch` file,
`patches/HASHES.txt`, `patches/apply.sh`, the vLLM kernel, `prompts/`,
`scripts/grade_aime.py`, `scripts/fresh_server_replay.py`, `program.md`.

## Running it

One-time, per machine:

```bash
git checkout -b autoguard-run
.venv-vllm/bin/python autoresearch/evaluate.py --dry-run     # inspect the plan
.venv-vllm/bin/python autoresearch/evaluate.py --baseline    # ~30-45 min, writes baseline.json
```

Then either drive the loop yourself following `program.md`, or hand it to
an agent:

```
claude   # then: "follow autoresearch/program.md"
```

Each iteration is one `.venv-vllm/bin/python autoresearch/evaluate.py`
(~30–60 min GPU, serial). `metrics.json` after each:

```json
{
  "score": 8123.5,                       // mean completion tokens, lower is better
  "failure": false,
  "improved_vs_baseline": true,
  "delta_completion_tokens": -1316.5,
  "delta_accuracy_cases": 0,
  "guard_fire_rate": 0.031,              // fraction of drafted tokens forced strict
  "baseline": { ... }, "guard": { ... }
}
```

## Manual smoke test of the arm (no loop)

```bash
bash patches/apply.sh spec-casc-tok-autoguard          # applies patch, installs autoguard.py, runs the test
.venv-vllm/bin/python scripts/fresh_server_replay.py \
    --arms spec_casc_tok_autoguard --spec-casc-tok-autoguard-alpha 0.3 \
    --cases case_001 --prompt-root prompts/aime24 \
    --runs-root autoresearch/runs --log-root autoresearch/logs \
    --max-new-tokens 32768
```

With the shipped no-op `decide()` this is bit-for-bit `spec_casc_tok`.

## Notes / limitations

- **Single GPU, fully serial.** Fresh-server-per-measurement is a hard
  requirement in this repo (`remote/ENVIRONMENT.md`); request position on a
  warm engine changes output length. One eval ≈ 30–60 min. Do not run two.
- **8 cases is small.** A ~8%+ length cut at `delta_accuracy_cases >= 0`
  is a real signal at this scale; single-case accuracy flips are not.
  Promote a promising guard to the full 30-case AIME24 set (and HumanEval)
  by hand before believing it — the same discipline
  `analysis/semantic_guard/` follows.
- **v1 scope.** `decide()` sees draft/target distributions, the committed
  token history, and round index. It does **not** see target hidden states
  (that needs the model-runner patch — a deliberate future extension).
- `evaluate.py` reverses a stale stateful `*-model-runner` patch to
  pristine before measuring, so a guard is not silently taxed by leftover
  per-round work from an earlier experiment.
