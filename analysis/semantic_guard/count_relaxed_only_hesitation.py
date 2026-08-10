#!/usr/bin/env python3
"""Of the hesitation-marker word occurrences counted by count_hesitation.py,
how many exist in the output *only because the relaxed verifier accepted a
draft token strict verification would have rejected*?

`patches/relaxation_trace.py` already computes this counterfactual per
emitted token -- `lossy_only_accepted` on each `accepted_draft` row in
proposals.jsonl is `lossy_would_accept and not strict_would_accept` (see
that module's docstring: "`lossy_only` is the whole point. It is computable
from a single relaxed run, because strict acceptance is a deterministic
function of the same (p, q, u) the relaxed rule already used."). This script
doesn't recompute that decision; it maps it onto text.

Method: reconstruct each run's emitted token stream in order from
proposals.jsonl (`output_position`), decode it one token at a time with the
same o200k_harmony encoding the model was served with (gpt-oss-20b), giving
each token an exact character span in the completion text. Re-run
count_hesitation.py's marker regexes over that reconstructed text (same
markers, same matching rules) and, for each match, check whether any token
overlapping its character span has `lossy_only_accepted: true`. A match
counts as "relaxed-only" if so -- i.e. the word (or the token(s) spelling
it) would very likely not have appeared had strict verification run
instead. `recovered` and `bonus` rows are never relaxed-only: recovery
resampling and the per-round bonus token use the same mechanism regardless
of which acceptance rule is in force (see relaxation_trace.py), so only
`accepted_draft` rows carry the flag.

`strict` runs are included for completeness and always score 0/0 --
lossy_would_accept == strict_would_accept there by construction (neutral
relaxation_param), so the concept doesn't apply; kept in the output rather
than special-cased out so the comparison table is uniform across arms.

Usage:
    python3 analysis/semantic_guard/count_relaxed_only_hesitation.py \\
        --runs-root runs/aime24_fresh --out-prefix analysis/semantic_guard/results/aime24
    python3 analysis/semantic_guard/count_relaxed_only_hesitation.py \\
        --runs-root runs/humaneval_fresh --out-prefix analysis/semantic_guard/results/humaneval
"""

from __future__ import annotations

import argparse
import bisect
import csv
import json
import pathlib
import sys
from collections import defaultdict
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from count_hesitation import MARKER_NAMES, MARKERS, arm_label  # noqa: E402

_ENCODING = None


def get_encoding():
    global _ENCODING
    if _ENCODING is None:
        from openai_harmony import HarmonyEncodingName, load_harmony_encoding

        _ENCODING = load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)
    return _ENCODING


def decode_piece(enc, pending_ids: list[int]) -> str | None:
    """decode_utf8 on a single token raises HarmonyError when that token's
    bytes are an incomplete UTF-8 sequence on their own (a multi-byte
    character split across adjacent tokens -- rare, but real: non-ASCII
    punctuation, accented letters). Caller accumulates ids across calls
    until this returns non-None, then attributes the whole merged span to
    every token in the group (only matters for marker-word matching if a
    hesitation word's characters straddle such a split, which doesn't
    happen for plain ASCII "wait"/"hmm"/etc. -- this exists so
    reconstruction never crashes on the surrounding non-ASCII text).
    """
    from openai_harmony import HarmonyError

    try:
        return enc.decode_utf8(pending_ids)
    except HarmonyError:
        return None


def load_tokens(proposals_path: pathlib.Path) -> list[dict[str, Any]]:
    rows = []
    with proposals_path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    rows.sort(key=lambda r: r["output_position"])
    return rows


# A genuine multi-byte UTF-8 character split across adjacent tokens never
# needs more than 3 continuation bytes after the lead token (UTF-8's own
# max character length is 4 bytes), so a real split always resolves within
# a handful of extra tokens. A buffer that grows past this is not "still
# resolving" -- it's a token whose bytes are not a valid UTF-8 prefix at
# all (confirmed by hand on one occurrence: token 35353 alone decodes to
# U+FFFD and, unlike its normal pairing with a specific continuation-byte
# token, this occurrence was followed by ordinary unrelated tokens that can
# never complete it). Without this cap, decode_utf8(pending_ids) keeps
# failing on every future call too (the malformed lead bytes are still in
# there), so the buffer silently swallows the REST OF THE DOCUMENT into one
# merged span -- and every hesitation-word match anywhere in that span then
# inherits whichever tokens' lossy_only_accepted flags happened to OR
# together across it, wildly overcounting "relaxed-only" hits. First caught
# on runs/semantic_guard_pilot/aime24/case_011: reconstruct() was returning
# 1,965 spans for a 5,029-token completion (average "token" > 2.5 raw
# tokens), traced to exactly this.
_MAX_PENDING_TOKENS = 4


def reconstruct(rows: list[dict[str, Any]]) -> tuple[str, list[int], list[int], list[bool]]:
    """Returns (full_text, token_start_offsets, token_end_offsets,
    token_is_relaxed_only), one entry per token, in emission order.
    """
    enc = get_encoding()
    pieces: list[str] = []
    starts: list[int] = []
    ends: list[int] = []
    relaxed_only: list[bool] = []
    pos = 0
    pending_ids: list[int] = []
    pending_flags: list[bool] = []

    def flush_one_lossy() -> None:
        # Pop and emit just the OLDEST pending token via a lossy per-token
        # decode (U+FFFD for any byte that still doesn't stand alone),
        # attributing ONLY that token's own flag -- not the whole buffer's
        # OR -- then let the rest of the (possibly still-valid) buffer keep
        # accumulating fresh. Bounds contamination to at most one span per
        # genuinely unresolvable token, not the remainder of the document.
        nonlocal pos
        stuck_id = pending_ids.pop(0)
        stuck_flag = pending_flags.pop(0)
        piece = enc.decode([stuck_id])
        pieces.append(piece)
        starts.append(pos)
        pos += len(piece)
        ends.append(pos)
        relaxed_only.append(stuck_flag)

    for row in rows:
        token_id = row.get("emitted_token_id")
        if token_id is None:
            continue
        pending_ids.append(token_id)
        pending_flags.append(bool(row.get("lossy_only_accepted")))
        piece = decode_piece(enc, pending_ids)
        if piece is None:
            if len(pending_ids) >= _MAX_PENDING_TOKENS:
                flush_one_lossy()
            continue  # still within a plausible multi-byte split -- keep accumulating
        pieces.append(piece)
        starts.append(pos)
        pos += len(piece)
        ends.append(pos)
        relaxed_only.append(any(pending_flags))
        pending_ids = []
        pending_flags = []
    while pending_ids:
        flush_one_lossy()
    return "".join(pieces), starts, ends, relaxed_only


def overlapping_tokens(m_start: int, m_end: int, starts: list[int], ends: list[int]) -> range:
    i = bisect.bisect_right(ends, m_start)
    j = i
    n = len(starts)
    while j < n and starts[j] < m_end:
        j += 1
    return range(i, j)


def analyze_run(run_dir: pathlib.Path) -> dict[str, Any] | None:
    proposals_path = run_dir / "proposals.jsonl"
    config_path = run_dir / "config.json"
    if not (proposals_path.is_file() and config_path.is_file()):
        return None
    config = json.loads(config_path.read_text(encoding="utf-8"))
    rows = load_tokens(proposals_path)
    if not rows:
        return None
    text, starts, ends, relaxed_only_tok = reconstruct(rows)

    marker_total: dict[str, int] = {name: 0 for name in MARKER_NAMES}
    marker_relaxed_only: dict[str, int] = {name: 0 for name in MARKER_NAMES}
    for name, pattern in MARKERS.items():
        for match in pattern.finditer(text):
            marker_total[name] += 1
            idxs = overlapping_tokens(match.start(), match.end(), starts, ends)
            if any(relaxed_only_tok[i] for i in idxs):
                marker_relaxed_only[name] += 1

    total = sum(marker_total.values())
    relaxed_only = sum(marker_relaxed_only.values())
    all_tokens_relaxed_only = sum(relaxed_only_tok)

    return {
        "case": config.get("prompt_case", run_dir.parent.parent.name),
        "tag": run_dir.name,
        "arm": arm_label(config),
        "total_tokens": len(starts),
        "relaxed_only_tokens": all_tokens_relaxed_only,
        **{f"{name}_total": marker_total[name] for name in MARKER_NAMES},
        **{f"{name}_relaxed_only": marker_relaxed_only[name] for name in MARKER_NAMES},
        "hesitation_total": total,
        "hesitation_relaxed_only": relaxed_only,
    }


def collect_rows(runs_root: pathlib.Path) -> list[dict[str, Any]]:
    run_dirs = sorted({p.parent for p in runs_root.glob("*/seed_*/*/run.json")})
    if not run_dirs:
        print(f"no runs under {runs_root}", file=sys.stderr)
        return []
    rows = []
    for run_dir in run_dirs:
        row = analyze_run(run_dir)
        if row is None:
            print(f"skipping {run_dir}: missing/empty proposals.jsonl", file=sys.stderr)
            continue
        rows.append(row)
    return rows


def write_case_by_arm(rows: list[dict[str, Any]], out_path: pathlib.Path) -> None:
    fields = [
        "case", "tag", "arm", "total_tokens", "relaxed_only_tokens",
        "hesitation_total", "hesitation_relaxed_only",
        *[f"{name}_total" for name in MARKER_NAMES],
        *[f"{name}_relaxed_only" for name in MARKER_NAMES],
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in sorted(rows, key=lambda r: (r["case"], r["arm"])):
            writer.writerow(row)


def compute_totals_by_arm(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_arm: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_arm[row["arm"]].append(row)

    totals: dict[str, dict[str, Any]] = {}
    for arm, group in by_arm.items():
        n = len(group)
        hesitation_total = sum(r["hesitation_total"] for r in group)
        hesitation_relaxed_only = sum(r["hesitation_relaxed_only"] for r in group)
        all_tokens = sum(r["total_tokens"] for r in group)
        all_relaxed_only_tokens = sum(r["relaxed_only_tokens"] for r in group)
        totals[arm] = {
            "runs": n,
            "hesitation_total": hesitation_total,
            "hesitation_relaxed_only": hesitation_relaxed_only,
            "pct_relaxed_only": round(100 * hesitation_relaxed_only / hesitation_total, 2) if hesitation_total else None,
            "all_tokens": all_tokens,
            "all_relaxed_only_tokens": all_relaxed_only_tokens,
            "pct_all_tokens_relaxed_only": round(100 * all_relaxed_only_tokens / all_tokens, 4) if all_tokens else None,
        }
    return totals


def write_totals_by_arm(totals: dict[str, dict[str, Any]], out_path: pathlib.Path) -> None:
    fields = [
        "arm", "runs", "hesitation_total", "hesitation_relaxed_only", "pct_relaxed_only",
        "all_tokens", "all_relaxed_only_tokens", "pct_all_tokens_relaxed_only",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for arm in sorted(totals):
            writer.writerow({"arm": arm, **totals[arm]})


def print_totals_md(totals: dict[str, dict[str, Any]], title: str) -> None:
    print(f"\n{title}\n")
    columns = ["arm", "runs", "hesitation words", "relaxed-only", "% relaxed-only", "% of all tokens relaxed-only"]
    print("| " + " | ".join(columns) + " |")
    print("|" + "|".join("---" for _ in columns) + "|")
    for arm in sorted(totals, key=lambda a: (totals[a]["pct_relaxed_only"] or 0), reverse=True):
        t = totals[arm]
        print(
            f"| {arm} | {t['runs']} | {t['hesitation_total']} | {t['hesitation_relaxed_only']} | "
            f"{t['pct_relaxed_only']} | {t['pct_all_tokens_relaxed_only']} |"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-root", type=pathlib.Path, required=True)
    parser.add_argument("--out-prefix", type=pathlib.Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = collect_rows(args.runs_root)
    if not rows:
        return 1

    benchmark = args.out_prefix.name
    write_case_by_arm(rows, args.out_prefix.with_name(f"{benchmark}_relaxed_only_case_by_arm.csv"))

    totals = compute_totals_by_arm(rows)
    write_totals_by_arm(totals, args.out_prefix.with_name(f"{benchmark}_relaxed_only_totals_by_arm.csv"))
    print_totals_md(totals, f"{benchmark}: hesitation words accepted only because of the relaxed verifier ({len(rows)} runs)")

    out_json = args.out_prefix.with_name(f"{benchmark}_relaxed_only_all_rows.json")
    out_json.write_text(
        json.dumps({"runs_root": str(args.runs_root), "rows": rows, "totals_by_arm": totals}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nwrote {args.out_prefix.with_name(f'{benchmark}_relaxed_only_case_by_arm.csv')}")
    print(f"wrote {args.out_prefix.with_name(f'{benchmark}_relaxed_only_totals_by_arm.csv')}")
    print(f"wrote {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
