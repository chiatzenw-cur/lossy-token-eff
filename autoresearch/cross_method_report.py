"""Paired baseline vs force-commit comparison from the per-dataset metrics ledger
(autoresearch/cross_method_metrics/<dataset>.csv). Usage:
    python autoresearch/cross_method_report.py <dataset> <threshold>
"""
import csv, json, pathlib, sys

REPO = pathlib.Path(__file__).resolve().parent.parent
ds, thr = sys.argv[1], int(sys.argv[2])
rows = list(csv.DictReader((REPO / "autoresearch/cross_method_metrics" / f"{ds}.csv").open(encoding="utf-8")))

PAIRS = [
    ("spec_casc_tok", "alpha0.8", "spec_casc_tok_force_commit", f"alpha0.8_t{thr}"),
    ("mentored_dec", "alpha0.75", "mentored_dec_force_commit", f"alpha0.75_t{thr}"),
]


def pick(method, params):
    return {r["case"]: r for r in rows if r["method"] == method and r["params"] == params}


def tok(r): return int(r["output_tokens"])


out = {}
for bm, bp, fm, fp in PAIRS:
    b, f = pick(bm, bp), pick(fm, fp)
    common = sorted(set(b) & set(f))
    if not common:
        out[bm] = {"n": 0, "note": f"no paired cases (base {len(b)}, fc {len(f)})"}
        continue
    graded = all(b[c]["correct"] != "" for c in common)
    n = len(common)
    res = {
        "server_mode": sorted({b[c]["server_mode"] for c in common} | {f[c]["server_mode"] for c in common}),
        "n": n,
        "base_mean_tokens": round(sum(tok(b[c]) for c in common) / n, 1),
        "fc_mean_tokens": round(sum(tok(f[c]) for c in common) / n, 1),
        "base_cap_hits": sum(b[c]["hit_cap"] == "True" for c in common),
        "fc_cap_hits": sum(f[c]["hit_cap"] == "True" for c in common),
        "byte_identical_tokens": sum(tok(b[c]) == tok(f[c]) for c in common),
    }
    res["delta_pct"] = round((res["fc_mean_tokens"] - res["base_mean_tokens"]) / res["base_mean_tokens"] * 100, 2)
    if graded:
        res["base_correct"] = sum(b[c]["correct"] == "True" for c in common)
        res["fc_correct"] = sum(f[c]["correct"] == "True" for c in common)
        res["accuracy_flips"] = [
            f"{c}: {'correct' if b[c]['correct']=='True' else 'not-correct'} -> {'correct' if f[c]['correct']=='True' else 'not-correct'} "
            f"(base {tok(b[c])} {b[c]['finish_reason']}, fc {tok(f[c])} {f[c]['finish_reason']})"
            for c in common if b[c]["correct"] != f[c]["correct"]
        ]
    else:
        res["accuracy"] = "no grader (token-only)"
    out[bm] = res
print(json.dumps({"dataset": ds, "threshold": thr, "results": out}, indent=2))
