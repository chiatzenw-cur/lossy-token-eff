#!/usr/bin/env python3
"""Final-results PDF: one page per benchmark, every number relative to lossless.

Rows per benchmark: lossless, tok (alpha 0.15, 0.25), tok_lt (alpha 0.15, 0.20,
0.25). Columns: accepted per pass, answer length, budget hits, verifier passes
(end-to-end speedup), accuracy. Paired per (problem, seed) against lossless
from campaign/tables/<ds>.csv; accuracy from campaign/results/<ds>.csv (graded
per seed). Graphs from campaign/graphs/<ds>*.png.

  python3 cascade/analysis/results_pdf.py   -> cascade/results/final_results.pdf
"""
import csv, statistics as st, pathlib, datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.image as mpimg

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "cascade" / "results" / "final_results.pdf"
BENCH = [  # (title, tables/results stem, graph stem, problems, budget tokens, task)
    ("GSM8K", "gsm8k_proper", "gsm8k_proper", 150, 2048, "grade-school math"),
    ("AIME24", "aime24_fine", "aime24_fine", 30, 32768, "olympiad math, long reasoning"),
    ("HumanEval", "humaneval_proper", "humaneval_proper", 150, 9000, "code generation"),
    ("LiveCodeBench", "livecodebench_proper", "livecodebench_proper", 90, 12000, "competitive programming"),
    ("MT-Bench", "mtbench_proper", "mtbench_proper", 80, 4096, "chat (no accuracy grader)"),
    ("LongBench-v2", "longbench_v2_proper", "longbench_v2_proper", 30, 8192, "long-context QA"),
]
ROWS = [("spec_casc_tok", "0.15"), ("spec_casc_tok", "0.25"),
        ("spec_casc_tok_lt", "0.15"), ("spec_casc_tok_lt", "0.2"), ("spec_casc_tok_lt", "0.25")]
LABEL = {"spec_casc_tok": "tok (paper's rule)", "spec_casc_tok_lt": "tok_lt (ours)"}


def load(stem):
    rows = [r for r in csv.DictReader(open(ROOT / "campaign" / "tables" / f"{stem}.csv")) if r["status"] == "ok"]
    acc = {(r["method"], r["alpha"]): r["accuracy"] for r in csv.DictReader(open(ROOT / "campaign" / "results" / f"{stem}.csv"))}
    by = {}
    for r in rows:
        by.setdefault((r["method"], r["params"]), {})[(r["case"], r["seed"])] = r
    return by, acc


def stats(c, s):
    keys = [k for k in c if k in s]
    lb = st.fmean(float(c[k]["l_bar"]) for k in keys) / st.fmean(float(s[k]["l_bar"]) for k in keys)
    ln = st.fmean(float(c[k]["output_tokens"]) for k in keys) / st.fmean(float(s[k]["output_tokens"]) for k in keys)
    hits = sum(1 for k in keys if c[k]["finish_reason"] == "length")
    sp = st.fmean(float(s[k]["draft_rounds"]) for k in keys) / st.fmean(float(c[k]["draft_rounds"]) for k in keys)
    return len(keys), lb, ln, hits, sp


def pct(v):
    return "—" if v in (None, "") else f"{100 * float(v):.0f}%"


def benchmark_table(stem):
    by, acc = load(stem)
    s = by[("strict", "strict")]
    n = len(s)
    s_lb = st.fmean(float(v["l_bar"]) for v in s.values())
    s_len = st.fmean(float(v["output_tokens"]) for v in s.values())
    s_hits = sum(1 for v in s.values() if v["finish_reason"] == "length")
    s_acc = acc.get(("strict", "strict"), "")
    table = [["lossless", "—", "1.00", "1.00", f"{s_hits} / {n}", "1.00", pct(s_acc)]]
    best_i, best_sp = None, -1
    for m, a in ROWS:
        c = by.get((m, "alpha" + a))
        if not c:
            table.append([LABEL[m], a, "n/a", "n/a", "n/a", "n/a", "n/a"]); continue
        k, lb, ln, hits, sp = stats(c, s)
        table.append([LABEL[m], a, f"{lb:.2f}", f"{ln:.2f}", f"{hits} / {k}", f"{sp:.2f}", pct(acc.get((m, a), ""))])
        if m == "spec_casc_tok_lt" and sp > best_sp:
            best_sp, best_i = sp, len(table) - 1
    base = f"lossless baseline: {s_lb:.2f} accepted per pass, {s_len:,.0f} tokens per answer, {s_hits} of {n} runs hit the budget, accuracy {pct(s_acc)}"
    return table, best_i, base, n


def draw_table(ax, table, best_i, col_labels):
    ax.axis("off")
    widths = [0.24, 0.07, 0.13, 0.12, 0.12, 0.17, 0.12]
    t = ax.table(cellText=table, colLabels=col_labels, loc="center", cellLoc="center", colLoc="center", colWidths=widths)
    t.auto_set_font_size(False); t.set_fontsize(9); t.scale(1, 1.6)
    for (r, c), cell in t.get_celld().items():
        cell.set_edgecolor("#c3c2b7")
        if r == 0:
            cell.set_facecolor("#e9e8e2"); cell.set_text_props(weight="bold")
        elif r == 1:
            cell.set_facecolor("#f4f4f0")
        elif best_i is not None and r == best_i + 1:
            cell.set_facecolor("#e3f0e8"); cell.set_text_props(weight="bold")
        if c == 0:
            cell.set_text_props(ha="left"); cell.PAD = 0.03
    return t


COLS = ["rule", "α", "accepted\nper pass", "answer\nlength", "budget\nhits", "verifier passes\n(speedup)", "accuracy"]

with PdfPages(OUT) as pdf:
    # ---- summary page ----
    fig = plt.figure(figsize=(8.5, 11)); fig.patch.set_facecolor("white")
    fig.text(0.5, 0.95, "Head-restricted relaxed speculative decoding: final results", ha="center", fontsize=15, weight="bold")
    fig.text(0.5, 0.925, f"Bill Xu · {datetime.date.today():%Y-%m-%d} · GPT-OSS-20B + EAGLE3 drafter · vLLM 0.26.0 · one H100 (Nibi) · 3 seeds per point",
             ha="center", fontsize=9, color="#52514e")
    summary = []
    for title, stem, _, nprob, budget, task in BENCH:
        table, best_i, base, n = benchmark_table(stem)
        b = table[best_i] if best_i is not None else None
        toks = [r for r in table[1:3]]
        tb = max(toks, key=lambda r: float(r[5]) if r[5] != "n/a" else -1)
        summary.append([title, f"{nprob} × 3", table[0][6], f"{b[1]}", b[2], b[3], b[5], b[6], f"{tb[1]}: {tb[5]}"])
    ax = fig.add_axes([0.03, 0.66, 0.94, 0.24]); ax.axis("off")
    t = ax.table(cellText=summary, colWidths=[0.15, 0.09, 0.09, 0.08, 0.10, 0.09, 0.14, 0.09, 0.17],
                 colLabels=["benchmark", "problems\n× seeds", "lossless\naccuracy", "best\ntok_lt α", "accepted\nper pass", "answer\nlength", "verifier passes\n(speedup)", "accuracy", "best tok\n(α: speedup)"],
                 loc="center", cellLoc="center")
    t.auto_set_font_size(False); t.set_fontsize(8.5); t.scale(1, 1.6)
    for (r, c), cell in t.get_celld().items():
        cell.set_edgecolor("#c3c2b7")
        if r == 0: cell.set_facecolor("#e9e8e2"); cell.set_text_props(weight="bold")
        if c == 6 and r > 0: cell.set_text_props(weight="bold")
    fig.text(0.06, 0.635, "Best tok_lt setting per benchmark (highest verifier-pass reduction among α = 0.15 / 0.20 / 0.25). Every number is the rule ÷ lossless on the same problems and seeds; lossless = 1.00.",
             fontsize=8, color="#52514e", wrap=True)
    reading = (
        "How to read this\n"
        "• accepted per pass: drafted tokens the big model kept per checking pass (the gain the source papers report).\n"
        "• answer length: mean tokens per answer ÷ lossless (the cost the source papers did not measure).\n"
        "• verifier passes: lossless passes ÷ rule passes — the end-to-end speedup; one pass = one big-model step.\n"
        "• budget hits: runs that ran to the token limit (looping / endless hedging).\n\n"
        "What it shows\n"
        "• On math, code and chat, tok_lt accepts 9–13% more per pass than lossless (tok: 2–6%), answers stay at lossless length,\n"
        "  accuracy is unchanged, and the big model does 6–10% fewer passes. tok, the paper's rule, gains little end to end.\n"
        "• LongBench-v2 (long-context QA) is the exception: no consistent speedup for either rule, and every relaxed setting is\n"
        "  3–8 accuracy points below lossless (within seed noise individually, but uniformly below).\n"
        "• Rambling is caused by letting through tokens the verifier ranks far below its own favourite; tok and tok_lt never do,\n"
        "  which is why their answers do not grow. Keeping that filter caps the gain at roughly 1.1× (see RESULTS.md).\n\n"
        "Rules\n"
        "• lossless: keep a drafted token with probability p/q (output identical to the big model alone).\n"
        "• tok (Narasimhan et al. 2025, token variant): free pass for tokens within α of the verifier's top choice; stricter than\n"
        "  lossless for all other tokens; residual from its blended distribution.\n"
        "• tok_lt (ours): same free pass; ordinary lossless check for all other tokens; lossless residual.\n\n"
        "Protocol: warm vLLM server per (rule, α, seed); 3 seeds; problems per benchmark as listed; token budgets gsm8k 2,048,\n"
        "AIME24 32,768, HumanEval 9,000, LiveCodeBench 12,000, MT-Bench 4,096, LongBench-v2 8,192. Accuracies graded per seed.\n"
        "Detail and caveats: cascade/RESULTS.md, cascade/JOURNAL.md."
    )
    fig.text(0.06, 0.60, reading, fontsize=8.2, va="top", family="DejaVu Sans", linespacing=1.45)
    pdf.savefig(fig); plt.close(fig)

    # ---- one page per benchmark ----
    for title, stem, gstem, nprob, budget, task in BENCH:
        table, best_i, base, n = benchmark_table(stem)
        fig = plt.figure(figsize=(8.5, 11)); fig.patch.set_facecolor("white")
        fig.text(0.5, 0.955, f"{title} — {task}", ha="center", fontsize=14, weight="bold")
        fig.text(0.5, 0.932, f"{nprob} problems × 3 seeds = {n} runs per point · budget {budget:,} tokens · relative to lossless, paired per problem and seed",
                 ha="center", fontsize=9, color="#52514e")
        fig.text(0.5, 0.912, base, ha="center", fontsize=9)
        ax = fig.add_axes([0.05, 0.66, 0.90, 0.23])
        draw_table(ax, table, best_i, COLS)
        fig.text(0.06, 0.645, "Shaded row: best tok_lt setting (fewest verifier passes). tok rows: the paper's rule at the tightest and loosest of the three settings.",
                 fontsize=8, color="#52514e")
        imgs = [ROOT / "campaign" / "graphs" / f"{gstem}.png", ROOT / "campaign" / "graphs" / f"{gstem}_accuracy.png"]
        imgs = [p for p in imgs if p.exists()]
        for i, p in enumerate(imgs):
            axi = fig.add_axes([0.02 + i * 0.49, 0.24, 0.48, 0.38] if len(imgs) == 2 else [0.15, 0.24, 0.70, 0.38])
            axi.imshow(mpimg.imread(p)); axi.axis("off")
        cap = ("Left: mean answer length vs mean accepted length per pass (x-axis), all settings of both rules; lossless is the ✕. "
               "Right: accuracy vs the same x-axis." if len(imgs) == 2 else
               "Mean answer length vs mean accepted length per pass, all settings of both rules; lossless is the ✕ (no accuracy grader for this benchmark).")
        fig.text(0.06, 0.215, cap, fontsize=8, color="#52514e", wrap=True)
        notes = {
            "GSM8K": "Short answers; the 7–11 budget-hit runs per point carry ~10% of all tokens, so per-seed speedups swing 0.93–1.22 even at 450 runs. Both rules tie at ~1.05–1.10×.",
            "AIME24": "Long reasoning; 6 of 90 lossless runs loop to 32k tokens and dominate the means. tok_lt α=0.15: same length, same loop rate, +1 accuracy point, 8% fewer passes. tok_lt α=0.25 loses accuracy (66%).",
            "HumanEval": "tok_lt gains 8–9% at α 0.15/0.25 with lossless length and accuracy; tok gains nothing end to end (≈1.00–1.01×).",
            "LiveCodeBench": "tok_lt 1.06× at α 0.15/0.20; both rules keep accuracy at or above lossless (89%).",
            "MT-Bench": "No accuracy grader (needs an LLM judge). tok_lt 1.08–1.10× at lossless length; tok ≈1.00–1.04×.",
            "LongBench-v2": "The exception. 30 problems only (150 would take ~66 h). No consistent speedup (per-seed 0.63–1.40) and every relaxed setting 3–8 points below lossless's 60% — the one task where the safe rules are not free, in line with the campaign's 150-problem result.",
        }[title]
        fig.text(0.06, 0.08, notes, fontsize=8.5, wrap=True, va="bottom")
        pdf.savefig(fig); plt.close(fig)

    # ---- notes page ----
    fig = plt.figure(figsize=(8.5, 11)); fig.patch.set_facecolor("white")
    fig.text(0.5, 0.95, "Notes and caveats", ha="center", fontsize=14, weight="bold")
    notes = (
        "Data\n"
        "• All runs on Nibi (Alliance), one H100 SXM 80 GB per job, vLLM 0.26.0, GPT-OSS-20B with the nebius EAGLE3 drafter,\n"
        "  temperature 1.0, top-p 1.0, 6 drafted tokens per pass, seeds 0/1/2.\n"
        "• One warm vLLM server per (rule, α, seed) — request order on a warm engine is a documented (small) confound; the\n"
        "  campaign's own paper tables used a fresh server per measurement. Use the 3-seed means, never a single seed.\n"
        "• Rows are paired: each run is compared with the lossless run of the same problem and the same seed.\n"
        "• Accuracy graders: gsm8k / AIME24 / LongBench-v2 exact-answer match, HumanEval / LiveCodeBench code execution;\n"
        "  MT-Bench has none. A report bug that applied one seed's verdict to all three seeds was fixed on 2026-09-16 and every\n"
        "  multi-seed report regenerated; all accuracies here are the corrected per-seed ones.\n\n"
        "Reading the numbers\n"
        "• A rule only helps if the speedup column is above 1.00 while the answer-length column stays near 1.00 and accuracy is\n"
        "  unchanged. The source papers report only the acceptance column, which is why their gains do not survive this test.\n"
        "• AIME24 and gsm8k means are dominated by the few runs that hit the token budget (each is 2–32k tokens); the budget-hit\n"
        "  column is the loop rate. Differences of ±3 loops per 90–450 runs are noise.\n"
        "• LongBench-v2 uses 30 problems (its answers take ~73 s each); accuracy resolution there is coarse (±5 points).\n\n"
        "What was not done\n"
        "• Wall-clock timing under a clean protocol (verifier passes are the cost proxy); Qwen3-8B (the new rules exist only for\n"
        "  vLLM's V1 runner); fresh-server-per-measurement re-runs of these sweeps.\n\n"
        "Files: cascade/RESULTS.md (report), cascade/results/per_benchmark_summary.md (every rule × benchmark), cascade/JOURNAL.md\n"
        "(dated log incl. failures and fixes), campaign/{tables,results,graphs}/<benchmark>_proper.* and aime24_fine.* (raw)."
    )
    fig.text(0.06, 0.90, notes, fontsize=8.6, va="top", linespacing=1.5)
    pdf.savefig(fig); plt.close(fig)
print(f"wrote {OUT.relative_to(ROOT)}")
