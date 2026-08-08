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
unlabelled copy of strict. `remote/run_server_vllm.sh` writes **all five**
files in every mode (baseline, strict, and lossy for whichever method is
active), each to its own strict-equivalent value, so a value left over from
an earlier run can never leak into a control arm.

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
