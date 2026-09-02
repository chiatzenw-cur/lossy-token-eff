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
DEFAULT: no-op.  The autoresearch loop's job is to replace the body below.
======================================================================
"""

from __future__ import annotations

import torch


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
    # No-op: every position keeps plain spec_casc_tok verification.
    # Baseline. Replace this with a real guard.
    return torch.zeros_like(draft_token_ids, dtype=torch.bool)


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
