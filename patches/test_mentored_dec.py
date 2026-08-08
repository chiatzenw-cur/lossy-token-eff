#!/usr/bin/env python3
"""Acceptance test for the mentored-dec patch. Run by patches/apply_mentored_dec.sh.

Ported from the sibling lossy-spec-decode-repetition repo's test_lenience.py,
adjusted for the alpha-primary knob (that repo exposed lam directly; this one
derives lam = 1-alpha internally and exposes alpha, matching Xia et al. Table 2).

Checks the two things that have actually gone wrong here before (in the
sibling repo, under the lam-named predecessor of this patch):

1. alpha reaches the module (it was silently a no-op when passed via the
   environment, because vLLM sanitises EngineCore's env), and
2. alpha reaches the *kernel* (the V2 file was patched while the V1 runner
   was live, so the lossy arm was bit-identical to strict).

(2) needs a GPU and is skipped without one; (1) is not.
"""

from __future__ import annotations

import math
import os
import pathlib
import subprocess
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-mentored-dec-alpha-{os.getuid()}")
MODULES = (
    "vllm.v1.sample.rejection_sampler",
    "vllm.v1.worker.gpu.spec_decode.rejection_sampler_utils",
)

READ_BACK = """
import importlib, json, sys
out = {}
for name in sys.argv[1:]:
    m = importlib.import_module(name)
    out[name] = {
        "alpha": getattr(m, "_MENTORED_DEC_ALPHA", None),
        "lam": getattr(m, "_MENTORED_DEC_LAM", None),
        "log_lam": getattr(m, "_MENTORED_DEC_LOG_LAM", None),
        "path": getattr(m, "_MENTORED_DEC_ALPHA_FILE", None),
    }
print("JSON:" + json.dumps(out))
"""


def read_back_in_subprocess() -> dict[str, dict[str, object]]:
    """Import both modules fresh; alpha is read once, at import."""
    import json

    proc = subprocess.run(
        [sys.executable, "-c", READ_BACK, *MODULES],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise AssertionError(f"import failed:\n{proc.stderr[-3000:]}")
    for line in proc.stdout.splitlines():
        if line.startswith("JSON:"):
            return json.loads(line[5:])
    raise AssertionError(f"no result from subprocess:\n{proc.stdout[-2000:]}")


def test_alpha_plumbing() -> None:
    saved = ALPHA_FILE.read_text() if ALPHA_FILE.is_file() else None
    try:
        ALPHA_FILE.write_text("0.63\n")  # lam = 0.37, matches sibling repo's test value
        got = read_back_in_subprocess()
        for name in MODULES:
            assert got[name]["alpha"] == 0.63, f"{name}: {got[name]}"
            assert abs(got[name]["lam"] - 0.37) < 1e-12, f"{name}: {got[name]}"
            assert got[name]["path"] == str(ALPHA_FILE), f"{name}: {got[name]}"
        log_lam = got["vllm.v1.worker.gpu.spec_decode.rejection_sampler_utils"]["log_lam"]
        assert log_lam is not None and abs(log_lam - math.log(0.37)) < 1e-12, log_lam
        print(f"  ok  both modules read {ALPHA_FILE} -> alpha=0.63 (lam=0.37)")

        ALPHA_FILE.unlink()
        got = read_back_in_subprocess()
        for name in MODULES:
            assert got[name]["alpha"] == 0.0, f"{name}: {got[name]}"
            assert got[name]["lam"] == 1.0, f"{name}: {got[name]}"
        print("  ok  missing file falls back to alpha=0.0 (stock rule)")

        ALPHA_FILE.write_text("1.0\n")
        try:
            read_back_in_subprocess()
            raise AssertionError("import should fail for alpha=1.0 (lam would be 0)")
        except AssertionError as exc:
            if "should fail" in str(exc):
                raise
            print("  ok  alpha=1.0 (lam=0, division by zero) is rejected at import")

        ALPHA_FILE.write_text("-0.1\n")
        try:
            read_back_in_subprocess()
            raise AssertionError("import should fail for a negative alpha")
        except AssertionError as exc:
            if "should fail" in str(exc):
                raise
            print("  ok  negative alpha is rejected at import")
    finally:
        if saved is None:
            ALPHA_FILE.unlink(missing_ok=True)
        else:
            ALPHA_FILE.write_text(saved)


def test_kernel_uses_alpha() -> None:
    """Drive the V1 verify kernel directly: no model, no server, no sampler.

    One request per uniform draw, each with a single draft token whose
    target/draft ratio is fixed, so the accept/reject boundary is exactly
    u <= ratio / lam, lam = 1-alpha, and can be predicted in closed form.
    """
    import torch

    if not torch.cuda.is_available():
        print("  skip  no CUDA device; kernel test not run")
        return
    from vllm.v1.sample.rejection_sampler import rejection_random_sample_kernel

    device = "cuda"
    vocab, draft_tok, recovered_tok, bonus_tok = 8, 3, 5, 7
    uniform = torch.linspace(0.05, 0.95, 19, device=device, dtype=torch.float32)
    n = uniform.numel()

    def run(ratio: float, alpha: float) -> torch.Tensor:
        lam = 1.0 - alpha
        draft_probs = torch.full((n, vocab), 0.5 / (vocab - 1), device=device)
        draft_probs[:, draft_tok] = 0.5
        target_probs = torch.full((n, vocab), (1.0 - 0.5 * ratio) / (vocab - 1), device=device)
        target_probs[:, draft_tok] = 0.5 * ratio
        out = torch.full((n, 2), -1, dtype=torch.int32, device=device)
        rejection_random_sample_kernel[(n,)](
            out,
            torch.arange(1, n + 1, dtype=torch.int32, device=device),
            torch.full((n,), draft_tok, dtype=torch.int32, device=device),
            draft_probs.contiguous(),
            target_probs.contiguous(),
            torch.full((n,), bonus_tok, dtype=torch.int32, device=device),
            torch.full((n,), recovered_tok, dtype=torch.int32, device=device),
            uniform,
            torch.zeros(n, dtype=torch.bool, device=device),
            1,  # max_spec_len
            vocab,
            None,  # synthetic_conditional_rates
            lam,
            NO_DRAFT_PROBS=False,
            SYNTHETIC_MODE=False,
        )
        return out.cpu()

    for ratio, alpha in ((0.5, 0.0), (0.5, 0.8), (0.1, 0.8), (0.1, 0.0)):
        lam = 1.0 - alpha
        out = run(ratio, alpha)
        accepted = out[:, 0] == draft_tok
        expected = uniform.cpu() <= ratio / lam
        assert torch.equal(accepted, expected), (
            f"ratio={ratio} alpha={alpha} (lam={lam})\n"
            f" got      {accepted.tolist()}\n expected {expected.tolist()}"
        )
        # An accepted draft is followed by the bonus token; a rejected one is
        # replaced by the recovered token and stops the request.
        assert torch.equal(out[accepted][:, 1], torch.full((int(accepted.sum()),), bonus_tok, dtype=torch.int32))
        assert torch.equal(out[~accepted][:, 0], torch.full((int((~accepted).sum()),), recovered_tok, dtype=torch.int32))
        print(f"  ok  kernel accepts iff u <= p/(q*lam)   p/q={ratio} alpha={alpha} (lam={lam:.2f})")

    strict = run(0.5, 0.0)
    relaxed = run(0.5, 0.8)
    assert (relaxed[:, 0] == draft_tok).sum() > (strict[:, 0] == draft_tok).sum(), (
        "alpha=0.8 did not accept more than alpha=0.0; alpha is not reaching the kernel"
    )
    print("  ok  alpha=0.8 accepts strictly more draft tokens than alpha=0.0")


def main() -> int:
    failures = 0
    for test in (test_alpha_plumbing, test_kernel_uses_alpha):
        print(f"{test.__name__}:")
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all mentored-dec patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
