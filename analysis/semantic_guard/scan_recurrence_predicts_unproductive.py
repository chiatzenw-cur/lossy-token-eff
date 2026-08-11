#!/usr/bin/env python3
"""Scans ALL the hidden-state data we already have (the 8 hidden_state_pilot
`r_fuzzy` AIME24 runs) -- not just the flagged onsets/restart from earlier
work -- and checks whether hidden-state recurrence (S_k, same score as
find_hidden_state_recurrence_onsets.py and
check_macro_loop_hidden_recurrence.py) actually PREDICTS "unproductive"
generation, under several proxies for "unproductive" that this repo's
existing per-token trace data can support directly (no new labeling
scheme invented):

  1. Hesitation markers (wait/hmm/let's/actually/but -- same regex set as
     count_hesitation.py), matched against each token's own decoded text.
     A weak, noisy proxy (documented as such there too), but cheap and
     already-defined.
  2. `lossy_only_accepted` -- the token was accepted only because
     verification was relaxed; strict would have rejected it. Already
     checked once against the visible loop ONSET specifically (found
     ~flat there); this checks it against the recurrence SCORE directly,
     continuously, over every position, not just onsets.
  3. Target/draft entropy and target top-1 shortfall -- continuous
     uncertainty measures already logged per token by relaxation_trace.py.
     Correlated directly against S_k rather than bucketed.
  4. case_028's own labeled "abandoned final-channel attempt" span
     (30953-31478, see the README's macro-loop section) -- the one place
     in this dataset where "unproductive" has a ground-truth boundary
     (every token in that span was later discarded when the model
     restarted `analysis`), not a proxy.

k=32 chosen as a middle ground of the k in {8,16,32,64} checked earlier
(cheap enough to run across all 8 cases -- O(k) cost per case -- while
still showing a strong signal on the one confirmed macro-loop restart).

No scipy in this environment -- Pearson and Spearman (via rank transform)
implemented directly with numpy.

Usage:
    python3 analysis/semantic_guard/scan_recurrence_predicts_unproductive.py
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Any

import numpy as np

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "analysis" / "semantic_guard"))
from join_hidden_states import build_sequence, load_committed_rows, load_hidden_states, recurrence_scores  # noqa: E402

RUNS_ROOT = REPO_ROOT / "runs/hidden_state_pilot/aime24"
TAG = "rFuzzy0p3"
K = 32
MIN_GAP = 32

MARKERS = {
    "wait": re.compile(r"\bwait\b", re.IGNORECASE),
    "hmm": re.compile(r"\bhmm+\b", re.IGNORECASE),
    "lets": re.compile(r"\blet's\b", re.IGNORECASE),
    "actually": re.compile(r"\bactually\b", re.IGNORECASE),
    "but": re.compile(r"\bbut\b", re.IGNORECASE),
}

# case_028's abandoned final-channel attempt (see README "Do macro-loops
# show hidden-state recurrence too?"): every token in [30953, 31478) was
# discarded outright when the model restarted `analysis` at 31478. Ground
# truth, not a proxy -- the only span in this dataset with one.
ABANDONED_SPANS = {
    "case_028": [(30953, 31478)],
}


def is_hesitation(text: str | None) -> bool:
    if not text:
        return False
    return any(p.search(text) for p in MARKERS.values())


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    if x.size < 2 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx = np.argsort(np.argsort(x))
    ry = np.argsort(np.argsort(y))
    return pearson(rx.astype(float), ry.astype(float))


def main() -> int:
    run_dirs = sorted({p.parent for p in RUNS_ROOT.glob(f"*/seed_*/{TAG}/hidden_states.bin")})
    print(f"{len(run_dirs)} runs with hidden_states.bin under {RUNS_ROOT}\n")

    all_rows: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        case = run_dir.parent.parent.name
        hidden = load_hidden_states(run_dir / "hidden_states.bin")
        committed = load_committed_rows(run_dir / "proposals.jsonl")
        matched_rows, vecs = build_sequence(committed, hidden)
        if len(matched_rows) < 4 * MIN_GAP:
            print(f"{case}: too short ({len(matched_rows)} positions), skipping")
            continue

        scores = recurrence_scores(vecs, min_gap=MIN_GAP, k_values=(K,))[K]
        spans = ABANDONED_SPANS.get(case, [])

        n_valid = 0
        for row, s in zip(matched_rows, scores):
            if np.isnan(s):
                continue
            n_valid += 1
            pos = row["output_position"]
            in_abandoned = any(a <= pos < b for a, b in spans)
            all_rows.append({
                "case": case,
                "output_position": pos,
                "S": float(s),
                "target_entropy": row.get("target_entropy"),
                "draft_entropy": row.get("draft_entropy"),
                "target_top1_shortfall": row.get("target_top1_shortfall"),
                "lossy_only_accepted": bool(row.get("lossy_only_accepted")),
                "hesitation": is_hesitation(row.get("emitted_token_text")),
                "in_abandoned_span": in_abandoned,
            })
        print(f"{case}: {n_valid} scored positions (S{K}, min_gap={MIN_GAP})")

    out_path = REPO_ROOT / "analysis" / "semantic_guard" / "results" / "recurrence_vs_unproductive.jsonl"
    with out_path.open("w", encoding="utf-8") as handle:
        for r in all_rows:
            handle.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nwrote {len(all_rows)} scored positions -> {out_path}")

    S = np.array([r["S"] for r in all_rows])

    print(f"\n{'='*90}\nProxy 1: hesitation-marker tokens (wait/hmm/let's/actually/but) vs. all others\n{'='*90}")
    hes_mask = np.array([r["hesitation"] for r in all_rows])
    print(f"  n_hesitation={hes_mask.sum()}, n_other={(~hes_mask).sum()}")
    print(f"  mean S{K}: hesitation={S[hes_mask].mean():.4f}  other={S[~hes_mask].mean():.4f}  "
          f"median: hesitation={np.median(S[hes_mask]):.4f}  other={np.median(S[~hes_mask]):.4f}")

    print(f"\n{'='*90}\nProxy 2: lossy_only_accepted (strict would have rejected; relaxed accepted anyway)\n{'='*90}")
    loa_mask = np.array([r["lossy_only_accepted"] for r in all_rows])
    print(f"  n_lossy_only={loa_mask.sum()}, n_other={(~loa_mask).sum()}")
    print(f"  mean S{K}: lossy_only={S[loa_mask].mean():.4f}  other={S[~loa_mask].mean():.4f}  "
          f"median: lossy_only={np.median(S[loa_mask]):.4f}  other={np.median(S[~loa_mask]):.4f}")

    print(f"\n{'='*90}\nProxy 3: continuous uncertainty measures -- correlation with S{K}\n{'='*90}")
    for field in ("target_entropy", "draft_entropy", "target_top1_shortfall"):
        vals = np.array([r[field] if r[field] is not None else np.nan for r in all_rows], dtype=float)
        valid = ~np.isnan(vals)
        if valid.sum() < 10:
            print(f"  {field}: not enough non-null values")
            continue
        r_pearson = pearson(S[valid], vals[valid])
        r_spearman = spearman(S[valid], vals[valid])
        print(f"  {field}: pearson r={r_pearson:+.4f}  spearman rho={r_spearman:+.4f}  (n={valid.sum()})")

    print(f"\n{'='*90}\nProxy 4 (ground truth, case_028 only): inside the abandoned final-channel span vs. rest of that run\n{'='*90}")
    case028 = [r for r in all_rows if r["case"] == "case_028"]
    if case028:
        S028 = np.array([r["S"] for r in case028])
        ab_mask = np.array([r["in_abandoned_span"] for r in case028])
        print(f"  n_inside={ab_mask.sum()}, n_outside={(~ab_mask).sum()} (whole run, not just neighborhood)")
        print(f"  mean S{K}: inside={S028[ab_mask].mean():.4f}  outside={S028[~ab_mask].mean():.4f}  "
              f"median: inside={np.median(S028[ab_mask]):.4f}  outside={np.median(S028[~ab_mask]):.4f}")
        # percentile of the abandoned span's mean within a null distribution
        # of same-length contiguous windows elsewhere in the same run
        span_len = int(ab_mask.sum())
        rng = np.random.default_rng(20260810)
        outside_idx = np.where(~ab_mask)[0]
        n_boot = 2000
        boot_means = []
        for _ in range(n_boot):
            start = rng.integers(0, len(S028) - span_len)
            window = S028[start : start + span_len]
            if np.isnan(window).any():
                continue
            boot_means.append(window.mean())
        boot_means = np.array(boot_means)
        pct = 100 * float(np.mean(boot_means <= S028[ab_mask].mean()))
        print(f"  abandoned-span mean S{K} vs. {len(boot_means)} random same-length windows elsewhere in this run: "
              f"{pct:.1f}th percentile")
    else:
        print("  no case_028 data found")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
