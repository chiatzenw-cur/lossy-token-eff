# Metrics: what every number in this workspace means and where it comes from

## Per run (`runs/<dataset>/<method>/<params>/<case>/seed_0/run.json`)

| field | meaning | source |
|---|---|---|
| `output_tokens` | completion length in tokens | vLLM usage |
| `draft_rounds` | verifier rounds = target forward passes during decoding | differenced vLLM `/metrics` counters |
| `l_bar` | mean accepted draft tokens per round | `accepted_tokens / draft_rounds` |
| `mean_accept_length` | `l_bar + 1` (the bonus/recovered token is always emitted) | derived |
| `wall_time_seconds` | request time as seen by the client (generation + per-request overhead; no server start) | client |
| `finish_reason` | `stop` (EOS) or `length` (hit `--max-new-tokens`) | vLLM |
| `reached_final_channel` | GPT-OSS only: the Harmony final channel was opened (an answer was attempted) | client parse |
| `analysis_chars`, `final_chars` | GPT-OSS only: reasoning vs answer split of the completion | client parse |
| `server_request_ordinal` | 1 = first request the engine ever served (clean); >1 = warm engine (`persistent_arm_replay.py`) | client |

`README.md` (repo root) documents a known off-by-one between trace-counted
rounds and `/metrics`-counted rounds; it is constant, so ratios are safe.

## Per arm (campaign tables, `cascade/results/speed_ignoring_accuracy.*`)

All comparisons are **paired**: the method's cases intersected with
strict's, ratio of means over that set.

| name | formula | reading |
|---|---|---|
| `len_ratio` | `mean L_method / mean L_strict` | > 1 = the relaxed rule makes the model talk more |
| `rounds_speedup` | `mean rounds_strict / mean rounds_method` | end-to-end speed proxy: one round = one target pass; equals Xia et al. Eq. 4 up to the drafter-cost term |
| `lc_speedup` | `((l̄_m+1)/(l̄_s+1)) / len_ratio` | Eq. 4 rebuilt from l̄ and length; should track `rounds_speedup` |
| `wall_speedup` | `mean wall_strict / mean wall_method` | measured; noisier (ordinal confound), no server-start cost |
| l̄ speedup (`campaign/FINDINGS.md`) | `(l̄_m+1)/(l̄_s+1)` | per-round gain only — the number the source papers report; ignores length |
| `budget_hit_rate` | fraction of cases with `finish_reason == length` | garbage proxy: loops and rambling run into the budget |
| `no_final_rate` | GPT-OSS: fraction with `reached_final_channel == False` | never answered |
| `clean` | `budget_hit_rate <= strict's + 0.05` | "not obvious garbage" in the meeting's sense |
| `accuracy` | dataset grader (`campaign_report.py`); MT-Bench has none | context, not a ranking key here |
| `full` | paired with >= 50% of strict's cases | 3-case calibration probes are excluded from rankings |

Why rounds and not l̄: `rounds ~= L / (l̄ + 1)`. A rule that raises l̄ by 30%
and L by 40% has *more* rounds than strict. That is the whole finding of
the campaign, and l̄-only tables hide it.

## Throughput (`cascade/analysis/timing_report.py`, E3/E4)

| name | formula |
|---|---|
| `tok/s` | `sum output_tokens / sum wall_time_seconds` over an arm |
| `rounds/s` | `sum draft_rounds / sum wall` — target passes per second, ~constant across N |
| `tok/s vs baseline` | speedup over no-drafter decoding, the number users feel |
| `c_rel` | `((l̄_strict + 1) / S_strict - 1) / N` with `S_strict = tok/s(strict)/tok/s(baseline)` — Xia Eq. 2 solved for the drafter's relative cost on this stack |

## Per token (traces, `proposals.jsonl`; `cascade/analysis/trace_rank_analysis.py`, E7)

| field | meaning |
|---|---|
| `strict_would_accept` | the lossless test on the same `(p, q, u)` |
| `lossy_would_accept` / `actually_accepted` | the relaxed rule's decision / what the kernel emitted |
| `lossy_only_accepted` | accepted, and strict would have rejected: committed only because the bar was lowered |
| `p`, `q`, `target_rank`, `target_top1_prob` | the drafted token's verifier probability, drafter probability, rank under the verifier (0 = argmax), and the verifier's top-1 |
| `ooh80` (derived) | `p < 0.2 * target_top1_prob`: outside `spec_casc_tok`'s trusted set at alpha 0.8 |
| `lossy_only_per_1k`, `ooh80_per_1k` | counts per 1000 emitted tokens; the exposure a rule creates |
| `ooh80_share` | of the lossy-only accepts, the fraction outside the head |
| `accepted_ooh80_per_1k` | out-of-head tokens among *all* accepts, including ones strict would also have accepted (~50/1k for strict itself: lossless verification also commits low-p tokens, at rate `p/q`) |

Rows describe the *drafted* token; on rejected rows the emitted token's own
`emitted_p` / `emitted_target_rank` are separate fields (the tracer's
comment explains the conflation this avoids).

## Caveats to carry into any write-up

- The 50 -> 150 case extensions used warm servers; check
  `server_request_ordinal` before treating per-case wall times or lengths
  as ordinal-1 data. Rounds and l̄ are unaffected in kind, only in the
  request-history confound documented in `remote/ENVIRONMENT.md`.
- Qwen3 `spec_casc_tok` and `cactus` numbers come from accept-test-only V2
  ports (residual on raw `p`).
- The 3 calibration probe cases per method are included in
  `campaign/tables/*.csv` at grid alphas that were not chosen for the full
  sweep; rank only `full` points.
- Seed 0 only, temperature 1.0, top-p 1.0, `NUM_SPEC=6`, batch size 1.
