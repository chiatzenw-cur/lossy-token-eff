"""Grade finished cross-method runs, append per-case metrics to a ledger CSV,
then delete that run's raw text outputs. Only the four campaign methods under
autoresearch/cross_method_runs/ are touched; run.json is always kept.

Usage: python autoresearch/cross_method_metrics.py [--once]
"""
import argparse, csv, importlib, json, pathlib, sys, time
from unittest import mock

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
for _m in ("matplotlib", "matplotlib.pyplot", "matplotlib.ticker", "matplotlib.figure"):
    sys.modules[_m] = mock.MagicMock()
from campaign_report import GRADERS  # noqa: E402

RUNS = REPO / "autoresearch" / "cross_method_runs"
LEDGER_DIR = REPO / "autoresearch" / "cross_method_metrics"
METHODS = ("spec_casc_tok", "spec_casc_tok_force_commit", "mentored_dec", "mentored_dec_force_commit",
           "spec_casc_tok_qwen3_force_commit", "mentored_dec_qwen3_force_commit",
           "cactus_force_commit", "r_fuzzy_force_commit", "spec_casc_opt_force_commit",
           "cactus_qwen3_force_commit", "r_fuzzy_qwen3_force_commit", "spec_casc_opt_qwen3_force_commit")
RAW_FILES = ("output.txt", "proposals.jsonl", "response.json")
FIELDS = ["dataset", "method", "params", "case", "server_mode", "output_tokens", "finish_reason",
          "hit_cap", "reached_final_channel", "l_bar", "verdict", "correct", "record_valid",
          "think_close_seen", "think_close_char"]


FIXED_RS_SHA256 = {
    "spec_casc_tok_force_commit": "3b422e8ed28a63829828322295e632ace68f401c86b5b7a8acb215c8549f2444",
    "mentored_dec_force_commit": "ab5116f4f69338c70b5a58c2d315fbe46abf03fb7b693e38d43a9329ee53d220",
    "cactus_force_commit": "57cb258370388df8efcc5d11aceac0481551952942cd74e0def1c72a39bb19dd",
    "r_fuzzy_force_commit": "8fe4dac3cd5e2442169c5aa8aa85f0b42d53fed5df1d5b89d8cb2d4c523d9651",
    "spec_casc_opt_force_commit": "6be37559762d97b4896517f48a1117c5440261db772d94733c7e3646035d13fb",
}


def record_valid(method, mode, run_dir):
    if method.endswith("_qwen3_force_commit"):
        # Qwen3 V2 hook is stateless per request (decision reads only that request's buffer).
        return True
    """Force-commit runs on warm servers are valid only if they ran under the
    per-request-keyed patch: the installed rejection_sampler.py hash, recorded in
    config.json as vllm.v1_sha256, must match the fixed hash. Fresh-per-case runs and
    non-force methods are valid."""
    if mode != "warm" or method not in FIXED_RS_SHA256:
        return True
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    return config.get("vllm", {}).get("v1_sha256") == FIXED_RS_SHA256[method]


def ledger_path(dataset):
    return LEDGER_DIR / f"{dataset}.csv"


def load_ledger(dataset):
    path = ledger_path(dataset)
    if not path.is_file():
        return set()
    with path.open(encoding="utf-8") as h:
        return {(r["method"], r["params"], r["case"]) for r in csv.DictReader(h)}


def server_mode(dataset, method):
    # aime24 mentored_dec arms were run fresh-per-case earlier; everything else
    # in this campaign ran on warm servers.
    return "fresh" if (dataset == "aime24" and method.startswith("mentored_dec")) else "warm"


def grade_run(dataset, run_dir):
    spec = GRADERS.get(dataset.removesuffix("_qwen3"))
    if spec is None:
        return None, None  # token-only dataset (mtbench)
    module = importlib.import_module(spec["module"])
    kwargs = spec["kwargs"](module) if callable(spec["kwargs"]) else spec["kwargs"]
    row = module.grade(run_dir, REPO / "prompts" / dataset, **kwargs)
    if row is None:
        return None, None
    verdict = row["verdict"]
    return verdict, verdict in spec["correct_verdicts"]


def process(dataset, method, params, case_dir):
    run_json = case_dir / "seed_0" / "run.json"
    if not run_json.is_file():
        return None
    data = json.loads(run_json.read_text(encoding="utf-8"))
    if data.get("status") != "ok":
        return None
    seed_dir = case_dir / "seed_0"
    verdict, correct = grade_run(dataset, seed_dir)
    think_seen, think_char = "", ""
    if dataset.endswith("_qwen3") and (seed_dir / "output.txt").is_file():
        text = (seed_dir / "output.txt").read_text(encoding="utf-8")
        at = text.find("</think>")
        think_seen, think_char = str(at >= 0), str(at)
    finish = data.get("finish_reason")
    row = {
        "dataset": dataset, "method": method, "params": params, "case": case_dir.name,
        "server_mode": server_mode(dataset, method),
        "output_tokens": data.get("output_tokens"), "finish_reason": finish,
        "hit_cap": finish == "length", "reached_final_channel": data.get("reached_final_channel"),
        "l_bar": data.get("l_bar"), "verdict": verdict or "", "correct": "" if correct is None else correct,
    }
    row["record_valid"] = record_valid(method, row["server_mode"], seed_dir)
    row["think_close_seen"], row["think_close_char"] = think_seen, think_char
    return row


def append_row(dataset, row):
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    path = ledger_path(dataset)
    new = not path.is_file()
    with path.open("a", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def delete_raw(seed_dir):
    for name in RAW_FILES:
        p = seed_dir / name
        if p.is_file():
            p.unlink()


def sweep(datasets):
    done = 0
    for dataset in datasets:
        recorded = load_ledger(dataset)
        for method in METHODS:
            mdir = RUNS / dataset / method
            if not mdir.is_dir():
                continue
            for params_dir in sorted(p for p in mdir.iterdir() if p.is_dir()):
                for case_dir in sorted(p for p in params_dir.iterdir() if p.is_dir()):
                    key = (method, params_dir.name, case_dir.name)
                    if key in recorded:
                        continue
                    row = process(dataset, method, params_dir.name, case_dir)
                    if row is None:
                        continue
                    append_row(dataset, row)
                    delete_raw(case_dir / "seed_0")
                    recorded.add(key)
                    done += 1
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--datasets", nargs="+", default=["aime24", "gsm8k", "humaneval", "mtbench", "livecodebench", "longbench_v2",
                                                      "aime24_qwen3", "gsm8k_qwen3", "humaneval_qwen3", "mtbench_qwen3",
                                                      "livecodebench_qwen3", "longbench_v2_qwen3"])
    args = ap.parse_args()
    while True:
        n = sweep(args.datasets)
        if n:
            print(f"{time.strftime('%FT%T')} graded+cleaned {n} run(s)", flush=True)
        if args.once:
            return
        time.sleep(120)


if __name__ == "__main__":
    main()
