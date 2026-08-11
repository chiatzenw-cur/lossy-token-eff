#!/usr/bin/env python3
"""Marks tokens where the hidden-state recurrence test (join_hidden_states.py's
S_k scores -- cosine similarity of the target's own hidden state against its
best match at least `min_gap` positions earlier, averaged over a trailing
k-step window) thinks a loop is happening, and saves them with full context
-- same "save the candidates first, judge them after" discipline as
find_window_entropy_ramp_onsets.py, for the same reason: keeps detection
auditable independent of any interpretation of it.

Run against PLAIN, UNGUARDED trajectories, same principle as the window-
entropy onset check: a guard's whole purpose is to prevent whatever the
trajectory would otherwise do, so checking "did a loop start here" against
an already-intervened run is circular.

No cross-run calibration (no strict-baseline hidden-state capture exists
yet to calibrate a fixed threshold against, unlike the window-entropy
guard's Q90-from-strict-runs). Threshold is instead PER-RUN and empirical:
the top `--percentile` of that run's own S_k score distribution (default
99th) -- self-calibrating or the correct scale entirely if hidden-state
similarity has a somehow different natural range on a different case, model,
or projection dimension; a fixed absolute cosine-similarity cutoff would
not travel across those the same way.

Onset EVENTS, not every matching position: same streak-collapse as the
window-entropy script, for the same reason (a threshold, once crossed,
tends to stay crossed for consecutive positions).

Usage:
    python3 analysis/semantic_guard/find_hidden_state_recurrence_onsets.py \\
        --runs-root runs/hidden_state_pilot/aime24 --tag rFuzzy0p3 \\
        --k 8 --percentile 99 --min-gap 32 \\
        --out analysis/semantic_guard/results/hidden_state_recurrence_onsets.jsonl
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from count_relaxed_only_hesitation import decode_piece, get_encoding  # noqa: E402
from join_hidden_states import build_sequence, load_committed_rows, load_hidden_states, recurrence_scores  # noqa: E402

CONTEXT_CHARS = 400


def reconstruct_text_with_offsets(run_dir: pathlib.Path) -> tuple[str, dict[int, tuple[int, int]]]:
    """Full completion text plus {output_position: (char_start, char_end)}.
    Same safe buffered multi-byte handling as count_relaxed_only_hesitation.py
    and find_window_entropy_ramp_onsets.py -- duplicated rather than shared
    as a single helper because each caller needs a slightly different
    return shape; kept small and simple rather than over-abstracted for a
    one-off pilot analysis."""
    # load_committed_rows filters to accepted_draft/recovered; for text
    # reconstruction we need EVERY row (bonus tokens are part of the text
    # too), so read proposals.jsonl fresh here rather than reusing it.
    all_rows = [json.loads(line) for line in (run_dir / "proposals.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    all_rows.sort(key=lambda r: r["output_position"])

    enc = get_encoding()
    pieces: list[str] = []
    starts: list[int] = []
    offsets: dict[int, tuple[int, int]] = {}
    pos = 0
    pending_ids: list[int] = []
    pending_output_positions: list[int] = []
    MAX_PENDING = 4

    def flush_lossy() -> None:
        nonlocal pos
        stuck_id = pending_ids.pop(0)
        stuck_out_pos = pending_output_positions.pop(0)
        piece = enc.decode([stuck_id])
        pieces.append(piece)
        starts.append(pos)
        offsets[stuck_out_pos] = (pos, pos + len(piece))
        pos += len(piece)

    for row in all_rows:
        token_id = row.get("emitted_token_id")
        if token_id is None:
            continue
        pending_ids.append(token_id)
        pending_output_positions.append(row["output_position"])
        piece = decode_piece(enc, pending_ids)
        if piece is None:
            if len(pending_ids) >= MAX_PENDING:
                flush_lossy()
            continue
        pieces.append(piece)
        starts.append(pos)
        end = pos + len(piece)
        # Merged multi-token piece: attribute the whole span to the LAST
        # (most recent) output_position in the group, consistent with how
        # onsets are keyed by their own output_position.
        for op in pending_output_positions:
            offsets[op] = (pos, end)
        pos = end
        pending_ids = []
        pending_output_positions = []
    while pending_ids:
        flush_lossy()

    return "".join(pieces), offsets


def find_onsets(
    run_dir: pathlib.Path, k: int, percentile: float, min_gap: int
) -> list[dict[str, Any]]:
    hidden = load_hidden_states(run_dir / "hidden_states.bin")
    committed = load_committed_rows(run_dir / "proposals.jsonl")
    matched_rows, vecs = build_sequence(committed, hidden)
    if len(matched_rows) < 2 * min_gap:
        return []

    scores = recurrence_scores(vecs, min_gap=min_gap, k_values=(k,))[k]
    valid = scores[~np.isnan(scores)]
    if valid.size == 0:
        return []
    threshold = float(np.percentile(valid, percentile))

    flagged = scores >= threshold
    onsets: list[dict[str, Any]] = []
    prev_flagged = False
    current: dict[str, Any] | None = None
    for i, row in enumerate(matched_rows):
        if flagged[i] and not prev_flagged:
            current = {
                "case": run_dir.parent.parent.name,
                "tag": run_dir.name,
                "round": row["round"],
                "pos_in_round": row["pos_in_round"],
                "output_position": row["output_position"],
                "draft_token_text": row.get("draft_token_text"),
                "emitted_token_text": row.get("emitted_token_text"),
                "emission_source": row["emission_source"],
                "strict_would_accept": row.get("strict_would_accept"),
                "lossy_would_accept": row.get("lossy_would_accept"),
                "lossy_only_accepted": row.get("lossy_only_accepted"),
                "target_entropy": row.get("target_entropy"),
                "draft_entropy": row.get("draft_entropy"),
                f"S{k}": round(float(scores[i]), 5),
                "threshold_used": round(threshold, 5),
                "streak_length": 1,
            }
            onsets.append(current)
        elif flagged[i] and prev_flagged and current is not None:
            current["streak_length"] += 1
            current[f"S{k}"] = max(current[f"S{k}"], round(float(scores[i]), 5))
        prev_flagged = bool(flagged[i])

    if onsets:
        text, offsets = reconstruct_text_with_offsets(run_dir)
        for onset in onsets:
            span = offsets.get(onset["output_position"])
            if span is None:
                onset["context_before"] = None
                onset["context_after"] = None
                continue
            _, end = span
            start = max(0, end - CONTEXT_CHARS)
            onset["context_before"] = text[start:end]
            onset["context_after"] = text[end : end + CONTEXT_CHARS]

    return onsets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-root", type=pathlib.Path, required=True)
    parser.add_argument("--tag", default="rFuzzy0p3")
    parser.add_argument("--k", type=int, default=8, help="Trajectory window size (S_k) to threshold on.")
    parser.add_argument("--percentile", type=float, default=99.0, help="Per-run empirical percentile cutoff.")
    parser.add_argument("--min-gap", type=int, default=32, help="Exclude the trailing D positions from the recurrence search.")
    parser.add_argument("--out", type=pathlib.Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dirs = sorted({p.parent for p in args.runs_root.glob(f"*/seed_*/{args.tag}/hidden_states.bin")})
    if not run_dirs:
        print(f"no {args.tag} runs with hidden_states.bin under {args.runs_root}", file=sys.stderr)
        return 1

    all_onsets: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        onsets = find_onsets(run_dir, k=args.k, percentile=args.percentile, min_gap=args.min_gap)
        print(f"{run_dir.parent.parent.name}: {len(onsets)} onset events (S{args.k} >= P{args.percentile})", file=sys.stderr)
        all_onsets.extend(onsets)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for onset in all_onsets:
            handle.write(json.dumps(onset, ensure_ascii=False) + "\n")

    streak_lengths = [o["streak_length"] for o in all_onsets]
    print(f"\n{len(run_dirs)} runs, {len(all_onsets)} onset events total -> wrote {args.out}")
    if streak_lengths:
        print(f"streak length: mode={max(set(streak_lengths), key=streak_lengths.count)} max={max(streak_lengths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
