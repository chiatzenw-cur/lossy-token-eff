# cascade/ — speculative-cascade workspace

Bill's working area for the "explore speculative cascades further" thread
from the 2026-09 results review (Chiatzen's campaign found `spec_casc_tok`
to be the one training-free relaxation that never inflates completion
length; HaoChen asked whether *any* method gives real end-to-end speed if
accuracy is ignored, as long as the output is not obvious garbage).
Everything here builds on the existing campaign machinery — it does not
fork it. Read `campaign/PLAN.md`, `campaign/FINDINGS.md` and
`patches/README.md` first if you have not.

**Start here:** `EXPERIMENTS.md` is the runnable plan — every experiment,
why, the exact command, cost, outputs, and decision rule. `bash
cascade/run.sh <id>` runs one.

```
cascade/
  README.md          this file: rules, what the data says, the hypothesis, layout
  RESULTS.md         the results report (2026-09-13): every experiment relative to lossless, interpretation, conclusion, caveats
  EXPERIMENTS.md     the registry: E0..E8 with commands, costs, predictions, decision rules
  METHODS.md         every acceptance rule in the repo (10 incl. 5 new), knobs, traps, how they relate
  METRICS.md         what every number means and where it comes from
  SETUP.md           what must be true before anything runs; verified vs unverified
  DIRECTIONS.md      the reasoning behind the experiment list (D1..D9), what to skip and why
  JOURNAL.md         dated log
  run.sh             `bash cascade/run.sh E1-gsm8k [--target nibi] [--mode persistent] [--dry-run]`
  analysis/
    speed_ignoring_accuracy.py   end-to-end speed of every campaign point (rounds, wall, length, garbage)
    trace_rank_analysis.py       out-of-head lossy-only accepts vs inflation, from proposals.jsonl traces
    timing_report.py             tok/s, rounds/s, c_rel estimate across arms / draft lengths
    results_pdf.py               builds results/final_results.pdf (summary + one page per benchmark + notes)
  results/           outputs of the above (regenerable); final_results.pdf is the shareable report
  cluster/           Nibi: env build, sbatch wrappers, rsync, first-login checklist
patches/vllm-0.26.0-spec-casc-{tok-lt,opt-ent,diff,chow,opt-head}.patch   the 5 new variants (+ test_*.py)
```

## 1. The two cascade rules, exactly as this repo runs them

Both are patches to vLLM 0.26.0's `rejection_sample()` (one patch live at a
time, alpha from a uid-scoped `/tmp` file). Per drafted token `x` with
drafter `q` and verifier `p` (full table of all ten rules: `METHODS.md`):

**`spec_casc_opt`** (Narasimhan et al. 2025 Eq. 10; Xia et al. 2026 App. B) —
a per-position *switch*:

```
defer  iff  max_u q(u) < max_u p(u) - alpha * TV(p, q)
accept iff  defer and p(x)/q(x) >= u,   OR   not defer (always)
```

Only the accept test changes; residual on rejection is stock `p`. `alpha
-> -inf` is exactly strict. The decision looks only at the two argmax
probabilities — never at `p(x)` of the token actually drafted.

**`spec_casc_tok`** (the paper's token-level variant, Eq. 15) — a
full-vocabulary *blend* with the verifier's trusted top set `A`:

```
A         = { v : p(v) >= (1 - alpha) * max_w p(w) }
eta       = 1 - sum_{v in A} q(v)
pi_rej(v) = q(v) + eta * p(v)   if v in A,   else   eta * p(v)
accept iff pi_rej(x)/q(x) >= u ;  residual sampled from norm(max(0, pi_rej - q))
```

Inside `A` the drafted token is accepted with probability 1. Outside `A` it
is accepted with probability `min(1, eta * p(x)/q(x))` — **stricter than
lossless** since `eta <= 1`. Strict is `alpha -> -inf`, **not** `alpha = 0`.

## 2. What the data says

**Campaign tables** (`results/speed_ignoring_accuracy.md`; GPT-OSS-20B +
EAGLE3, full-sweep points, paired against strict; definitions in
`METRICS.md`):

| dataset | strict acc | `spec_casc_tok` best clean point | `spec_casc_opt` at its loosest alpha (0.05) |
|---|---:|---|---|
| gsm8k | 0.96 | a=0.8: **1.21x** rounds, len 0.96x, acc 0.97 | 0.94x rounds, len 1.46x, acc 0.94 |
| aime24 | 0.77 | a=0.15: **1.09x**, len 1.00x, acc 0.83 | **0.59x** (a net slowdown), len 2.48x, acc 0.37, 43% budget hits (strict 7%) |
| humaneval | 0.96 | a=0.8: 1.08x, len 1.04x, acc 0.94 | 0.77x, len 1.73x, acc 0.82 |
| livecodebench | 0.89 | a=0.15: 1.04x, len 1.00x, acc 0.92 | 0.86x, len 1.64x, acc 0.49 |
| longbench_v2 | 0.56 | a=0.8: 1.04x, len 1.13x, acc 0.53 | 0.76x, len 1.79x, acc 0.47 |
| mtbench (no grader) | -- | a=0.8: 1.14x, len 0.96x | 1.32x, len 1.09x |

1. **The clean end-to-end ceiling is small.** Across all five methods, the
   best point that does not produce more budget-exhausted outputs than
   strict is 1.04x–1.21x on every graded GPT-OSS dataset (1.68x on
   MT-Bench, ungraded, from cactus). `spec_casc_tok` *is* that point on
   gsm8k, aime24 and livecodebench, with accuracy at or above strict. On
   Qwen3-8B (weak drafter, l̄ 0.7–2.2) every cascade point is within
   0.94x–1.07x.
2. **`spec_casc_opt` is a net slowdown on every long-form dataset at its
   loosest setting** (0.59x–0.86x): its length inflation (1.46x–2.48x)
   outruns its acceptance gain.

**Traces** (`results/trace_rank_analysis.md`, E7; 1,226 traced runs in
`old_runs/`): the one rule with **zero** out-of-head lossy-only accepts
(tokens strict would have rejected, with `p(x) < 0.2 max p`) is the one
rule that never inflates; every inflating rule commits 16–155 such tokens
per 1,000, in the same order as its inflation; and `spec_casc_tok` with
the head restriction removed (alpha = 1) inflates 19x. Within an arm,
per-case rates do not predict which cases loop — it is a rule-level
exposure effect, not a per-token trigger. Full table and caveats in
`EXPERIMENTS.md` (E7).

## 3. The hypothesis and the plan

*Length inflation is driven by committing draft tokens the verifier
considers unlikely, not by relaxation per se.* **Refined after the first
cluster runs (JOURNAL 2026-09-12):** "unlikely" is a matter of degree, and
the safe zone is narrow — on AIME24 a free pass for tokens within ~15–20%
of the verifier's top choice (`tok_lt`) gives +11–14% accepted
tokens/round with no inflation and no accuracy loss (990-run sweep), while
wider free passes bring the rambling back. **And the ceiling is set by the
same quantity (JOURNAL 2026-09-13, E6):** bolting the narrow head onto
opt's much looser trigger removes opt's 2.5× rambling but also its
acceptance gain — with the head in place, acceptance is the same as
tok_lt's whatever the trigger. So ≈1.05–1.1× on long reasoning (≈1.2× on
short math) is what head-restricted training-free relaxation can deliver
with this drafter. Two design axes follow
(`METHODS.md` "How the cascade rules relate"): the **trigger** (when to
stop running the strict test) and the **head restriction** (whether the
free pass is limited to the verifier's own top set). Every rule in Xia et
al. varies the trigger; only tok restricts the head.

The five new variants isolate the two axes — `spec_casc_tok_lt` (tok's
restriction, lossless tail), `spec_casc_opt_head` (opt's trigger + tok's
restriction), `spec_casc_opt_ent` (a different trigger for opt),
`spec_casc_diff` / `spec_casc_chow` (the source paper's baseline triggers)
— and `EXPERIMENTS.md` E1–E6 run them with predictions written down in
advance. All five are V1-only (GPT-OSS-20B; Qwen3 needs E8); all passed E0
on an H100 (2026-09-11), and `tok_lt` / `opt_head` have since been run at
scale on every benchmark — see `RESULTS.md` and `results/final_results.pdf`.

## 4. Data caveats

(a) The 50->150 case extensions used one warm server per arm, so
`wall_speedup` carries the request-ordinal confound; `rounds_speedup` is
the column to trust. (b) Qwen3 `spec_casc_tok`/`cactus` numbers come from
an accept-test-only V2 port (residual on raw `p`). (c) The consolidated V2
file only exists on the old box (E8). (d) Everything is seed 0,
temperature 1, `NUM_SPEC=6`, batch 1.

## 5. Adding another variant (~30 minutes)

The pattern is spec-casc-opt's; the generators that built the five variants
lived at `/tmp/casc_work/make_variants{,2}.py` on Bill's Mac — the steps:

1. Pristine `rejection_sampler.py` from the vLLM v0.26.0 tag; sha256 must
   equal `HASHES.txt`'s `upstream` line.
2. Apply `vllm-0.26.0-spec-casc-opt.patch`; edit the mask block, module
   comment, alpha-file name, `[... PATCH]` print prefix and the tracer's
   `relaxation_method`; rename `_SPEC_CASC_ALPHA*` to a unique symbol
   (the server script probes it with `hasattr`). A second knob follows
   `spec-casc-opt-head`'s pattern.
3. `diff -u --label a/vllm/v1/sample/rejection_sampler.py --label b/...` ->
   `patches/vllm-0.26.0-<label>.patch`; `patch -p1 --dry-run` against
   pristine; sha256 into `HASHES.txt`.
4. Register: `scripts/lossy_methods.py`, `patches/apply.sh` (case list +
   usage + knob listing), `remote/run_server_vllm.sh` (env default, knob
   file, `neutralise_all_knobs`, `case` block with `probe_patched`),
   `scripts/campaign_run.py` (`ALPHA_GRIDS`; single-knob methods only),
   and for a second knob `scripts/fresh_server_replay.py` (flag, params
   suffix, env passthrough).
5. `patches/test_<method>.py` (plumbing, formula; import the kernel test
   from `test_spec_casc_opt.py` if the kernel hunk is unchanged).
6. Add an experiment id to `run.sh` and a section to `EXPERIMENTS.md`.

A *blend* rule (relaxed residual) starts from the spec-casc-tok patch
instead — it shows where `recovery_target_probs` is substituted.
