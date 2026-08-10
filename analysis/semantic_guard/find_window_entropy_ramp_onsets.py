#!/usr/bin/env python3
"""Applies the window-entropy guard's exact trigger condition -- mean(w64) <
mean(w32) < mean(w16) < mean(w8), jointly for target and draft entropy,
over the trailing committed tokens -- to PLAIN, UNGUARDED r_fuzzy traces,
and saves every place the condition first starts holding (an "onset
candidate") with enough surrounding text to judge by eye whether it's
actually the start of a repetition/loop.

Deliberately run against the UNGUARDED trajectory, not a guarded one: the
guard's whole purpose is to prevent whatever would have happened next, so
checking "did a loop start here" against a run where the guard already
intervened is confounded by the intervention itself. This script asks the
question the guard's design assumes an answer to, directly: on a real,
unaltered r_fuzzy trajectory, does mean(w64)<mean(w32)<mean(w16)<mean(w8)
actually mark the onset of degenerate behaviour, or does it fire on benign
positions too?

Onset EVENTS, not every matching position: the condition, once true, tends
to stay true for many consecutive tokens (entropy environments don't flip
instantly), so this records only the position where a match streak BEGINS
(the previous position did not match), the same "onset" framing repetition-
onset analysis elsewhere uses -- one candidate per apparent episode, not
one per token inside it.

Saves the candidate list FIRST (this script), separately from judging it
(a later, manual pass reading the saved context) -- so the detection step
stays auditable independent of any interpretation of it.

Usage:
    python3 analysis/semantic_guard/find_window_entropy_ramp_onsets.py \\
        --runs-root runs/semantic_guard_pilot/aime24 --tag rFuzzy0p3 \\
        --out analysis/semantic_guard/results/window_entropy_ramp_onsets.jsonl
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from count_relaxed_only_hesitation import decode_piece, get_encoding, load_tokens  # noqa: E402

WINDOW_SIZES = (64, 32, 16, 8)
CONTEXT_CHARS = 400  # before AND after the onset token


def is_monotonic_ramp(history: list[float]) -> bool:
    means = [sum(history[-w:]) / w for w in WINDOW_SIZES]
    return all(means[i] < means[i + 1] for i in range(len(means) - 1))


def window_means(history: list[float]) -> dict[str, float]:
    return {f"w{w}": round(sum(history[-w:]) / w, 5) for w in WINDOW_SIZES}


def _safe_decode(enc, token_id: int | None) -> str | None:
    if token_id is None:
        return None
    try:
        return enc.decode([token_id])
    except Exception:
        return None


def find_onsets_for_run(run_dir: pathlib.Path) -> list[dict[str, Any]]:
    """Single pass: reconstructs text (token-by-token, char-offset-tracked,
    same safe multi-byte handling as count_relaxed_only_hesitation.py) while
    separately tracking entropy history over committed
    (accepted_draft/recovered) tokens, so onset positions and their
    surrounding text come from the exact same walk -- no separate alignment
    pass to get wrong.
    """
    rows = load_tokens(run_dir / "proposals.jsonl")
    enc = get_encoding()

    pieces: list[str] = []
    starts: list[int] = []
    pos = 0
    pending_ids: list[int] = []
    MAX_PENDING = 4

    target_hist: list[float] = []
    draft_hist: list[float] = []
    prev_ramp = False
    onsets: list[dict[str, Any]] = []
    committed_index = 0  # index into target_hist/draft_hist of the CURRENT (just-appended) entry
    current_onset: dict[str, Any] | None = None  # the most recent onset, still being extended

    def flush_lossy() -> None:
        nonlocal pos
        stuck_id = pending_ids.pop(0)
        piece = enc.decode([stuck_id])
        pieces.append(piece)
        starts.append(pos)
        pos += len(piece)

    for row in rows:
        token_id = row.get("emitted_token_id")
        if token_id is None:
            continue
        pending_ids.append(token_id)
        piece = decode_piece(enc, pending_ids)
        if piece is None:
            if len(pending_ids) >= MAX_PENDING:
                flush_lossy()
            continue
        pieces.append(piece)
        starts.append(pos)
        pos += len(piece)
        pending_ids = []

        if row["emission_source"] in ("accepted_draft", "recovered"):
            t_ent = row.get("target_entropy")
            d_ent = row.get("draft_entropy")
            if t_ent is not None and d_ent is not None:
                target_hist.append(t_ent)
                draft_hist.append(d_ent)
                committed_index += 1
                ramp_now = (
                    len(target_hist) >= max(WINDOW_SIZES)
                    and is_monotonic_ramp(target_hist)
                    and is_monotonic_ramp(draft_hist)
                )
                if ramp_now and not prev_ramp:
                    current_onset = {
                        "case": run_dir.parent.parent.name,
                        "tag": run_dir.name,
                        "round": row["round"],
                        "output_position": row["output_position"],
                        "committed_index": committed_index,
                        # Decoded directly here, not read from the trace: these
                        # fields (draft_token_text/emitted_token_text) only exist
                        # in traces collected after relaxation_trace.py grew them,
                        # so relying on the trace would silently go None on any
                        # older run -- decoding independently works regardless of
                        # when the trace was collected.
                        "draft_token_id": row.get("draft_token_id"),
                        "draft_token_text": _safe_decode(enc, row.get("draft_token_id")),
                        "emitted_token_id": row.get("emitted_token_id"),
                        "emitted_token_text": _safe_decode(enc, row.get("emitted_token_id")),
                        "emission_source": row["emission_source"],
                        "target_window_means": window_means(target_hist),
                        "draft_window_means": window_means(draft_hist),
                        "streak_length": 1,
                        "char_offset": pos,  # filled precisely below, after the full pass
                    }
                    onsets.append(current_onset)
                elif ramp_now and prev_ramp and current_onset is not None:
                    current_onset["streak_length"] += 1
                prev_ramp = ramp_now

    while pending_ids:
        flush_lossy()

    full_text = "".join(pieces)
    # char_offset was recorded as `pos` right after emitting the onset
    # token itself (== the token's END offset, i.e. where its own text
    # finishes) -- use it to slice context before/after.
    for onset in onsets:
        end = onset.pop("char_offset")
        start = max(0, end - CONTEXT_CHARS)
        onset["context_before"] = full_text[start:end]
        onset["context_after"] = full_text[end : end + CONTEXT_CHARS]
    return onsets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-root", type=pathlib.Path, required=True)
    parser.add_argument("--tag", default="rFuzzy0p3")
    parser.add_argument("--out", type=pathlib.Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dirs = sorted({p.parent for p in args.runs_root.glob(f"*/seed_*/{args.tag}/proposals.jsonl")})
    if not run_dirs:
        print(f"no {args.tag} traces under {args.runs_root}", file=sys.stderr)
        return 1

    all_onsets: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        onsets = find_onsets_for_run(run_dir)
        print(f"{run_dir.parent.parent.name}: {len(onsets)} onset events", file=sys.stderr)
        all_onsets.extend(onsets)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for onset in all_onsets:
            handle.write(json.dumps(onset, ensure_ascii=False) + "\n")

    print(f"\n{len(run_dirs)} runs, {len(all_onsets)} onset events total -> wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
