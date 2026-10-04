import sys, json, pathlib
sys.path.insert(0, "/home/chiatzen/lossy-token-eff/scripts")
from unittest import mock
for _m in ("matplotlib","matplotlib.pyplot","matplotlib.ticker","matplotlib.figure"):
    sys.modules[_m]=mock.MagicMock()
from campaign_report import load_all_runs, grade_accuracy
REPO = pathlib.Path("/home/chiatzen/lossy-token-eff")
ds, thr = sys.argv[1], int(sys.argv[2])
runs_root = REPO / "autoresearch/cross_method_runs"
rows = load_all_runs(runs_root, ds)
acc = grade_accuracy(runs_root, ds)
PAIRS = [
    ("spec_casc_tok", "alpha0.8", "spec_casc_tok_force_commit", f"alpha0.8_t{thr}"),
    ("mentored_dec", "alpha0.75", "mentored_dec_force_commit", f"alpha0.75_t{thr}"),
]
def pick(method, params):
    out = {}
    for r in rows:
        if r["method"] == method and r["params"] == params and r["status"] == "ok":
            out[r["case"]] = r
    return out
results = {}
for bm, bp, fm, fp in PAIRS:
    b, f = pick(bm, bp), pick(fm, fp)
    common = sorted(set(b) & set(f))
    if not common:
        results[bm] = {"n": 0, "note": f"no paired cases yet (base {len(b)}, fc {len(f)})"}
        continue
    def caps(d): return sum(1 for c in common if d[c]["finish_reason"] == "length")
    def mean(d): return sum(d[c]["output_tokens"] for c in common) / len(common)
    key = lambda m, p, c: (m, p, c)
    graded = any(key(bm, bp, c) in acc for c in common)
    res = {
        "n": len(common),
        "base_mean_tokens": round(mean(b), 1), "fc_mean_tokens": round(mean(f), 1),
        "delta_pct": round((mean(f) - mean(b)) / mean(b) * 100, 2),
        "base_caps": caps(b), "fc_caps": caps(f),
    }
    if graded:
        res["base_correct"] = sum(acc.get(key(bm, bp, c), False) for c in common)
        res["fc_correct"] = sum(acc.get(key(fm, fp, c), False) for c in common)
        flips = []
        for c in common:
            x, y = acc.get(key(bm, bp, c)), acc.get(key(fm, fp, c))
            if x != y:
                flips.append(f"{c}: {'correct' if x else 'not-correct'} -> {'correct' if y else 'not-correct'} "
                             f"(base {b[c]['output_tokens']} {b[c]['finish_reason']}, fc {f[c]['output_tokens']} {f[c]['finish_reason']})")
        res["accuracy_flips"] = flips
    else:
        res["accuracy"] = "no grader (token-only)"
    tok_changed = [c for c in common if b[c]["output_tokens"] != f[c]["output_tokens"]]
    res["token_changed_cases"] = len(tok_changed)
    res["byte_identical_tokens"] = len(common) - len(tok_changed)
    results[bm] = res
print(json.dumps({"dataset": ds, "threshold": thr, "results": results}, indent=2))
