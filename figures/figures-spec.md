# Figure spec: the six result figures

Regenerate with `python3 scripts/paper_figures.py --runs-root <path to runs/>`
(the run tree is gitignored; without it the script falls back to the
verifier-rounds values cached in `points.csv`, so the PNGs are reproducible
from tracked files alone). `points.csv` holds every plotted point.

**Change on 2026-09-24:** the original Overleaf figures joined each method's
sweep points in file order, so several curves doubled back on themselves
(the "visible zigzags" listed below). The figures here sort each curve by
mean accepted length ℓ̄ before drawing, and the script asserts x-monotonicity,
so no curve doubles back. Up-then-down movement in *y* (e.g. r_fuzzy
completion length on Qwen GSM8K) is real data and remains. In the campaign
data ℓ̄ is monotone in α for every curve, so sorting by ℓ̄ and by α give the
same result.

Six PNGs in `figures/`, each 2070×2100 px, matplotlib. Three plot types × two target models:

| File | Section | Label | y-axis |
|---|---|---|---|
| `gpt_oss_20b_completion_length.png` | 3.3 | `fig:gpt-cl` | mean completion length (tokens) |
| `qwen3_8b_completion_length.png` | 3.3 | `fig:qwen-cl` | mean completion length (tokens) |
| `gpt_oss_20b_verifier_rounds.png` | 3.4 | `fig:gpt-rd` | mean verifier rounds (target forward passes) |
| `qwen3_8b_verifier_rounds.png` | 3.4 | `fig:qwen-rd` | mean verifier rounds |
| `gpt_oss_20b_accuracy.png` | 3.5 | `fig:gpt-acc` | accuracy, 0 to 100% |
| `qwen3_8b_accuracy.png` | 3.5 | `fig:qwen-acc` | accuracy, 0 to 100% |

Each is `\begin{figure}[htbp] \centering \includegraphics[width=\textwidth]{...}`, one float per figure, GPT first then Qwen, at the top of its subsection.

## Layout (identical in all six)

1. Bold suptitle = model name (`GPT-OSS-20B` or `Qwen3-8B`).
2. 3 rows × 2 columns of panels, bold titles, fixed order: row 1 `GSM8K`, `AIME24`; row 2 `HumanEval`, `LiveCodeBench`; row 3 `MT-Bench`, `LongBench-v2`.
3. x-axis on every panel = mean accepted length ℓ̄. Label `mean accepted length ℓ̄` printed once under each column. All panels in a figure share one x-range; the three GPT figures share it too, as do the three Qwen figures:
   1. GPT: x ≈ 1.7 to 5.0, ticks 2.0 to 5.0 step 0.5.
   2. Qwen: x ≈ 0.5 to 3.7, ticks 1.0 to 3.5 step 0.5.
4. y-axis: auto-scaled per panel for length and rounds (no shared scale); fixed 0 to 100% (ticks 0, 25%, 50%, 75%, 100%) on every accuracy panel.
5. Light grey grid, ticks on all four sides, white background, linear axes.
6. One legend centred below the grid, 3 columns × 2 rows: row 1 `mentored_dec`, `spec_casc_opt`, `spec_casc_tok`; row 2 `cactus`, `r_fuzzy`, `lossless (strict)`.

## Series encoding (identical in all six)

| Series | Colour | Marker | Line |
|---|---|---|---|
| `mentored_dec` | blue | filled circle | solid, thick |
| `cactus` | red | filled square | solid, thick |
| `spec_casc_opt` | green | filled triangle up | solid, thick |
| `r_fuzzy` | orange | filled diamond | solid, thick |
| `spec_casc_tok` | purple | small star | solid, thinner |
| `lossless (strict)` | dark grey/black | large × | no line, single marker |

1. Each method is a polyline of its sweep points: normally 3 (the three matched ℓ̄ targets), `spec_casc_tok` only 2 (can't reach the top target). Overlapping runs can make a curve look like 2 points.
2. Points are joined in increasing ℓ̄ order (superseded: the Overleaf originals joined them in file order, which produced zigzags in r_fuzzy on Qwen GSM8K / HumanEval / LiveCodeBench, opt and r_fuzzy on GPT LongBench-v2 rounds, and cactus on Qwen AIME24 length).
3. The × sits at (ℓ̄*, value*) from `tab:strict`, always leftmost or near-leftmost, no curve (nothing to sweep).
4. Methods occupy different ℓ̄ ranges (best-effort matching): tok is always the shortest, leftmost curve; cactus goes furthest right in all GPT panels and Qwen AIME24 / LCB / MT-Bench / LongBench (on Qwen GSM8K and HumanEval, opt goes furthest); mentored sits in the middle; opt and r_fuzzy rise steepest.
5. MT-Bench panel in both accuracy figures is empty except grey centred text `no grader` (axes still drawn).

## Data behind the figures

1. Every point is a mean over the dataset's cases (150 GSM8K / HumanEval / LongBench-v2, 90 LiveCodeBench, 80 MT-Bench, 30 AIME24), one seed, at one α grid point; x is that run's measured ℓ̄, not the nominal target.
2. The paper's tables are exactly the rightmost point of each curve plus the ×: `tab:gpt` / `tab:qwen` (length ratio, accuracy), `tab:gpt-rd` / `tab:qwen-rd` (rounds), `tab:strict` (the × marker).
3. α grids, same for both targets: mentored_dec {0.15, 0.35, 0.55, 0.75}; cactus {0.03, 0.08, 0.18, 0.35}; spec_casc_opt {−0.3, −0.1, −0.02, 0.05}; r_fuzzy {0.03, 0.08, 0.15, 0.25}; spec_casc_tok {0.15, 0.35, 0.55, 0.8}. Three target ℓ̄ per dataset (≈20th/55th/90th percentile of the jointly reachable span); each method runs at the grid point nearest each target, hence ≤3 points per curve and 2 for tok.
4. Sources: ℓ̄, completion length and accuracy come from `campaign/results/<stem>.csv`; verifier rounds are the mean of `draft_rounds` over status `ok` runs in `runs/<stem>/<method>/<alpha dir>/case_*/seed_*/run.json` (see `cascade/METRICS.md`). `<stem>` is the dataset name for GPT-OSS-20B and `<dataset>_qwen3` for Qwen3-8B.
