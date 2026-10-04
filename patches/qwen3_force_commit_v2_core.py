"""Qwen3 force-commit core for the V2 spec-decode sampler.

Forces the single closing token `</think>` once a request's generated-token count
reaches the threshold without `</think>` having been emitted. Operates on the
processed target logits right before rejection_sample(): a forced row becomes a
one-hot on the closing token, so the drafted token is rejected and recovery emits
the forced token. Once `</think>` is in the request's history the force is a
permanent no-op for that request.
"""

import torch

FORCE_LOGIT = -1e30


def closing_token_id(tokenizer) -> int:
    ids = tokenizer.encode("</think>", add_special_tokens=False)
    if len(ids) != 1:
        raise ValueError(f"'</think>' must be one token for force-commit; got {ids}")
    return ids[0]


def force_commit_rows(
    logits: torch.Tensor,
    expanded_idx_mapping: torch.Tensor,
    expanded_local_pos: torch.Tensor,
    pos: torch.Tensor,
    all_token_ids: torch.Tensor,
    prompt_len: torch.Tensor,
    close_id: int,
    threshold: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Returns (logits, force_mask). The input tensor is returned unchanged when
    nothing is forced; otherwise a modified copy is returned."""
    mask = torch.zeros(logits.shape[0], dtype=torch.bool, device=logits.device)
    out = logits
    for row in (expanded_local_pos == 0).nonzero(as_tuple=True)[0].tolist():
        req = int(expanded_idx_mapping[row])
        p = int(pos[row])
        pl = int(prompt_len[req])
        if p - pl < threshold:
            continue
        if bool((all_token_ids[req, pl:p] == close_id).any()):
            continue
        if out is logits:
            out = logits.clone()
        out[row] = FORCE_LOGIT
        out[row, close_id] = 0.0
        mask[row] = True
    return out, mask
