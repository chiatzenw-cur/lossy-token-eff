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
ACTIVE STRATEGY -- iteration 4: iter1's wide-set future-guard window,
PLUS a stuck-run full-strict backstop.
======================================================================

Iteration 1 (ungated future-guard K=8, wide 38-id set) is the current best:
13056 vs 13364 baseline (-2.3%, acc 6/8, fire 0.267). Iterations 2
(length-gate) and 3 (narrow marker set) both regressed -- the length gate
suppressed case_002's beneficial early window; narrowing the set broke
case_002 and case_006 accuracy (the wide connectives are load-bearing).

The one case iter1 does NOT help is case_003: it stays pinned at the 32768
token cap (finish=length, final channel never opened) in both baseline and
iter1 -- a pure "analysis-channel ramble that never commits to a final
answer" failure. That single case is 32768/8 = 4096 tokens of the mean.

Iteration 4 leaves iter1's window mechanism exactly as-is and adds a
backstop: once the run has emitted more than _BACKSTOP_LEN committed
tokens AND the harmony ``final`` channel has never opened (token 17196
absent from the whole committed history), force strict on the ENTIRE draft
block every round. This is provably lossless (all-True === strict ===
spec_casc_tok's own alpha=-inf limit) so it cannot cost accuracy; it only
fires on genuinely non-terminating rambles, where removing the drafter's
ability to pull the trajectory off the target distribution should let it
collapse toward what the trusted model alone would produce (case_004
already terminated under iter1's window alone: 32768 -> 30466).
_BACKSTOP_LEN = 24000 clears case_002's worst observed length (20070 in
the baseline) with margin, so the healthy long case is never touched.

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
_BACKSTOP_LEN = 24000


def _window_remaining_at_round_start(committed_token_ids: list[int]) -> int:
    """Reconstruct the future-guard window counter (0..K) as it stands at
    the start of this round, from committed history alone. Only the last K
    committed tokens can matter: a marker older than that has already
    counted all the way down."""
    tail = committed_token_ids[-_K:]
    remaining = 0
    for tok in tail:
        if tok in _MARKER_IDS:
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

    remaining = _window_remaining_at_round_start(committed_token_ids)
    draft = draft_token_ids.tolist()
    flags = [False] * n
    for j in range(n):
        flags[j] = remaining > 0
        if draft[j] in _MARKER_IDS:
            remaining = _K
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
