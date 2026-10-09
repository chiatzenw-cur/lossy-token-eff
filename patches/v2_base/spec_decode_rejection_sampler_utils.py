# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
import math
import os
import sys

import torch

from vllm.triton_utils import tl, tldevice, triton
from vllm.v1.worker.gpu.sample.gumbel import gumbel_block_argmax, tl_rand32

# mentored-dec (V2): re-added 2026-08-20 after discovering the proof-of-
# concept edits below were built starting from a PRISTINE copy of this
# file, not from mentored-dec's own already-patched V2 state -- meaning
# this method's real V2 contribution was accidentally dropped (the exact
# same "silently inert" failure mode this whole investigation started from,
# now self-inflicted). Ported from vllm-0.26.0-mentored-dec.patch's own V2
# hunk verbatim (same alpha-file convention, same math): accept iff
# p(x)/(lam*q(x)) >= u, i.e. log p(x) > log(u) + log(lam) + log(q(x)).
# alpha=0 gives lam=1.0 and log(lam)=0.0 exactly, a true additive no-op.
_MENTORED_DEC_ALPHA_FILE = f"/tmp/lossy-token-eff-mentored-dec-alpha-{os.getuid()}"
try:
    with open(_MENTORED_DEC_ALPHA_FILE) as _f:
        _MENTORED_DEC_ALPHA = float(_f.read().strip())
    _MENTORED_DEC_ALPHA_SOURCE = _MENTORED_DEC_ALPHA_FILE
except (OSError, ValueError):
    _MENTORED_DEC_ALPHA = 0.0
    _MENTORED_DEC_ALPHA_SOURCE = f"default, no readable {_MENTORED_DEC_ALPHA_FILE}"
if not 0.0 <= _MENTORED_DEC_ALPHA < 1.0:
    raise ValueError(f"mentored-dec alpha must be in [0, 1); got {_MENTORED_DEC_ALPHA}")
_MENTORED_DEC_LAM = 1.0 - _MENTORED_DEC_ALPHA
_MENTORED_DEC_LOG_LAM = math.log(_MENTORED_DEC_LAM)
print(
    f"[MENTORED-DEC PATCH V2 (re-added)] pid={os.getpid()} alpha={_MENTORED_DEC_ALPHA} "
    f"lam={_MENTORED_DEC_LAM} log_lam={_MENTORED_DEC_LOG_LAM} "
    f"({_MENTORED_DEC_ALPHA_SOURCE})",
    file=sys.stderr,
    flush=True,
)

# LOSSY-VERIFICATION PILOT PATCH (not upstream vLLM), PROOF-OF-CONCEPT
# (2026-08-20).
#
# CACTUS accept-test only -- V2 (GPU model runner) counterpart of the V1
# patch in vllm/v1/sample/rejection_sampler.py, ported the same way
# mentored-dec's own V2 half already is (see that file's own module
# comment). This exists because Qwen3-8B was found to route through THIS
# file's rejection_sample(), never the V1 one -- confirmed by instrumenting
# both RejectionSampler.__init__ methods and observing only this file's
# constructor fire. Every V1-only patch (cactus/spec_casc_opt/r_fuzzy/
# spec_casc_tok) was therefore silently inert for Qwen3-8B; mentored_dec
# was the sole exception because it was the only method already patching
# both files. See campaign/JOURNAL.md's 2026-08-20 entry for the full
# diagnostic trail.
#
# ACCEPT-TEST ONLY, matching this repo's own cactus_accept_only convention
# (see vllm-0.26.0-cactus.patch's own V1 module comment): boosts gamma_x =
# min(p(x) + sqrt(2*alpha*p(x)*(1-p(x))), 1) and tests gamma_x/q(x) >= u,
# but does NOT rebuild the full H_x recovery distribution the real V1
# cactus patch's "v2 correctness fix" requires -- recovery on rejection
# still samples from stock p, not H_x. That is a real, known gap (this
# repo's own history: an earlier "accept-only" cactus was explicitly kept
# separate and NOT called "cactus" for exactly this reason), not an
# oversight; closing it means also porting the resample kernel, out of
# scope for tonight's validation that V2-patching fixes the root cause at
# all.
_CACTUS_ALPHA_FILE = f"/tmp/lossy-token-eff-cactus-alpha-{os.getuid()}"
try:
    with open(_CACTUS_ALPHA_FILE) as _f:
        _CACTUS_ALPHA = float(_f.read().strip())
    _CACTUS_ALPHA_SOURCE = _CACTUS_ALPHA_FILE
except (OSError, ValueError):
    _CACTUS_ALPHA = 0.0  # gamma_x == p(x) exactly -> strict spec-dec
    _CACTUS_ALPHA_SOURCE = f"default, no readable {_CACTUS_ALPHA_FILE}"
if _CACTUS_ALPHA < 0.0:
    raise ValueError(f"CACTUS alpha must be >= 0 (it bounds a KL divergence); got {_CACTUS_ALPHA}")
print(
    f"[CACTUS PATCH V2-ACCEPT-ONLY, PROOF-OF-CONCEPT] pid={os.getpid()} "
    f"alpha={_CACTUS_ALPHA} ({_CACTUS_ALPHA_SOURCE})",
    file=sys.stderr,
    flush=True,
)

# spec-casc-opt and r-fuzzy (V2, PROOF-OF-CONCEPT, 2026-08-20): both defer
# to the ordinary ratio test (cactus's own gamma_x boost above included --
# they compose correctly, see below) OR skip it and accept the draft token
# unconditionally, based on a full-vocabulary comparison of p and q.
# Ported from the V1 patches' own formulas exactly:
#   spec-casc-opt: defer iff max_u q(u) < max_u p(u) - alpha * TV(p, q)
#   r-fuzzy:       defer iff JSD(p, q) >= alpha
# Computed once per call in plain PyTorch in rejection_sample() below (same
# "materialize target_logits/draft_logits as dense tensors, reduce once,
# pass a mask into the kernel" style the V1 patches already use), not as a
# new full-vocab Triton reduction -- draft_logits is already a dense
# [max_num_reqs, num_speculative_steps, V] tensor at that point, gathered
# into [num_logits, V] via expanded_idx_mapping/expanded_local_pos to match
# target_logits's own layout.
#
# Composability with cactus and each other: each method's own alpha
# defaults to its "no relaxation" value when it is NOT the active method
# (run_server_vllm.sh's neutralise_all_knobs() writes every method's own
# neutral value to its own file on EVERY server start, active method
# included -- this is the same invariant the V1 patches already depend on).
# spec-casc-opt's own -inf makes its own defer condition always True (its
# own "always defer" case); r-fuzzy's own -inf does the same (JSD >= -inf
# is always True). ANDing the two together means an inactive method's own
# always-True defer never overrides the OTHER (possibly active) method's
# real decision, and the final defer_mask degrades to "always defer" (i.e.
# fall through to cactus's own gamma_x-boosted ratio test, itself neutral
# at alpha=0) when NEITHER is active. This composition is exact, not an
# approximation: at most one of the three methods' alphas is ever non-
# neutral on a given server (run_server_vllm.sh's own LOSSY_RULE dispatch
# invariant), so the other two's neutral values are true no-ops here, not
# just "small effects."
_SPEC_CASC_ALPHA_FILE = f"/tmp/lossy-token-eff-spec-casc-alpha-{os.getuid()}"
try:
    with open(_SPEC_CASC_ALPHA_FILE) as _f:
        _SPEC_CASC_ALPHA = float(_f.read().strip())
    _SPEC_CASC_ALPHA_SOURCE = _SPEC_CASC_ALPHA_FILE
except (OSError, ValueError):
    _SPEC_CASC_ALPHA = float("-inf")
    _SPEC_CASC_ALPHA_SOURCE = f"default, no readable {_SPEC_CASC_ALPHA_FILE}"
print(
    f"[SPEC-CASC-OPT PATCH V2, PROOF-OF-CONCEPT] pid={os.getpid()} "
    f"alpha={_SPEC_CASC_ALPHA} ({_SPEC_CASC_ALPHA_SOURCE})",
    file=sys.stderr,
    flush=True,
)

_R_FUZZY_ALPHA_FILE = f"/tmp/lossy-token-eff-r-fuzzy-alpha-{os.getuid()}"
try:
    with open(_R_FUZZY_ALPHA_FILE) as _f:
        _R_FUZZY_ALPHA = float(_f.read().strip())
    _R_FUZZY_ALPHA_SOURCE = _R_FUZZY_ALPHA_FILE
except (OSError, ValueError):
    _R_FUZZY_ALPHA = float("-inf")
    _R_FUZZY_ALPHA_SOURCE = f"default, no readable {_R_FUZZY_ALPHA_FILE}"
print(
    f"[R-FUZZY PATCH V2, PROOF-OF-CONCEPT] pid={os.getpid()} "
    f"alpha={_R_FUZZY_ALPHA} ({_R_FUZZY_ALPHA_SOURCE})",
    file=sys.stderr,
    flush=True,
)

# spec-casc-tok (V2, ACCEPT-TEST ONLY, PROOF-OF-CONCEPT, 2026-08-20). Same
# accept-only scoping caveat as cactus above: this does NOT rebuild the
# full pi_rej recovery distribution the real V1 patch's "needed for
# residual sampling over the whole vocab" comment requires -- recovery on
# rejection still samples from stock p.
#
#   A = {v : p(v) >= (1-alpha)*max(p)}        (the trusted top set)
#   eta = 1 - sum_{v in A} q(v)
#   pi_rej(x) = eta*p(x) + q(x) if x in A, else eta*p(x)
#   accept iff pi_rej(x)/q(x) >= u
#
# alpha=-inf is the true strict point here (NOT alpha=0.0 -- see
# patches/README.md's own warning): (1-alpha)*max(p) -> +inf makes A empty
# everywhere, eta = 1 - 0 = 1, pi_rej(x) = p(x) exactly.
#
# Composed with cactus as a DELTA from p(x), not a replacement, since only
# one method is ever really active (the mutual-exclusivity invariant every
# other composition here already relies on): cactus contributes
# (gamma_x - p_x), spec-casc-tok contributes (pi_rej_x - p_x), and at most
# one of those two deltas is non-zero on a given server, so
# effective_p_x = p_x + (gamma_x - p_x) + (pi_rej_x - p_x)
#              = gamma_x + pi_rej_x - p_x
# is exact, not an approximation, under that invariant -- both reduce to
# p_x alone when neither is active, matching the SPEC_CASC_ALPHA/R_FUZZY
# defer_mask composition's own reasoning above.
_SPEC_CASC_TOK_ALPHA_FILE = f"/tmp/lossy-token-eff-spec-casc-tok-alpha-{os.getuid()}"
try:
    with open(_SPEC_CASC_TOK_ALPHA_FILE) as _f:
        _SPEC_CASC_TOK_ALPHA = float(_f.read().strip())
    _SPEC_CASC_TOK_ALPHA_SOURCE = _SPEC_CASC_TOK_ALPHA_FILE
except (OSError, ValueError):
    _SPEC_CASC_TOK_ALPHA = float("-inf")
    _SPEC_CASC_TOK_ALPHA_SOURCE = f"default, no readable {_SPEC_CASC_TOK_ALPHA_FILE}"
print(
    f"[SPEC-CASC-TOK PATCH V2, PROOF-OF-CONCEPT] pid={os.getpid()} "
    f"alpha={_SPEC_CASC_TOK_ALPHA} ({_SPEC_CASC_TOK_ALPHA_SOURCE})",
    file=sys.stderr,
    flush=True,
)

# spec-casc-tok-hsr-guard (V2 port, 2026-08-22): the actuator half of the
# hidden-state-recurrence-triggered strict window. See
# analysis/semantic_guard/README.md's "spec_casc_tok_hsr_guard" section and
# patches/vllm-0.26.0-spec-casc-tok-hsr-guard.patch's own module comment
# (the V1 original this is ported from) for the full design and mechanism.
# Own, SEPARATE alpha file from plain spec-casc-tok's -- these are
# different top-level methods, mutually exclusive like every other pair in
# this file, never both genuinely active on the same server.
_SPEC_CASC_TOK_HSR_GUARD_ALPHA_FILE = f"/tmp/lossy-token-eff-spec-casc-tok-hsr-guard-alpha-{os.getuid()}"
try:
    with open(_SPEC_CASC_TOK_HSR_GUARD_ALPHA_FILE) as _f:
        _SPEC_CASC_TOK_HSR_GUARD_ALPHA = float(_f.read().strip())
    _SPEC_CASC_TOK_HSR_GUARD_ALPHA_SOURCE = _SPEC_CASC_TOK_HSR_GUARD_ALPHA_FILE
except (OSError, ValueError):
    _SPEC_CASC_TOK_HSR_GUARD_ALPHA = float("-inf")
    _SPEC_CASC_TOK_HSR_GUARD_ALPHA_SOURCE = f"default, no readable {_SPEC_CASC_TOK_HSR_GUARD_ALPHA_FILE}"
# Cross-file coordination with the model-runner's own hidden-state-
# recurrence tracker (vllm/v1/worker/gpu/model_runner.py, the
# _HSR_GUARD/_HSRecurrenceGuard hook near its speculator.propose() call
# site) -- WRITTEN there on a trigger, READ AND DECREMENTED here. Both
# sides run in strict alternation within one generation loop (verify round
# N, propose round N+1, verify round N+1, ...), never concurrently, so
# this is safe by construction, not by locking -- same convention as
# every other stateful file in this repo.
_HSR_REMAINING_FILE = f"/tmp/lossy-token-eff-hsr-guard-remaining-{os.getuid()}"
_HSR_LIVE_DEBUG_ENABLED = os.path.exists(f"/tmp/lossy-token-eff-hsr-guard-live-debug-enable-{os.getuid()}")


def _hsr_read_remaining() -> int:
    try:
        with open(_HSR_REMAINING_FILE) as f:
            return max(0, int(f.read().strip()))
    except (OSError, ValueError):
        return 0


def _hsr_write_remaining(value: int) -> None:
    try:
        with open(_HSR_REMAINING_FILE, "w") as f:
            f.write(str(max(0, value)))
    except OSError:
        pass


print(
    f"[SPEC-CASC-TOK-HSR-GUARD PATCH V2] pid={os.getpid()} "
    f"alpha={_SPEC_CASC_TOK_HSR_GUARD_ALPHA} ({_SPEC_CASC_TOK_HSR_GUARD_ALPHA_SOURCE})",
    file=sys.stderr,
    flush=True,
)


@triton.jit
def _compute_max_and_sumexp(logits):
    max = tl.max(logits, axis=0)
    sumexp = tl.where(
        max > float("-inf"),
        tl.sum(tl.exp(logits - max)),
        0.0,
    )
    return max, sumexp


@triton.jit
def _compute_global_logsumexp(
    local_max_ptr,
    local_max_stride,
    local_sumexp_ptr,
    local_sumexp_stride,
    logit_idx,
    vocab_num_blocks,
    PADDED_VOCAB_NUM_BLOCKS: tl.constexpr,
):
    blocks = tl.arange(0, PADDED_VOCAB_NUM_BLOCKS)
    blocks_mask = blocks < vocab_num_blocks
    maxes = tl.load(
        local_max_ptr + logit_idx * local_max_stride + blocks,
        mask=blocks_mask,
        other=float("-inf"),
    )
    sumexps = tl.load(
        local_sumexp_ptr + logit_idx * local_sumexp_stride + blocks,
        mask=blocks_mask,
        other=0.0,
    )
    global_max = tl.max(maxes, axis=0)
    global_lse = global_max + tl.log(tl.sum(sumexps * tl.exp(maxes - global_max)))
    return global_lse


@triton.jit
def _compute_global_residual_mass(
    local_residual_mass_ptr,
    local_residual_mass_stride,
    prefix_joint_ratio,
    target_logits_ptr,
    target_logits_stride,
    target_local_max_ptr,
    target_local_max_stride,
    target_local_sumexp_ptr,
    target_local_sumexp_stride,
    draft_sampled_ptr,
    logit_idx,
    vocab_num_blocks,
    PADDED_VOCAB_NUM_BLOCKS: tl.constexpr,
    HAS_DRAFT_LOGITS: tl.constexpr,
):
    if HAS_DRAFT_LOGITS:
        blocks = tl.arange(0, PADDED_VOCAB_NUM_BLOCKS)
        mask = blocks < vocab_num_blocks
        partials = tl.load(
            local_residual_mass_ptr + logit_idx * local_residual_mass_stride + blocks,
            mask=mask,
            other=0.0,
        )
        return tl.sum(partials, axis=0)
    else:
        # One-hot draft. M_s is a point mass at this draft token
        # so the residual mass reduces to the closed form:
        #   p * (1 - M_b(draft_token)).
        draft_token = tl.load(draft_sampled_ptr + logit_idx + 1).to(tl.int64)
        target_lse = _compute_global_logsumexp(
            target_local_max_ptr,
            target_local_max_stride,
            target_local_sumexp_ptr,
            target_local_sumexp_stride,
            logit_idx,
            vocab_num_blocks,
            PADDED_VOCAB_NUM_BLOCKS,
        )
        target_logit = tl.load(
            target_logits_ptr + logit_idx * target_logits_stride + draft_token,
        ).to(tl.float32)
        m_b = tl.exp(target_logit - target_lse)
        return prefix_joint_ratio * (1.0 - m_b)


@triton.jit
def _compute_global_target_argmax(
    target_local_max_ptr,
    target_local_max_stride,
    target_local_argmax_ptr,
    target_local_argmax_stride,
    logit_idx,
    vocab_num_blocks,
    PADDED_VOCAB_NUM_BLOCKS: tl.constexpr,
):
    blocks = tl.arange(0, PADDED_VOCAB_NUM_BLOCKS)
    blocks_mask = blocks < vocab_num_blocks
    local_max = tl.load(
        target_local_max_ptr + logit_idx * target_local_max_stride + blocks,
        mask=blocks_mask,
        other=float("-inf"),
    )
    max_block_idx = tl.argmax(local_max, axis=0)
    return tl.load(
        target_local_argmax_ptr + logit_idx * target_local_argmax_stride + max_block_idx
    ).to(tl.int64)


@triton.jit
def _compute_global_logprobs_and_logsumexp(
    token,
    mask,
    logit_idx,
    req_state_idx,
    draft_step,
    # [num_logits, V]
    target_logits_ptr,
    target_logits_stride,
    # [num_logits, num_blocks]
    target_local_max_ptr,
    target_local_max_stride,
    target_local_sumexp_ptr,
    target_local_sumexp_stride,
    # [max_num_reqs, num_speculative_steps, V]
    draft_logits_ptr,
    draft_logits_stride_0,
    draft_logits_stride_1,
    # [num_logits, num_blocks]
    draft_local_max_ptr,
    draft_local_max_stride,
    draft_local_sumexp_ptr,
    draft_local_sumexp_stride,
    vocab_num_blocks,
    PADDED_VOCAB_NUM_BLOCKS: tl.constexpr,
    HAS_DRAFT_LOGITS: tl.constexpr,
):
    target_logit = tl.load(
        target_logits_ptr + logit_idx * target_logits_stride + token,
        mask=mask,
        other=float("-inf"),
    ).to(tl.float32)
    target_lse = _compute_global_logsumexp(
        target_local_max_ptr,
        target_local_max_stride,
        target_local_sumexp_ptr,
        target_local_sumexp_stride,
        logit_idx,
        vocab_num_blocks,
        PADDED_VOCAB_NUM_BLOCKS,
    )
    target_log_prob = target_logit - target_lse
    if HAS_DRAFT_LOGITS:
        draft_logit = tl.load(
            draft_logits_ptr
            + req_state_idx * draft_logits_stride_0
            + draft_step * draft_logits_stride_1
            + token,
            mask=mask,
            other=float("-inf"),
        ).to(tl.float32)
        draft_lse = _compute_global_logsumexp(
            draft_local_max_ptr,
            draft_local_max_stride,
            draft_local_sumexp_ptr,
            draft_local_sumexp_stride,
            logit_idx,
            vocab_num_blocks,
            PADDED_VOCAB_NUM_BLOCKS,
        )
        draft_log_prob = draft_logit - draft_lse
    else:
        # One-hot draft: q(token) = 1, log_q = 0.
        draft_log_prob = 0.0
        draft_lse = 0.0
    return target_log_prob, draft_log_prob, target_lse, draft_lse


@triton.jit
def _compute_local_logits_stats_kernel(
    # [num_logits, num_blocks]
    target_local_argmax_ptr,
    target_local_argmax_stride,
    # [num_logits, num_blocks]
    target_local_max_ptr,
    target_local_max_stride,
    # [num_logits, num_blocks]
    target_local_sumexp_ptr,
    target_local_sumexp_stride,
    # [num_logits, num_blocks]
    draft_local_max_ptr,
    draft_local_max_stride,
    # [num_logits, num_blocks]
    draft_local_sumexp_ptr,
    draft_local_sumexp_stride,
    # [num_logits, V]
    target_logits_ptr,
    target_logits_stride,
    # [max_num_reqs, num_speculative_steps, V]
    draft_logits_ptr,
    draft_logits_stride_0,
    draft_logits_stride_1,
    # [num_logits]
    expanded_idx_mapping_ptr,
    # [num_logits]
    expanded_local_pos_ptr,
    # [max_num_reqs]
    temp_ptr,
    vocab_size,
    num_speculative_steps,
    BLOCK_SIZE: tl.constexpr,
    HAS_DRAFT_LOGITS: tl.constexpr,
):
    logit_idx = tl.program_id(0).to(tl.int64)
    draft_step_idx = tl.load(expanded_local_pos_ptr + logit_idx)

    if draft_step_idx >= num_speculative_steps:
        # Bonus token. Max/argmax and summed exponentials are not needed.
        return

    req_state_idx = tl.load(expanded_idx_mapping_ptr + logit_idx).to(tl.int64)
    temp = tl.load(temp_ptr + req_state_idx).to(tl.float32)

    block_idx = tl.program_id(1)
    block_offsets = block_idx * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
    mask = block_offsets < vocab_size

    if temp == 0.0:
        # Greedy sampling. Only the target max/argmax are needed.
        target_logits = tl.load(
            target_logits_ptr + logit_idx * target_logits_stride + block_offsets,
            mask=mask,
            other=float("-inf"),
        ).to(tl.float32)
        value, idx = tl.max(target_logits, axis=0, return_indices=True)
        token_id = block_idx * BLOCK_SIZE + idx
        tl.store(
            target_local_argmax_ptr
            + logit_idx * target_local_argmax_stride
            + block_idx,
            token_id,
        )
        tl.store(
            target_local_max_ptr + logit_idx * target_local_max_stride + block_idx,
            value,
        )
    else:
        # Get local target max and summed exponentials.
        target_logits = tl.load(
            target_logits_ptr + logit_idx * target_logits_stride + block_offsets,
            mask=mask,
            other=float("-inf"),
        ).to(tl.float32)
        target_max, target_sumexp = _compute_max_and_sumexp(target_logits)
        tl.store(
            target_local_max_ptr + logit_idx * target_local_max_stride + block_idx,
            target_max,
        )
        tl.store(
            target_local_sumexp_ptr
            + logit_idx * target_local_sumexp_stride
            + block_idx,
            target_sumexp,
        )
        if HAS_DRAFT_LOGITS:
            # Get local draft max and summed exponentials.
            draft_logits = tl.load(
                draft_logits_ptr
                + req_state_idx * draft_logits_stride_0
                + draft_step_idx * draft_logits_stride_1
                + block_offsets,
                mask=mask,
                other=float("-inf"),
            ).to(tl.float32)
            draft_max, draft_sumexp = _compute_max_and_sumexp(draft_logits)
            tl.store(
                draft_local_max_ptr + logit_idx * draft_local_max_stride + block_idx,
                draft_max,
            )
            tl.store(
                draft_local_sumexp_ptr
                + logit_idx * draft_local_sumexp_stride
                + block_idx,
                draft_sumexp,
            )


@triton.jit
def _compute_cumulative_log_p_kernel(
    # [num_logits]
    cumulative_log_p_ptr,
    # [num_logits, V]
    target_logits_ptr,
    target_logits_stride,
    # [num_logits, num_blocks]
    target_local_max_ptr,
    target_local_max_stride,
    # [num_logits, num_blocks]
    target_local_sumexp_ptr,
    target_local_sumexp_stride,
    # [num_logits]
    draft_sampled_ptr,
    # [max_num_reqs, num_speculative_steps, V]
    draft_logits_ptr,
    draft_logits_stride_0,
    draft_logits_stride_1,
    # [num_logits, num_blocks]
    draft_local_max_ptr,
    draft_local_max_stride,
    # [num_logits, num_blocks]
    draft_local_sumexp_ptr,
    draft_local_sumexp_stride,
    # [num_reqs + 1]
    cu_num_logits_ptr,
    # [num_reqs]
    idx_mapping_ptr,
    # [max_num_reqs]
    temp_ptr,
    vocab_num_blocks,
    PADDED_VOCAB_NUM_BLOCKS: tl.constexpr,
    HAS_DRAFT_LOGITS: tl.constexpr,
):
    req_idx = tl.program_id(0)
    req_state_idx = tl.load(idx_mapping_ptr + req_idx).to(tl.int64)
    start_idx = tl.load(cu_num_logits_ptr + req_idx).to(tl.int64)
    end_idx = tl.load(cu_num_logits_ptr + req_idx + 1)
    num_draft_tokens = end_idx - start_idx - 1
    temp = tl.load(temp_ptr + req_state_idx).to(tl.float32)
    if temp == 0.0:
        return

    log_p = 0.0
    for step in range(num_draft_tokens):
        logit_idx = start_idx + step
        draft_token = tl.load(draft_sampled_ptr + logit_idx + 1).to(tl.int64)
        target_logprob, draft_logprob, _, _ = _compute_global_logprobs_and_logsumexp(
            draft_token,
            True,  # mask
            logit_idx,
            req_state_idx,
            step,
            target_logits_ptr,
            target_logits_stride,
            target_local_max_ptr,
            target_local_max_stride,
            target_local_sumexp_ptr,
            target_local_sumexp_stride,
            draft_logits_ptr,
            draft_logits_stride_0,
            draft_logits_stride_1,
            draft_local_max_ptr,
            draft_local_max_stride,
            draft_local_sumexp_ptr,
            draft_local_sumexp_stride,
            vocab_num_blocks,
            PADDED_VOCAB_NUM_BLOCKS,
            HAS_DRAFT_LOGITS,
        )
        log_p = tl.minimum(log_p + (target_logprob - draft_logprob), 0.0)
        tl.store(cumulative_log_p_ptr + logit_idx, log_p)


@triton.jit
def _compute_local_residual_mass_kernel(
    # [num_logits, num_blocks]
    local_residual_mass_ptr,
    local_residual_mass_stride,
    # [num_logits]
    cumulative_log_p_ptr,
    # [num_logits, V]
    target_logits_ptr,
    target_logits_stride,
    # [num_logits, num_blocks]
    target_local_max_ptr,
    target_local_max_stride,
    # [num_logits, num_blocks]
    target_local_sumexp_ptr,
    target_local_sumexp_stride,
    # [max_num_reqs, num_speculative_steps, V]
    draft_logits_ptr,
    draft_logits_stride_0,
    draft_logits_stride_1,
    # [num_logits, num_blocks]
    draft_local_max_ptr,
    draft_local_max_stride,
    # [num_logits, num_blocks]
    draft_local_sumexp_ptr,
    draft_local_sumexp_stride,
    # [num_logits]
    expanded_idx_mapping_ptr,
    # [num_logits]
    expanded_local_pos_ptr,
    # [max_num_reqs]
    temp_ptr,
    vocab_size,
    num_speculative_steps,
    vocab_num_blocks,
    BLOCK_SIZE: tl.constexpr,
    PADDED_VOCAB_NUM_BLOCKS: tl.constexpr,
):
    logit_idx = tl.program_id(0).to(tl.int64)
    draft_step_idx = tl.load(expanded_local_pos_ptr + logit_idx)
    if draft_step_idx == 0 or draft_step_idx >= num_speculative_steps:
        # The acceptance threshold, h, looks one position ahead and sums
        # over: max(p_i * M_b(x|x_{<i}) - M_s(x|x_{<i}), 0). Tokens at the
        # first and last (bonus) positions aren't needed for this computation.
        return

    req_state_idx = tl.load(expanded_idx_mapping_ptr + logit_idx).to(tl.int64)
    temp = tl.load(temp_ptr + req_state_idx).to(tl.float32)
    if temp == 0.0:
        return

    block_idx = tl.program_id(1)
    block_offsets = block_idx * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
    mask = block_offsets < vocab_size
    target_log_probs, draft_log_probs, _, _ = _compute_global_logprobs_and_logsumexp(
        block_offsets,
        mask,
        logit_idx,
        req_state_idx,
        draft_step_idx,
        target_logits_ptr,
        target_logits_stride,
        target_local_max_ptr,
        target_local_max_stride,
        target_local_sumexp_ptr,
        target_local_sumexp_stride,
        draft_logits_ptr,
        draft_logits_stride_0,
        draft_logits_stride_1,
        draft_local_max_ptr,
        draft_local_max_stride,
        draft_local_sumexp_ptr,
        draft_local_sumexp_stride,
        vocab_num_blocks,
        PADDED_VOCAB_NUM_BLOCKS,
        True,  # HAS_DRAFT_LOGITS
    )

    # Compute the residual mass: max(p_i * M_b(x|x_{<i}) - M_s(x|x_{<i}), 0)
    p = tl.exp(tl.load(cumulative_log_p_ptr + logit_idx - 1).to(tl.float32))
    m_b = tl.exp(target_log_probs)
    m_s = tl.exp(draft_log_probs)
    partial = tl.sum(tl.maximum(p * m_b - m_s, 0.0), axis=0)
    tl.store(
        local_residual_mass_ptr + logit_idx * local_residual_mass_stride + block_idx,
        partial,
    )


@triton.jit
def _rejection_kernel(
    # [num_reqs, num_speculative_steps + 1]
    sampled_ptr,
    sampled_stride,
    # [num_reqs]
    rejected_steps_ptr,
    # [num_reqs]
    target_rejected_logsumexp_ptr,
    # [num_reqs]
    draft_rejected_logsumexp_ptr,
    # [num_logits, V]
    target_logits_ptr,
    target_logits_stride,
    # [num_logits, num_blocks]
    target_local_argmax_ptr,
    target_local_argmax_stride,
    # [num_logits, num_blocks]
    target_local_max_ptr,
    target_local_max_stride,
    # [num_logits, num_blocks]
    target_local_sumexp_ptr,
    target_local_sumexp_stride,
    # [num_logits]
    draft_sampled_ptr,
    # [max_num_reqs, num_speculative_steps, V]
    draft_logits_ptr,
    draft_logits_stride_0,
    draft_logits_stride_1,
    # [num_logits, num_blocks]
    draft_local_max_ptr,
    draft_local_max_stride,
    # [num_logits, num_blocks]
    draft_local_sumexp_ptr,
    draft_local_sumexp_stride,
    # [num_reqs + 1]
    cu_num_logits_ptr,
    # [num_reqs]
    idx_mapping_ptr,
    # [max_num_reqs]
    temp_ptr,
    # [max_num_reqs]
    seed_ptr,
    # [num_logits]
    pos_ptr,
    # [num_speculative_steps]
    synthetic_conditional_rates_ptr,
    # [num_logits]
    cumulative_log_p_ptr,
    # [num_logits, num_blocks]
    local_residual_mass_ptr,
    local_residual_mass_stride,
    # scalar; CACTUS's own alpha, 0.0 for the strict rule (gamma_x == p(x))
    cactus_alpha,
    # scalar; spec-casc-tok's own alpha, -inf for the strict rule (NOT 0.0
    # -- see this method's own module comment)
    casc_tok_alpha,
    # scalar; log(1-mentored_dec_alpha), 0.0 for the strict rule -- a true
    # additive no-op on the RHS threshold (see this method's own module
    # comment for why it composes on the threshold, not effective_p_x).
    log_mentored_dec_lam,
    # [num_logits] bool, or None iff NOT HAS_DRAFT_LOGITS; spec-casc-opt AND
    # r-fuzzy's combined defer decision (True == run the ratio test below,
    # False == accept unconditionally). See the module comment for the
    # composition argument (each inactive method's own alpha defaults to
    # "always defer", so this degrades to True when neither is active).
    defer_mask_ptr,
    # [num_logits] float32, or None iff NOT HAS_CASC_TOK; spec-casc-tok's own
    # per-token max(p) and eta (see module comment for the formula and the
    # "composed as a delta from p(x)" argument).
    casc_tok_top1_ptr,
    casc_tok_eta_ptr,
    vocab_num_blocks,
    PADDED_VOCAB_NUM_BLOCKS: tl.constexpr,
    HAS_DRAFT_LOGITS: tl.constexpr,
    # Separate from HAS_DRAFT_LOGITS on purpose: defer_mask can be None even
    # when draft_logits itself is real (the num_reqs<=8 warmup guard at the
    # call site above) -- gating the tl.load on HAS_DRAFT_LOGITS alone would
    # dereference a null pointer on every warmup/CUDA-graph-capture pass.
    HAS_DEFER_MASK: tl.constexpr,
    # Same reasoning as HAS_DEFER_MASK, for casc_tok_top1_ptr/casc_tok_eta_ptr.
    HAS_CASC_TOK: tl.constexpr,
    SYNTHETIC_MODE: tl.constexpr,
    USE_BLOCK_VERIFICATION: tl.constexpr,
):
    req_idx = tl.program_id(0)
    req_state_idx = tl.load(idx_mapping_ptr + req_idx).to(tl.int64)
    start_idx = tl.load(cu_num_logits_ptr + req_idx).to(tl.int64)
    end_idx = tl.load(cu_num_logits_ptr + req_idx + 1)
    num_draft_tokens = end_idx - start_idx - 1
    seed = tl.load(seed_ptr + req_state_idx)
    temp = tl.load(temp_ptr + req_state_idx).to(tl.float32)
    is_greedy = temp == 0.0

    accepted_length = tl.zeros((), tl.int64)
    target_lse = 0.0
    draft_lse = 0.0
    accepted = True
    for i in range(num_draft_tokens):
        logit_idx = start_idx + i
        draft_sampled = tl.load(draft_sampled_ptr + logit_idx + 1).to(tl.int64)
        pos = tl.load(pos_ptr + logit_idx)
        u = tl_rand32(seed, pos, includes_zero=False)
        if USE_BLOCK_VERIFICATION and not is_greedy:
            # Block verification (Sun et al., 2024): https://arxiv.org/abs/2403.10444
            prefix_joint_ratio = tl.exp(
                tl.load(cumulative_log_p_ptr + logit_idx).to(tl.float32)
            )
            if i < num_draft_tokens - 1:
                residual_mass = _compute_global_residual_mass(
                    local_residual_mass_ptr,
                    local_residual_mass_stride,
                    prefix_joint_ratio,
                    target_logits_ptr,
                    target_logits_stride,
                    target_local_max_ptr,
                    target_local_max_stride,
                    target_local_sumexp_ptr,
                    target_local_sumexp_stride,
                    draft_sampled_ptr,
                    logit_idx + 1,
                    vocab_num_blocks,
                    PADDED_VOCAB_NUM_BLOCKS,
                    HAS_DRAFT_LOGITS,
                )
                denom = residual_mass + 1.0 - prefix_joint_ratio
                h = tl.where(denom > 0.0, residual_mass / denom, 1.0)
            else:
                h = prefix_joint_ratio
            accepted_length = tl.where(u <= h, i + 1, accepted_length)
            tl.store(sampled_ptr + req_idx * sampled_stride + i, draft_sampled)
        elif accepted:
            if is_greedy:
                # Greedy sampling. Accept IFF draft matches target argmax.
                # NOTE: Target argmax is stored directly so that resampling
                # can be skipped upon rejection.
                target_argmax = _compute_global_target_argmax(
                    target_local_max_ptr,
                    target_local_max_stride,
                    target_local_argmax_ptr,
                    target_local_argmax_stride,
                    logit_idx,
                    vocab_num_blocks,
                    PADDED_VOCAB_NUM_BLOCKS,
                )
                if SYNTHETIC_MODE:
                    rate = tl.load(synthetic_conditional_rates_ptr + i)
                    # -1 is used for padded draft token ids that should be rejected.
                    accepted &= (u < rate) & (draft_sampled >= 0)
                else:
                    accepted &= target_argmax == draft_sampled
                tl.store(
                    sampled_ptr + req_idx * sampled_stride + i,
                    draft_sampled if accepted else target_argmax,
                )
            else:
                # Speculative decoding (Leviathan et al., 2023): https://arxiv.org/abs/2211.17192
                # -1 is used for padded draft token ids that should be rejected.
                is_valid_draft = draft_sampled >= 0
                # Avoid possible OOB ptr access.
                draft_sampled = tl.maximum(0, draft_sampled)
                target_logprob, draft_logprob, target_lse, draft_lse = (
                    _compute_global_logprobs_and_logsumexp(
                        draft_sampled,
                        True,  # mask
                        logit_idx,
                        req_state_idx,
                        i,
                        target_logits_ptr,
                        target_logits_stride,
                        target_local_max_ptr,
                        target_local_max_stride,
                        target_local_sumexp_ptr,
                        target_local_sumexp_stride,
                        draft_logits_ptr,
                        draft_logits_stride_0,
                        draft_logits_stride_1,
                        draft_local_max_ptr,
                        draft_local_max_stride,
                        draft_local_sumexp_ptr,
                        draft_local_sumexp_stride,
                        vocab_num_blocks,
                        PADDED_VOCAB_NUM_BLOCKS,
                        HAS_DRAFT_LOGITS,
                    )
                )
                if SYNTHETIC_MODE:
                    rate = tl.load(synthetic_conditional_rates_ptr + i)
                    accepted &= u < rate
                else:
                    # spec-casc-opt / r-fuzzy: defer=False means pi_rej == q
                    # (accept unconditionally, Eq. 12 Narasimhan et al.
                    # 2025); defer=True runs the (cactus-boosted) ratio test
                    # below exactly as before. Both methods' own alphas
                    # default to "always defer" when inactive, so this is a
                    # true no-op composition, not an approximation -- see
                    # the module comment above.
                    defer = True
                    if HAS_DEFER_MASK:
                        defer = tl.load(defer_mask_ptr + logit_idx)
                    if defer:
                        # Probability ratio test: p(x) > u * q(x)
                        # Equivalent log form: log_p(x) > log(u) + log_q(x)
                        # CACTUS (accept-test only): gamma_x = min(p(x) +
                        # sqrt(2*alpha*p(x)*(1-p(x))), 1), then test
                        # gamma_x/q(x) >= u in place of p(x)/q(x) >= u.
                        # alpha=0 gives gamma_x == p(x) exactly (variance_term
                        # == 0), recovering the strict test bit-for-bit.
                        p_x = tl.exp(target_logprob)
                        variance_term = tl.maximum(
                            2.0 * cactus_alpha * p_x * (1.0 - p_x), 0.0
                        )
                        gamma_x = tl.minimum(p_x + tl.sqrt(variance_term), 1.0)

                        # spec-casc-tok: pi_rej(x) = eta*p(x) + q(x) if x is
                        # in the trusted top set A, else eta*p(x). Composed
                        # with cactus as a delta from p(x) -- see the module
                        # comment for why this is exact under the mutual-
                        # exclusivity invariant, not an approximation.
                        pi_rej_x = p_x
                        if HAS_CASC_TOK:
                            q_x = tl.exp(draft_logprob)
                            top1 = tl.load(casc_tok_top1_ptr + logit_idx)
                            eta = tl.load(casc_tok_eta_ptr + logit_idx)
                            x_in_top_set = p_x >= (1.0 - casc_tok_alpha) * top1
                            pi_rej_x = eta * p_x
                            if x_in_top_set:
                                pi_rej_x += q_x

                        effective_p_x = gamma_x + pi_rej_x - p_x
                        log_effective_p_x = tl.log(tl.maximum(effective_p_x, 1e-30))
                        # mentored-dec composes on the RHS threshold (it
                        # scales q, not p), so it's a separate additive term
                        # here rather than folded into effective_p_x above --
                        # log_mentored_dec_lam=0.0 when inactive, a true
                        # no-op alongside whichever of the p(x)-side methods
                        # (if any) is active.
                        accepted &= (
                            log_effective_p_x
                            > tl.log(u) + draft_logprob + log_mentored_dec_lam
                        )
                accepted &= is_valid_draft
                tl.store(sampled_ptr + req_idx * sampled_stride + i, draft_sampled)
            accepted_length += accepted
    tl.store(rejected_steps_ptr + req_idx, accepted_length)
    if USE_BLOCK_VERIFICATION and not is_greedy and accepted_length < num_draft_tokens:
        # Compute the target and draft log exponential sums for the
        # rejected token.
        rejected_idx = start_idx + accepted_length
        target_lse = _compute_global_logsumexp(
            target_local_max_ptr,
            target_local_max_stride,
            target_local_sumexp_ptr,
            target_local_sumexp_stride,
            rejected_idx,
            vocab_num_blocks,
            PADDED_VOCAB_NUM_BLOCKS,
        )
        if HAS_DRAFT_LOGITS:
            draft_lse = _compute_global_logsumexp(
                draft_local_max_ptr,
                draft_local_max_stride,
                draft_local_sumexp_ptr,
                draft_local_sumexp_stride,
                rejected_idx,
                vocab_num_blocks,
                PADDED_VOCAB_NUM_BLOCKS,
            )
    tl.store(target_rejected_logsumexp_ptr + req_idx, target_lse)
    tl.store(draft_rejected_logsumexp_ptr + req_idx, draft_lse)


@triton.jit
def _resample_kernel(
    # [num_reqs, num_blocks]
    resampled_local_argmax_ptr,
    resampled_local_argmax_stride,
    # [num_reqs, num_blocks]
    resampled_local_max_ptr,
    resampled_local_max_stride,
    # [num_logits, V]
    target_logits_ptr,
    target_logits_stride,
    # [num_reqs]
    target_rejected_logsumexp_ptr,
    # [max_num_reqs, num_speculative_steps, V]
    draft_logits_ptr,
    draft_logits_stride_0,
    draft_logits_stride_1,
    # [num_reqs]
    draft_rejected_logsumexp_ptr,
    # [num_reqs]
    rejected_step_ptr,
    # [num_reqs + 1]
    cu_num_logits_ptr,
    # [num_logits]
    expanded_idx_mapping_ptr,
    # [num_logits]
    draft_sampled_ptr,
    # [max_num_reqs]
    temp_ptr,
    # [max_num_reqs]
    seed_ptr,
    # [num_logits]
    pos_ptr,
    # [num_logits]
    cumulative_log_p_ptr,
    vocab_size,
    BLOCK_SIZE: tl.constexpr,
    HAS_DRAFT_LOGITS: tl.constexpr,
    USE_FP64: tl.constexpr,
    USE_BLOCK_VERIFICATION: tl.constexpr,
):
    req_idx = tl.program_id(0)
    resample_idx = tl.load(rejected_step_ptr + req_idx)
    start_idx = tl.load(cu_num_logits_ptr + req_idx).to(tl.int64)
    end_idx = tl.load(cu_num_logits_ptr + req_idx + 1)
    resample_token_idx = start_idx + resample_idx
    req_state_idx = tl.load(expanded_idx_mapping_ptr + resample_token_idx).to(tl.int64)

    temp = tl.load(temp_ptr + req_state_idx).to(tl.float32)
    is_bonus = resample_token_idx == end_idx - 1
    if temp == 0.0 and not is_bonus:
        # Greedy + non-bonus token. No resampling needed because
        # the target argmax is already in the sampled tensor.
        return

    block_idx = tl.program_id(1)
    block = block_idx * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
    mask = block < vocab_size
    target_logits = tl.load(
        target_logits_ptr + resample_token_idx * target_logits_stride + block,
        mask=mask,
        other=float("-inf"),
    ).to(tl.float32)

    # Compute the residual logits to resample the rejected token from.
    if is_bonus:
        # Bonus token (no rejections). Directly use the target logits.
        residual_logits = target_logits
    elif HAS_DRAFT_LOGITS:
        draft_logits = tl.load(
            draft_logits_ptr
            + req_state_idx * draft_logits_stride_0
            + resample_idx * draft_logits_stride_1
            + block,
            mask=mask,
            other=float("-inf"),
        ).to(tl.float32)
        target_lse = tl.load(target_rejected_logsumexp_ptr + req_idx)
        draft_lse = tl.load(draft_rejected_logsumexp_ptr + req_idx)
        target_log_probs = target_logits - target_lse
        if USE_BLOCK_VERIFICATION:
            # Block residual is:
            #   max(p_tau * M_b(x) - M_s(x), 0) / Z.
            # Scale the target logprobs by log(p_tau). p_0 = 1, so skip
            # shifting when nothing was accepted (tau == 0).
            log_p_tau = 0.0
            if resample_idx > 0:
                log_p_tau = tl.load(cumulative_log_p_ptr + resample_token_idx - 1).to(
                    tl.float32
                )
            target_log_probs += log_p_tau
        draft_log_probs = draft_logits - draft_lse
        # Compute the residual:
        #   r(x) = max(p(x) - q(x), 0)
        # Gumbel sampling needs logits, so we compute it in log space:
        #   log(r(x)) = log(max(exp(log_p(x)) - exp(log_q(x)), 0))
        # The more numerically stable form is:
        #   log(max(exp(a) - exp(b), 0)) = a + log(max(1 - exp(b - a), 0))
        ratio = tl.exp(draft_log_probs - target_log_probs)
        residual_logits = tl.where(
            ratio < 1.0,
            target_log_probs + tldevice.log1p(-ratio),
            float("-inf"),
        ).to(tl.float32)
    else:
        # One-hot draft. The residual is just the target distribution with
        # the rejected draft token probability zeroed out.
        # NOTE: During block verification, the residual becomes:
        #   0                   if x == rejected_draft_token
        #   p_tau * M_b(x) / Z  otherwise
        # Therefore p_tau is a constant that cancels under normalization,
        # and does not need to be applied.
        rejected_draft_token = tl.load(draft_sampled_ptr + resample_token_idx + 1)
        residual_logits = tl.where(
            block != rejected_draft_token,
            target_logits,
            float("-inf"),
        ).to(tl.float32)

    # Resample the rejected/bonus token.
    value, idx = gumbel_block_argmax(
        residual_logits,
        block,
        mask,
        resample_token_idx,
        expanded_idx_mapping_ptr,
        temp_ptr,
        seed_ptr,
        pos_ptr,
        None,  # processed_logits_ptr
        0,  # processed_logits_stride
        None,  # processed_logits_col_ptr
        vocab_size,
        APPLY_TEMPERATURE=False,
        USE_FP64=USE_FP64,
    )
    token_id = block_idx * BLOCK_SIZE + idx
    tl.store(
        resampled_local_argmax_ptr
        + req_idx * resampled_local_argmax_stride
        + block_idx,
        token_id,
    )
    tl.store(
        resampled_local_max_ptr + req_idx * resampled_local_max_stride + block_idx,
        value,
    )


@triton.jit
def _insert_resampled_kernel(
    # [num_reqs, num_speculative_steps + 1]
    sampled_ptr,
    sampled_stride,
    # [num_reqs]
    num_sampled_ptr,
    # [num_reqs, num_blocks]
    resampled_local_argmax_ptr,
    resampled_local_argmax_stride,
    # [num_reqs, num_blocks]
    resampled_local_max_ptr,
    resampled_local_max_stride,
    resample_num_blocks,
    # [num_reqs + 1]
    cu_num_logits_ptr,
    # [num_reqs]
    expanded_idx_mapping_ptr,
    # [max_num_reqs]
    temp_ptr,
    PADDED_RESAMPLE_NUM_BLOCKS: tl.constexpr,
):
    req_idx = tl.program_id(0)
    num_sampled = tl.load(num_sampled_ptr + req_idx)
    start_idx = tl.load(cu_num_logits_ptr + req_idx)
    end_idx = tl.load(cu_num_logits_ptr + req_idx + 1)
    resample_token_idx = start_idx + num_sampled
    req_state_idx = tl.load(expanded_idx_mapping_ptr + resample_token_idx)

    # Increment the number of sampled tokens.
    tl.store(num_sampled_ptr + req_idx, num_sampled + 1)

    temp = tl.load(temp_ptr + req_state_idx).to(tl.float32)
    is_bonus = resample_token_idx == end_idx - 1
    if temp == 0.0 and not is_bonus:
        # Greedy + non-bonus token. The target argmax is already
        # in the sampled tensor.
        return

    # Insert the resampled token.
    block = tl.arange(0, PADDED_RESAMPLE_NUM_BLOCKS)
    mask = block < resample_num_blocks
    resampled_local_max = tl.load(
        resampled_local_max_ptr + req_idx * resampled_local_max_stride + block,
        mask=mask,
        other=float("-inf"),
    )
    resampled_max_block_idx = tl.argmax(resampled_local_max, axis=0)
    resampled = tl.load(
        resampled_local_argmax_ptr
        + req_idx * resampled_local_argmax_stride
        + resampled_max_block_idx,
    )
    tl.store(
        sampled_ptr + req_idx * sampled_stride + num_sampled,
        resampled,
    )


def rejection_sample(
    # [num_logits, V]
    target_logits: torch.Tensor,
    # [max_num_reqs, num_speculative_steps, V]
    draft_logits: torch.Tensor | None,
    # [num_logits]
    draft_sampled: torch.Tensor,
    # [num_reqs + 1]
    cu_num_logits: torch.Tensor,
    # [num_logits]
    pos: torch.Tensor,
    # [num_reqs]
    idx_mapping: torch.Tensor,
    # [num_logits]
    expanded_idx_mapping: torch.Tensor,
    # [num_logits]
    expanded_local_pos: torch.Tensor,
    # [max_num_reqs]
    temperature: torch.Tensor,
    # [max_num_reqs]
    seed: torch.Tensor,
    num_speculative_steps: int,
    # [num_speculative_steps]
    synthetic_conditional_rates: torch.Tensor | None = None,
    use_fp64: bool = False,
    use_block_verification: bool = False,
) -> tuple[torch.Tensor, torch.Tensor]:
    num_reqs = cu_num_logits.shape[0] - 1
    num_logits, vocab_size = target_logits.shape
    draft_logits_stride_0 = 0
    draft_logits_stride_1 = 0
    if has_draft_logits := draft_logits is not None:
        draft_logits_stride_0 = draft_logits.stride(0)
        draft_logits_stride_1 = draft_logits.stride(1)
        # In some cases (e.g. MiMo v2.5 Pro + DFlash) the target model's
        # vocab size is larger than the draft's due to padding.
        vocab_size = min(vocab_size, draft_logits.size(-1))

    # Compute the per-vocab-block logits stats, such as target argmax
    # (for greedy requests), and target max + softmax exponential
    # (for non-greedy requests).
    VOCAB_BLOCK_SIZE = 8192
    vocab_num_blocks = triton.cdiv(vocab_size, VOCAB_BLOCK_SIZE)
    padded_vocab_num_blocks = triton.next_power_of_2(vocab_num_blocks)
    target_local_argmax = target_logits.new_empty(
        num_logits, vocab_num_blocks, dtype=torch.int64
    )
    target_local_max = target_logits.new_empty(
        num_logits, vocab_num_blocks, dtype=torch.float32
    )
    target_local_sumexp = target_logits.new_empty(
        num_logits, vocab_num_blocks, dtype=torch.float32
    )
    draft_local_max = target_logits.new_empty(
        num_logits, vocab_num_blocks, dtype=torch.float32
    )
    draft_local_sumexp = target_logits.new_empty(
        num_logits, vocab_num_blocks, dtype=torch.float32
    )
    _compute_local_logits_stats_kernel[(num_logits, vocab_num_blocks)](
        target_local_argmax,
        target_local_argmax.stride(0),
        target_local_max,
        target_local_max.stride(0),
        target_local_sumexp,
        target_local_sumexp.stride(0),
        draft_local_max,
        draft_local_max.stride(0),
        draft_local_sumexp,
        draft_local_sumexp.stride(0),
        target_logits,
        target_logits.stride(0),
        draft_logits,
        draft_logits_stride_0,
        draft_logits_stride_1,
        expanded_idx_mapping,
        expanded_local_pos,
        temperature,
        vocab_size,
        num_speculative_steps,
        BLOCK_SIZE=VOCAB_BLOCK_SIZE,
        HAS_DRAFT_LOGITS=has_draft_logits,
    )

    # Precompute the running joint ratio and residual mass for block
    # verification.
    if use_block_verification:
        assert synthetic_conditional_rates is None, (
            "Block verification is incompatible with synthetic acceptance rates."
        )

        # Compute the log of the running joint ratio, p_i.
        # cumulative_log_p[start + i] = log(p_{i+1}), the cumulative ratio after
        # the (i+1)-th draft token.
        cumulative_log_p = target_logits.new_empty(num_logits, dtype=torch.float32)
        _compute_cumulative_log_p_kernel[(num_reqs,)](
            cumulative_log_p,
            target_logits,
            target_logits.stride(0),
            target_local_max,
            target_local_max.stride(0),
            target_local_sumexp,
            target_local_sumexp.stride(0),
            draft_sampled,
            draft_logits,
            draft_logits_stride_0,
            draft_logits_stride_1,
            draft_local_max,
            draft_local_max.stride(0),
            draft_local_sumexp,
            draft_local_sumexp.stride(0),
            cu_num_logits,
            idx_mapping,
            temperature,
            vocab_num_blocks,
            PADDED_VOCAB_NUM_BLOCKS=padded_vocab_num_blocks,
            HAS_DRAFT_LOGITS=has_draft_logits,
            num_warps=1,
        )

        # Compute the per-vocab-block partials of the residual mass, later reduced
        # to the total by _compute_global_residual_mass. Only launched for full
        # draft logits distributions. One-hot drafts used a closed-form residual
        # mass instead.
        if has_draft_logits:
            local_residual_mass = target_logits.new_empty(
                num_logits, vocab_num_blocks, dtype=torch.float32
            )
            _compute_local_residual_mass_kernel[(num_logits, vocab_num_blocks)](
                local_residual_mass,
                local_residual_mass.stride(0),
                cumulative_log_p,
                target_logits,
                target_logits.stride(0),
                target_local_max,
                target_local_max.stride(0),
                target_local_sumexp,
                target_local_sumexp.stride(0),
                draft_logits,
                draft_logits_stride_0,
                draft_logits_stride_1,
                draft_local_max,
                draft_local_max.stride(0),
                draft_local_sumexp,
                draft_local_sumexp.stride(0),
                expanded_idx_mapping,
                expanded_local_pos,
                temperature,
                vocab_size,
                num_speculative_steps,
                vocab_num_blocks,
                BLOCK_SIZE=VOCAB_BLOCK_SIZE,
                PADDED_VOCAB_NUM_BLOCKS=padded_vocab_num_blocks,
            )
        else:
            local_residual_mass = None
    else:
        cumulative_log_p = None
        local_residual_mass = None

    # Sample up until the first rejected/bonus token, and store
    # the step.
    sampled = draft_sampled.new_empty(
        num_reqs, num_speculative_steps + 1, dtype=torch.int64
    )
    num_sampled = sampled.new_empty(num_reqs, dtype=torch.int32)
    target_rejected_logsumexp = target_logits.new_empty(num_reqs, dtype=torch.float32)
    draft_rejected_logsumexp = target_logits.new_empty(num_reqs, dtype=torch.float32)

    # spec-casc-opt / r-fuzzy defer_mask (V2, PROOF-OF-CONCEPT) -- see the
    # module comment above for the composition argument. Gathers
    # draft_logits (dense [max_num_reqs, num_speculative_steps, V]) into
    # [num_logits, V] via expanded_idx_mapping/expanded_local_pos to match
    # target_logits's own layout, exactly like the V1 patches' own
    # "materialize once in plain PyTorch" approach.
    #
    # num_reqs <= 8 guard: vLLM profiles and captures CUDA graphs with a
    # large dummy batch (hundreds-thousands of synthetic sequences) before
    # serving anything real -- materializing a dense [num_logits, vocab_size]
    # probability tensor for THAT batch size is what actually OOM'd here
    # first (Qwen3-8B's 151936-wide vocab x a huge warmup num_logits, on top
    # of the KV cache already reserved at 85% GPU utilization). Real serving
    # in this campaign is always exactly 1 request (fresh-server-per-
    # measurement), so this mirrors relaxation_trace.py's own
    # `_MAX_REAL_BATCH = 8` warmup filter exactly -- not a new convention.
    # Skipping this on a warmup pass means defer_mask stays None there,
    # which is harmless: warmup output is never served to a real client.
    defer_mask: torch.Tensor | None = None
    if has_draft_logits and num_reqs <= 8:
        # Clamp before gathering: expanded_idx_mapping/expanded_local_pos
        # cover the FULL flattened num_logits space, which includes
        # positions with no real draft_logits entry (the bonus-token slot
        # in particular -- expanded_local_pos == num_speculative_steps
        # there, one past draft_logits's own valid step range; see
        # _compute_local_residual_mass_kernel's own
        # `if draft_step_idx == 0 or draft_step_idx >= num_speculative_steps:
        # return` guard for the same boundary, enforced there instead of
        # here). Gathering unclamped raised a real CUDA
        # "index out of bounds" device-side assert. The clamped/wrong
        # values this produces at those positions are never a problem:
        # _rejection_kernel's own accept loop only ever reads
        # defer_mask[start_idx + i] for i in range(num_draft_tokens), which
        # are exactly the real draft positions, never the bonus slot.
        idx_mapping_c = expanded_idx_mapping.clamp(0, draft_logits.shape[0] - 1)
        local_pos_c = expanded_local_pos.clamp(0, draft_logits.shape[1] - 1)
        draft_logits_gathered = draft_logits[idx_mapping_c, local_pos_c][:, :vocab_size]
        target_logits_v = target_logits[:, :vocab_size]
        target_probs = target_logits_v.softmax(dim=-1, dtype=torch.float32)
        draft_probs = draft_logits_gathered.softmax(dim=-1, dtype=torch.float32)

        draft_max = draft_probs.max(dim=-1).values
        target_max = target_probs.max(dim=-1).values
        tv = (target_probs - draft_probs).clamp_min(0.0).sum(dim=-1)
        defer_spec_casc_opt = draft_max < (target_max - _SPEC_CASC_ALPHA * tv)

        _eps = 1e-12
        m = 0.5 * (target_probs + draft_probs)
        log_m = torch.log(m.clamp_min(_eps))
        kl_pm = (target_probs * (torch.log(target_probs.clamp_min(_eps)) - log_m)).sum(dim=-1)
        kl_qm = (draft_probs * (torch.log(draft_probs.clamp_min(_eps)) - log_m)).sum(dim=-1)
        jsd = (0.5 * kl_pm + 0.5 * kl_qm).clamp_min(0.0)
        defer_r_fuzzy = jsd >= _R_FUZZY_ALPHA

        defer_mask = (defer_spec_casc_opt & defer_r_fuzzy).contiguous()

        # spec-casc-tok: A = {v: p(v) >= (1-alpha)*max(p)}, eta = 1 -
        # sum_{v in A} q(v). Reuses target_probs/draft_probs already
        # materialized above -- no extra gather needed. alpha is whichever
        # of plain spec-casc-tok / spec-casc-tok-hsr-guard is actually
        # active (mutually exclusive, both default -inf) -- see the
        # _SPEC_CASC_TOK_HSR_GUARD_ALPHA module comment.
        _effective_casc_tok_alpha = max(_SPEC_CASC_TOK_ALPHA, _SPEC_CASC_TOK_HSR_GUARD_ALPHA)
        casc_tok_top1 = target_probs.max(dim=-1).values
        in_top_set = target_probs >= (1.0 - _effective_casc_tok_alpha) * casc_tok_top1.unsqueeze(-1)

        # HSR GUARD actuator: force the trusted top set A EMPTY for however
        # many of THIS round's own leading draft positions (request 0 only)
        # are still owed strict verification, per the model-runner's own
        # tracker (see _HSR_REMAINING_FILE's module comment). Only consulted
        # when hsr-guard is actually the active method for this server --
        # harmless to skip otherwise, and skipping avoids a stray nonzero
        # remaining-file value (e.g. left over from a prior hsr-guard run on
        # this same box) silently affecting a DIFFERENT method's own
        # spec-casc-tok block.
        #
        # BUG FIXED 2026-08-23 (found via live debug logging in
        # model_runner.py after a radical-parameter test came back
        # bit-identical to baseline despite the tracker firing 1364/6350
        # times): this used to gate on `_SPEC_CASC_TOK_HSR_GUARD_ALPHA >
        # _SPEC_CASC_TOK_ALPHA` -- i.e. "did hsr-guard's own alpha win the
        # max() above" -- but a TIE also wins max(), and every hsr-guard run
        # in this whole investigation (this session's Qwen3-8B port AND the
        # original GPT-OSS-20B calibration work it was ported from) passes
        # --spec-casc-tok-alpha and --spec-casc-tok-hsr-guard-alpha as the
        # SAME value (0.3 == 0.3, matching analysis/semantic_guard's own
        # documented reproduce command) -- so the strict `>` was always
        # False and the actuator NEVER actually applied, regardless of
        # whether the tracker triggered. The correct check for "is hsr-guard
        # the active method" is whether its own alpha file was even
        # readable/finite -- exactly what model_runner.py's own
        # _hsr_guard_is_active() already checks; mirrored here instead of
        # reusing the unrelated max()-tiebreak comparison.
        #
        # Implementation: rather than a new kernel parameter, override
        # casc_tok_top1 to +inf at guarded rows. The kernel's own
        # from-scratch membership recheck (`p_x >= (1-alpha)*top1`) can then
        # never be true for any finite p_x, so x_in_top_set is forced False
        # there with zero kernel changes -- and eta is already correctly
        # recomputed below from the SAME masked in_top_set, so pi_rej_x
        # reduces to exactly p_x (eta=1, no += q_x term) at those rows,
        # i.e. exactly the alpha=-inf strict limit, matching
        # spec-casc-tok-semantic-guard's own override mechanism in the V1
        # patch this is ported from.
        hsr_remaining_before = 0
        if _SPEC_CASC_TOK_HSR_GUARD_ALPHA > float("-inf"):
            hsr_remaining_before = _hsr_read_remaining()
            if _HSR_LIVE_DEBUG_ENABLED and hsr_remaining_before > 0:
                print(f"[HSR ACTUATOR DEBUG] read remaining={hsr_remaining_before} "
                      f"idx_mapping_c={idx_mapping_c.tolist()} local_pos_c={local_pos_c.tolist()}",
                      file=sys.stderr, flush=True)
            if hsr_remaining_before > 0:
                # BUG FIXED 2026-08-23 (found via live debug prints showing
                # idx_mapping_c=[466, 466, ...] -- never 0 -- so this mask
                # was unconditionally all-False): idx_mapping_c is a row
                # index INTO draft_logits (`idx_mapping_c =
                # expanded_idx_mapping.clamp(0, draft_logits.shape[0] - 1)`
                # above), i.e. "which request-block this position's data
                # comes from" -- NOT a 0-based request-id. For a single real
                # request its value is whatever persistent slot vLLM
                # assigned it (466 in the observed case), never necessarily
                # literal 0. Compare against idx_mapping_c[0] (this
                # request's own actual id) instead -- correct under this
                # whole system's documented single-real-request-per-process
                # invariant (every position in a real decode round belongs
                # to the same one request, so this reduces to a pure
                # local_pos_c comparison in practice, exactly as intended).
                hsr_guard_mask = (idx_mapping_c == idx_mapping_c[0]) & (local_pos_c < hsr_remaining_before)
                if _HSR_LIVE_DEBUG_ENABLED:
                    print(f"[HSR ACTUATOR DEBUG] mask={hsr_guard_mask.tolist()} any={bool(hsr_guard_mask.any())}",
                          file=sys.stderr, flush=True)
                if bool(hsr_guard_mask.any()):
                    in_top_set = in_top_set & ~hsr_guard_mask.unsqueeze(-1)
                    casc_tok_top1 = torch.where(hsr_guard_mask, float("inf"), casc_tok_top1)

        casc_tok_eta = (1.0 - (draft_probs * in_top_set).sum(dim=-1)).contiguous()
        casc_tok_top1 = casc_tok_top1.contiguous()
    else:
        casc_tok_top1 = None
        casc_tok_eta = None
        hsr_remaining_before = 0
        _effective_casc_tok_alpha = max(_SPEC_CASC_TOK_ALPHA, _SPEC_CASC_TOK_HSR_GUARD_ALPHA)

    _rejection_kernel[(num_reqs,)](
        sampled,
        sampled.stride(0),
        num_sampled,
        target_rejected_logsumexp,
        draft_rejected_logsumexp,
        target_logits,
        target_logits.stride(0),
        target_local_argmax,
        target_local_argmax.stride(0),
        target_local_max,
        target_local_max.stride(0),
        target_local_sumexp,
        target_local_sumexp.stride(0),
        draft_sampled,
        draft_logits,
        draft_logits_stride_0,
        draft_logits_stride_1,
        draft_local_max,
        draft_local_max.stride(0),
        draft_local_sumexp,
        draft_local_sumexp.stride(0),
        cu_num_logits,
        idx_mapping,
        temperature,
        seed,
        pos,
        synthetic_conditional_rates,
        cumulative_log_p,
        local_residual_mass,
        local_residual_mass.stride(0) if local_residual_mass is not None else 0,
        _CACTUS_ALPHA,
        _effective_casc_tok_alpha,
        _MENTORED_DEC_LOG_LAM,
        defer_mask,
        casc_tok_top1,
        casc_tok_eta,
        vocab_num_blocks,
        PADDED_VOCAB_NUM_BLOCKS=padded_vocab_num_blocks,
        HAS_DRAFT_LOGITS=has_draft_logits,
        HAS_DEFER_MASK=defer_mask is not None,
        HAS_CASC_TOK=casc_tok_top1 is not None,
        SYNTHETIC_MODE=synthetic_conditional_rates is not None,
        USE_BLOCK_VERIFICATION=use_block_verification,
        num_warps=1,
    )

    # HSR GUARD: decrement the remaining-strict-window budget by however
    # many of request 0's own draft positions this round actually walked
    # (num_sampled[0], the kernel's own per-request commit count -- a safe,
    # slightly coarser stand-in for V1's own "positions the accept/reject
    # walk actually reached" count: never decrements by more than what was
    # genuinely guarded this round, since it's clamped against
    # hsr_remaining_before below, so this can only make the guard stay
    # active for a token or two longer than V1's exact semantics would,
    # never shorter/incorrectly-early -- consistent with this whole
    # method's own "imprecise trigger, safe actuator" design). Write only
    # when hsr-guard is actually the active method (mirrors the read gate
    # above) -- a strict/other-method server must never touch this file.
    if hsr_remaining_before > 0:
        _hsr_walked = min(hsr_remaining_before, int(num_sampled[0].item()))
        _hsr_write_remaining(hsr_remaining_before - _hsr_walked)

    # Resample the rejected/bonus tokens.
    RESAMPLE_BLOCK_SIZE = 1024
    resample_num_blocks = triton.cdiv(vocab_size, RESAMPLE_BLOCK_SIZE)
    padded_resample_num_blocks = triton.next_power_of_2(resample_num_blocks)
    resampled_local_argmax = target_logits.new_empty(
        num_reqs, resample_num_blocks, dtype=torch.int64
    )
    resampled_local_max = target_logits.new_empty(
        num_reqs,
        resample_num_blocks,
        dtype=torch.float64 if use_fp64 else torch.float32,
    )
    _resample_kernel[(num_reqs, resample_num_blocks)](
        resampled_local_argmax,
        resampled_local_argmax.stride(0),
        resampled_local_max,
        resampled_local_max.stride(0),
        target_logits,
        target_logits.stride(0),
        target_rejected_logsumexp,
        draft_logits,
        draft_logits_stride_0,
        draft_logits_stride_1,
        draft_rejected_logsumexp,
        num_sampled,
        cu_num_logits,
        expanded_idx_mapping,
        draft_sampled,
        temperature,
        seed,
        pos,
        cumulative_log_p,
        vocab_size,
        BLOCK_SIZE=RESAMPLE_BLOCK_SIZE,
        HAS_DRAFT_LOGITS=has_draft_logits,
        USE_FP64=use_fp64,
        USE_BLOCK_VERIFICATION=use_block_verification,
    )

    # Insert the resampled tokens into the output sampled.
    _insert_resampled_kernel[(num_reqs,)](
        sampled,
        sampled.stride(0),
        num_sampled,
        resampled_local_argmax,
        resampled_local_argmax.stride(0),
        resampled_local_max,
        resampled_local_max.stride(0),
        resample_num_blocks,
        cu_num_logits,
        expanded_idx_mapping,
        temperature,
        PADDED_RESAMPLE_NUM_BLOCKS=padded_resample_num_blocks,
    )
    return sampled, num_sampled
