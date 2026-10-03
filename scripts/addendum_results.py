#!/usr/bin/env python3
"""Write campaign/addendum/RESULTS.md from the addendum's CSVs (every number is
read from a named CSV row, never typed in), plus the hand-written observations
in campaign/addendum/RESULTS_notes.md (included verbatim at the end).

  python3 scripts/addendum_results.py
"""

from __future__ import annotations

import csv
import datetime as dt
import pathlib
from collections import Counter, defaultdict

REPO = pathlib.Path(__file__).resolve().parent.parent
ADD = REPO / "campaign" / "addendum"
AN = ADD / "analysis"
DS_ORDER = ["gsm8k", "aime24", "humaneval", "livecodebench", "mtbench", "longbench_v2"]
METHOD_ORDER = ["mentored_dec", "cactus", "spec_casc_opt", "r_fuzzy", "spec_casc_tok"]
N_CASES = {"gsm8k": 150, "humaneval": 150, "longbench_v2": 150, "livecodebench": 90, "mtbench": 80, "aime24": 30}


def rows(path: pathlib.Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def f(x, nd=2):
    if x in (None, ""):
        return "-"
    try:
        v = float(x)
    except ValueError:
        return str(x)
    return f"{v:.{nd}f}"


def pct(x, nd=0):
    return "-" if x in (None, "") else f"{100 * float(x):.{nd}f}%"


def rel(p: pathlib.Path) -> str:
    return str(p.relative_to(REPO))


def cell_sort(r):
    return (r.get("target", ""), DS_ORDER.index(r["dataset"]) if r.get("dataset") in DS_ORDER else 9,
            METHOD_ORDER.index(r["method"]) if r.get("method") in METHOD_ORDER else 9)


def section_status() -> list[str]:
    m = rows(ADD / "manifest.csv")
    out = ["## Status", ""]
    if not m:
        return out + ["(no manifest yet)", ""]
    by = defaultdict(Counter)
    for r in m:
        by[r["step"]][r["status"]] += 1
    used = sum(float(r["gpu_hours_actual"] or 0) for r in m)
    left = sum(float(r["gpu_hours_est"] or 0) for r in m if r["status"] in ("queued", "running", "pending"))
    blocked = sum(float(r["gpu_hours_est"] or 0) for r in m if r["status"] == "blocked")
    out += [f"Source: `{rel(ADD / 'manifest.csv')}` ({len(m)} rows). GPU-hours used so far (sum of "
            f"`gpu_hours_actual`): {used:.1f}; estimated remaining, runnable rows: {left:.1f}; blocked rows: {blocked:.1f}.", "",
            "| step | " + " | ".join(["done", "running", "queued", "pending", "blocked"]) + " |", "|---|---:|---:|---:|---:|---:|"]
    for step in sorted(by, key=lambda s: [float(x) for x in s.split(".")]):
        c = by[step]
        out.append(f"| {step} | " + " | ".join(str(c.get(k, 0)) for k in ("done", "running", "queued", "pending", "blocked")) + " |")
    return out + [""]


def section_step1() -> list[str]:
    out = ["## Step 1: zero-GPU analyses (seed 0, the paper's data)", ""]
    s = rows(AN / "eq4_vs_measured_summary.csv")
    if s:
        s = s[0]
        out += [f"**Eq. 4 vs measured** (`{rel(AN / 'eq4_vs_measured_summary.csv')}`, row 1; per cell: "
                f"`{rel(AN / 'eq4_vs_measured.csv')}`), {s['cells']} loosest cells: Eq. 4 predicts a win in "
                f"{s['eq4_wins']}, rounds win in {s['rounds_wins']}, time win in {s['time_wins']}; "
                f"{s['eq4_wins_that_are_time_losses']} Eq. 4 wins and {s['rounds_wins_that_are_time_losses']} rounds wins "
                f"are time losses (paper: 33 / 38 / 27 / 6 / 11 -- reproduced exactly). New: {s['time_losses_beyond_ci']} "
                f"cells are time losses beyond the 95% paired bootstrap interval; of the Eq. 4-win time losses "
                f"{s['eq4_wins_that_are_time_losses_beyond_ci']}, and of the rounds-win time losses "
                f"{s['rounds_wins_that_are_time_losses_beyond_ci']}, lie beyond it.", ""]
    e = sorted(rows(AN / "eq4_vs_measured.csv"), key=cell_sort)
    if e:
        out += ["| target | dataset | method | alpha | lambda | gain | gain/lambda | rounds ratio [95% CI] | time ratio [95% CI] |",
                "|---|---|---|---:|---:|---:|---:|---|---|"]
        for r in e:
            out.append(f"| {r['target']} | {r['dataset']} | {r['method']} | {r['alpha']} | {f(r['lambda'])} | {f(r['gain'])} | "
                       f"{f(r['gain_over_lambda'])} | {f(r['rounds_ratio'])} [{f(r['rounds_ratio_ci_lo'])}, {f(r['rounds_ratio_ci_hi'])}] | "
                       f"{f(r['time_ratio'])} [{f(r['time_ratio_ci_lo'])}, {f(r['time_ratio_ci_hi'])}] |")
        out.append("")
    si = sorted(rows(AN / "split_inflation.csv"), key=cell_sort)
    if si:
        out += [f"**Where the extra length goes** (`{rel(AN / 'split_inflation.csv')}`; thinking = GPT-OSS analysis channel / "
                "Qwen3 `<think>` blocks, characters):", "",
                "| target | dataset | method | lambda (tokens) | lambda thinking | lambda answer | share of extra in thinking |",
                "|---|---|---|---:|---:|---:|---:|"]
        for r in si:
            out.append(f"| {r['target']} | {r['dataset']} | {r['method']} | {f(r['lambda'])} | {f(r['lambda_think_chars'])} | "
                       f"{f(r['lambda_answer_chars'])} | {pct(r['extra_share_think'])} |")
        out.append("")
    ce = sorted(rows(AN / "censoring.csv"), key=cell_sort)
    if ce:
        out += [f"**Censoring** (`{rel(AN / 'censoring.csv')}`): cap-out rates and lambda / accuracy restricted to pairs where both "
                "runs finished.", "",
                "| target | dataset | method | cap-out relaxed | cap-out strict | lambda all | lambda both finished | "
                "acc relaxed / strict (all) | acc relaxed / strict (both finished) | n both finished |",
                "|---|---|---|---:|---:|---:|---:|---|---|---:|"]
        for r in ce:
            out.append(f"| {r['target']} | {r['dataset']} | {r['method']} | {pct(r['capout_rate_relaxed'])} | {pct(r['capout_rate_strict'])} | "
                       f"{f(r['lambda_all'])} | {f(r['lambda_both_finished'])} | {pct(r['acc_relaxed_all'])} / {pct(r['acc_strict_all'])} | "
                       f"{pct(r['acc_relaxed_both_finished'])} / {pct(r['acc_strict_both_finished'])} | {r['n_pairs_both_finished']} |")
        out.append("")
    di = sorted(rows(AN / "distribution.csv"), key=cell_sort)
    if di:
        out += [f"**Uniform shift or runaway completions?** (`{rel(AN / 'distribution.csv')}`): per-case L_relaxed / L_strict.", "",
                "| target | dataset | method | p10 | p50 | p90 | share > 2 | top-10% cases' share of net extra |",
                "|---|---|---|---:|---:|---:|---:|---:|"]
        for r in di:
            out.append(f"| {r['target']} | {r['dataset']} | {r['method']} | {f(r['ratio_p10'])} | {f(r['ratio_p50'])} | "
                       f"{f(r['ratio_p90'])} | {pct(r['share_ratio_gt2'])} | {pct(r['top10pct_share_of_net_extra'])} |")
        out.append("")
    rp = sorted(rows(AN / "repetition.csv"), key=cell_sort)
    if rp:
        out += [f"**Exact repetition** (`{rel(AN / 'repetition.csv')}`; per run: `{rel(AN / 'repetition_runs.csv')}`): share of "
                "tokens inside a 50-gram that occurred earlier in the same output, and the longest repeated token run.", "",
                "| target | dataset | method | rep-50 share relaxed | rep-50 share strict | longest repeat relaxed | longest repeat strict |",
                "|---|---|---|---:|---:|---:|---:|"]
        for r in rp:
            out.append(f"| {r['target']} | {r['dataset']} | {r['method']} | {pct(r['mean_rep50_frac_relaxed'], 2)} | "
                       f"{pct(r['mean_rep50_frac_strict'], 2)} | {f(r['mean_longest_repeat_relaxed'], 0)} | {f(r['mean_longest_repeat_strict'], 0)} |")
        out.append("")
    tr = rows(AN / "time_per_round_regression.csv")
    sp = rows(AN / "time_per_round_spearman.csv")
    if tr:
        out += [f"**Time per round** (`{rel(AN / 'time_per_round.csv')}`, `{rel(AN / 'time_per_round_regression.csv')}`, "
                f"`{rel(AN / 'time_per_round_spearman.csv')}`): OLS of time per round on output tokens (dataset = all):", ""]
        for r in tr:
            if r["dataset"] == "all":
                out.append(f"- {r['target']}, {r['scope']} runs (n={r['n_runs']}): slope {float(r['slope_s_per_token']):.3g} s/token, "
                           f"intercept {float(r['intercept_s']) * 1000:.1f} ms, R^2 {f(r['r2'], 3)}")
        if sp:
            out.append(f"- Spearman(lambda, time-per-round ratio) over {sp[0]['n_cells']} cells: rho = {f(sp[0]['spearman_rho'], 3)}, "
                       f"two-sided permutation p = {sp[0]['permutation_p_two_sided']} (20,000 shuffles)")
        out.append("")
    ad = rows(AN / "admitted_tokens.csv")
    if ad:
        out += [f"**What the relaxed rules admit** (`{rel(AN / 'admitted_tokens.csv')}`, GPT-OSS traced runs, loosest alpha): "
                "tokens accepted only because of the relaxation vs tokens both rules accept.", "",
                "| method | class | tokens | target p median | target p mean | target rank mean | rank p90 | target entropy mean |",
                "|---|---|---:|---:|---:|---:|---:|---:|"]
        for r in sorted(ad, key=lambda r: (METHOD_ORDER.index(r["method"]), r["token_class"])):
            if r["scope"] == "loosest_alpha":
                out.append(f"| {r['method']} | {r['token_class']} | {r['n_tokens']} | {f(r['p_median'], 3)} | {f(r['p_mean'], 3)} | "
                           f"{f(r['rank_mean'], 1)} | {f(r['rank_p90'], 0)} | {f(r['entropy_mean'], 2)} |")
        out.append("")
    mj = rows(AN / "mtbench_judge_summary.csv")
    if not mj:
        return out + ["**MT-Bench judge (step 1.9)**: pending (`scripts/addendum_mtbench_judge.py`).", ""]
    loose = {(r["target"], r["method"]): r["alpha"] for r in rows(AN / "eq4_vs_measured.csv") if r["dataset"] == "mtbench"}
    out += [f"**MT-Bench judge (step 1.9)** (`{rel(AN / 'mtbench_judge_summary.csv')}`, seed-0 rows at the loosest "
            f"alpha; per run: `{rel(AN / 'mtbench_judge.csv')}`): FastChat single-answer grading of turn 1 "
            "(`single-math-v1` with the GPT-4 reference answer for math/reasoning/coding, `single-v1` otherwise), "
            "judge claude-fable-5-1 at effort medium through the Message Batches API; a run whose output never "
            "reaches an answer scores 1 without a call. Mean score out of 10 with a 95% bootstrap interval; "
            "'answered only' leaves the no-answer runs out.", "",
            "| target | method | alpha | mean score [95% CI] | answered only | no answer | refusals |",
            "|---|---|---:|---|---:|---:|---:|"]
    for target in ("gpt-oss-20b", "qwen3-8b"):
        for method in ["strict", *METHOD_ORDER]:
            alpha = "strict" if method == "strict" else loose.get((target, method))
            r = next((x for x in mj if (x["target"], x["method"], x["alpha"], x["seed"]) == (target, method, alpha, "0")), None)
            if r:
                out.append(f"| {target} | {method} | {alpha} | {f(r['mean_score'])} [{f(r['mean_score_ci_lo'])}, "
                           f"{f(r['mean_score_ci_hi'])}] | {f(r.get('mean_score_answered_only'))} | {r['n_no_answer']} | "
                           f"{r['n_refusal']} |")
    return out + [""]


def section_best() -> list[str]:
    path = ADD / "best_setting.csv"
    b = sorted(rows(path), key=cell_sort)
    out = ["## Step 5: alpha grid completion and best-setting validation", ""]
    if not b:
        return out + ["Pending.", ""]
    out += [f"Source: `{rel(path)}`, one row per (target, dataset, method). Chosen alpha = the grid alpha with the "
            "lowest seed-0 time ratio among those whose accuracy is within 2 points of strict (mtbench, ungraded: "
            "rounds ratio < 1); `chosen_alpha_by_rounds_ratio` = the same choice made on the rounds ratio. Time "
            "ratios of the step-5.1 additions are taken against the step-0.5 strict reference on the same machine "
            "(Nibi for GPT-OSS, Killarney for Qwen3; `s0_time_ratio_basis`, `hardware_s0_*`). Seed 1 = the step-5.2 "
            "validation run, paired with strict seed 1 on the same machine (`s1_hardware`, `s1_strict_hardware`; "
            "'-' = not complete yet); validated = seed-1 time ratio < 1 and the same accuracy rule holds on seed 1. "
            "s1 same node = seed-1 pairs whose arm and strict ran on one node (`s1_same_node_pairs`; README "
            "deviations 13-17): a seed-1 time verdict on cross-node pairs carries the node effect, the rounds ratio "
            "does not.", "",
            "| target | dataset | method | grid complete | chosen alpha (by rounds) | s0 lambda | s0 rounds ratio | "
            "s0 time ratio | s0 acc / strict | s1 lambda | s1 rounds ratio | s1 time ratio | s1 acc / strict | "
            "s1 same node | validated |",
            "|---|---|---|---|---|---:|---:|---:|---|---:|---:|---:|---|---:|---|"]
    for r in b:
        s1_full = int(float(r.get("s1_n_pairs") or 0)) == N_CASES.get(r["dataset"], -1)  # all cases paired
        s1 = (lambda k: f(r.get(k)) if s1_full else "-")
        out.append(f"| {r['target']} | {r['dataset']} | {r['method']} | {r['grid_complete']} | "
                   f"{r['chosen_alpha'] or '-'} ({r['chosen_alpha_by_rounds_ratio'] or '-'}) | {f(r.get('s0_lambda'))} | "
                   f"{f(r.get('s0_rounds_ratio'))} | {f(r.get('s0_time_ratio'))} | {pct(r.get('s0_accuracy'))} / "
                   f"{pct(r.get('s0_accuracy_strict'))} | {s1('s1_lambda')} | {s1('s1_rounds_ratio')} | {s1('s1_time_ratio')} | "
                   + (f"{pct(r.get('s1_accuracy'))} / {pct(r.get('s1_accuracy_strict'))}" if s1_full else "-")
                   + (f" | {r.get('s1_same_node_pairs') or '?'}/{r.get('s1_n_pairs')}" if s1_full else " | -")
                   + f" | {({'True': 'yes', 'False': 'no'}).get(r.get('validated') or '', '-')} |")
    return out + [""]


def section_aime() -> list[str]:
    path = ADD / "aime24_repeats.csv"
    a = rows(path)
    out = ["## Step 6: AIME24 accuracy repeats", ""]
    if not a:
        return out + ["Pending.", ""]
    seeds = sorted({k.removeprefix("acc_s") for k in a[0] if k.startswith("acc_s") and k[5:].isdigit()})
    out += [f"Source: `{rel(path)}`, one row per (target, method); seed 0 = the campaign (old box), seeds 1-4 = Nibi. "
            "Interval: two-level bootstrap (problems, then seeds within a problem), 10,000 resamples.", "",
            "| target | method | alpha | " + " | ".join(f"acc s{s}" for s in seeds) + " | mean over seeds [95% CI] | sd across seeds | seeds |",
            "|---|---|---:|" + "---:|" * len(seeds) + "---|---:|---|"]
    for r in a:
        out.append(f"| {r['target']} | {r['method']} | {r['alpha']} | " + " | ".join(pct(r.get(f"acc_s{s}")) for s in seeds)
                   + f" | {pct(r.get('acc_mean_over_seeds'), 1)} [{pct(r.get('acc_ci_lo'), 1)}, {pct(r.get('acc_ci_hi'), 1)}] | "
                   f"{f(r.get('acc_sd_across_seeds'), 3)} | {r.get('seeds_complete') or '-'} |")
    return out + [""]


SB_CAT_ORDER = ["all", "coding", "math", "humanities", "stem", "writing", "summarization", "roleplay", "rag",
                "multilingual", "reasoning", "qa"]


def arrow(lo, hi) -> str:
    """Marks a ratio whose 95% interval excludes 1."""
    if lo in (None, "") or hi in (None, ""):
        return ""
    return "↓" if float(hi) < 1 else ("↑" if float(lo) > 1 else "")


def same_node_note(r: dict) -> str:
    """' · T same-node 0.91 (249 pairs)' or ' · cross-node' when a row's pairs did not all run on one node."""
    if r.get("same_node") != "False":
        return ""
    if r.get("time_ratio_same_node"):
        return f" · T same-node {f(r['time_ratio_same_node'])} ({r['same_node_pairs']} pairs)"
    return " · cross-node"


def section_speedbench() -> list[str]:
    out = ["## Step 7: SPEED-Bench qualitative split (seed 0; GPT-OSS on Nibi, Qwen3's first 40 prompts per arm on Nibi "
           "and the rest on Killarney)", ""]
    found = False
    for family in ("gpt-oss-20b", "qwen3-8b"):
        path = ADD / "tables" / f"speedbench__{family}.csv"
        eq4_path = ADD / "tables" / f"speedbench_eq4__{family}.csv"
        sum_path = ADD / "tables" / f"speedbench_eq4_summary__{family}.csv"
        pilot_path = ADD / "tables" / f"speedbench_pilot__{family}.csv"
        pilot = rows(pilot_path)
        if pilot:
            found = True
            out += [f"**Token-budget pilot, {family}** (`{rel(pilot_path)}`; strict at 8192 on each category's first 20 "
                    "cases, >10% cap-outs would raise the category to 16384): "
                    + "; ".join(f"{p['category']} {p['capouts']}/{p['n_done']} cap-outs of {p['n_target']} "
                                f"(mean {f(p['mean_completion_tokens'], 0)}, max {p['max_completion_tokens']} tokens) -> "
                                f"budget {p['budget']}" for p in pilot) + ".", ""]
        t = rows(path)
        if not t:
            continue
        found = True
        by = {(r["method"], r["category"]): r for r in t}
        methods = [m for m in METHOD_ORDER if any(k[0] == m for k in by)]
        out += [f"### {family}", "",
                f"Source: `{rel(path)}`, one row per (method, category); Eq. 4 per (method, category): `{rel(eq4_path)}`; "
                f"per-method counts: `{rel(sum_path)}`. Cell = lambda (completion tokens relaxed / strict) · R = verifier "
                "rounds ratio · T = wall-time ratio, all vs strict on the same cases; ↓/↑ = the 95% paired bootstrap "
                "interval lies entirely below/above 1. Strict column: mean completion tokens and cap-out rate. Where "
                "not every pair ran its arm and its strict case on one node (`same_node` False; README deviations "
                "13-17), the cell adds T over the same-node pairs and their count (`time_ratio_same_node`, "
                "`same_node_pairs`), or 'cross-node' when fewer than 10 pairs share a node; R is hardware-independent.", "",
                "| category | strict tokens (cap-out) | " + " | ".join(f"{m} ({next(r['alpha'] for (mm, _), r in by.items() if mm == m)})"
                                                           for m in methods) + " |",
                "|---|---:|" + "---|" * len(methods)]
        for cat in SB_CAT_ORDER:
            s = by.get(("strict", cat))
            if not s:
                continue
            cells = []
            for m in methods:
                r = by.get((m, cat))
                if not r:
                    cells.append("-")
                    continue
                cells.append(f"λ {f(r['lambda'])}{arrow(r['lambda_ci_lo'], r['lambda_ci_hi'])} · "
                             f"R {f(r['rounds_ratio'])}{arrow(r['rounds_ratio_ci_lo'], r['rounds_ratio_ci_hi'])} · "
                             f"T {f(r['time_ratio'])}{arrow(r['time_ratio_ci_lo'], r['time_ratio_ci_hi'])} "
                             f"(n={r['n_pairs']}){same_node_note(r)}")
            out.append(f"| {cat} | {f(s['mean_completion_tokens'], 0)} ({pct(s['capout_rate'])}) | " + " | ".join(cells) + " |")
        out.append("")
        e = rows(eq4_path)
        for r in rows(sum_path):
            m = r["method"]
            cats = [x for x in e if x["method"] == m and x["category"] != "all"]
            saves_r = [x["category"] for x in cats if x["rounds_win"] == "1"]
            saves_t = [x["category"] for x in cats if x["time_win"] == "1"]
            lam = sorted(cats, key=lambda x: float(x["lambda"]))
            overall = by.get((m, "all"), {})
            node = (f" Over all categories T {f(overall.get('time_ratio'))}{same_node_note(overall)}"
                    f" (`{rel(path)}` row `{m}`, category `all`)." if overall.get("same_node") == "False" else "")
            out.append(f"- **{m}** (alpha {r['alpha']}, `{rel(sum_path)}` row `{m}`): fewer verifier rounds in "
                       f"{r['rounds_wins']}/{r['categories']} categories ({', '.join(saves_r) or 'none'}); less wall time in "
                       f"{r['time_wins']}/{r['categories']} ({', '.join(saves_t) or 'none'}); Eq. 4 predicts a win in "
                       f"{r['eq4_wins']}/{r['categories']}; completions longer by lambda {f(lam[0]['lambda'])} "
                       f"({lam[0]['category']}) to {f(lam[-1]['lambda'])} ({lam[-1]['category']}); rounds and time "
                       f"disagree in: {r['rounds_time_disagree'] or 'none'}.{node}")
        out.append("")
    return out + ([] if found else ["Pending.", ""])


def section_seeds() -> list[str]:
    s = sorted(rows(ADD / "seeds" / "summary.csv"), key=cell_sort)
    out = ["## Step 2: seeds on the relaxed arms", ""]
    if not s:
        return out + ["Pending.", ""]
    seeds = sorted({k.split("_s")[-1] for k in s[0] if k.startswith("lambda_s")})
    out += [f"Source: `{rel(ADD / 'seeds' / 'summary.csv')}` (per-seed tables `campaign/addendum/seeds/<dataset>__seed<k>.csv`). "
            "Seed 0 is the campaign's run (old box, H100 PCIe); seeds 1-2 ran on Nibi (H100 SXM), except Qwen3 aime24's "
            "(Killarney H100, step 2.2; README deviation 12). Ratios pair each seed's "
            "relaxed arm with strict of the same seed; '-' = that seed is not complete yet.", "",
            "| target | dataset | method | alpha | " + " | ".join(f"lambda s{k}" for k in seeds) + " | lambda mean (sd) | "
            + " | ".join(f"time ratio s{k}" for k in seeds) + " | time mean (sd) | " + " | ".join(f"acc s{k}" for k in seeds) + " |",
            "|---|---|---|---:|" + "---:|" * (3 * len(seeds) + 2)]
    for r in s:
        out.append(f"| {r['target']} | {r['dataset']} | {r['method']} | {r['alpha']} | "
                   + " | ".join(f(r.get(f"lambda_s{k}")) for k in seeds)
                   + f" | {f(r['lambda_mean'])} ({f(r['lambda_sd'])}) | "
                   + " | ".join(f(r.get(f"time_ratio_s{k}")) for k in seeds)
                   + f" | {f(r['time_ratio_mean'])} ({f(r['time_ratio_sd'])}) | "
                   + " | ".join(pct(r.get(f"accuracy_s{k}")) for k in seeds) + " |")
    return out + [""]


def section_hardware() -> list[str]:
    ss = rows(AN / "seed_shift.csv")
    hm = rows(AN / "hardware_tpr_model.csv")
    out = ["## Hardware dependence of the time ratios (found in step 2)", ""]
    if not ss:
        return out + ["Pending.", ""]
    out += [f"`{rel(AN / 'seed_shift.csv')}`: GPT-OSS cells with seeds 0-2 complete. Seed 0 = the campaign's run on the "
            "old box (H100 PCIe); seeds 1-2 = Nibi (H100 SXM).", "",
            "| metric | cells | mean seed 0 | mean seed 1 | mean seed 2 | mean s1-s0 | mean s2-s1 | cells s1 < s0 | win/loss flips |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in ss:
        out.append(f"| {r['metric']} | {r['n_cells']} | {f(r['mean_s0'], 3)} | {f(r['mean_s1'], 3)} | {f(r['mean_s2'], 3)} | "
                   f"{f(r['mean_s1_minus_s0'], 3)} | {f(r['mean_s2_minus_s1'], 3)} | {r['cells_s1_below_s0']} | "
                   f"{r.get('cells_win_loss_flip_across_seeds') or '-'} |")
    if hm:
        out += ["", f"`{rel(AN / 'hardware_tpr_model.csv')}`: time per round = c0 + c1 x tokens per round (per-run OLS, "
                "strict + loosest arms):", "",
                "| machine | dataset | runs | c0 (ms) | c1 (ms/token) | c1/c0 | R^2 |", "|---|---|---:|---:|---:|---:|---:|"]
        for r in hm:
            out.append(f"| {r['machine']} | {r['dataset']} | {r['n_runs']} | {f(r['c0_ms'])} | {f(r['c1_ms_per_token'])} | "
                       f"{f(r['c1_over_c0'], 3)} | {f(r['r2'])} |")
    return out + [""]


def section_tables(title: str, pattern: str) -> list[str]:
    files = sorted((ADD / "tables").glob(pattern))
    out = [title, ""]
    if not files:
        return out + ["Pending.", ""]
    for p in files:
        t = rows(p)
        if not t:
            continue
        out += [f"`{rel(p)}`:", "", "| " + " | ".join(t[0].keys()) + " |", "|" + "---|" * len(t[0])]
        for r in t:
            out.append("| " + " | ".join(f(v, 3) if k not in ("source", "dataset", "method", "condition") else v for k, v in r.items()) + " |")
        out.append("")
    return out


def main() -> int:
    lines = ["# NAACL-2027 addendum: results", "",
             f"Generated {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} by `scripts/addendum_results.py` "
             "from the CSVs it names; hand-written observations are in the last section (from `RESULTS_notes.md`). "
             "Settings and deviations: `campaign/addendum/README.md`.", ""]
    lines += section_status()
    lines += section_step1()
    lines += section_seeds()
    lines += section_hardware()
    lines += section_tables("## Step 3: lossless draft-length sweep (strict, seed 0)", "nspec__*.csv")
    lines += section_tables("## Step 4.1: temperature (strict, seed 0)", "temp__*.csv")
    lines += section_tables("## Step 4.2: Qwen3 at its recommended sampler", "qwenT0.6__*.csv")
    lines += section_tables("## Step 4.3: standalone LM drafter (Qwen3-0.6B)", "lmdraft__*.csv")
    lines += section_best()
    lines += section_aime()
    lines += section_speedbench()
    notes = ADD / "RESULTS_notes.md"
    lines += ["## Observations, failures and anything that looked wrong", ""]
    lines += [notes.read_text(encoding="utf-8").strip() if notes.is_file() else "(none yet)", ""]
    (ADD / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {rel(ADD / 'RESULTS.md')} ({len(lines)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
