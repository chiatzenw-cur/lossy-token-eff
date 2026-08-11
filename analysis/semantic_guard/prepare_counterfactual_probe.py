#!/usr/bin/env python3
"""Phase A of the single-event counterfactual experiment (see the parent
conversation): for a confirmed loop onset t*, finds the nearest preceding
lossy_only_accepted position t, reconstructs the exact prefix text up to
(but not including) t, and writes it as a new ephemeral prompt "case" --
reusing run_experiment_vllm.py's existing case-based interface unchanged
(same fresh-server discipline, same tracing) rather than writing new
one-off request code.

This prefix, fed back through vLLM's plain /v1/completions endpoint (not
chat -- this repo's rendered prompts already end in the harmony
"<|start|>assistant" turn marker, exactly as if the model had generated
everything up to here itself), is stage 1: run it under STRICT with
max_new_tokens=1 to get the ONE token strict verification would actually
have produced at position t instead of the lossy-only accept that happened
in the real run. See build_counterfactual_continuation.py for stage 2
(splicing that token on and continuing under r_fuzzy).

Usage:
    python3 analysis/semantic_guard/prepare_counterfactual_probe.py
"""

from __future__ import annotations

import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "analysis" / "semantic_guard"))
from count_relaxed_only_hesitation import decode_piece, get_encoding  # noqa: E402

PROBE_PROMPT_ROOT = REPO_ROOT / "prompts" / "counterfactual_probe"

# (label, source_case, run_dir, onset output_position)
ONSETS = [
    (
        "case_028_onset31322",
        "case_028",
        REPO_ROOT / "runs/semantic_guard_pilot/aime24/case_028/seed_0/rFuzzy0p3",
        31322,
    ),
    (
        "case_020_onset3673",
        "case_020",
        REPO_ROOT / "runs/hidden_state_pilot/aime24/case_020/seed_0/rFuzzy0p3",
        3673,
    ),
    (
        "case_020_onset28786",
        "case_020",
        REPO_ROOT / "runs/hidden_state_pilot/aime24/case_020/seed_0/rFuzzy0p3",
        28786,
    ),
]


def find_nearest_preceding_lossy_only(run_dir: pathlib.Path, t_star: int) -> dict | None:
    rows = [json.loads(line) for line in (run_dir / "proposals.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    rows.sort(key=lambda r: r["output_position"])
    committed = [r for r in rows if r["emission_source"] in ("accepted_draft", "recovered")]
    prior = [r for r in committed if r["output_position"] < t_star and r.get("lossy_only_accepted")]
    return prior[-1] if prior else None


def reconstruct_prefix_text(run_dir: pathlib.Path, up_to_output_position: int) -> str:
    """Decoded text of every committed token with output_position <
    up_to_output_position (i.e. NOT including the intervention token
    itself) -- same safe buffered multi-byte handling as the onset-finder
    scripts."""
    rows = [json.loads(line) for line in (run_dir / "proposals.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    rows.sort(key=lambda r: r["output_position"])
    rows = [r for r in rows if r["output_position"] < up_to_output_position]

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


def write_probe_case(label: str, source_case: str, prefix_text: str) -> pathlib.Path:
    source_dir = REPO_ROOT / "prompts" / "aime24" / source_case
    original_prompt = (source_dir / "rendered_prompt.txt").read_text(encoding="utf-8")
    metadata = json.loads((source_dir / "metadata.json").read_text(encoding="utf-8"))

    case_dir = PROBE_PROMPT_ROOT / label
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "rendered_prompt.txt").write_text(original_prompt + prefix_text, encoding="utf-8")
    metadata = dict(metadata, counterfactual_probe=True, source_case=source_case)
    (case_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return case_dir


def main() -> int:
    manifest = []
    for label, source_case, run_dir, t_star in ONSETS:
        intervention = find_nearest_preceding_lossy_only(run_dir, t_star)
        if intervention is None:
            print(f"{label}: no preceding lossy-only accept found, skipping")
            continue
        t = intervention["output_position"]
        prefix_text = reconstruct_prefix_text(run_dir, up_to_output_position=t)
        case_dir = write_probe_case(label, source_case, prefix_text)
        print(f"{label}: onset t*={t_star}, intervention t={t} (gap={t_star - t}), wrote {case_dir}")
        manifest.append(
            {
                "label": label,
                "source_case": source_case,
                "run_dir": str(run_dir),
                "onset_output_position": t_star,
                "intervention_output_position": t,
                "original_draft_token_text": intervention.get("draft_token_text"),
                "original_p": intervention.get("p"),
                "original_q": intervention.get("q"),
                "probe_case_dir": str(case_dir),
                "probe_case_name": label,
            }
        )

    manifest_path = REPO_ROOT / "analysis" / "semantic_guard" / "results" / "counterfactual_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nwrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
