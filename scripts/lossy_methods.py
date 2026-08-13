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
        if self.name in (
            "spec_casc_tok", "spec_casc_tok_antiloop", "spec_casc_tok_force_commit",
            "spec_casc_tok_self_check", "spec_casc_tok_free_judgment",
            "spec_casc_tok_semantic_guard", "spec_casc_tok_semantic_guard_v2",
            "spec_casc_tok_semantic_guard_and",
            "spec_casc_tok_semantic_guard_future_guard", "spec_casc_tok_semantic_guard_future_guard_and",
        ) and alpha == 0.0:
            raise ValueError(
                f"{self.name} alpha=0.0 is NOT the strict point for this method (alpha=-inf is) -- "
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
        if self.name == "r_fuzzy_semantic_guard":
            return (
                f"accept iff JSD(p,q) < {alpha:g} AND draft token is not a hesitation marker "
                "(else strict p/q test) -- r_fuzzy plus an always-on token-id override, "
                "see analysis/semantic_guard/README.md"
            )
        if self.name == "r_fuzzy_semantic_guard_v2":
            return (
                f"accept iff JSD(p,q) < {alpha:g} AND draft token is not in the wider v2 "
                "marker/connective set (else strict p/q test) -- see the patch's own module "
                "comment for the v1-vs-v2 scope difference and analysis/semantic_guard/README.md"
            )
        if self.name == "r_fuzzy_window_entropy_guard":
            return (
                f"accept iff JSD(p,q) < {alpha:g} AND rolling-32 mean target+draft entropy over "
                "committed tokens is below its strict-calibrated Q90 (else strict p/q test) -- "
                "distributional sibling of the token-marker guards, see analysis/semantic_guard/README.md"
            )
        if self.name == "spec_casc_tok":
            return (
                f"pi_rej(v) = q(v)+eta*p(v) for v with p(v) >= (1-{alpha:g})*max(p), else eta*p(v); "
                f"eta = 1 - sum_{{v in that set}} q(v)"
            )
        if self.name == "spec_casc_tok_antiloop":
            return (
                f"pi_rej(v) = q(v)+eta*p(v) for v with p(v) >= (1-{alpha:g})*max(p), else eta*p(v) -- "
                "UNLESS the drafted token would complete a 3rd consecutive periodic repeat "
                "(period<=12, persistent cross-round history), in which case that token's p(v) is "
                "forced to 0 (renormalized) before eta/pi_rej are computed, so it is unconditionally "
                "rejected and gets zero recovery mass too -- see analysis/semantic_guard/README.md"
            )
        if self.name == "spec_casc_tok_force_commit":
            return (
                f"pi_rej(v) = q(v)+eta*p(v) for v with p(v) >= (1-{alpha:g})*max(p), else eta*p(v) -- "
                "UNLESS this sequence has crossed its token-count budget without a natural "
                "final-channel-open, in which case target_probs is one-hot forced onto the next "
                "token of the final-channel-open boundary at the first drafted position each round "
                "(read back from the sequence's own emitted history, not assumed) until that "
                "6-token boundary completes, then permanently a no-op -- see analysis/semantic_guard/README.md"
            )
        if self.name == "spec_casc_tok_self_check":
            return (
                f"pi_rej(v) = q(v)+eta*p(v) for v with p(v) >= (1-{alpha:g})*max(p), else eta*p(v) -- "
                "UNLESS a periodic self-check is active, in which case target_probs is one-hot forced "
                "onto a fixed question/pivot/final-open phrase; the question's ANSWER position is left "
                "fully unconstrained and read back to decide whether to force the pivot -- "
                "see analysis/semantic_guard/README.md"
            )
        if self.name == "spec_casc_tok_free_judgment":
            return (
                f"pi_rej(v) = q(v)+eta*p(v) for v with p(v) >= (1-{alpha:g})*max(p), else eta*p(v) -- "
                "PLUS a fixed criterion-question sequence appended after the real drafted tokens each "
                "round (num_speculative_tokens configured wider to fit it), read as a free judgment from "
                "the target's own already-parallel verification pass, always force-rejected so it never "
                "costs real budget -- v1 is observation-only (traced, not acted on) -- "
                "see analysis/semantic_guard/README.md"
            )
        if self.name == "spec_casc_tok_semantic_guard":
            return (
                f"pi_rej(v) = q(v)+eta*p(v) for v with p(v) >= (1-{alpha:g})*max(p), else eta*p(v) -- "
                "UNLESS the draft token is a hesitation marker, in which case the trusted top set is "
                "forced empty (pi_rej=p exactly, this method's own strict limit) regardless of alpha -- "
                "see analysis/semantic_guard/README.md"
            )
        if self.name == "spec_casc_tok_semantic_guard_v2":
            return (
                f"pi_rej(v) = q(v)+eta*p(v) for v with p(v) >= (1-{alpha:g})*max(p), else eta*p(v) -- "
                "UNLESS the draft token is in the WIDER 35-id/14-word marker set, in which case the "
                "trusted top set is forced empty (pi_rej=p exactly) regardless of alpha -- same "
                "mechanism as spec_casc_tok_semantic_guard, wider set only -- see analysis/semantic_guard/README.md"
            )
        if self.name == "spec_casc_tok_semantic_guard_and":
            return (
                f"pi_rej(v) = q(v)+eta*p(v) for v with p(v) >= (1-{alpha:g})*max(p), else eta*p(v) -- "
                "UNLESS the draft token is a hesitation marker, in which case accept iff BOTH the "
                "lossless test AND this rule would accept (min(p,pi_rej) as the effective target) -- "
                "see analysis/semantic_guard/README.md"
            )
        if self.name == "spec_casc_tok_semantic_guard_future_guard":
            return (
                f"pi_rej(v) = q(v)+eta*p(v) for v with p(v) >= (1-{alpha:g})*max(p), else eta*p(v) -- "
                "UNLESS a hesitation/discourse marker (wider set) was accepted within the last K "
                "verified positions, in which case use the raw lossless test instead -- "
                "see analysis/semantic_guard/README.md"
            )
        if self.name == "spec_casc_tok_semantic_guard_future_guard_and":
            return (
                f"pi_rej(v) = q(v)+eta*p(v) for v with p(v) >= (1-{alpha:g})*max(p), else eta*p(v) -- "
                "UNLESS a hesitation/discourse marker (wider set) was accepted within the last K "
                "verified positions, in which case accept iff BOTH the lossless test AND this rule "
                "would accept (min(p,pi_rej) as the effective target, same AND-combination as "
                "spec_casc_tok_semantic_guard_and but applied to the K-window instead of the marker "
                "itself) -- see analysis/semantic_guard/README.md"
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
            name="r_fuzzy_semantic_guard",
            hashes_label="r-fuzzy-semantic-guard",
            env_var="R_FUZZY_GUARD_ALPHA",
            alpha_file=pathlib.Path(f"/tmp/lossy-token-eff-r-fuzzy-semantic-guard-alpha-{_uid()}"),
            log_prefix="[R-FUZZY-SEMANTIC-GUARD PATCH]",
            strict_alpha=float("-inf"),
            alpha_domain="(-inf, inf)",
            default_alpha=0.3,
            taxonomy={
                "family": "r-fuzzy + semantic guard (this repo's own pilot experiment, not in Xia et al.)",
                "paper_name": "r-fuzzy-semantic-guard",
                "reference": "analysis/semantic_guard/README.md",
            },
        ),
        MethodSpec(
            name="r_fuzzy_semantic_guard_v2",
            hashes_label="r-fuzzy-semantic-guard-v2",
            env_var="R_FUZZY_GUARD_V2_ALPHA",
            alpha_file=pathlib.Path(f"/tmp/lossy-token-eff-r-fuzzy-semantic-guard-v2-alpha-{_uid()}"),
            log_prefix="[R-FUZZY-SEMANTIC-GUARD-V2 PATCH]",
            strict_alpha=float("-inf"),
            alpha_domain="(-inf, inf)",
            default_alpha=0.3,
            taxonomy={
                "family": "r-fuzzy + wider semantic guard (this repo's own pilot experiment, not in Xia et al.)",
                "paper_name": "r-fuzzy-semantic-guard-v2",
                "reference": "analysis/semantic_guard/README.md",
            },
        ),
        MethodSpec(
            name="r_fuzzy_window_entropy_guard",
            hashes_label="r-fuzzy-window-entropy-guard",
            env_var="R_FUZZY_WENTROPY_GUARD_ALPHA",
            alpha_file=pathlib.Path(f"/tmp/lossy-token-eff-r-fuzzy-window-entropy-guard-alpha-{_uid()}"),
            log_prefix="[R-FUZZY-WINDOW-ENTROPY-GUARD PATCH]",
            strict_alpha=float("-inf"),
            alpha_domain="(-inf, inf)",
            default_alpha=0.3,
            taxonomy={
                "family": "r-fuzzy + window-entropy guard (this repo's own pilot experiment, not in Xia et al.)",
                "paper_name": "r-fuzzy-window-entropy-guard",
                "reference": "analysis/semantic_guard/README.md",
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
        MethodSpec(
            name="spec_casc_tok_antiloop",
            hashes_label="spec-casc-tok-antiloop",
            env_var="SPEC_CASC_TOK_ANTILOOP_ALPHA",
            alpha_file=pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-antiloop-alpha-{_uid()}"),
            log_prefix="[SPEC-CASC-TOK-ANTILOOP PATCH]",
            strict_alpha=float("-inf"),
            alpha_domain="(-inf, inf), NOT 0.0 for strict",
            default_alpha=0.3,
            taxonomy={
                "family": "spec-casc-tok + reactive repetition breaker (this repo's own pilot experiment, not in Xia et al.)",
                "paper_name": "spec-casc-tok-antiloop",
                "reference": "analysis/semantic_guard/README.md",
            },
        ),
        MethodSpec(
            name="spec_casc_tok_force_commit",
            hashes_label="spec-casc-tok-force-commit",
            env_var="SPEC_CASC_TOK_FORCE_COMMIT_ALPHA",
            alpha_file=pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-force-commit-alpha-{_uid()}"),
            log_prefix="[SPEC-CASC-TOK-FORCE-COMMIT PATCH]",
            strict_alpha=float("-inf"),
            alpha_domain="(-inf, inf), NOT 0.0 for strict",
            default_alpha=0.3,
            taxonomy={
                "family": "spec-casc-tok + reactive budget-exhaustion breaker (this repo's own pilot "
                "experiment, not in Xia et al.) -- targets the \"never commits to final channel\" "
                "rambling failure, distinct from spec-casc-tok-antiloop's literal-repetition target",
                "paper_name": "spec-casc-tok-force-commit",
                "reference": "analysis/semantic_guard/README.md",
            },
        ),
        MethodSpec(
            name="spec_casc_tok_self_check",
            hashes_label="spec-casc-tok-self-check",
            env_var="SPEC_CASC_TOK_SELF_CHECK_ALPHA",
            alpha_file=pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-self-check-alpha-{_uid()}"),
            log_prefix="[SPEC-CASC-TOK-SELF-CHECK PATCH]",
            strict_alpha=float("-inf"),
            alpha_domain="(-inf, inf), NOT 0.0 for strict",
            default_alpha=0.3,
            taxonomy={
                "family": "spec-casc-tok + periodic self-assessment and reactive pivot (this repo's own "
                "pilot experiment, not in Xia et al.) -- outsources the \"is this unproductive?\" judgment "
                "to the model's own self-report instead of a structural/statistical proxy",
                "paper_name": "spec-casc-tok-self-check",
                "reference": "analysis/semantic_guard/README.md",
            },
        ),
        MethodSpec(
            name="spec_casc_tok_free_judgment",
            hashes_label="spec-casc-tok-free-judgment",
            env_var="SPEC_CASC_TOK_FREE_JUDGMENT_ALPHA",
            alpha_file=pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-free-judgment-alpha-{_uid()}"),
            log_prefix="[SPEC-CASC-TOK-FREE-JUDGMENT PATCH]",
            strict_alpha=float("-inf"),
            alpha_domain="(-inf, inf), NOT 0.0 for strict",
            default_alpha=0.3,
            taxonomy={
                "family": "spec-casc-tok + free judgment via extended verification span (this repo's own "
                "pilot experiment, not in Xia et al.) -- exploits EAGLE's already-parallel verification "
                "pass to get a judgment signal at marginal FLOPs cost and zero real generation-budget "
                "cost; v1 is observation-only",
                "paper_name": "spec-casc-tok-free-judgment",
                "reference": "analysis/semantic_guard/README.md",
            },
        ),
        MethodSpec(
            name="spec_casc_tok_semantic_guard",
            hashes_label="spec-casc-tok-semantic-guard",
            env_var="SPEC_CASC_TOK_GUARD_ALPHA",
            alpha_file=pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-semantic-guard-alpha-{_uid()}"),
            log_prefix="[SPEC-CASC-TOK-SEMANTIC-GUARD PATCH]",
            strict_alpha=float("-inf"),
            alpha_domain="(-inf, inf), NOT 0.0 for strict",
            default_alpha=0.3,
            taxonomy={
                "family": "spec-casc-tok + semantic guard (this repo's own pilot experiment, not in Xia et al.)",
                "paper_name": "spec-casc-tok-semantic-guard",
                "reference": "analysis/semantic_guard/README.md",
            },
        ),
        MethodSpec(
            name="spec_casc_tok_semantic_guard_v2",
            hashes_label="spec-casc-tok-semantic-guard-v2",
            env_var="SPEC_CASC_TOK_GUARD_V2_ALPHA",
            alpha_file=pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-semantic-guard-v2-alpha-{_uid()}"),
            log_prefix="[SPEC-CASC-TOK-SEMANTIC-GUARD-V2 PATCH]",
            strict_alpha=float("-inf"),
            alpha_domain="(-inf, inf), NOT 0.0 for strict",
            default_alpha=0.3,
            taxonomy={
                "family": "spec-casc-tok + semantic guard, wider marker set (this repo's own pilot experiment, not in Xia et al.)",
                "paper_name": "spec-casc-tok-semantic-guard-v2",
                "reference": "analysis/semantic_guard/README.md",
            },
        ),
        MethodSpec(
            name="spec_casc_tok_semantic_guard_and",
            hashes_label="spec-casc-tok-semantic-guard-and",
            env_var="SPEC_CASC_TOK_GUARD_AND_ALPHA",
            alpha_file=pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-semantic-guard-and-alpha-{_uid()}"),
            log_prefix="[SPEC-CASC-TOK-SEMANTIC-GUARD-AND PATCH]",
            strict_alpha=float("-inf"),
            alpha_domain="(-inf, inf), NOT 0.0 for strict",
            default_alpha=0.3,
            taxonomy={
                "family": "spec-casc-tok + AND-combined semantic guard (this repo's own pilot experiment, not in Xia et al.)",
                "paper_name": "spec-casc-tok-semantic-guard-and",
                "reference": "analysis/semantic_guard/README.md",
            },
        ),
        MethodSpec(
            name="spec_casc_tok_semantic_guard_future_guard",
            hashes_label="spec-casc-tok-semantic-guard-future-guard",
            env_var="SPEC_CASC_TOK_FUTURE_GUARD_ALPHA",
            alpha_file=pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-semantic-guard-future-guard-alpha-{_uid()}"),
            log_prefix="[SPEC-CASC-TOK-SEMANTIC-GUARD-FUTURE-GUARD PATCH]",
            strict_alpha=float("-inf"),
            alpha_domain="(-inf, inf), NOT 0.0 for strict",
            default_alpha=0.3,
            taxonomy={
                "family": "spec-casc-tok + K-token future-guard semantic guard (this repo's own pilot experiment, not in Xia et al.)",
                "paper_name": "spec-casc-tok-semantic-guard-future-guard",
                "reference": "analysis/semantic_guard/README.md",
            },
        ),
        MethodSpec(
            name="spec_casc_tok_semantic_guard_future_guard_and",
            hashes_label="spec-casc-tok-semantic-guard-future-guard-and",
            env_var="SPEC_CASC_TOK_FUTURE_GUARD_AND_ALPHA",
            alpha_file=pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-semantic-guard-future-guard-and-alpha-{_uid()}"),
            log_prefix="[SPEC-CASC-TOK-SEMANTIC-GUARD-FUTURE-GUARD-AND PATCH]",
            strict_alpha=float("-inf"),
            alpha_domain="(-inf, inf), NOT 0.0 for strict",
            default_alpha=0.3,
            taxonomy={
                "family": "spec-casc-tok + K-token future-guard semantic guard, AND-combined inside the window (this repo's own pilot experiment, not in Xia et al.)",
                "paper_name": "spec-casc-tok-semantic-guard-future-guard-and",
                "reference": "analysis/semantic_guard/README.md",
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
