#!/usr/bin/env python3
"""Joins a run's hidden_states.bin (patches/hidden_state_trace.py's binary
capture) against its proposals.jsonl (relaxation_trace.py), and computes
the recurrence signals patches/hidden_state_trace.py exists to support:
single-state cosine similarity and k-step trajectory-recurrence similarity
against all earlier committed positions.

Round-key offset: hidden_states.bin's round 0 is the PROMPT'S OWN prefill
forward pass (one giant "round" the size of the prompt, never a real verify
round -- see patches/hidden_state_trace.py's own module docstring), so
proposals.jsonl's round N joins against hidden_states.bin's round N+1.
Verified empirically (not just assumed) on a real run: every proposals.jsonl
row's (round+1, pos_in_round) has a matching hidden-state row, zero missing,
before this offset was trusted for real analysis.

Only COMMITTED positions (accepted_draft, recovered -- same convention as
count_relaxed_only_hesitation.py and the window-entropy guard) get a
recurrence score computed against; hidden_states.bin also carries rows for
never-reached positions in a round (the whole padded draft block was
forward-passed regardless of where the round's own accept/reject walk
stopped), which are skipped here rather than scored.

Usage:
    python3 analysis/semantic_guard/join_hidden_states.py \\
        --run-dir runs/semantic_guard_pilot/aime24/case_005/seed_0/rFuzzy0p3 \\
        --out analysis/semantic_guard/results/case_005_hidden_recurrence.jsonl
"""

from __future__ import annotations

import argparse
import json
import pathlib
import struct
from typing import Any

import numpy as np

_ROW_HEADER = struct.Struct("<IH")
_PROJECTION_DIM = 128
_ROW_SIZE = _ROW_HEADER.size + _PROJECTION_DIM * 2  # float16


def load_hidden_states(path: pathlib.Path) -> dict[tuple[int, int], np.ndarray]:
    """{(round, pos_in_round): unit-normalized [128] float32 vector},
    round 0 (prefill) included as-is -- caller applies the +1 offset."""
    data = path.read_bytes()
    if len(data) % _ROW_SIZE != 0:
        raise ValueError(f"{path}: size {len(data)} is not a multiple of row size {_ROW_SIZE}")
    out: dict[tuple[int, int], np.ndarray] = {}
    for off in range(0, len(data), _ROW_SIZE):
        rnd, pos = _ROW_HEADER.unpack(data[off : off + _ROW_HEADER.size])
        vec = np.frombuffer(data[off + _ROW_HEADER.size : off + _ROW_SIZE], dtype=np.float16).astype(np.float32)
        out[(rnd, pos)] = vec
    return out


def load_committed_rows(proposals_path: pathlib.Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in proposals_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows.sort(key=lambda r: r["output_position"])
    return [r for r in rows if r["emission_source"] in ("accepted_draft", "recovered")]


def build_sequence(
    committed: list[dict[str, Any]], hidden: dict[tuple[int, int], np.ndarray]
) -> tuple[list[dict[str, Any]], np.ndarray]:
    """Returns (rows actually matched, [n, 128] float32 vectors in emission
    order) -- rows with no hidden-state match (shouldn't happen on a clean
    run; see module docstring's validation note) are dropped, not silently
    padded, so a join gap is visible in the returned count rather than
    hidden inside a garbage vector."""
    matched_rows = []
    vecs = []
    for row in committed:
        key = (row["round"] + 1, row["pos_in_round"])
        vec = hidden.get(key)
        if vec is None:
            continue
        matched_rows.append(row)
        vecs.append(vec)
    return matched_rows, np.stack(vecs) if vecs else np.zeros((0, _PROJECTION_DIM), dtype=np.float32)


def recurrence_scores(vecs: np.ndarray, min_gap: int, k_values: tuple[int, ...]) -> dict[int, np.ndarray]:
    """For each k in k_values, S_k(t) = max over j < t - min_gap of the mean
    cosine similarity across the trailing k positions ending at t and j
    respectively (k=1 is plain single-state recurrence). vecs are already
    L2-normalized (see hidden_state_trace.py), so cosine similarity is a
    plain dot product. O(n^2), fine for a single run's length (tens of
    thousands of positions is still a sub-second matmul); not meant to run
    across a full sweep as-is.
    """
    n = vecs.shape[0]
    sims = vecs @ vecs.T  # [n, n] pairwise cosine similarity
    out: dict[int, np.ndarray] = {}
    for k in k_values:
        if n <= k:
            out[k] = np.full(n, np.nan)
            continue
        # trailing-k-mean similarity between window ending at t and window
        # ending at j: average of sims[t-r, j-r] for r in 0..k-1. For fixed
        # r, sims[t-r, j-r] as a function of (t, j) is sims itself SHIFTED
        # down-and-right by r -- i.e. the source is sims[:n-r, :n-r] (starts
        # at 0) and the destination is k_sim[r:, r:] (starts at r), not
        # sims[r:, r:] added into k_sim[r:, r:] (that adds sims[t, j] back
        # onto itself at the same (t, j) for every r, which silently
        # collapses k_mean to plain sims regardless of k -- caught by a
        # standalone numeric check against a hand-computed value, since
        # every k gave bit-identical scores where they clearly shouldn't
        # have).
        k_sim = np.zeros((n, n))
        count = np.zeros((n, n))
        for r in range(k):
            if r == 0:
                k_sim += sims
                count += 1
            else:
                k_sim[r:, r:] += sims[: n - r, : n - r]
                count[r:, r:] += 1
        k_mean = np.divide(k_sim, count, out=np.full_like(k_sim, np.nan), where=count > 0)
        scores = np.full(n, np.nan)
        for t in range(n):
            j_max = t - min_gap
            if j_max <= 0:
                continue
            scores[t] = np.nanmax(k_mean[t, :j_max])
        out[k] = scores
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run-dir", type=pathlib.Path, required=True, help="e.g. runs/.../case_XXX/seed_0/<tag>")
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--min-gap", type=int, default=32, help="Exclude the trailing D positions from the recurrence search (D in the design doc).")
    parser.add_argument("--k", type=int, nargs="+", default=[1, 4, 8, 16], help="Trajectory-recurrence window sizes S_k.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    hidden_path = args.run_dir / "hidden_states.bin"
    proposals_path = args.run_dir / "proposals.jsonl"
    if not hidden_path.is_file():
        print(f"no hidden_states.bin under {args.run_dir} -- was capture enabled for this run?")
        return 1

    hidden = load_hidden_states(hidden_path)
    committed = load_committed_rows(proposals_path)
    matched_rows, vecs = build_sequence(committed, hidden)
    print(f"{len(committed)} committed rows, {len(matched_rows)} matched to a hidden-state vector ({len(committed) - len(matched_rows)} unmatched)")

    scores = recurrence_scores(vecs, min_gap=args.min_gap, k_values=tuple(args.k))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for i, row in enumerate(matched_rows):
            out_row = {
                "case": args.run_dir.parent.parent.name,
                "tag": args.run_dir.name,
                "round": row["round"],
                "pos_in_round": row["pos_in_round"],
                "output_position": row["output_position"],
                "draft_token_text": row.get("draft_token_text"),
                "emitted_token_text": row.get("emitted_token_text"),
                "emission_source": row["emission_source"],
                "strict_would_accept": row.get("strict_would_accept"),
                "lossy_would_accept": row.get("lossy_would_accept"),
                "lossy_only_accepted": row.get("lossy_only_accepted"),
                **{f"S{k}": (None if np.isnan(scores[k][i]) else round(float(scores[k][i]), 5)) for k in args.k},
            }
            handle.write(json.dumps(out_row, ensure_ascii=False) + "\n")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
