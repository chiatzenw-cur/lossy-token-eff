#!/usr/bin/env python3
"""Phase C of the single-event counterfactual experiment: compares each
counterfactual continuation (Phase B: one earlier lossy-only-accept flipped
to what strict actually produced, then resumed under r_fuzzy) against the
ORIGINAL run's own factual continuation from the same intervention point --
the "did nothing" control, already paid for, free to reuse.

Reports, per case, per seed:
  - the counterfactual's generated text (first ~CONTEXT_CHARS chars, plus
    a window around where the original onset would have landed)
  - the original factual continuation over the same token-count span
  - a crude repetition/degeneracy proxy (distinct-trigram ratio) as a cheap
    quantitative complement to manual reading -- NOT a substitute for it;
    this whole experiment is n=3 (or n=6 counting seed repeats), read the
    actual text.

Usage:
    python3 analysis/semantic_guard/compare_counterfactual_continuation.py
"""

from __future__ import annotations

import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "analysis" / "semantic_guard"))
from count_relaxed_only_hesitation import decode_piece, get_encoding  # noqa: E402

CONTINUATION_RUNS_ROOT = REPO_ROOT / "runs" / "counterfactual_continuation"
MANIFEST_PATH = REPO_ROOT / "analysis" / "semantic_guard" / "results" / "counterfactual_continuation_manifest.json"
SEEDS = (0, 1)
DISPLAY_CHARS = 1500


def reconstruct_original_continuation(run_dir: pathlib.Path, from_output_position: int, n_tokens: int) -> str:
    """Decoded text of the original run's own tokens starting at
    from_output_position (the intervention point, inclusive -- i.e. what
    ACTUALLY happened there and after), for up to n_tokens committed
    positions."""
    rows = [json.loads(line) for line in (run_dir / "proposals.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    rows.sort(key=lambda r: r["output_position"])
    rows = [r for r in rows if r["output_position"] >= from_output_position][:n_tokens]

    enc = get_encoding()
    pieces: list[str] = []
    pending_ids: list[int] = []
    MAX_PENDING = 4

    def flush_lossy() -> None:
        stuck_id = pending_ids.pop(0)
        pieces.append(enc.decode([stuck_id]))

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
        pending_ids = []
    while pending_ids:
        flush_lossy()

    return "".join(pieces)


def distinct_trigram_ratio(text: str) -> float | None:
    words = text.split()
    if len(words) < 3:
        return None
    trigrams = [tuple(words[i : i + 3]) for i in range(len(words) - 2)]
    return len(set(trigrams)) / len(trigrams)


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for entry in manifest:
        label = entry["label"]
        run_dir = pathlib.Path(entry["run_dir"])
        t = entry["intervention_output_position"]
        print(f"\n{'=' * 100}\n{label}  (intervention t={t}: {entry['original_token_text']!r} -> {entry['counterfactual_token_text']!r})\n{'=' * 100}")

        for seed in SEEDS:
            cf_dir = CONTINUATION_RUNS_ROOT / label / f"seed_{seed}" / "rFuzzy0p3"
            resp_path = cf_dir / "response.json"
            if not resp_path.is_file():
                print(f"\n--- seed {seed}: NOT FOUND at {resp_path} ---")
                continue
            response = json.loads(resp_path.read_text(encoding="utf-8"))
            cf_text = response["choices"][0]["text"]
            n_cf_tokens = response["usage"]["completion_tokens"]

            orig_text = reconstruct_original_continuation(run_dir, from_output_position=t, n_tokens=n_cf_tokens)

            cf_dtr = distinct_trigram_ratio(cf_text)
            orig_dtr = distinct_trigram_ratio(orig_text)

            print(f"\n--- seed {seed}: {n_cf_tokens} tokens generated ---")
            print(f"distinct-trigram ratio: counterfactual={cf_dtr}, original={orig_dtr}")
            print(f"\n[COUNTERFACTUAL continuation, first {DISPLAY_CHARS} chars]")
            print(cf_text[:DISPLAY_CHARS])
            print(f"\n[ORIGINAL factual continuation, same token count, first {DISPLAY_CHARS} chars]")
            print(orig_text[:DISPLAY_CHARS])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
