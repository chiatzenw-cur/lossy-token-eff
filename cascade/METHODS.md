# Methods: every acceptance rule in this repo, as implemented

Notation: `p` verifier (target) next-token distribution, `q` drafter
distribution, `x` the drafted token, `u ~ U(0,1)` the acceptance draw.
Strict (lossless) speculative decoding accepts iff `p(x)/q(x) >= u` and
resamples rejections from `norm(max(0, p - q))`. Every relaxed rule below
replaces that test (and, for the blend-type rules, the residual). All are
patches to vLLM 0.26.0's `rejection_sample()`; `patches/README.md` has the
mechanics. Alpha always comes from a `/tmp/lossy-token-eff-<label>-alpha-$UID`
file written by `remote/run_server_vllm.sh`, never from the environment.

## The rules

| method (`--methods` name) | patch label | rule | alpha meaning | strict point | default | campaign grid | type | status |
|---|---|---|---|---|---|---|---|---|
| `mentored_dec` | `mentored-dec` | accept iff `p(x)/((1-a) q(x)) >= u` | boost; forward-KL budget | 0 | 0.37 | 0.15 0.35 0.55 0.75 | accept-test | campaign |
| `cactus` | `cactus` | accept iff `g_x/q(x) >= u`, `g_x = min(p(x)+sqrt(2a p(x)(1-p(x))), 1)`; residual on relaxed target | reverse-KL budget | 0 | 0.25 | 0.03 0.08 0.18 0.35 | blend | campaign |
| `r_fuzzy` | `r-fuzzy` | if `JSD(p,q) < a`: accept always; else strict | divergence threshold | -inf | 0.3 | 0.03 0.08 0.15 0.25 | switch | campaign |
| `spec_casc_opt` | `spec-casc-opt` | defer iff `max q < max p - a*TV(p,q)`; deferred -> strict, else accept | deferral cost (Eq. 10) | -inf | 0.05 | -0.3 -0.1 -0.02 0.05 | switch | campaign |
| `spec_casc_tok` | `spec-casc-tok` | `A = {v: p(v) >= (1-a) max p}`, `eta = 1 - q(A)`, `pi(v) = q(v)+eta p(v)` on A else `eta p(v)`; accept iff `pi(x)/q(x) >= u`; residual on `pi` | head width (Eq. 15) | **-inf, not 0** | 0.3 | 0.15 0.35 0.55 0.8 | blend | campaign |
| `spec_casc_tok_lt` | `spec-casc-tok-lt` | accept always iff `p(x) >= (1-a) max p`; else strict | head width; lossless tail | **-inf, not 0**; a <= 1 | 0.3 | 0.15 0.35 0.55 0.8 | switch | verified on H100 (E0); run at scale on all 6 benchmarks (RESULTS.md) |
| `spec_casc_opt_ent` | `spec-casc-opt-ent` | defer iff `H(q) > H(p) + a*TV(p,q)` (nats); deferred -> strict, else accept | deferral cost, entropy plug-in (App. C.2) | -inf | 0.0 | -2 -0.5 0 0.5 (guess) | switch | verified on H100 (E0); not yet run at scale |
| `spec_casc_diff` | `spec-casc-diff` | defer iff `max q < max p - a`; deferred -> strict, else accept | constant margin (Eq. 5) | -inf | 0.0 | -0.3 -0.1 -0.02 0.05 | switch | verified on H100 (E0); not yet run at scale |
| `spec_casc_chow` | `spec-casc-chow` | defer iff `max q < 1 - a`; deferred -> strict, else accept | drafter confidence threshold (Eq. 2) | -inf; a <= 1 | 0.5 | 0.1 0.3 0.5 0.7 | switch | verified on H100 (E0); not yet run at scale |
| `spec_casc_opt_head` | `spec-casc-opt-head` | defer iff (`max q < max p - a*TV`) **or** (`p(x) < (1-b) max p`); deferred -> strict, else accept | a as opt; **b** = head width, second knob | -inf (any b); b = 1 is plain opt | a 0.05, b 0.8 | a: opt's grid; b in {0.15, 0.35} | switch | verified on H100 (E0); run on AIME24 (E6, RESULTS.md) |

"switch" rules only change the accept test; their residual is stock `p`.
"blend" rules build a full relaxed distribution and resample rejections
from it (`recovery_target_probs` in the patch). The guard variants layered
on `spec_casc_tok` and `r_fuzzy` (antiloop, force-commit, self-check,
semantic guards, hsr-guard, judge-nudge) are documented in
`analysis/semantic_guard/README.md` and `old_runs/readme.md`; they are not
part of this workspace's plan.

## How the cascade rules relate

Two independent design axes fall out of the table:

1. **The trigger** — when does the rule stop running the strict test?
   opt: two argmaxes and TV; diff: two argmaxes; chow: the drafter's
   argmax alone; opt_ent: two entropies and TV; r_fuzzy: JSD. All of these
   trust the drafter *wholesale* at the triggered positions: whatever token
   it drafted is committed, including tokens the verifier considers
   unlikely.
2. **The head restriction** — is the free pass limited to tokens the
   verifier itself ranks highly? tok and tok_lt: yes (`p(x) >= (1-a) max p`);
   opt_head: yes, on top of opt's trigger; every other rule: no.

`cascade/results/trace_rank_analysis.md` (E7) shows axis 2 is what
separates the non-inflating rule from the inflating ones. E1 and E6 test
whether that holds when the restriction is added to a looser trigger.

## Alpha traps

- `spec_casc_tok`, `spec_casc_tok_lt`: alpha = 0 is **not** strict (the
  verifier's own argmax is still a free pass); strict is alpha -> -inf.
  `scripts/lossy_methods.py` refuses 0.0 for this family. alpha = 1 means
  the whole vocabulary is trusted (accept every draft token); the one
  AIME24 run at tok alpha = 1 in `old_runs/` produced 19x the strict
  length.
- `spec_casc_opt`, `spec_casc_diff`, `spec_casc_opt_ent`, `spec_casc_opt_head`:
  more *negative* alpha defers more (safer); positive alpha trusts the
  drafter even when it is less confident than the verifier. opt at alpha
  > 0 lowers its bar most where TV is largest — where the models disagree
  most.
- `spec_casc_opt_ent`'s alpha multiplies TV against an entropy difference in
  nats; its grid is not comparable with opt's and must be calibrated.
- `spec_casc_opt_head`'s beta lives in `(-inf, 1]`; the run directory carries
  it as `alpha<a>_beta<b>` so two betas never collide.

## Implementation facts that matter when adding or reading a rule

- All five new variants derive from the `spec-casc-opt` patch: identical
  Triton kernel hunk (`defer=True` -> strict test, `defer=False` -> accept)
  with a different per-token boolean mask computed in PyTorch before the
  launch. Their kernel test is therefore `test_spec_casc_opt.py`'s own.
- The tracer (`patches/relaxation_trace.py`) derives `lossy_would_accept =
  strict_would_accept | ~defer_mask` for switch rules, so every traced run
  of a switch rule records its own strict counterfactual per token.
- V1 vs V2: these patches modify the V1 runner (`vllm/v1/sample/
  rejection_sampler.py`), which GPT-OSS-20B uses. Qwen3-8B uses the V2
  runner (`vllm/v1/worker/gpu/spec_decode/rejection_sampler_utils.py`), whose
  consolidated multi-method file exists only on the old box (E8). None of
  the new variants exist in V2.
- Manifest hashes for the five new patches were computed offline from the
  pristine v0.26.0 file (`HASHES.txt`); `apply.sh` re-verifies at install.
- Recipe for another variant: `README.md` section 5.
