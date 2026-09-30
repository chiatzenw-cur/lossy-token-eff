#!/usr/bin/env python3
"""Step 1 of the NAACL-2027 addendum (campaign/addendum/README.md): zero-GPU
analyses of the existing campaign runs, written to campaign/addendum/analysis/.
Every CSV is described, one line each, in campaign/addendum/analysis/README.md
(written by this script too, so the description cannot drift from the code).

  python3 scripts/addendum_analysis.py [--runs-root runs] [--seed 0] [--only NAME ...]

Needs numpy; the repetition analysis also needs the `tokenizers` package
(tokenizer.json of openai/gpt-oss-20b and Qwen/Qwen3-8B are fetched from the
HF Hub on first use). Correctness comes from campaign/addendum/analysis/grades.csv
(scripts/addendum_grade.py: the campaign's own graders, run on Nibi).

Cells: the "loosest" cell of a (target, dataset, method) is its maximum alpha
in campaign/results/<dataset>.csv (the paper's main tables); it is paired with
`strict` of the same dataset on the cases where both have an ok run (all cases
at seed 0: the campaign is complete). 5 methods x 6 datasets x 2 targets = 60.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import re
import sys
from collections import defaultdict

import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "campaign" / "addendum" / "analysis"
BASE = ["gsm8k", "aime24", "humaneval", "livecodebench", "mtbench", "longbench_v2"]
FIVE = ["mentored_dec", "cactus", "spec_casc_opt", "r_fuzzy", "spec_casc_tok"]
TARGETS = {"": "gpt-oss-20b", "_qwen3": "qwen3-8b"}
BOOT = 10000
RNG_SEED = 20261001

README: dict[str, str] = {}


def note(name: str, text: str) -> None:
    README[name] = text


# ------------------------------------------------------------------- helpers

def alpha_of(params: str) -> str:
    if params in ("strict", "baseline"):
        return params
    head = params.split("_", 1)[0]  # multi-knob dirs (guard variants): alpha0.3_budget10_pct99_k8
    try:
        return f"{float(head.removeprefix('alpha').replace('neg', '-')):g}"
    except ValueError:
        return params


def params_dir(method: str, alpha: str) -> str:
    if method in ("strict", "baseline"):
        return method
    return f"alpha{float(alpha):g}".replace("-", "neg")


def loosest() -> dict[tuple[str, str], str]:
    """(dataset incl. suffix, method) -> loosest alpha string."""
    out = {}
    for base in BASE:
        for suffix in TARGETS:
            ds = base + suffix
            with (REPO / "campaign" / "results" / f"{ds}.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            for method in FIVE:
                out[(ds, method)] = f"{max(float(r['alpha']) for r in rows if r['method'] == method):g}"
    return out


SPECIAL = re.compile(r"<\|[^|>]*\|>")


def split_think_answer(text: str, target: str) -> tuple[int, int, bool]:
    """(think_chars, answer_chars, answer_started), content characters only (special-token
    markers removed), defined the same way for both families: GPT-OSS thinking = the
    analysis channel before `<|channel|>final`, answer = the final channel's message;
    Qwen3 thinking = inside <think>...</think>, answer = after </think>. No answer
    marker (e.g. a cap-out mid-thinking) -> everything is thinking."""
    if target == "gpt-oss-20b":
        i = text.find("<|channel|>final")
        head, tail = (text, "") if i < 0 else (text[:i], text[i:])
        head = head.replace("<|channel|>analysis<|message|>", "")
        head = re.sub(r"<\|end\|><\|start\|>assistant$", "", head)
        if tail:
            tail = tail.split("<|message|>", 1)[1] if "<|message|>" in tail else ""
        started = i >= 0
    else:
        # every <think>...</think> block is thinking (Qwen3 under some relaxed rules re-opens
        # <think> after answering); an unclosed trailing block runs to the end; if the output
        # starts inside thinking (a </think> before any <think>) the prefix is thinking too.
        head_parts, tail_parts = [], []
        first_open, first_close = text.find("<think>"), text.find("</think>")
        inside = first_close >= 0 and (first_open < 0 or first_close < first_open)
        pos = 0
        for m in re.finditer(r"</?think>", text):
            (head_parts if inside else tail_parts).append(text[pos:m.start()])
            inside = m.group(0) == "<think>"
            pos = m.end()
        (head_parts if inside else tail_parts).append(text[pos:])
        head, tail = "".join(head_parts), "".join(tail_parts)
        started = first_close >= 0
    return len(SPECIAL.sub("", head)), len(SPECIAL.sub("", tail)), started


def load_grades() -> dict[str, tuple[str, str]]:
    path = OUT / "grades.csv"
    if not path.is_file():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        return {r["relpath"]: (r["verdict"], r["correct"]) for r in csv.DictReader(handle)}


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def ratio(a, b):
    return a / b if (a is not None and b not in (None, 0)) else None


def fmt(x, nd=6):
    if x is None:
        return ""
    if isinstance(x, float):
        if math.isnan(x):
            return ""
        return f"{x:.{nd}g}"
    return x


OUT_SUFFIX = ""  # "__seed<k>" when run with --seed k != 0, so the seed-0 (paper) files are never overwritten


def write_csv(name: str, rows: list[dict], fields: list[str]) -> None:
    name = name.replace(".csv", f"{OUT_SUFFIX}.csv")
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: fmt(row.get(k)) for k in fields})
    print(f"wrote {OUT / name} ({len(rows)} rows)")


def boot_ratio_ci(a: np.ndarray, b: np.ndarray, rng) -> tuple[float, float]:
    """95% percentile interval of mean(a)/mean(b), resampling paired cases."""
    n = len(a)
    idx = rng.integers(0, n, size=(BOOT, n))
    r = a[idx].mean(axis=1) / b[idx].mean(axis=1)
    return float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))


def spearman(x: list[float], y: list[float], rng) -> tuple[float, float]:
    """Spearman rho (average ranks for ties) and a two-sided permutation p-value (20,000 draws)."""
    def ranks(v):
        v = np.asarray(v, dtype=float)
        order = v.argsort(kind="mergesort")
        r = np.empty(len(v))
        r[order] = np.arange(1, len(v) + 1)
        for val in np.unique(v):
            m = v == val
            if m.sum() > 1:
                r[m] = r[m].mean()
        return r
    rx, ry = ranks(x), ranks(y)
    rho = float(np.corrcoef(rx, ry)[0, 1])
    perms = np.array([np.corrcoef(rx, rng.permutation(ry))[0, 1] for _ in range(20000)])
    p = float((np.abs(perms) >= abs(rho) - 1e-12).mean())
    return rho, p


# ------------------------------------------------------------------- loading

def load_runs(runs_root: pathlib.Path) -> list[dict]:
    grades = load_grades()
    rows = []
    for base in BASE:
        for suffix, target in TARGETS.items():
            ds = base + suffix
            for run_json in sorted((runs_root / ds).glob("*/*/case_*/seed_*/run.json")):
                run_dir = run_json.parent
                case, params, method = run_dir.parent.name, run_dir.parent.parent.name, run_dir.parent.parent.parent.name
                try:
                    run = json.loads(run_json.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                text = ""
                out_txt = run_dir / "output.txt"
                if out_txt.is_file():
                    text = out_txt.read_text(encoding="utf-8", errors="replace")
                think, answer, started = split_think_answer(text, target)
                rel = str(run_dir.relative_to(runs_root))
                verdict, correct = grades.get(rel, ("", ""))
                rounds = run.get("draft_rounds")
                wall = run.get("wall_time_seconds")
                try:
                    stamp = json.loads((run_dir / "config.json").read_text(encoding="utf-8")).get("timestamp_utc") or ""
                except (OSError, json.JSONDecodeError):
                    stamp = ""
                rows.append({
                    "target": target, "dataset": base, "method": method, "alpha": alpha_of(params), "params": params,
                    "case": case, "seed": int(run_dir.name.removeprefix("seed_")),
                    "server_request_ordinal": run.get("server_request_ordinal"),
                    "output_tokens": run.get("output_tokens"), "analysis_chars": run.get("analysis_chars"),
                    "final_chars": run.get("final_chars"), "reached_final_channel": run.get("reached_final_channel"),
                    "finish_reason": run.get("finish_reason"), "reached_max_new_tokens": run.get("reached_max_new_tokens"),
                    "draft_rounds": rounds, "accepted_tokens": run.get("accepted_tokens"), "l_bar": run.get("l_bar"),
                    "wall_time_seconds": wall, "think_chars": think, "answer_chars": answer,
                    "answer_started": started, "correct": int(correct) if correct in ("0", "1") else None,
                    "verdict": verdict, "status": run.get("status"), "input_tokens": run.get("input_tokens"),
                    "draft_tokens": run.get("draft_tokens"),
                    "time_per_round": (wall / rounds) if (wall and rounds) else None,
                    "timestamp_utc": stamp, "machine": machine_of(stamp),
                    "relpath": rel, "_text": text,
                })
    return rows


ADDENDUM_START = "2026-09-29"  # the campaign ran on the old box through 2026-09-16; addendum runs are on Nibi


def machine_of(stamp: str) -> str:
    """oldbox = the campaign's H100 PCIe box (the paper's data); nibi = Nibi H100 SXM (addendum runs)."""
    if not stamp:
        return ""
    return "nibi" if stamp[:10] >= ADDENDUM_START else "oldbox"


def index(rows: list[dict], seed: int) -> dict[tuple, dict[str, dict]]:
    """(target, dataset, method, alpha) -> case -> row (ok runs at this seed)."""
    out: dict[tuple, dict[str, dict]] = defaultdict(dict)
    for r in rows:
        if r["seed"] == seed and r["status"] == "ok":
            if r["params"] == params_dir(r["method"], r["alpha"]):  # single-knob dirs only
                out[(r["target"], r["dataset"], r["method"], r["alpha"])][r["case"]] = r
    return out


def loosest_cells(rows, seed):
    idx = index(rows, seed)
    loose = loosest()
    cells = []
    for suffix, target in TARGETS.items():
        for base in BASE:
            strict = idx.get((target, base, "strict", "strict"), {})
            for method in FIVE:
                alpha = loose[(base + suffix, method)]
                relaxed = idx.get((target, base, method, alpha), {})
                cases = sorted(set(strict) & set(relaxed))
                cells.append({"target": target, "dataset": base, "method": method, "alpha": alpha,
                              "pairs": [(relaxed[c], strict[c]) for c in cases]})
    return cells


# ----------------------------------------------------------------- analyses

PER_REQUEST_FIELDS = [
    "target", "dataset", "method", "alpha", "params", "case", "seed", "server_request_ordinal", "output_tokens",
    "analysis_chars", "final_chars", "reached_final_channel", "finish_reason", "reached_max_new_tokens",
    "draft_rounds", "accepted_tokens", "l_bar", "wall_time_seconds", "think_chars", "answer_chars", "correct",
    "verdict", "answer_started", "time_per_round", "input_tokens", "draft_tokens", "status",
    "timestamp_utc", "machine",
]


def a_per_request(rows, cells, args):
    write_csv("per_request.csv", rows, PER_REQUEST_FIELDS)
    note("per_request.csv",
         "one row per run.json under runs/<dataset>[_qwen3]/ (every method, alpha, case, seed). Columns up to "
         "wall_time_seconds are copied from run.json (analysis_chars/final_chars/reached_final_channel are the "
         "runner's Harmony split and are meaningless for Qwen3). think_chars/answer_chars: content characters "
         "(special-token markers removed) of output.txt -- GPT-OSS: analysis channel vs the final channel's "
         "message; Qwen3: text inside every <think>...</think> block (an unclosed trailing block counts as thinking) "
         "vs everything outside them; no answer marker -> all thinking "
         "(answer_started=False). correct/verdict: campaign graders (grade_*.py) via scripts/addendum_grade.py "
         "(analysis/grades.csv); blank for mtbench (no grader) and for runs not graded yet. "
         "time_per_round = wall_time_seconds / draft_rounds. timestamp_utc: config.json; machine: oldbox = the "
         "campaign's H100 PCIe box (runs before 2026-09-29, the paper's data), nibi = Nibi H100 SXM (the "
         "addendum's runs: seeds 1+, and the step-5.1 grid cells at seed 0).")


def a_split_inflation(rows, cells, args):
    out = []
    for c in cells:
        p = c["pairs"]
        if not p:
            continue
        Lr, Ls = [r["output_tokens"] for r, _ in p], [s["output_tokens"] for _, s in p]
        tr, ts = sum(r["think_chars"] for r, _ in p), sum(s["think_chars"] for _, s in p)
        ar, as_ = sum(r["answer_chars"] for r, _ in p), sum(s["answer_chars"] for _, s in p)
        extra_total = (tr + ar) - (ts + as_)
        out.append({
            "target": c["target"], "dataset": c["dataset"], "method": c["method"], "alpha": c["alpha"], "n_pairs": len(p),
            "mean_tokens_relaxed": mean(Lr), "mean_tokens_strict": mean(Ls), "lambda": ratio(mean(Lr), mean(Ls)),
            "mean_think_chars_relaxed": tr / len(p), "mean_think_chars_strict": ts / len(p),
            "mean_answer_chars_relaxed": ar / len(p), "mean_answer_chars_strict": as_ / len(p),
            "lambda_think_chars": ratio(tr, ts), "lambda_answer_chars": ratio(ar, as_),
            "extra_chars_total": extra_total, "extra_chars_think": tr - ts,
            "extra_share_think": ((tr - ts) / extra_total) if extra_total > 0 else None,
        })
    write_csv("split_inflation.csv", out, list(out[0].keys()))
    note("split_inflation.csv",
         "per loosest cell (seed 0), paired with strict on the same cases: mean completion tokens relaxed/strict "
         "and lambda = their ratio; thinking vs answer characters (definition as in per_request.csv), "
         "lambda_think_chars / lambda_answer_chars = ratio of summed characters; extra_share_think = "
         "(think_r - think_s) / ((think_r + answer_r) - (think_s + answer_s)), blank when the relaxed arm is "
         "not longer in characters overall.")


def a_censoring(rows, cells, args):
    out = []
    for c in cells:
        p = c["pairs"]
        if not p:
            continue
        cap_r = mean([1.0 if r["finish_reason"] == "length" else 0.0 for r, _ in p])
        cap_s = mean([1.0 if s["finish_reason"] == "length" else 0.0 for _, s in p])
        fin = [(r, s) for r, s in p if r["finish_reason"] == "stop" and s["finish_reason"] == "stop"]
        graded = all(r["correct"] is not None and s["correct"] is not None for r, s in p)
        row = {
            "target": c["target"], "dataset": c["dataset"], "method": c["method"], "alpha": c["alpha"],
            "n_pairs": len(p), "capout_rate_relaxed": cap_r, "capout_rate_strict": cap_s,
            "n_pairs_both_finished": len(fin),
            "lambda_all": ratio(mean([r["output_tokens"] for r, _ in p]), mean([s["output_tokens"] for _, s in p])),
            "lambda_both_finished": ratio(mean([r["output_tokens"] for r, _ in fin]), mean([s["output_tokens"] for _, s in fin])) if fin else None,
        }
        if graded:
            row.update({
                "acc_relaxed_all": mean([r["correct"] for r, _ in p]), "acc_strict_all": mean([s["correct"] for _, s in p]),
                "acc_relaxed_both_finished": mean([r["correct"] for r, _ in fin]) if fin else None,
                "acc_strict_both_finished": mean([s["correct"] for _, s in fin]) if fin else None,
            })
        out.append(row)
    fields = ["target", "dataset", "method", "alpha", "n_pairs", "capout_rate_relaxed", "capout_rate_strict",
              "n_pairs_both_finished", "lambda_all", "lambda_both_finished", "acc_relaxed_all", "acc_strict_all",
              "acc_relaxed_both_finished", "acc_strict_both_finished"]
    write_csv("censoring.csv", out, fields)
    note("censoring.csv",
         "per loosest cell (seed 0): cap-out rate (finish_reason == length) relaxed and strict; lambda over all "
         "pairs and over pairs where BOTH runs finished (finish_reason == stop); accuracy over all pairs and over "
         "both-finished pairs, relaxed and strict (blank for mtbench / cells not fully graded).")


def a_distribution(rows, cells, args):
    out = []
    for c in cells:
        p = [(r, s) for r, s in c["pairs"] if s["output_tokens"]]
        if not p:
            continue
        ratios = np.array([r["output_tokens"] / s["output_tokens"] for r, s in p])
        extra = np.array([r["output_tokens"] - s["output_tokens"] for r, s in p], dtype=float)
        k = max(1, math.ceil(0.1 * len(p)))
        top = np.sort(extra)[::-1][:k].sum()
        pos = extra[extra > 0]
        top_pos = np.sort(pos)[::-1][:k].sum() if len(pos) else 0.0
        q = np.percentile(ratios, [10, 25, 50, 75, 90])
        out.append({
            "target": c["target"], "dataset": c["dataset"], "method": c["method"], "alpha": c["alpha"], "n_pairs": len(p),
            "ratio_p10": q[0], "ratio_p25": q[1], "ratio_p50": q[2], "ratio_p75": q[3], "ratio_p90": q[4],
            "share_ratio_gt2": float((ratios > 2).mean()), "share_ratio_lt_half": float((ratios < 0.5).mean()),
            "extra_tokens_total": float(extra.sum()), "top10pct_cases": k,
            "top10pct_share_of_net_extra": float(top / extra.sum()) if extra.sum() > 0 else None,
            "top10pct_share_of_positive_extra": float(top_pos / pos.sum()) if len(pos) and pos.sum() > 0 else None,
        })
    write_csv("distribution.csv", out, list(out[0].keys()))
    note("distribution.csv",
         "per loosest cell (seed 0): quantiles (10/25/50/75/90) of the per-case ratio L_relaxed / L_strict "
         "(completion tokens, paired by case), share of cases with ratio > 2 (and < 0.5), and the share of the "
         "extra tokens contributed by the top 10% of cases (ceil(0.1 n) cases with the largest L_r - L_s): of the "
         "net extra (sum of all differences; blank when <= 0) and of the positive extra only.")


def _rolling(ids: np.ndarray, L: int, B: np.uint64, Bp: np.ndarray, G: np.ndarray) -> np.ndarray:
    """Canonical 64-bit wraparound polynomial hash of every L-gram of ids."""
    n = len(ids)
    i = np.arange(n - L + 1)
    with np.errstate(over="ignore"):
        return (G[i + L] - G[i]) * Bp[i + L - 1]


def repetition_stats(ids: list[int]) -> tuple[float, int]:
    """(fraction of tokens inside a 50-gram that already occurred earlier, longest repeated token run)."""
    n = len(ids)
    if n < 2:
        return 0.0, 0
    a = np.asarray(ids, dtype=np.uint64) + np.uint64(1)
    B = np.uint64(1000003)
    Binv = np.uint64(pow(1000003, -1, 2**64))
    with np.errstate(over="ignore"):
        Bp = np.cumprod(np.full(n, B, dtype=np.uint64))  # B^1..B^n
        Bp = np.concatenate([[np.uint64(1)], Bp])        # B^0..B^n
        Binvp = np.cumprod(np.full(n, Binv, dtype=np.uint64))
        Binvp = np.concatenate([[np.uint64(1)], Binvp[:-1]])  # Binv^0..Binv^(n-1)
        G = np.concatenate([[np.uint64(0)], np.cumsum(a * Binvp)])  # G[i] = sum_{j<i} a_j Binv^j

    def has_repeat(L: int) -> bool:
        h = _rolling(a, L, B, Bp, G)
        return len(np.unique(h)) < len(h)

    frac = 0.0
    if n >= 50:
        h = _rolling(a, 50, B, Bp, G)
        _, first, inv = np.unique(h, return_index=True, return_inverse=True)
        repeated = first[inv] < np.arange(len(h))
        cov = np.zeros(n + 1, dtype=np.int64)
        starts = np.nonzero(repeated)[0]
        np.add.at(cov, starts, 1)
        np.add.at(cov, starts + 50, -1)
        frac = float((np.cumsum(cov)[:n] > 0).mean())
    lo, hi = 0, n - 1  # longest L with a repeated L-gram (overlap allowed)
    if not has_repeat(1):
        return frac, 0
    lo = 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if has_repeat(mid):
            lo = mid
        else:
            hi = mid - 1
    return frac, lo


def a_repetition(rows, cells, args):
    try:
        from tokenizers import Tokenizer
    except ImportError:
        print("repetition: `tokenizers` not installed -- skipped", file=sys.stderr)
        return
    toks = {"gpt-oss-20b": Tokenizer.from_pretrained("openai/gpt-oss-20b"),
            "qwen3-8b": Tokenizer.from_pretrained("Qwen/Qwen3-8B")}
    wanted = set()
    for c in cells:
        for r, s in c["pairs"]:
            wanted.add(id(r))
            wanted.add(id(s))
    per_run = []
    todo = [r for r in rows if id(r) in wanted]
    for target, tok in toks.items():
        batch = [r for r in todo if r["target"] == target]
        for start in range(0, len(batch), 256):
            chunk = batch[start:start + 256]
            enc = tok.encode_batch([r["_text"] for r in chunk], add_special_tokens=False)
            for r, e in zip(chunk, enc):
                frac, longest = repetition_stats(e.ids)
                r["_rep_frac"], r["_rep_longest"], r["_retok"] = frac, longest, len(e.ids)
                per_run.append({"target": r["target"], "dataset": r["dataset"], "method": r["method"],
                                "alpha": r["alpha"], "case": r["case"], "seed": r["seed"],
                                "output_tokens": r["output_tokens"], "retokenized_tokens": len(e.ids),
                                "repeated_50gram_token_fraction": frac, "longest_exact_repeat_tokens": longest})
    write_csv("repetition_runs.csv", per_run, list(per_run[0].keys()))
    out = []
    for c in cells:
        p = c["pairs"]
        if not p:
            continue
        out.append({"target": c["target"], "dataset": c["dataset"], "method": c["method"], "alpha": c["alpha"],
                    "n_pairs": len(p),
                    "mean_rep50_frac_relaxed": mean([r["_rep_frac"] for r, _ in p]),
                    "mean_rep50_frac_strict": mean([s["_rep_frac"] for _, s in p]),
                    "mean_longest_repeat_relaxed": mean([r["_rep_longest"] for r, _ in p]),
                    "mean_longest_repeat_strict": mean([s["_rep_longest"] for _, s in p]),
                    "share_runs_rep50_frac_gt_0.2_relaxed": mean([1.0 if r["_rep_frac"] > 0.2 else 0.0 for r, _ in p]),
                    "share_runs_rep50_frac_gt_0.2_strict": mean([1.0 if s["_rep_frac"] > 0.2 else 0.0 for _, s in p])})
    write_csv("repetition.csv", out, list(out[0].keys()))
    note("repetition_runs.csv",
         "per run of the 60 loosest cells and their strict pairs (seed 0): output.txt re-tokenized with the "
         "target's own tokenizer.json (HF `tokenizers`, no special tokens added; retokenized_tokens vs "
         "output_tokens shows the round-trip). repeated_50gram_token_fraction = fraction of tokens covered by "
         "a 50-token window whose exact token sequence already occurred earlier in the same output; "
         "longest_exact_repeat_tokens = longest token sequence that occurs at least twice (overlap allowed). "
         "Exact matching via 64-bit polynomial hashes.")
    note("repetition.csv",
         "per loosest cell (seed 0): means of the two per-run repetition measures (repetition_runs.csv) for the "
         "relaxed arm and its strict pair, plus the share of runs with more than 20% of tokens inside repeated "
         "50-grams.")


def ols(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    slope, intercept = np.polyfit(x, y, 1)
    pred = slope * x + intercept
    ss_res, ss_tot = float(((y - pred) ** 2).sum()), float(((y - y.mean()) ** 2).sum())
    return float(slope), float(intercept), 1 - ss_res / ss_tot if ss_tot else None


def a_time_per_round(rows, cells, args):
    rng = np.random.default_rng(RNG_SEED)
    out = []
    lam, tpr_ratio = [], []
    for c in cells:
        p = [(r, s) for r, s in c["pairs"] if r["time_per_round"] and s["time_per_round"]]
        if not p:
            continue
        tr, ts = mean([r["time_per_round"] for r, _ in p]), mean([s["time_per_round"] for _, s in p])
        lmb = ratio(mean([r["output_tokens"] for r, _ in p]), mean([s["output_tokens"] for _, s in p]))
        out.append({"target": c["target"], "dataset": c["dataset"], "method": c["method"], "alpha": c["alpha"],
                    "n_pairs": len(p), "mean_time_per_round_relaxed_s": tr, "mean_time_per_round_strict_s": ts,
                    "time_per_round_ratio": ratio(tr, ts), "lambda": lmb})
        lam.append(lmb)
        tpr_ratio.append(ratio(tr, ts))
    write_csv("time_per_round.csv", out, list(out[0].keys()))
    reg = []
    machine = "oldbox" if args.seed == 0 else "nibi"  # one machine per fit: time per round is hardware-specific
    for target in TARGETS.values():
        fam = [r for r in rows if r["target"] == target and r["seed"] == args.seed and r["status"] == "ok" and r["time_per_round"]
               and r["method"] in ("strict", *FIVE) and r["params"] == params_dir(r["method"], r["alpha"])
               and r["machine"] == machine]
        for scope, subset in (("strict", [r for r in fam if r["method"] == "strict"]), ("all", fam)):
            slope, intercept, r2 = ols([r["output_tokens"] for r in subset], [r["time_per_round"] for r in subset])
            reg.append({"target": target, "scope": scope, "dataset": "all", "n_runs": len(subset),
                        "slope_s_per_token": slope, "intercept_s": intercept, "r2": r2})
        for base in BASE:  # extra: per dataset, strict only (prompt length differs a lot across datasets)
            subset = [r for r in fam if r["method"] == "strict" and r["dataset"] == base]
            slope, intercept, r2 = ols([r["output_tokens"] for r in subset], [r["time_per_round"] for r in subset])
            reg.append({"target": target, "scope": "strict", "dataset": base, "n_runs": len(subset),
                        "slope_s_per_token": slope, "intercept_s": intercept, "r2": r2})
    write_csv("time_per_round_regression.csv", reg, list(reg[0].keys()))
    rho, pval = spearman(lam, tpr_ratio, rng)
    write_csv("time_per_round_spearman.csv",
              [{"n_cells": len(lam), "x": "lambda", "y": "time_per_round_ratio", "spearman_rho": rho,
                "permutation_p_two_sided": pval}],
              ["n_cells", "x", "y", "spearman_rho", "permutation_p_two_sided"])
    note("time_per_round.csv",
         "per loosest cell (seed 0): mean of per-run time per round (wall_time_seconds / draft_rounds; per-run "
         "values are in per_request.csv) for the relaxed arm and its strict pair, their ratio, and lambda.")
    note("time_per_round_regression.csv",
         "OLS of per-run time per round (s) on output_tokens, per target, seed 0: scope=strict (strict runs only) "
         "and scope=all (strict + the five rules at every alpha run; guard/cascade variants excluded), dataset=all; "
         "plus per-dataset strict-only fits (extra). Old-box runs only (machine=oldbox in per_request.csv): the "
         "addendum's step-5.1 grid cells are seed 0 too but ran on Nibi, whose time per round differs.")
    note("time_per_round_spearman.csv",
         "Spearman rho between lambda and the time-per-round ratio over the 60 loosest cells (average ranks), "
         "two-sided permutation p-value from 20,000 shuffles (numpy seed 20261001).")


def a_admitted_tokens(rows, cells, args):
    loose = loosest()
    from array import array
    groups: dict[tuple, dict[str, array]] = defaultdict(lambda: {"p": array("d"), "rank": array("d"), "entropy": array("d")})
    n_runs = defaultdict(int)
    for base in BASE:
        for suffix, target in TARGETS.items():
            ds = base + suffix
            for method in FIVE:
                for trace in sorted((REPO / "runs" / ds / method).glob(f"*/case_*/seed_{args.seed}/proposals.jsonl")):
                    alpha = alpha_of(trace.parent.parent.parent.name)
                    scopes = ["all_alphas"] + (["loosest_alpha"] if alpha == loose[(ds, method)] else [])
                    for scope in scopes:
                        n_runs[(target, method, scope)] += 1
                    with trace.open(encoding="utf-8") as handle:
                        for line in handle:
                            if '"actually_accepted":true' not in line:
                                continue
                            d = json.loads(line)
                            if d.get("lossy_only_accepted"):
                                cls = "lossy_only"
                            elif d.get("strict_would_accept") and d.get("lossy_would_accept"):
                                cls = "both"
                            else:
                                continue
                            for scope in scopes:
                                g = groups[(target, method, scope, cls)]
                                for key, field in (("p", "p"), ("rank", "target_rank"), ("entropy", "target_entropy")):
                                    value = d.get(field)
                                    g[key].append(float("nan") if value is None else float(value))
    out = []
    for (target, method, scope, cls), g in sorted(groups.items()):
        row = {"target": target, "method": method, "scope": scope, "token_class": cls,
               "n_traced_runs": n_runs[(target, method, scope)], "n_tokens": len(g["p"])}
        for key in ("p", "rank", "entropy"):
            v = np.frombuffer(g[key], dtype=float)
            v = v[~np.isnan(v)]
            if len(v):
                row[f"{key}_mean"] = float(v.mean())
                row[f"{key}_median"] = float(np.median(v))
                row[f"{key}_p10"] = float(np.percentile(v, 10))
                row[f"{key}_p90"] = float(np.percentile(v, 90))
        out.append(row)
    fields = ["target", "method", "scope", "token_class", "n_traced_runs", "n_tokens"] + [
        f"{k}_{s}" for k in ("p", "rank", "entropy") for s in ("mean", "median", "p10", "p90")]
    write_csv("admitted_tokens.csv", out, fields)
    note("admitted_tokens.csv",
         "traced runs only (runs/<dataset>/<method>/<alpha>/case_*/seed_0/proposals.jsonl, patches/relaxation_trace.py; "
         "the campaign traced its first 12 cases and the calibration probes): drafted tokens that were committed, split "
         "into lossy_only (lossy_only_accepted: the relaxed rule accepted, strict would not have on the same u) and both "
         "(strict_would_accept and lossy_would_accept). Distribution (mean, median, p10, p90) of the target's "
         "probability p of that token, its rank under the target (0 = argmax), and the target's entropy at that "
         "position (nats), per (target, method); scope = the loosest alpha only, or every traced alpha. GPT-OSS only: "
         "the Qwen3 runs' proposals.jsonl files are empty (the tracer hooks the V1 sampler; Qwen3-8B runs on V2).")


def a_eq4(rows, cells, args):
    rng = np.random.default_rng(RNG_SEED)
    out = []
    for c in cells:
        p = [(r, s) for r, s in c["pairs"] if r["draft_rounds"] is not None and s["draft_rounds"] is not None]
        if not p:
            continue
        lr, ls = mean([r["l_bar"] for r, _ in p]), mean([s["l_bar"] for _, s in p])
        Lr, Ls = np.array([r["output_tokens"] for r, _ in p], float), np.array([s["output_tokens"] for _, s in p], float)
        Rr, Rs = np.array([r["draft_rounds"] for r, _ in p], float), np.array([s["draft_rounds"] for _, s in p], float)
        Tr, Ts = np.array([r["wall_time_seconds"] for r, _ in p], float), np.array([s["wall_time_seconds"] for _, s in p], float)
        gain = (lr + 1) / (ls + 1)
        lam = Lr.mean() / Ls.mean()
        rounds_ratio, time_ratio = Rr.mean() / Rs.mean(), Tr.mean() / Ts.mean()
        t_lo, t_hi = boot_ratio_ci(Tr, Ts, rng)
        r_lo, r_hi = boot_ratio_ci(Rr, Rs, rng)
        out.append({
            "target": c["target"], "dataset": c["dataset"], "method": c["method"], "alpha": c["alpha"], "n_pairs": len(p),
            "l_bar_relaxed": lr, "l_bar_strict": ls, "gain": gain, "lambda": lam, "gain_over_lambda": gain / lam,
            "rounds_ratio": rounds_ratio, "rounds_ratio_ci_lo": r_lo, "rounds_ratio_ci_hi": r_hi,
            "time_ratio": time_ratio, "time_ratio_ci_lo": t_lo, "time_ratio_ci_hi": t_hi,
            "eq4_predicts_win": int(gain / lam > 1), "rounds_win": int(rounds_ratio < 1), "time_win": int(time_ratio < 1),
            "time_loss_beyond_ci": int(t_lo > 1),
        })
    write_csv("eq4_vs_measured.csv", out, list(out[0].keys()))
    n = {k: sum(r[k] for r in out) for k in ("eq4_predicts_win", "rounds_win", "time_win", "time_loss_beyond_ci")}
    eq4_time_loss = sum(1 for r in out if r["eq4_predicts_win"] and r["time_ratio"] > 1)
    rounds_time_loss = sum(1 for r in out if r["rounds_win"] and r["time_ratio"] > 1)
    eq4_time_loss_sig = sum(1 for r in out if r["eq4_predicts_win"] and r["time_loss_beyond_ci"])
    rounds_time_loss_sig = sum(1 for r in out if r["rounds_win"] and r["time_loss_beyond_ci"])
    summary = [{"cells": len(out), "eq4_wins": n["eq4_predicts_win"], "rounds_wins": n["rounds_win"],
                "time_wins": n["time_win"], "time_losses_beyond_ci": n["time_loss_beyond_ci"],
                "eq4_wins_that_are_time_losses": eq4_time_loss, "rounds_wins_that_are_time_losses": rounds_time_loss,
                "eq4_wins_that_are_time_losses_beyond_ci": eq4_time_loss_sig,
                "rounds_wins_that_are_time_losses_beyond_ci": rounds_time_loss_sig,
                "expected_from_paper": "33 eq4 / 38 rounds / 27 time / 6 eq4->time loss / 11 rounds->time loss"}]
    write_csv("eq4_vs_measured_summary.csv", summary, list(summary[0].keys()))
    print("eq4 summary:", json.dumps(summary[0]))
    note("eq4_vs_measured.csv",
         "per loosest cell (seed 0), paired with strict: Xia et al. Eq. 4 relative to lossless at equal N_draft "
         "reduces to gain/lambda with gain = (l_bar + 1) / (l_bar* + 1) (mean per-run l_bar, relaxed vs strict) "
         "and lambda = mean completion tokens ratio. Measured: rounds_ratio = mean draft_rounds ratio, time_ratio "
         "= mean wall_time_seconds ratio, each with a 95% paired bootstrap interval (10,000 case resamples, numpy "
         "seed 20261001). Flags: eq4_predicts_win = gain/lambda > 1; rounds_win = rounds_ratio < 1; time_win = "
         "time_ratio < 1; time_loss_beyond_ci = the time interval lies entirely above 1.")
    note("eq4_vs_measured_summary.csv",
         "counts over the 60 cells of eq4_vs_measured.csv; '... that are time losses' = time_ratio > 1 (and the "
         "_beyond_ci variants use time_loss_beyond_ci); expected_from_paper = the sanity values the campaign "
         "plan quotes from the paper's tables.")


ANALYSES = {
    "per_request": a_per_request, "split_inflation": a_split_inflation, "censoring": a_censoring,
    "distribution": a_distribution, "repetition": a_repetition, "time_per_round": a_time_per_round,
    "admitted_tokens": a_admitted_tokens, "eq4": a_eq4,
}


def write_readme() -> None:
    path = OUT / "README.md"
    existing = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^- `([^`]+)`: (.*)$", line)
            if m:
                existing[m.group(1)] = m.group(2)
    existing.update(README)
    lines = ["# Step 1 analyses (zero-GPU)", "",
             "Written by `scripts/addendum_analysis.py` from the local `runs/` tree; one line per CSV. "
             "Cells, pairing and the loosest-alpha rule are defined in the script's docstring: loosest = the "
             "maximum alpha of the method in `campaign/results/<dataset>.csv`, paired with `strict` of the same "
             "dataset on the same cases, seed 0, 60 cells (5 methods x 6 datasets x 2 targets).", ""]
    lines += [f"- `{name}`: {text}" for name, text in sorted(existing.items())]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-root", type=pathlib.Path, default=REPO / "runs")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--only", nargs="*", choices=sorted(ANALYSES), default=None)
    args = parser.parse_args()
    global OUT_SUFFIX
    OUT_SUFFIX = f"__seed{args.seed}" if args.seed != 0 else ""
    rows = load_runs(args.runs_root)
    print(f"loaded {len(rows)} runs")
    cells = loosest_cells(rows, args.seed)
    for name, fn in ANALYSES.items():
        if args.only and name not in args.only:
            continue
        fn(rows, cells, args)
    if OUT_SUFFIX:  # describe the per-seed variants without touching the seed-0 descriptions
        for name in list(README):
            README[name.replace(".csv", f"{OUT_SUFFIX}.csv")] = (f"as `{name}`, but seed {args.seed} (Nibi, H100 SXM) "
                                                                 "instead of the paper's seed 0; cells without that seed are absent.")
            del README[name]
    write_readme()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
