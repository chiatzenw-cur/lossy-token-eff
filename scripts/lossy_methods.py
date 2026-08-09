"""Registry of relaxed spec-dec methods, shared by run_experiment_vllm.py and
fresh_server_replay.py.

The sibling repo's run_experiment_vllm.py hardcoded three near-identical
blocks (one per method: lenience/spec_casc_opt/cactus) for the in-force
check, the server-log scrape, and the acceptance-rule description. That was
already visible strain at 3 methods; this repo has 5, so it's a table here
instead -- one source of truth per method, not one function definition
repeated per method.

Every method in this repo (unlike the sibling repo's heterogeneous
lenience_factor/spec_casc_alpha/cactus_alpha) exposes a single knob named
alpha, matching Xia et al. Table 2 -- a direct consequence of the mentored-dec
rename (see patches/README.md), which is what makes one generic registry
entry per method possible instead of one bespoke CLI flag per method.
"""

from __future__ import annotations

import dataclasses
import os
import pathlib
import re


@dataclasses.dataclass(frozen=True)
class MethodSpec:
    name: str  # CLI value, e.g. "mentored_dec"
    hashes_label: str  # label in patches/HASHES.txt, e.g. "mentored-dec"
    alpha_file: pathlib.Path  # /tmp knob file the patched sampler reads
    env_var: str  # remote/run_server_vllm.sh's env var name for this alpha --
    # NOT always f"{name.upper()}_ALPHA": spec_casc_opt's is SPEC_CASC_ALPHA
    # (shortened, baked into the already-verified patch's /tmp file name and
    # into run_server_vllm.sh), not the derivable SPEC_CASC_OPT_ALPHA. Stated
    # explicitly per-method so this can never silently drift out of sync with
    # the shell script again the way a f-string derivation just did once.
    log_prefix: str  # what the patch prints to stderr at import
    strict_alpha: float  # the value that recovers strict spec-dec exactly
    alpha_domain: str  # human-readable, for error messages
    default_alpha: float  # matches remote/run_server_vllm.sh's own default
    taxonomy: dict[str, str]
    touches_v2: bool = False  # only mentored-dec patches the V2 runner too

    def validate_alpha(self, alpha: float) -> None:
        if self.name == "mentored_dec" and not (0.0 <= alpha < 1.0):
            raise ValueError(f"mentored_dec alpha must be in [0, 1); got {alpha}")
        if self.name == "cactus" and alpha < 0.0:
            raise ValueError(f"cactus alpha must be >= 0 (it bounds a KL divergence); got {alpha}")
        if self.name == "spec_casc_tok" and alpha == 0.0:
            raise ValueError(
                "spec_casc_tok alpha=0.0 is NOT the strict point for this method (alpha=-inf is) -- "
                "see patches/README.md. Passing 0.0 here is almost certainly a copy-paste from a "
                "different method's convention, not an intentional relaxation value."
            )

    def acceptance_rule(self, alpha: float) -> str:
        if self.name == "mentored_dec":
            return f"accept iff p(x) / ({1.0 - alpha:g} * q(x)) >= u  (lam = 1-alpha = {1.0 - alpha:g})"
        if self.name == "cactus":
            return f"accept iff gamma_x / q(x) >= u, gamma_x = min(p(x) + sqrt(2*{alpha:g}*p(x)*(1-p(x))), 1)"
        if self.name == "spec_casc_opt":
            return f"defer to strict p/q test iff max_u q(u) < max_u p(u) - {alpha:g}*TV(p,q), else accept unconditionally"
        if self.name == "r_fuzzy":
            return f"accept iff JSD(p,q) < {alpha:g} (then pi_rej=q, unconditional accept), else strict p/q test"
        if self.name == "spec_casc_tok":
            return (
                f"pi_rej(v) = q(v)+eta*p(v) for v with p(v) >= (1-{alpha:g})*max(p), else eta*p(v); "
                f"eta = 1 - sum_{{v in that set}} q(v)"
            )
        raise ValueError(self.name)


def _uid() -> int:
    return os.getuid()


METHODS: dict[str, MethodSpec] = {
    spec.name: spec
    for spec in (
        MethodSpec(
            name="mentored_dec",
            hashes_label="mentored-dec",
            env_var="MENTORED_DEC_ALPHA",
            alpha_file=pathlib.Path(f"/tmp/lossy-token-eff-mentored-dec-alpha-{_uid()}"),
            log_prefix="[MENTORED-DEC PATCH]",
            strict_alpha=0.0,
            alpha_domain="[0, 1)",
            default_alpha=0.37,
            touches_v2=True,
            taxonomy={
                "family": "mentored decoding (Tran-Thien 2023, beta=1)",
                "paper_name": "mentored-dec",
                "reference": "Xia et al. 2026 (arXiv:2607.08690) Table 2 / Eq. 9",
            },
        ),
        MethodSpec(
            name="cactus",
            hashes_label="cactus",
            env_var="CACTUS_ALPHA",
            alpha_file=pathlib.Path(f"/tmp/lossy-token-eff-cactus-alpha-{_uid()}"),
            log_prefix="[CACTUS PATCH",  # v2, full-residual" follows; prefix match only
            strict_alpha=0.0,
            alpha_domain="[0, inf)",
            default_alpha=0.25,
            taxonomy={
                "family": "CACTUS (Hao & Mou 2026)",
                "paper_name": "cactus",
                "reference": "Xia et al. 2026 (arXiv:2607.08690) Table 2 / Eq. 6-7",
            },
        ),
        MethodSpec(
            name="spec_casc_opt",
            hashes_label="spec-casc-opt",
            env_var="SPEC_CASC_ALPHA",  # shortened, NOT SPEC_CASC_OPT_ALPHA -- see the field comment above
            alpha_file=pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-alpha-{_uid()}"),
            log_prefix="[SPEC-CASC-OPT PATCH]",
            strict_alpha=float("-inf"),
            alpha_domain="(-inf, inf)",
            default_alpha=0.05,
            taxonomy={
                "family": "speculative cascades [OPT] (Narasimhan et al. 2025)",
                "paper_name": "spec-casc-opt",
                "reference": "Xia et al. 2026 (arXiv:2607.08690) Table 2 / Eq. 12",
            },
        ),
        MethodSpec(
            name="r_fuzzy",
            hashes_label="r-fuzzy",
            env_var="R_FUZZY_ALPHA",
            alpha_file=pathlib.Path(f"/tmp/lossy-token-eff-r-fuzzy-alpha-{_uid()}"),
            log_prefix="[R-FUZZY PATCH]",
            strict_alpha=float("-inf"),
            alpha_domain="(-inf, inf)",
            default_alpha=0.3,
            taxonomy={
                "family": "(reducible) fuzzy speculative decoding (Holsman et al. 2025)",
                "paper_name": "r-fuzzy",
                "reference": "Xia et al. 2026 (arXiv:2607.08690) Table 2 / Eq. 10",
            },
        ),
        MethodSpec(
            name="spec_casc_tok",
            hashes_label="spec-casc-tok",
            env_var="SPEC_CASC_TOK_ALPHA",
            alpha_file=pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-alpha-{_uid()}"),
            log_prefix="[SPEC-CASC-TOK PATCH]",
            strict_alpha=float("-inf"),
            alpha_domain="(-inf, inf), NOT 0.0 for strict",
            default_alpha=0.3,
            taxonomy={
                "family": "speculative cascades [Tok] (Narasimhan et al. 2025 appendix)",
                "paper_name": "spec-casc-tok",
                "reference": "Xia et al. 2026 (arXiv:2607.08690) Appendix B, Eq. 15",
            },
        ),
    )
}

TRACE_PATH_FILE = pathlib.Path(f"/tmp/lossy-token-eff-trace-{_uid()}")

# The tracer hook only exists inside a PATCHED rejection_sampler.py -- pristine
# vLLM has no instrumentation at all, so a "strict" run on pristine vLLM
# cannot produce a trace. Every patch's kernel is bit-identical to pristine's
# at its own strict alpha (that's the whole point of the strict-recovery
# property each patch's test suite checks), so running "strict" through any
# one patch, alpha pinned to that patch's strict value, gets the same output
# distribution AND a trace. mentored_dec is the designated carrier: its
# accept-kernel change is the smallest (one multiply, no full-vocab
# reduction), so it's the least likely of the five to be the source of any
# measurement artifact if one ever turns up.
STRICT_TRACE_CARRIER = "mentored_dec"

_ALPHA_RE = re.compile(r"alpha=(-?inf|nan|[0-9.eE+-]+)")


def parse_alpha_from_log_line(line: str) -> float | None:
    match = _ALPHA_RE.search(line)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None
