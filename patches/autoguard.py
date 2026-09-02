"""autoguard.decide() -- the ONE file the autoresearch loop edits.

Installed by ``patches/apply.sh spec-casc-tok-autoguard`` to
``<venv>/lib/pythonX/site-packages/vllm/v1/sample/autoguard.py`` (plain cp,
like ``relaxation_trace.py``). Imported by the frozen
``vllm-0.26.0-spec-casc-tok-autoguard.patch`` (a thin delegator that is a
verbatim copy of the ``spec-casc-tok-semantic-guard`` patch with the
hard-coded hesitation-marker id list swapped for a call into ``decide()``).

======================================================================
CONTRACT  (the frozen wrapper ``_autoguard_mask`` in rejection_sampler.py
           enforces all of this -- a broken decide() degrades to a no-op
           mask, i.e. plain spec_casc_tok, it never crashes the server)
======================================================================

decide() is called ONCE PER VERIFICATION ROUND, in plain PyTorch, on the
GPU, BEFORE that round's accept/reject kernel runs. It returns a boolean
tensor of shape ``[num_tokens]`` (one entry per drafted position, flattened
over the batch; this repo serves exactly one real request per server, so in
practice positions ``0 .. num_draft_tokens[0]-1`` are request 0's draft
block). ``True`` at a position => that position is verified with the
LOSSLESS rule this round (spec_casc_tok's trusted top set is forced empty
there, which is provably identical to running its own alpha=-inf strict
limit at that row alone). ``False`` => plain spec_casc_tok behaviour,
unchanged.

An all-False return === plain ``spec_casc_tok`` (the baseline this whole
setup is measured against). An all-True return === lossless ``strict``.
The research question is which *sparse, well-targeted* mask cuts completion
length without losing accuracy.

Arguments (all keyword-only):

    round_index : int
        0 on the first verification round of the generation, +1 each round.
    committed_token_ids : list[int]
        Every token committed so far for request 0, oldest-first (capped at
        the last 40000). This is the generated text as ids -- decode / scan
        it for repetition, channel markers, hesitation words, etc. It does
        NOT include this round's draft.
    draft_token_ids : torch.Tensor  [num_tokens] int
        This round's proposed tokens.
    draft_probs : torch.Tensor  [num_tokens, vocab] float32
        Drafter distribution q for each drafted position.
    target_probs : torch.Tensor  [num_tokens, vocab] float32
        Verifier distribution p for each drafted position (softmax of the
        target logits -- the real thing the lossless test uses).
    num_draft_tokens : list[int]
        Per-request draft counts. ``num_draft_tokens[0]`` is request 0's.
    vocab_size : int

Must return: torch.Tensor, shape ``[num_tokens]``, coercible to bool. Any
other shape, a raised exception, or a non-tensor => treated as all-False
(logged once to stderr).

Keep it cheap: this runs on the hot path every round. Vectorised torch ops
over the ``[num_tokens, vocab]`` tensors are fine; a python loop over the
vocab is not. No file I/O, no new imports beyond torch / stdlib.

======================================================================
ACTIVE STRATEGY -- iteration 7: iter6 + a CLUSTER gate on the window
trigger (a marker arms a window only when it is part of a marker cluster).
======================================================================

Current best is iter6 (wide K=8 window + >14000 full-strict backstop):
12062 vs 13364 baseline (-9.7%, acc 6/8, fire 0.452). Its residual cost is
the tax the window still puts on the already-short healthy cases:
case_008 1250 -> 3923, case_007 5206 -> 6947, case_001 1551 -> 2051
(~+5200 tokens spread over the 8 = ~+650 on the mean). That tax is
isolated wide-set connectives ("so" / "now" / "thus") firing windows in
healthy prose (analysis Direction A: forcing strict at such a token can
swap the word and trigger *more* hedging).

iter3 removing the connectives from the set entirely broke case_002 and
case_006 accuracy -- they are load-bearing *inside the spirals*. iter7
keeps the wide set but gates the TRIGGER: a marker only (re)arms a
K-window when there are at least _CLUSTER_MIN markers within the last
_CLUSTER_WIN committed/drafted tokens -- i.e. the trajectory is in a
hesitation cluster, not just using one connective in a normal step. The
spiraling cases (case_002/003/004 sit at ~35 markers / 1000 tokens
throughout) keep their windows; isolated markers in short healthy runs
(case_007 tails off to ~5-13 / 1000) stop arming. Backstop and K=8
unchanged. Measured against iter6's 12062; revert on any accuracy loss.

History: iter1 (ungated wide K=8 window) 13056 (-2.3%). iter2 (len>6000
gate) and iter3 (narrow marker set) both regressed. iter4 added the
full-strict stuck-run backstop at 24000 -> 12626. iter5 (K=12 window)
regressed to 15117 but RESCUED case_003 once (32768-cap-wrong ->
18738-correct) at the cost of case_002/007 -> the cap. iter6 pulled the
backstop in to 14000 (case_004 27024 -> 22516) -> 12062. case_003's
non-termination is the model's own reasoning not converging on a hard
combinatorics problem, not drafter pull -- neither full strict (iter4/6)
nor a mask can fix it; only iter5's K=12 perturbation did, unreliably.

Underlying window mechanism (unchanged from iter 1): port of
``spec_casc_tok_semantic_guard_future_guard`` (K=8, the best result in
analysis/semantic_guard/: -1.4% mean length on 30-case AIME24 at 25/30 vs
26/30 baseline). It leaves an accepted hesitation/discourse marker's OWN
verification untouched and forces strict on the K drafted positions that
FOLLOW it, on the theory (analysis SUMMARY.md sec 5) that the length
blow-up is a round-count effect: the drafter rides a marker into a
self-correction / restart cascade, and a short forced-strict window right
after the marker lets the trusted model settle the trajectory before the
relaxed rule resumes.

The window state (`strict_remaining`, 0..K) is reconstructed from
``committed_token_ids`` every round rather than carried in a module global:
walking the committed tail is exact for the cross-round hand-off (a marker
older than K committed tokens has already counted down to 0) and cannot
accumulate drift. Within the current round the countdown steps over the
drafted ids (an approximation -- the frozen kernel steps over
accepted/first-rejected positions and stops at the first rejection -- but
spec_casc_tok accepts the large majority of drafted tokens, and any error
is re-corrected from committed ground truth on the very next round).
"""

from __future__ import annotations

import torch

# Wider marker / discourse-connective set -- identical to the frozen
# spec_casc_tok_semantic_guard_future_guard patch's own _SEMANTIC_GUARD_TOKEN_IDS
# (itself lifted from r_fuzzy_semantic_guard_v2). Grouped comments are the
# surface words each id block encodes for gpt-oss-20b's tokenizer.
_MARKER_IDS = frozenset((
    29126, 17114, 5238, 24305,       # wait
    112576, 186402, 165972,          # hmm
    138925, 87471, 4771, 50557,      # actually
    8293, 7943, 889, 3072,           # but
    58369, 35717, 41021,             # let's
    84787, 23586,                    # thus
    2167, 1416,                      # we
    5808, 2632,                      # so
    10620, 6549,                     # now
    12845,                           # let (sentence-initial only)
    56734, 45438,                    # compute
    151907, 65037,                   # similarly
    55292, 38966,                    # define
    3879, 7217,                      # from
))
_K = 8

# Stuck-run backstop: harmony bare "final" token (the one that follows
# <|channel|>), and the committed-length past which a run that has still not
# opened its final channel is treated as non-terminating and forced fully
# strict. All-True is provably lossless (=== strict), so this is
# accuracy-safe by construction.
_FINAL_TOKEN = 17196
_BACKSTOP_LEN = 14000

# Cluster gate: a marker only (re)arms a K-window when at least _CLUSTER_MIN
# markers fall within the last _CLUSTER_WIN tokens -- suppresses windows
# from isolated discourse connectives in healthy prose while leaving the
# marker-dense spirals fully guarded.
_CLUSTER_WIN = 32
_CLUSTER_MIN = 2


def _window_remaining_at_round_start(
    committed_token_ids: list[int], cluster_active: bool
) -> int:
    """Reconstruct the future-guard window counter (0..K) as it stands at
    the start of this round, from committed history alone. Only the last K
    committed tokens can matter: a marker older than that has already
    counted all the way down. Markers only arm while cluster_active."""
    tail = committed_token_ids[-_K:]
    remaining = 0
    for tok in tail:
        if tok in _MARKER_IDS and cluster_active:
            remaining = _K
        elif remaining > 0:
            remaining -= 1
    return remaining


def decide(
    *,
    round_index: int,
    committed_token_ids: list[int],
    draft_token_ids: torch.Tensor,
    draft_probs: torch.Tensor,
    target_probs: torch.Tensor,
    num_draft_tokens: list[int],
    vocab_size: int,
) -> torch.Tensor:
    n = int(draft_token_ids.shape[0])
    if n == 0:
        return torch.zeros(0, dtype=torch.bool, device=draft_token_ids.device)

    # Stuck-run backstop: a long run that has never opened its final channel
    # is non-terminating -- force the whole block strict (lossless).
    if (
        len(committed_token_ids) > _BACKSTOP_LEN
        and _FINAL_TOKEN not in committed_token_ids
    ):
        return torch.ones(n, dtype=torch.bool, device=draft_token_ids.device)

    # Marker count in the recent context -> is the trajectory in a cluster?
    recent = committed_token_ids[-_CLUSTER_WIN:]
    cluster_count = sum(1 for t in recent if t in _MARKER_IDS)

    remaining = _window_remaining_at_round_start(
        committed_token_ids, cluster_count >= _CLUSTER_MIN
    )
    draft = draft_token_ids.tolist()
    flags = [False] * n
    dc = cluster_count
    for j in range(n):
        flags[j] = remaining > 0
        if draft[j] in _MARKER_IDS:
            dc += 1
            if dc >= _CLUSTER_MIN:
                remaining = _K
            elif remaining > 0:
                remaining -= 1
        elif remaining > 0:
            remaining -= 1
    return torch.tensor(flags, dtype=torch.bool, device=draft_token_ids.device)


# ======================================================================
# REFERENCE STRATEGIES  (not active -- copy logic into decide() to use)
#
# These are starting points, deliberately simple, each targeting one of the
# failure shapes analysis/semantic_guard/ documents. None has been tuned.
# ======================================================================
#
# --- A. entropy spike: force strict where the verifier itself is very
#        uncertain about the drafted token (low p(x)) AND the drafter is
#        confident (high q(x)) -- the drafter pulling the trajectory
#        somewhere the target would not have gone.
#
#     px = target_probs.gather(1, draft_token_ids.long().unsqueeze(1)).squeeze(1)
#     qx = draft_probs.gather(1, draft_token_ids.long().unsqueeze(1)).squeeze(1)
#     return (px < 0.05) & (qx > 0.5)
#
# --- B. length budget: once the generation is already long (a proxy for
#        "this run is inflating"), tighten to lossless for the rest of it.
#
#     if len(committed_token_ids) > 12000:
#         return torch.ones_like(draft_token_ids, dtype=torch.bool)
#     return torch.zeros_like(draft_token_ids, dtype=torch.bool)
#
# --- C. recent-token repetition: if the last N committed tokens contain a
#        short exact cycle, force strict on any drafted token that would
#        extend it.
#
#     tail = committed_token_ids[-64:]
#     cyc = set()
#     for period in range(1, 13):
#         if len(tail) > 2 * period and tail[-period:] == tail[-2 * period:-period]:
#             cyc.update(tail[-period:])
#     if not cyc:
#         return torch.zeros_like(draft_token_ids, dtype=torch.bool)
#     bad = torch.tensor(sorted(cyc), device=draft_token_ids.device, dtype=draft_token_ids.dtype)
#     return torch.isin(draft_token_ids, bad)
