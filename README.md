# lossy-token-eff

Practical evaluation of training-free relaxed (lossy) speculative decoding
methods (Xia et al. 2026, arXiv:2607.08690) on vLLM 0.26.0: does relaxing
the verifier's acceptance rule actually save end-to-end tokens and time, or
does it buy accepted length at the cost of longer, worse completions?

- **Models**: GPT-OSS-20B + EAGLE3 draft; Qwen3-8B + Qwen3-0.6B draft
  (plus Llama-3.1-8B / R1-Llama prompts for the addendum).
- **Methods** (`patches/`): `mentored_dec`, `cactus`, `spec_casc_opt`,
  `r_fuzzy`, `spec_casc_tok`, against a lossless `strict` control; plus
  guard variants built on `spec_casc_tok` (semantic guard, force-commit,
  autoguard, ...).
- **Datasets**: AIME24, GSM8K, HumanEval, LiveCodeBench, MT-Bench,
  LongBench-v2 (+ SPEED-Bench in the addendum).

## Where the results are

| question | read |
|---|---|
| Headline numbers quoted in the paper | [`campaign/addendum/RESULTS.md`](campaign/addendum/RESULTS.md) |
| l̄-matched completion-length comparison, 6 datasets × 5 methods | [`campaign/FINDINGS.md`](campaign/FINDINGS.md), `campaign/tables/`, `campaign/graphs/` |
| Does any method give real wall-clock speed if accuracy is ignored? | [`cascade/RESULTS.md`](cascade/RESULTS.md) |
| Can a guard stop `spec_casc_tok` from inflating length? | [`autoresearch/FINDINGS.md`](autoresearch/FINDINGS.md), [`autoresearch/FINDINGS_cross_method.md`](autoresearch/FINDINGS_cross_method.md) |
| Hesitation markers / semantic guard analyses | [`analysis/semantic_guard/README.md`](analysis/semantic_guard/README.md) |
| First AIME24 + HumanEval measurement (phase 1) | [`docs/phase1_aime24_humaneval.md`](docs/phase1_aime24_humaneval.md) |

## Repository layout

```
patches/          vLLM 0.26.0 rejection-sampler patches, one per method; apply.sh switches between them
remote/           server launch script and environment notes (ENVIRONMENT.md)
scripts/          runners, graders, campaign drivers, report generators
campaign/         main campaign: PLAN, JOURNAL, FINDINGS, calibration, results CSVs, tables, graphs
  addendum/       follow-up campaign: manifest, per-step outputs, RESULTS.md
cascade/          speculative-cascade experiments (E0..E8), methods/metrics docs, results
autoresearch/     autonomous guard-search loop and cross-method force-commit study
analysis/         semantic_guard/: lexical and hidden-state analyses of rambling
docs/             standalone write-ups (phase 1)
prompts/          per-dataset prompt files (built by scripts/build_*_prompts.py)
runs/             per-run outputs of the campaign (runs/<dataset>[_qwen3]/<method>/<alpha>/<case>/seed_0/)
old_runs/         per-run outputs of the guard-variant study on AIME24 / HumanEval (see old_runs/readme.md)
runs_phase1/      per-run outputs of phase 1 and the early pilots (see runs_phase1/readme.md)
logs/             stdout of campaign batches
```

Each run directory holds `output.txt` (the full completion), `response.json`,
`config.json` (arm + sampling settings), `run.json` (token counts, accepted
length, timing) and `server_info.json`. That is enough to regrade every
accuracy and length number (`scripts/grade_*.py`, `scripts/summarize_arms.py`).

**Not included**: the per-round verifier traces (`proposals.jsonl`, ~18 GB),
hidden-state dumps (`hidden_states.bin`) and request copies
(`request.json`, the same text as `prompts/`). Analyses that read the traces
(verifier-round counts, `analysis/semantic_guard/*` trace scans,
`autoresearch/cross_method_metrics.py` round stats) need them regenerated
with `scripts/fresh_server_replay.py`. SPEED-Bench prompt texts are also
excluded for licensing; rebuild with `scripts/build_speedbench_prompts.py`.

## Reproducing

1. Environment: `remote/ENVIRONMENT.md` (vLLM 0.26.0+cu129, one H100).
2. Install a method: `bash patches/apply.sh <method>` (see `patches/README.md`).
3. Run arms: `scripts/fresh_server_replay.py` (one fresh server per
   `(case, arm)`) or `scripts/campaign_run.py` for a full dataset sweep.
4. Grade and summarise: `scripts/grade_<dataset>.py`, then
   `scripts/summarize_arms.py --runs-root runs/<dataset> --prompt-root prompts/<dataset>`.
