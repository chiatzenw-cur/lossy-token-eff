#!/usr/bin/env python3
"""Detects "macro-loop" restarts -- the pattern noticed while reading the
case_028 counterfactual continuation (see the README's "Single-event
counterfactual" section): the model reaches a tentative answer inside an
`analysis`-channel message, emits `<|end|>`, then immediately opens a BRAND
NEW `<|start|>assistant<|channel|>analysis<|message|>` turn and re-derives
from scratch, rather than ever committing to a `final`-channel answer. This
is a different failure shape than the token-level repetition loops the
window-entropy/hidden-state-recurrence detectors were built for: the
surface tokens across two restart cycles are mostly DIFFERENT (it's a fresh
derivation each time, not a repeated phrase), so a token-identity or
raw-entropy detector has no reason to fire on it. The question this script
exists to help answer: does the hidden-state trajectory nonetheless show
elevated recurrence at these points -- i.e. does the model return to a
similar *latent* state each time it restarts, even though it says different
words?

Detection is on raw committed token IDs (not decoded text) for exactness:
a restart = the exact 6-token id sequence
    <|end|> <|start|> "assistant" <|channel|> "analysis" <|message|>
appearing anywhere in the model's own generated tokens. Every occurrence is
a genuine restart here (not the model's own initial turn-open): this
repo's rendered prompts already end in the harmony `<|start|>assistant`
turn marker (confirmed by inspecting `rendered_prompt.txt` directly), so
the model's first generated tokens are `<|channel|>analysis<|message|>...`
only -- it never generates its own leading `<|end|><|start|>assistant`,
so the full 6-token pattern cannot match the opening turn at all. (An
earlier version of this script incorrectly dropped the first hit per run
assuming it was that initial turn-open, which -- for cases with exactly
one restart -- silently zeroed out the only real hit. Caught by a manual
recount that found a hit this script's first version reported as none.)

Special/plain token ids used (looked up once via get_encoding(), stable
across runs since they come from the fixed o200k_harmony vocab):
    <|end|>=200007  <|start|>=200006  <|channel|>=200005  <|message|>=200008
    "assistant"=173781  "analysis"=35644  "final"=17196

Usage:
    python3 analysis/semantic_guard/find_macro_loop_restarts.py \\
        --runs-root runs/hidden_state_pilot/aime24 --tag rFuzzy0p3 \\
        --out analysis/semantic_guard/results/macro_loop_restarts.jsonl
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from count_relaxed_only_hesitation import get_encoding  # noqa: E402

RESTART_PATTERN = [200007, 200006, 173781, 200005, 35644, 200008]
FINAL_OPEN_PATTERN = [200007, 200006, 173781, 200005, 17196, 200008]
CONTEXT_CHARS = 300


def load_committed(run_dir: pathlib.Path) -> tuple[list[int], list[int]]:
    rows = [json.loads(line) for line in (run_dir / "proposals.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    rows.sort(key=lambda r: r["output_position"])
    committed = [r for r in rows if r["emission_source"] in ("accepted_draft", "recovered", "bonus")]
    ids = [r["emitted_token_id"] for r in committed if r.get("emitted_token_id") is not None]
    positions = [r["output_position"] for r in committed if r.get("emitted_token_id") is not None]
    return ids, positions


def find_pattern_hits(ids: list[int], positions: list[int], pattern: list[int]) -> list[int]:
    """output_position of the token immediately AFTER the pattern ends
    (i.e. the first token of the new message's content)."""
    hits = []
    n = len(pattern)
    for i in range(len(ids) - n + 1):
        if ids[i : i + n] == pattern:
            end_idx = i + n
            if end_idx < len(positions):
                hits.append(positions[end_idx])
    return hits


def context_text(run_dir: pathlib.Path, output_position: int) -> str:
    enc = get_encoding()
    rows = [json.loads(line) for line in (run_dir / "proposals.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    rows.sort(key=lambda r: r["output_position"])
    rows = [r for r in rows if r["output_position"] >= output_position][:80]
    ids = [r["emitted_token_id"] for r in rows if r.get("emitted_token_id") is not None]
    try:
        return enc.decode(ids)[:CONTEXT_CHARS]
    except Exception:
        return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-root", type=pathlib.Path, required=True)
    parser.add_argument("--tag", default="rFuzzy0p3")
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()

    run_dirs = sorted({p.parent for p in args.runs_root.glob(f"*/seed_*/{args.tag}/proposals.jsonl")})
    if not run_dirs:
        print(f"no {args.tag} runs under {args.runs_root}", file=sys.stderr)
        return 1

    all_events: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        case = run_dir.parent.parent.name
        ids, positions = load_committed(run_dir)
        restart_hits = find_pattern_hits(ids, positions, RESTART_PATTERN)
        final_hits = find_pattern_hits(ids, positions, FINAL_OPEN_PATTERN)

        print(f"{case}: {len(restart_hits)} macro-loop restart(s) at {restart_hits}, "
              f"{len(final_hits)} final-channel-open(s) at {final_hits}, {len(ids)} committed tokens", file=sys.stderr)

        for pos in restart_hits:
            all_events.append({
                "case": case,
                "run_dir": str(run_dir),
                "output_position": pos,
                "event": "macro_loop_restart",
                "context_after": context_text(run_dir, pos),
            })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for event in all_events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(f"\n{len(run_dirs)} runs, {len(all_events)} macro-loop restart events -> wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
