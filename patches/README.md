# Relaxed speculative decoding patches for vLLM 0.26.0

Five training-free relaxed speculative decoding methods, patched into
vLLM's rejection sampler, named and parameterised to match the taxonomy in
Xia et al. 2026, "A Practical Investigation of Training-free Relaxed
Speculative Decoding" (arXiv:2607.08690, Table 2). All five are mutually
exclusive at the file level (they patch the same pristine
`rejection_sampler.py`) — use `patches/apply.sh <method>` to switch between
them; it refuses to guess if a different method's patch is already installed.

vLLM exposes no acceptance-relaxation knob of its own:
`rejection_sample_method` offers only `standard` (min(1, p/q), lossless),
`synthetic` (a prescribed acceptance rate, ignoring p and q entirely), and
`block`. Every method below needs a real patch.

| method | source | alpha's meaning | alpha at strict |
|---|---|---|---|
| `mentored-dec` | Tran-Thien 2023 (β=1); Xia et al. Table 2 Eq. 9 | boosts π_rej(x) = min(p(x)/(1-α), 1) | **0.0** |
| `cactus` | Hao & Mou 2026 | bounds reverse KL(π‖p) ≤ α | **0.0** |
| `spec-casc-opt` | Narasimhan et al. 2025 | deferral cost in a cascade loss | **-inf** |
| `r-fuzzy` | Holsman et al. 2025 (reducible variant) | Jensen-Shannon divergence threshold | **-inf** |
| `spec-casc-tok` | Narasimhan et al. 2025 appendix ("Tok") | trusted-top-set threshold | **-inf, NOT 0.0** |

**Read that last column before touching spec-casc-tok.** Every other method
in this table uses its "no relaxation" value as the safe default when its
config file is missing — that convention holds for four of five methods, but
`spec-casc-tok`'s own formula is NOT the identity at α=0 (see the module
comment in `vllm-0.26.0-spec-casc-tok.patch` and `test_spec_casc_tok.py`'s
`test_alpha_zero_is_not_strict_but_neg_inf_is` for the derivation). Getting
this wrong silently turns a "no config file" fallback into an active
relaxation instead of the intended strict control arm.

## Layout

```
patches/
  HASHES.txt                     single hash manifest (upstream + all 5 patched states)
  apply.sh                       apply/verify one method: bash patches/apply.sh <method>
  vllm-0.26.0-<method>.patch     the diff, one per method
  relaxation_trace.py            shared per-proposal-token tracer, installed by apply.sh
  test_<method>.py               kernel-level correctness test, run by apply.sh
```

## What each patch touches

Two structural shapes, matching whether the method ever *blends* q and p or
only *switches* between them wholesale:

- **`mentored-dec`, `cactus`, `spec-casc-tok`** modify the accept/reject test
  AND recovery/residual sampling. `mentored-dec`'s relaxed target only moves
  the accept threshold (residual stays on stock p — Tran-Thien's own
  π_res(v) = p(v)); `cactus` and `spec-casc-tok` build a full relaxed
  probability tensor and substitute it for `target_probs` wherever
  `sample_recovered_tokens` is called (the same fix CACTUS's own patch
  history required once — an earlier "accept-only" version left recovery on
  raw p, which is *not* what the paper specifies; that version is kept only
  as `vllm-0.26.0-cactus-accept-only.patch` in the sibling repo, not ported
  here).
- **`spec-casc-opt`, `r-fuzzy`** only modify the accept/reject test. Both
  binary-switch the *whole* per-token target between q (unconditional
  accept, since π_rej(x)/q(x) ≡ 1) and p (run the strict test) — never a
  blend — so residual sampling on the rejected branch is always exactly
  vLLM's stock p-based recovery, unmodified.

`mentored-dec` is also the only method that patches
`vllm/v1/worker/gpu/spec_decode/rejection_sampler_utils.py` (the V2 model
runner) in addition to `rejection_sampler.py` (V1) — ported directly from the
sibling repo's `lenience` patch, which discovered the hard way that vLLM
0.26.0's `use_v2_model_runner` is unset by default (selecting V1) in this
config, so a V2-only patch is silently inert. The other four methods were
built after that was known and only needed the V1 file.

## Naming carried over from the sibling repo

This repo starts from `lossy-spec-decode-repetition`'s already-audited
`cactus` and `spec-casc-opt` patches (ported near-verbatim — see the git
history for the two fixes that porting needed: the tracer import name, and
its `lenience_factor` kwarg). `lenience` is renamed to `mentored-dec` here
and reparameterised: that repo exposed the multiplicative factor λ directly
(and, before that, briefly called it "beta" — a real naming collision with
Tran-Thien's own, different, fixed-at-1 β parameter). This repo exposes α
instead, deriving λ = 1-α internally, so the CLI/config surface matches
arXiv:2607.08690 Table 2 directly. The accept-probability equivalence
between the unclamped-ratio implementation and the paper's own
min(p(x)/λ,1)-then-divide formula is exact for any valid probabilities (not
an approximation) — see the module comment in
`vllm-0.26.0-mentored-dec.patch` for the case analysis.

## Cross-repo isolation

Every `/tmp` knob file is prefixed `lossy-token-eff-`, not the sibling repo's
`lossy-spec-decode-`, and is additionally uid-scoped. A server from either
repo cannot pick up the other's stale knob value if both ever run on this box
at once (they're two separate git repos, so this is a real possibility, not
a hypothetical).

## Apply

```bash
bash patches/apply.sh mentored-dec     # or: cactus, spec-casc-opt, r-fuzzy, spec-casc-tok
```

Checks the vLLM version, checks the target file's sha256 against
`HASHES.txt` (pristine, the requested method, or a *different* method — each
gives a different, specific error rather than silently proceeding), applies
if pristine, re-verifies the result, installs `relaxation_trace.py` if
missing, and runs `test_<method>.py`. Re-running with the same method on an
already-patched install verifies and exits 0.

Installs by `cp --remove-destination`, not a plain `cp`: `uv` installs via
hardlink from `~/.cache/uv/archive-v0`, and a bare `cp` onto an installed
file writes *through* that hardlink, silently patching the cached wheel for
every other venv built from it — including the sibling repo's own already-
verified `.venv-vllm`. `relaxation_trace.py` is a genuinely new file, so a
plain `cp` for *that* one file is fine (nothing to write through).

## Selecting alpha

Every method's α is read from a `/tmp/lossy-token-eff-<method>-alpha-$UID`
file, never an environment variable — vLLM spawns `EngineCore` with a
sanitised environment, confirmed via `/proc/<pid>/environ`, so an env var
silently leaves every knob at its default and the "lossy" arm is an
unlabelled copy of strict. `remote/run_server_vllm.sh` writes **all six**
files (the five taxonomy methods plus `r-fuzzy-semantic-guard`, see below)
in every mode (baseline, strict, and lossy for whichever method is active),
each to its own strict-equivalent value, so a value left over from an
earlier run can never leak into a control arm.

## Testing without a model

```bash
.venv-vllm/bin/python patches/test_<method>.py
```

Each test suite checks the config-file plumbing (no GPU needed), the
relaxation formula against hand-computed or closed-form values (no GPU
needed), and — for methods with the highest blast radius if wrong — drives
the actual Triton kernel directly, no model or server involved (needs a
GPU). `spec-casc-tok`'s suite additionally checks the discontinuity above by
construction, and that residual sampling actually consumes the relaxed
distribution rather than silently falling back to raw p (the same class of
bug CACTUS's own patch history had to fix once).

## Version

Version-specific: hunks are line-addressed against 0.26.0. After any vLLM
change, re-derive the diffs by hand rather than forcing them — this is
exactly what porting from the sibling repo's 0.20.1-era `lenience` patch to
this repo's 0.26.0 install required in the first place.

## A sixth, experimental variant: `r-fuzzy-semantic-guard`

Not one of Xia et al.'s five methods — a pilot built on top of plain
`r-fuzzy`, testing a hypothesis from `analysis/semantic_guard/`: that
hesitation/self-correction marker tokens (`wait`, `hmm`, `actually`, `but`,
`let's`) disproportionately seed later trajectory corruption when relaxed
acceptance lets one through that strict verification would have rejected.
`vllm-0.26.0-r-fuzzy-semantic-guard.patch` is r-fuzzy's own patch plus one
addition: an unconditional OR of a hesitation-marker token-id check into
r-fuzzy's `defer_mask`, computed in plain PyTorch before the kernel launch —
the kernel itself is byte-identical to plain r-fuzzy's. See the patch's own
module-level comment for the full token-id derivation and
`analysis/semantic_guard/README.md` for the offline evidence motivating the
experiment and (once run) its results.

Mutually exclusive with plain `r-fuzzy` at the file level, like every other
pair here (`bash patches/apply.sh r-fuzzy-semantic-guard`), with its own
`HASHES.txt` label, its own alpha file
(`/tmp/lossy-token-eff-r-fuzzy-semantic-guard-alpha-$UID` — r-fuzzy's own
alpha; the guard override itself has no separate on/off knob, it's always
active in this patch), and its own registry entry in
`scripts/lossy_methods.py` (`r_fuzzy_semantic_guard`), so it runs through
the exact same experiment/grading pipeline as the other five arms rather
than a bespoke script.

## A seventh, wider variant: `r-fuzzy-semantic-guard-v2`

Same mechanism as v1 above, wider token set: v1's 18 ids (the 5
hesitation/self-correction markers) plus 17 more covering
`Thus`/`We`/`So`/`Now`/`Let`/`Compute`/`Similarly`/`Define`/`From`, added at
the user's request from a frequency count of AIME24 sentence-initial
tokens. **Read `vllm-0.26.0-r-fuzzy-semantic-guard-v2.patch`'s own module
comment before treating this as "v1 but better"**: most of the additions
are generic reasoning-transition words, not hesitation markers — they open
correct reasoning as often as corrupted reasoning, so this is a broader,
more aggressive intervention, not a refinement, and the two should be read
as separate experiments (see `analysis/semantic_guard/README.md` for how
they compare once both have data). Same wiring pattern as v1: own
`HASHES.txt` label (`r-fuzzy-semantic-guard-v2`), own alpha file
(`/tmp/lossy-token-eff-r-fuzzy-semantic-guard-v2-alpha-$UID`), own registry
entry (`r_fuzzy_semantic_guard_v2`).

## An eighth variant, a different axis: `r-fuzzy-window-entropy-guard`

Not a wider token list — a genuinely different signal. The two guards above
gate on token *identity* (is the drafted token literally "wait"/"but"/...);
this one gates on the *shape* of the distribution the token was drawn from
over time: whether mean entropy over the trailing 64/32/16/8 committed
tokens is STRICTLY INCREASING as the window narrows toward the current
position (mean_w64 < mean_w32 < mean_w16 < mean_w8) — the exact staircase
onset analysis shows preceding a labeled repetition (e.g. target_entropy
1.056→1.064→1.086→1.137→1.662), checked directly for both target and draft
entropy jointly rather than fit to a threshold. Deliberately unquantified:
no calibrated cutoff, no percentile — a structural check on the *shape*
across four nested scales, not a magnitude check against a population
distribution, precisely because a level threshold can't distinguish "high
and flat" from "climbing into now" and would guard both alike.
`analysis/semantic_guard/calibrate_window_entropy_guard.py` reports the
condition's baseline rate on strict decoding for context (8.065% of windows
trigger the joint condition by chance — not a threshold, just what "normal"
looks like), not to derive anything used in the trigger itself. Falls back
to strict verification only while the staircase holds, and returns to
relaxed verification the moment it breaks — a temporary local fallback, not
a permanent per-request budget — see
`vllm-0.26.0-r-fuzzy-window-entropy-guard.patch`'s own module comment for
the full derivation (including why joint target-AND-draft rather than
target alone: KL(draft‖target) does *not* rise before a repetition onset in
the motivating analysis, so it isn't drafter/target disagreement
sharpening, it's the two distributions independently flattening together).

Mechanically distinct from the two token guards in one respect worth
knowing before reading the patch: it's *stateful* across rounds (a
module-level rolling-entropy history, correct without per-request keying
only because this repo's protocol serves exactly one request per fresh
server — see the patch's own comment), and it updates that history from
`output_token_ids` *after* the kernel runs, not before — the gate mask
itself is still computed pre-kernel like every other patch here, from
history plus an optimistic in-block extrapolation of this round's own
already-available target/draft probabilities.

Also extends the shared `relaxation_trace.py` (one new optional field,
`window_guard_active`, null for every other method) so the guard's own
activity is directly visible in the trace rather than only inferable.
Same wiring pattern as the other two: own `HASHES.txt` label
(`r-fuzzy-window-entropy-guard`), own alpha file
(`/tmp/lossy-token-eff-r-fuzzy-window-entropy-guard-alpha-$UID`), own
registry entry (`r_fuzzy_window_entropy_guard`).
