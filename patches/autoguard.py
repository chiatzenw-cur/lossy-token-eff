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
ACTIVE STRATEGY -- iteration 6: iter4 (wide K=8 window + stuck-run
full-strict backstop) with the backstop threshold pulled in to 14000.
======================================================================

Current best is iter4 (wide K=8 window + >24000 backstop): 12626 vs 13364
baseline (-5.5%, acc 6/8, fire 0.347).

History: iter1 (ungated wide K=8 window) 13056 (-2.3%). iter2 (len>6000
gate) and iter3 (narrow marker set) both regressed -- the gate suppressed
case_002's beneficial early window; narrowing broke case_002/case_006
accuracy. iter5 (K=12 window) regressed to 15117: it RESCUED case_003 for
the first time (32768-cap-wrong -> 18738-correct) but destabilised two
healthy runs (case_002, case_007 -> the cap). Lesson: case_003 is fixable,
but only with strict coverage through its dense-marker early region -- and
K=12 windows are too long for the healthy trajectories.

Iteration 6 keeps K=8 (safe for the healthy runs) and instead lowers the
backstop from 24000 to 14000, so a run that is long AND has still not
opened its harmony ``final`` channel (token 17196 absent) gets forced
fully strict ~10000 tokens earlier. This targets case_003's early region
without lengthening any window. The healthy long case, case_002, opens its
final channel at ~13688 committed tokens in iter4 -- before 14000 -- so it
still never trips the backstop; every shorter healthy case is far below
the threshold. Full strict is provably lossless (all-True === strict), so
even a mistimed trip cannot cost accuracy. Measured against iter4's 12626.

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
