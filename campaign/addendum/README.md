# NAACL-2027 addendum campaign

Started 2026-09-29 on branch `addendum-oct2026`. Everything the paper needs
from this campaign lives here; the paper's own tables (`campaign/tables/*.csv`,
`campaign/results/*.csv`) are never touched.

| file | what |
|---|---|
| `manifest.csv` | single source of truth: one row per (step, condition, dataset, method, alpha, seed) arm; `n_done` is recounted from `runs/` every cycle |
| `PROGRESS.md` | append-only action log (UTC); "Needs Bill" at the top |
| `lanes/<lane>.json` | the ordered work list each Nibi lane runs (regenerated every cycle) |
| `lanes/<lane>_status.jsonl` | copy of the lane's own journal on Nibi (item start/end, job, elapsed) |
| `lanes/state.json` | Slurm job chain per lane |
| `analysis/` | step 1 (zero-GPU) CSVs, each with a sibling line in `analysis/README.md` |
| `seeds/`, `tables/`, `best_setting.csv`, `aime24_repeats.csv` | steps 2-6 outputs |
| `RESULTS.md` | every number the paper will quote, with its CSV path and row |

## How it runs

- `scripts/addendum_campaign.py cycle` (Mac): pull finished runs back ->
  recount -> rewrite `manifest.csv` and the lane work lists -> push code and
  work lists to Nibi -> keep every lane's Slurm chain supplied -> commit
  (one commit per completed arm) and push the branch.
- `cascade/cluster/addendum_lane.sbatch` -> `scripts/addendum_lane.py`
  (Nibi, one H100 per job, `--time` 12 h, chained `afterany`): runs the
  lane's work list through `scripts/persistent_arm_replay.py` (one server
  per arm+seed, `--no-trace-proposals`), skip-if-done per case.
- Two lanes (user request 2026-09-29: "like 2 GPUs"), each with its own repo
  + `.venv-vllm` copy and a disjoint node set (`remote/stop_server.sh` kills
  every vLLM process of the user on a node; knob files are node-local):
  lane A = `~/projects/def-hongyanz/billxby/lossy-token-eff`, nodes g1-g14;
  lane B = `.../lossy-token-eff-lane2`, nodes g15-g28.

## Run roots and provenance

Each lane writes only to its own run root, `/scratch/billxby/lossy-addendum/lane<L>/runs`,
laid out exactly like the repo's `runs/`. Finished run dirs (run.json with
`status: ok`) are pulled into the repo's `runs/` tree only where the target
directory does not exist yet (staged, then moved; never merged, never
overwritten). Failed or interrupted run dirs on Nibi are moved to
`<lane root>/quarantine/`, not deleted.

Why not the repo copies' own `runs/` on Nibi: they already hold September
cascade-workspace runs (E1/E1F/E1P, `cascade/RESULTS.md`) at the same paths
as the campaign tree -- e.g. `gsm8k/strict/strict/case_*/seed_{0,1,2}` -- that
are different runs from the Mac's (old-box) seed-0 data. Running there would
make skip-if-done silently reuse them. The addendum therefore produces all of
its own runs; the E1P runs stay untouched on Nibi.

- `runs/<dataset>/<method>/<params>/case_NNN/seed_<k>/`: new seeds (steps 2, 5.2, 6) and the
  missing step-5.1 alphas (seed 0), exactly where the campaign's tree puts them.
- `runs/addendum/<condition>/<dataset>/...`: server-setting changes --
  `nspec<k>` (step 3), `temp<T>` (step 4.1), `qwenT0.6` (step 4.2), `lmdraft` (step 4.3),
  `nibiref` (step 0.5, below).

## Settings (unchanged from the campaign)

EAGLE-3 drafters, N_draft 6, temperature 1.0, top-p 1.0, server seed 0 (the
request seed is the `seed_<k>` value), vLLM 0.26.0 with the repo patches,
Qwen3 YaRN 65,536 via `MODEL_FAMILIES`, the campaign token budgets and case
counts. Loosest alpha per rule = the maximum alpha in
`campaign/results/<dataset>.csv` for that method (every rule loosens as its
alpha grows).

## Additions and deviations (each also logged in PROGRESS.md)

1. **Step 0.5, Nibi hardware reference (added).** All existing seed-0 data
   ran on the old box's H100 PCIe; Nibi's H100 SXM is ~3x faster per token
   (measured: 7.1 vs 2.2-2.4 ms/token on the same strict cases). Wall-time
   ratios of cells produced on Nibi need a Nibi strict baseline: `nibiref` =
   strict, seed 0, campaign settings, all cases. It is the N_draft = 6 row of
   step 3, the T = 1.0 row of step 4.1, and the time denominator for the step
   5.1 cells in step 5.2. Step-2 and step-6 ratios compare arms of the same
   seed, all produced on Nibi, so they need no reference.
2. **`patches/apply.sh`: `APPLY_SKIP_TEST_IF_APPLIED`.** Opt-in (set only by
   `addendum_lane.sbatch`): when the requested patch is already installed
   with a matching sha256, its self-test is skipped (~2.5 min of GPU per
   arm). Any fresh apply or switch still runs the test. Default behaviour
   unchanged.
3. **No lane C: Qwen3 runs on lanes A and B.** /project has a 500K-file
   quota (288K used); a third repo + venv copy is ~100K files, and Bill asked
   for two GPUs. Once the V2 sampler arrived (2026-09-30 00:36Z, installed in
   both lane venvs; the V2 file is not touched by GPT-OSS, which runs V1) the
   Qwen3 rows were spread over lanes A/B by estimated hours, in the plan's
   lane-C order (2.1 -> 0.5 -> 3 -> 4.1 -> 4.2 -> 5.1 -> 4.3 / 6 / 2.2 -> 5.2
   -> 7). Reordered with Bill on 2026-09-30 19:35Z, when the Nibi queue
   slowed: 2.1 -> 2.2 / 6 (AIME24 seeds) -> 4.2 -> 4.3 -> 0.5 -> 3 -> 4.1 ->
   5.1 -> 5.2 -> 7, so the rows the two-model claims rest on finish first.
4. **Step 2.2 aime24 seeds 1-2 are the same runs as step 6 seeds 1-2** (one
   manifest row each, step `2.2`, noted "shared by step 6").
5. **`patches/test_mentored_dec.py`: `MENTORED_DEC_TEST_V1_ONLY`.** The
   mentored-dec self-test also checks the V2 module, whose consolidated state
   is not on Nibi (D8), so every switch *to* mentored-dec failed there (job
   22880871, 06:23Z: V1 patch installed, V1 kernel checks all ok, only the V2
   plumbing check failed). GPT-OSS-20B runs V1 only, so the lanes set this
   variable for GPT-OSS items: with it set *and* the V2 module pristine the
   plumbing check covers V1 only. Qwen3 items never set it.
6. **`remote/run_server_vllm.sh` `SPEC_METHOD`** (default `eagle3`, spec
   JSON byte-identical otherwise) for step 4.3, and an optional `--top-k`
   in the client/replay scripts (sent and recorded only when given) for
   step 4.2.
7. **Runs come back with tar over ssh, not rsync** (`addendum_campaign.py
   collect`): macOS ships openrsync, and the guarantee needed here is
   directory-level no-clobber (never merge two runs' files into one
   `seed_N/`), which a staged tar extract + `os.rename` into a
   not-yet-existing target gives directly. Only run dirs whose run.json says
   `ok` are pulled; the lane's `status.jsonl` journal comes back every cycle.
8. **Step 7 (SPEED-Bench, added 2026-09-29 from Prof. Zhang) runs on both
   GPT-OSS lanes, not lane B alone.** Lane B takes the budget pilot first,
   then `strict`, `spec_casc_opt`, `mentored_dec`; lane A takes `cactus`,
   `r_fuzzy`, `spec_casc_tok` (Bill: "like 2 GPUs"). The step text does not
   define "the lane budget"; it is taken as one 12 h job on each of the two
   lanes, 24 GPU-h (`SB_BUDGET_H` in `scripts/addendum_campaign.py`).
9. **SPEED-Bench prompts** (`scripts/build_speedbench_prompts.py`): the
   qualitative parquet at revision `454f8845...` (sha256 `4f76bc45...`);
   the 494 placeholder rows are resolved with NVIDIA's own code
   (Model-Optimizer `examples/specdec_bench`, commit `834c90d7...`,
   `SPEEDBench._fetch_all_turns_data`). Case order is SPEED-Bench's own
   stratified interleaving (round-robin over categories), so case_001..case_040
   is the time-estimate sample and case_001..case_440 is exactly 40 per
   category. Turn 1 only, as for the repo's MT-Bench (167 rows are
   multi-turn; the later turns stay in `metadata.json`), rendered as the same
   Harmony conversation as MT-Bench (the renderer reproduces
   `prompts/mtbench/case_001` byte for byte). **Not committed:** the repo is
   public, the data is under the NVIDIA Evaluation Dataset License and its
   rows come from third-party sources (HLE asks that its questions stay off
   the open web), so `prompts/speedbench*/` is gitignored and
   `campaign/addendum/speedbench/cases.csv` records case -> question_id,
   category, source, src_id, token count and the sha256 of every rendered
   prompt. The 208 rows from `cais/hle` (gated) wait for a Hugging Face token
   (PROGRESS.md Needs Bill 4); every other category is complete.
10. **Step 7 mechanics.** The token-budget pilot (strict at 8192 on the first
   20 Reasoning and first 20 Math cases) writes to its own run root,
   `runs/addendum/speedbench_pilot/gpt-oss-20b/`, because a category whose
   budget is raised to 16384 is run again at the new budget and run
   directories are never overwritten. An arm whose cases need two budgets
   runs as two work items (one server session each). "The first 40 prompts
   of each arm" = the first 40 cases in case order that are runnable when the
   pilot finishes (prompt built, category budget decided), which leaves Math
   out: 16 of its first 20 cases are HLE, so its budget waits for the token.
   In the full phase Math's 18 non-HLE rows (Spec-Bench's GSM8K-style
   problems; at most 636 completion tokens in the pilot, so neither cap can
   bind) run at 8192 anyway; the 62 HLE Math rows wait for the Math pilot's
   decision. The reasoning pilot found 0/20 cap-outs, so every non-Math
   category runs at 8192 (`tables/speedbench_pilot__gpt-oss-20b.csv`). The per-arm
   estimate and the full-vs-440 decision are written to the manifest notes
   and PROGRESS.md before the rest is queued. While step 7 waits between
   these phases, a lane that runs out of work keeps its GPU for up to 40 min
   (`hold_minutes` in the work list, `scripts/addendum_lane.py`) instead of
   exiting, so the next phase does not wait in the Slurm queue.
   Qwen3-8B gets its own pilot and phases under the same rules (thinking
   lengths differ from GPT-OSS, so its budgets are decided on its own strict
   runs, in `runs/addendum/speedbench_pilot/qwen3-8b/`). Its step 7 starts
   once GPT-OSS has nothing runnable left (the cais/hle cases may still be
   missing); its short pilot and first-40 items run ahead of other work on
   their lane, the full arms after every other Qwen3 row (lane C order).
   Its prompts (`prompts/speedbench_qwen3/`, gitignored) come from
   `scripts/build_prompts_qwen3.py` on the GPT-OSS set, which reproduces the
   existing Qwen3 prompt sets byte for byte.
11. **3 h lane jobs from 2026-09-30 19:20Z (the plan allows up to 12 h).**
   After the first 12 h Qwen3 jobs timed out at 13:24Z, their chained
   successors sat PENDING for 6 h: ~850 H100 jobs were pending on Nibi and our
   fair-share had dropped to 0.23 after two days of continuous use, and a
   12 h job fits almost no backfill window. Those six pending jobs were
   cancelled and every lane now chains 3 h jobs (`JOB_TIME` in
   `scripts/addendum_campaign.py`); a job ending mid-arm loses only the case
   in progress (its partial dir is quarantined, the rest is skip-if-done).
12. **Qwen3 moved to Killarney (PAICE allocation `aip-hongyanz`), 2026-09-30
   ~23:15Z, with Bill's go-ahead.** On Nibi our fair-share had fallen to 0.23
   after 2.5 days of continuous use and the lane jobs sat 6 h+ in a queue of
   ~2,200 GPU jobs; on Killarney the account's fair-share is 0.58 (no usage
   yet), which ranks our jobs above every pending H100 job there (priority
   2.9M vs 2.7M). Environment: `cascade/cluster/setup_nibi.sh` with
   `PROJECT_DIR=~/projects/aip-hongyanz/billxby` and the three Qwen3 models
   (vLLM 0.26.0, torch 2.11.0+cu129), the consolidated V2 patch applied
   (68d0a904), two lane copies: K1 on kn169-kn173, K2 on kn174-kn178 (NVIDIA
   H100 80GB HBM3, driver 580.159). Smoke test (gsm8k_qwen3 case_001, seed
   7, strict and mentored_dec 0.75): bit-identical to the same test on Nibi
   (772 / 736 tokens, same l_bar), V2 alpha line printed. Every not-done
   Qwen3 row moved (`addendum_campaign.py move-qwen3`) except step 2.1's last
   four arms, which stay on Nibi so that step's pairs share one machine.
   Runs record their venv path, so `per_request.csv` labels them (machine =
   killarney). Step 7 Qwen3: the first 40 cases per arm ran on Nibi, the
   rest run on Killarney (each case's pair on one machine). Step 0.5's
   Qwen3 reference runs on Killarney, the machine of the Qwen3 cells it
   serves (steps 3, 4.1, 5.1/5.2).
13. **Killarney nodes differ in time per round; comparisons are kept on one
   lane (2026-10-01 14:30Z).** Step 4.2 (Qwen3 at T 0.6) ran strict,
   mentored_dec and r_fuzzy on K1 (kn173/kn169: 9.5-9.6 ms per round, the
   relaxed arms within 1% of strict) and cactus, spec_casc_opt and
   spec_casc_tok on K2 (kn176: 10.5-10.8 ms per round), so those three time
   ratios carry a ~11% node penalty; their rounds ratios and lambda do not
   (README deviation 12 had spread rows over K1/K2 one by one). Every
   not-yet-started Qwen3 row was then regrouped so that each comparison --
   a dataset's step-0.5 reference with its step-3, 4.1 and 5.1 rows; each
   step-4.3 dataset; Qwen3 SPEED-Bench -- sits on one lane (K1: gsm8k,
   livecodebench, mtbench, aime24 and step 4.3 livecodebench; K2: humaneval,
   longbench_v2, SPEED-Bench). A lane still moves between nodes of its set
   from one 3 h job to the next, so a group can span nodes; the rounds ratio
   is the hardware-independent comparison throughout.
14. **Four Killarney lanes from 2026-10-01 ~15:00Z, at Bill's suggestion**
   (beyond the plan's "at most three jobs running", which was set with
   Nibi's queue in mind). Disjoint H100 node sets: K1 kn169-kn171, K2
   kn176-kn178, K3 kn172-kn173, K4 kn174-kn175 (the pending K1/K2 jobs were
   narrowed in place with `scontrol update ExcNodeList`); K3/K4 are copies of
   K1's repo + patched venv (V2 68d0a904). The comparison groups were
   re-spread over the four lanes whole (README deviation 13): K1 Qwen3
   SPEED-Bench, K2 step-4.3 livecodebench + humaneval + longbench_v2 +
   mtbench, K3 livecodebench, K4 aime24 + gsm8k.
15. **Killarney lanes may share a node (2026-10-01 ~15:50Z).** The disjoint
   node sets of deviation 14 left K3/K4 (two nodes each) waiting for a GPU.
   The two reasons for disjoint sets do not hold on Killarney once
   `remote/stop_server.sh` is job-scoped: every job gets a private /tmp
   (`JobContainerType=job_container/tmpfs`), so the patched sampler's /tmp
   knob files are per job; and the stop script now signals only processes
   whose cgroup path names this job (`/job_<SLURM_JOB_ID>/`; checked in a
   dry run inside K1's job, which found exactly its own server) -- its
   nvidia-smi step already saw only the job's GPU, and outside Slurm it
   behaves as before. Ports differ per job (`30000 + SLURM_JOB_ID % 20000`
   in `cascade/cluster/addendum_lane.sbatch`). All pending Killarney jobs had
   their ExcNodeList cleared; new ones are submitted without --exclude.
   Verified at 16:10Z with K2 (job 5837981, lmdraft spec_casc_tok 0.8) and K3
   (job 5839003, strict) running side by side on kn176: their /tmp are
   separate bind mounts (`/slurm/tmpfs/<jobid>/.<jobid>/_tmp`), the same knob
   file `/tmp/lossy-token-eff-spec-casc-tok-alpha-<uid>` read 0.8 in K2 and
   -inf in K3, K3's knob writes (15:44:18Z) left K2's files untouched
   (15:40:42Z), and neither lane logged a failed or quarantined item.
   Caveat (extends deviation 13): a lane's next 3 h job may now land on any
   of the ten H100 nodes, so a comparison group is more likely to span nodes.
   Run directories do not record their node; the lane journals do (host per
   item), and the poll archives them in `lanes/<lane>_status.jsonl`. The
   final tables use them to name each Killarney arm's node(s) and to flag
   time ratios whose arm and reference ran on different nodes; rounds
   ratios are unaffected.
16. **Qwen3 SPEED-Bench arms spread over lanes (2026-10-01 ~17:25Z).** With
   the whole SPEED-Bench group on K1 (deviation 14), K1 held 10.0 of the
   ~24 remaining GPU-h while K2 and K4 would have idled after 3-4 h. Since
   deviation 15 a lane's next job may land on any node, so one lane no
   longer means one node, and step 4.3 showed no node penalty between
   kn169 and kn176 (JOURNAL). The two relaxed arms with only their first-40
   cases done (already pulled, so nothing reruns) moved whole: r_fuzzy to K2
   and cactus to K4, each after that lane's other work; spec_casc_opt
   (mid-run), mentored_dec and spec_casc_tok stay on K1. Estimated remaining
   GPU-h: K1 5.9, K2 5.3, K3 6.4, K4 5.9 (was 10.0 / 3.0 / 6.5 / 4.1). The
   final tables name each arm's node(s) and flag mixed-node time ratios
   (deviation 15); rounds ratios are unaffected.
17. **Killarney rebooted every H100 node from 2026-10-01 ~18:40Z** ("Reboot
   ASAP": each node drains and reboots once its last job ends). Rebooted
   nodes run NVIDIA driver 580.178.04 (was 580.159.03; kernel 6.8.0-136
   after), so time per round may differ before and after a node's reboot.
   Every job's Slurm log records its driver (`nvidia-smi` at job start); the
   final tables flag time ratios whose arm and reference straddle the
   change, alongside the node flags of deviation 15. Rounds ratios are
   unaffected. The first job on a freshly rebooted node (K3's 5839004 on
   kn172) failed after 4 s: /cvmfs was not mounted yet, `module load` failed
   without stopping the batch script, and the venv python (a link into
   /cvmfs) raised ELOOP. The next job in the chain started 4 s later and ran
   normally. Two guards since ~19:20Z: the batch script waits for the venv
   python before `module load`, and `scripts/addendum_lane.py` stops before
   taking work if the modules did not load (no EBROOTCUDA), so no item runs
   in a partial environment. The guard tripped as intended on kn169 at
   20:57Z (K1 5837978, K2 5838004), but waiting does not help: each job has
   a private mount namespace, and a job created before /cvmfs was mounted
   saw ELOOP for its whole 300 s wait while the next jobs, 2 s later, ran
   normally. Since ~21:25Z both waits are 30 s, so such a job hands over to
   the next one in its chain within about a minute.
18. **Qwen3 step-3 nspec10 runs at `--gpu-memory-utilization 0.80`.** The
   first Qwen3 nspec10 item (gsm8k, K4 job 5839007, 2026-10-01 19:31Z)
   failed twice at server start: vLLM's sampler warmup over Qwen3's
   152k-token vocabulary at 10 draft tokens needed 2.12 GiB after the KV
   cache had taken 0.85 of the GPU (1.55 GiB free). GPT-OSS's nspec10 rows
   ran at the default on Nibi. The two Qwen3 nspec10 rows (gsm8k,
   livecodebench) pass `GPU_UTIL=0.80` to `remote/run_server_vllm.sh`; every
   other row keeps 0.85. The KV pool's size does not change a single
   request's computation (prefix caching off, one request at a time), and
   0.80 still holds a full max-length request.
19. **Qwen3 longbench_v2 drafts with a copy of the EAGLE-3 drafter whose
   config allows 65536 positions (2026-10-02, approved by Bill).** Every
   Killarney longbench_v2_qwen3 item crashed once a sequence passed 40960
   positions: CUDA device-side assert `index out of bounds ... < 40960`. The
   bound sat in the drafter's compiled rope kernel (vllm_cache/
   torch_compile_cache/<hash>/rank_0_0/eagle_head; the target's kernels had
   65536). `--hf-overrides` raises the target's max_position_embeddings to
   65536 alongside YaRN (2026-08-22), but RedHatAI/Qwen3-8B-speculator.eagle3
   builds its rope table from its own transformer_layer_config
   (max_position_embeddings 40960, rope_scaling null; snapshot 08610ffa, the
   config unchanged since the 2025-10 upload). The old box ran 339 longbench
   cases past 40960 positions with the same drafter; nothing in the repo
   records how. The longbench_v2_qwen3 rows now use
   `hf/local/Qwen3-8B-speculator.eagle3-maxpos65536` on Killarney: the
   snapshot's files byte-identical except config.json's
   max_position_embeddings 40960 -> 65536. Plain RoPE continues past 40960
   with the same theta, so every position below 40960 gets exactly the values
   it had before (the 13 earlier Killarney longbench runs stay comparable).
   These items get their own compile cache (`VLLM_CACHE_ROOT=/scratch/
   billxby/vllm_cache_longdrafter`); its drafter kernel's bound is 65536.
20. **Qwen3 step 5.2 pairs each seed-1 arm with a Killarney strict seed 1
   (2026-10-02 ~04:55Z).** The Qwen3 seed-1 arms run on Killarney, but the
   strict seed 1 they are judged against ran on Nibi (step 2.1) for gsm8k,
   humaneval, livecodebench and mtbench; only aime24's (step 2.2) ran on
   Killarney. `add52` now adds, for those datasets, a strict seed 1 under
   `runs/addendum/nibiref` on the arm's lane (the step 0.5 idea, one seed
   on), and `addendum_tables.py best` pairs seed 1 by machine. That gives
   7 seed-1 arms with graded grids (gsm8k md 0.35; aime24 md 0.55, tok 0.35;
   humaneval md 0.55, tok 0.35; livecodebench md 0.35; mtbench md 0.55) and
   4 strict references. Cells whose chosen alpha is the campaign's own
   (tok 0.8 on gsm8k, livecodebench, mtbench) already have their seed-1 pair
   from step 2.1 on Nibi. Each dataset's rows share one lane: K1 aime24, K2
   gsm8k + mtbench, K3 humaneval, K4 livecodebench, each after that lane's
   longbench_v2 item. `cmd_plan` now honours an extra row's named Killarney
   lane (it used to spread every new Qwen3 row by load, which split the
   pairs until they were moved back). Longbench's step-5.2 rows follow once
   its grid is complete and graded.
21. **SPEED-Bench's 208 HLE prompts are not run (2026-10-02, Bill's
   decision).** They come from the gated `cais/hle` dataset (a Hugging Face
   token was never set up) and were judged not essential: every arm of both
   models has the other 672 of the 880 qualitative-split prompts, all eight
   other categories are complete (80 each), and no other step uses them.
   Humanities, Math and STEM keep only their non-HLE prompts (8, 18 and 6
   per arm), so their per-category ratios are thin; RESULTS.md gives n per
   cell. The 14 step-7 rows stay `blocked` in the manifest with this reason.

## Step 8 (more drafters, the Llama-3.1-8B family, the fix on Qwen3-8B)

Branch `addendum-step8` off main d35d52de7; plan and protocol in `step8/GOAL.md`, orchestration in
`scripts/step8_campaign.py`, Block 0 checks in `scripts/step8_block0.py`. Numbered from 29 (22-28 are used
by the unmerged `speedbench-oct` branch).

29. **Llama weights from mirrors (2026-10-03, approved by Bill).** `meta-llama/Llama-3.1-8B-Instruct` and
   `meta-llama/Llama-3.2-1B-Instruct` are gated and no Hugging Face token is set up. The runs use
   `RedHatAI/Llama-3.1-8B-Instruct` (snapshot 83c92747) and `alpindale/Llama-3.2-1B-Instruct` (snapshot
   f92201d8). Every non-weight file of both mirrors is blob-identical to Meta's (git oids of config.json
   0bb6fd75 / 3e3aaf51, generation_config.json cc7276af / 75ae0831, tokenizer.json 5cc5f00a,
   tokenizer_config.json db88166e / 4ff488a1, special_tokens_map.json 02ee80b6, read from the gated repos'
   public file listings). Meta hides its weight hashes, so the weights are checked against independent copies:
   Llama-3.1-8B-Instruct shards sha256 2b1879f356aed350..., 09d433f650646834..., fc1cdddd6bfa9112...,
   92ecfe1a2414458b... (identical in RedHatAI, NousResearch and unsloth; recomputed on Killarney after download),
   Llama-3.2-1B-Instruct model.safetensors sha256
   1ff795ff6a07e6a68085d206fb84417da2f083f68391c2843cd2b8ac6df8538f (identical in alpindale and unsloth). The
   NousResearch mirror was tried first and dropped: its tokenizer_config.json carries Meta's first-release chat
   template, which renders no "Cutting Knowledge Date" system header (all 350 prompts differed from the current
   template). Tables cite Meta's ids.
30. **Persistent server per arm for calibration and full runs (step 8 protocol, Bill 2026-10-03).** The
   matched-l_bar protocol of `scripts/campaign_run.py` (calibration on case_001-003 at the 4-point grids, targets
   at the 20/55/90th percentile of the shared span, nearest grid alpha) runs on one persistent server per arm
   (`persistent_arm_replay.py`, prefix caching off, one request at a time), never shared across arms: a fresh
   server costs ~4.5-5 min on these clusters. A full arm's server starts at case_004 (case_001-003 are its
   calibration runs, on their own server). Every run's config.json records host, Slurm job and its server's
   start time; the request ordinal is in run.json as before. The paper's Limitations already describes the
   body's runs as first cases after a fresh start, the rest on a reused process.
31. **The yuhuili EAGLE heads run from copies whose config allows 65536 positions.**
   `yuhuili/EAGLE3-DeepSeek-R1-Distill-LLaMA-8B`, `yuhuili/EAGLE3-LLaMA3.1-Instruct-8B` and
   `yuhuili/EAGLE-LLaMA3.1-Instruct-8B` declare max_position_embeddings 2048; vLLM caps the drafter at that, and
   R1-Distill's LiveCodeBench strict runs crashed past it (device-side assert in the drafter's compiled rope
   kernel, Block 0 job 5913648; the deviation-19 failure). `hf/local/<name>-maxpos65536` on Killarney: config.json
   with max_position_embeddings 65536, weights symlinked. Plain RoPE: positions below 2048 get the values they
   had. Whether the heads draft well past the length they were trained on is measured in Block 0 (acceptance vs
   position) and reported in RESULTS.md.
32. **Consolidated V2 sampler with spec_casc_tok_lt and spec_casc_opt_head (Block 6).**
   `patches/vllm-0.26.0-v2-consolidated-step8.patch` (sha256 796e3c85...): the 68d0a904 file plus the two
   rules as defer masks ANDed into the existing one (both are switch rules, so these are complete ports, not
   accept-test-only), and an observation-only q probe (Block 0(d)). At the two rules' neutral values every other
   method's decision is unchanged; checked bit for bit on GPU (job 5913862: strict and the five rules on the old
   and the new file, same case and seed) before the file replaces 68d0a904 in any lane venv.
33. **DeepSeek-R1-Distill-Llama-8B is served with a corrected tokenizer class.** Its tokenizer_config.json
   declares `LlamaTokenizerFast` (legacy) for a byte-level BPE tokenizer.json. Under transformers 5.18 (the
   lane venvs) that class encodes every prompt wrongly (spaces dropped: "Every morning Aya" -> Every / mor /
   ning / Ay / ago ...; 0 of 350 R1 prompts match the tokenizers library's encoding of the model's own
   tokenizer.json) and decodes without byte-level decoding (output.txt full of Ġ / Ċ, so LiveCodeBench code
   blocks could not be extracted). vLLM loads it the same way. The server now gets `--tokenizer
   hf/local/DeepSeek-R1-Distill-Llama-8B-tokenizer-fast` (`TOKENIZER` in `remote/run_server_vllm.sh`): the same
   tokenizer.json, special tokens and chat template, declared `PreTrainedTokenizerFast` (350 of 350 prompts match
   tokenizer.json; decoding correct). Llama-3.1-8B-Instruct (350/350), Qwen3-8B (1322/1322) and GPT-OSS-20B are
   unaffected. The first Block 0 R1 runs (a_*, b_*) ran on the mis-encoded prompts and are kept only as the
   record of this; every R1 number comes from the rerun (a2_*, b2_*, prof2_*).
34. **A compile cache per step-8 pair.** Qwen3-8B + Qwen3-1.7B (draft_model) crashed in the drafter's CUDA-graph
   capture (illegal memory access) right after vLLM loaded an AOT-compiled graph from the shared
   `$SCRATCH/vllm_cache`, which already held the same architecture compiled for Qwen3-0.6B (step 4.3). With a
   cache of its own it ran (strict and mentored_dec 0.75, job 5913861). Every step-8 pair now compiles into
   `/scratch/billxby/vllm_cache_step8/<pair>` (`VLLM_CACHE_ROOT`).
35. **A freshly compiled server is not bit-identical to a cache-loaded one on the V2 path; every pair's cache is
   warmed before its arms.** Llama-3.1-8B-Instruct + EAGLE-3, GSM8K case_001, seed 0: lossless gave 166 tokens
   whenever its server was the first on a fresh compile cache and 142 tokens on a warm one (two warm reruns, jobs
   5914666), byte-identical to all five rules at their strict points (Block 0 strict-limit check). Fresh
   compilation autotunes kernels by timing; a cache load replays one choice. Both outputs are lossless draws; only
   the numerics differ. Every step-8 pair therefore gets one throwaway warm-up server (case_001, outside the run
   tree) on its own cache before any measured arm, so no measured arm runs on a fresh compile.
36. **Medusa dropped from Block 2** (the plan's Medusa fallback). nebius/MEDUSA-Llama-3.1-8B-Instruct (6 heads)
   loads and serves, but vLLM's medusa path hands the sampler no draft probabilities: all 224 traced proposals have
   q(x) = 1.0 and no draft entropy (Block 0 q probe). The cascade and fuzzy rules need q (Bill's Block 0(d) rule).
37. **Block 3's second Qwen3-8B drafter is deepseek-ai/dspark_qwen3_8b_block7 (method dspark)**, the first in Bill's
   order (DSpark -> DFlash -> Thinking EAGLE-3) to pass the q probe: draft-prob tensor (1024, 6, 151936) present at
   the patched V2 sampler, 0% one-hot rows, mean max q 0.78-0.92, mean draft entropy 0.28-0.80 nats. vLLM 0.26.0
   runs dspark on the V2 runner only, so its cactus and spec_casc_tok rows are accept-test-only.
38. **Block 5 runs although R1-Distill's and Llama-3.2-1B's tokenizers are not identical (Bill, 2026-10-03).** Same
   vocabulary size (128256) and the same ids for 128249 tokens; the other 7 are special tokens R1 renamed (BOS/EOS
   128000/128001) or repurposed from Llama's reserved range (128011-128015: `<｜User｜>`, `<｜Assistant｜>`,
   `<think>`, `</think>`, pad), untrained in the 1B drafter. vLLM requires only the vocabulary size; acceptance
   near those ids may suffer, correctness cannot (lossless verification by the target).
39. **Block 4 (GPT-OSS-20B + RedHatAI EAGLE-3) runs on Killarney, not Nibi (2026-10-03 ~20:20Z).** At launch every
   Nibi GPU node was down or drained (sinfo: 324 "Node unexpectedly rebooted", 96 "gres/gpu count reported", 24
   drained for an image test / issue #1079); the Nibi warm-up and lane jobs sat in ReqNodeNotAvail and were
   cancelled. GPT-OSS-20B, the drafter and its prompt sets are on Killarney; the whole block runs there (one node
   type, like every other step-8 block).

## Step 9 (the 5 rules x 6 datasets grid for the five dedicated step-8 pairs)

Branch `addendum-step9` off main 32517782d; plan and protocol in `step9/GOAL.md`, orchestration in
`scripts/step9_campaign.py` (step 8's pair definitions imported unchanged), Block 0 in `step9/BLOCK0.md`.

40. **Qwen3-8B + DSpark on LongBench-v2 drafts with a copy of the DSpark head whose config allows 65536 positions.**
   `deepseek-ai/dspark_qwen3_8b_block7` (snapshot 03326e50) declares max_position_embeddings 40960 with plain RoPE
   (theta 1e6); Qwen3's longest LongBench-v2 sequence is 51,234 prompt tokens + the 8,192 budget. `hf/local/
   dspark_qwen3_8b_block7-maxpos65536` on Killarney differs only in that field (config sha256 e470e70a -> cbf2a274;
   weights symlinked, sha256 5c922d1f... = the published blob), as deviations 19 and 31 did for the EAGLE heads;
   positions below 40960 get the values they had. Only LongBench-v2 uses it, with a compile cache of its own
   (`vllm_cache_step8/qwen3-8b__dspark-maxpos65536`, first compiled by the block's Block 0 smoke run, so no measured
   arm runs on a fresh compile: deviation 35). The other step-9 datasets stay inside 40960 and use the original head.
41. **Sixteen Killarney lanes (K9-K16 new), prompt sets copied on the cluster.** K9-K16 are copies of K8's repo +
   venv (`cp -a`, like K5-K8). The Mac's link to Killarney ran at ~60 KB/s on 2026-10-05 (20 MB in 346 s; Nibi: 3 s),
   so the prompt sets go to the cluster once (`/scratch/billxby/step9/prompts_stage`) and every lane repo is made
   byte-identical to the committed sets there (`scripts/sync_prompt_sets.py`, sha256 digest per set; a lane whose sets
   do not verify gets no work). A first push from the Mac, stopped after 10 minutes, had left K1's
   `prompts/longbench_v2_qwen3/case_040/rendered_prompt.txt` truncated (32,256 of 81,537 bytes); the digest check
   caught it and the staged copy replaced it before any step-9 run.
42. **The Llama-3.1-8B-Instruct blocks (EAGLE-3 and EAGLE-1 heads: 3c, 3d, 4c, 4d, 5a, 5b) run on Nibi H100s; the
   GPT-OSS-20B, Qwen3-8B + DSpark and R1-Distill blocks on Killarney (2026-10-05 ~19:40Z).** Both H100 queues were deep
   at launch: Killarney's GPUs were CPU-bound (8 idle GPUs, no free CPUs) and Slurm's start estimate for our next
   Nibi job was ~9 h out, so both clusters take work. Every block runs whole on one cluster, and so does every pair's
   set of step-9 blocks: H100 80GB HBM3 on both, the lossless reference and every arm of a block on the same hardware
   and compile cache. (A first split, 19:15Z, also put GPT-OSS on Nibi; it was moved before any run.) Nibi holds the
   same snapshots as Killarney (Llama-3.1 83c92747 with all four shard sha256s of deviation 29, yuhuili heads ada412b6
   / d0e4a208; also gpt-oss-20b 6cee5e81 and RH head c2825cb4), the same 65536-position head configs (sha256 3e47bd97
   / f8aa3860, weights sha256 16d5bf95 / 875f4613 on both clusters) and the same patched samplers (V2 file 63d52ec3 in
   every Nibi and Killarney lane venv). Nibi has no per-job /tmp and the patched samplers read per-user /tmp knob
   files, so the four Nibi lanes (N1/N2 = the addendum's lanes A/B, N3/N4 copies of B) each get a disjoint node set
   (g1-7, g8-14, g15-21, g22-29); each Llama pair compiles into its own Nibi cache
   (`/scratch/billxby/vllm_cache_step9/<pair>`), warmed by one throwaway job before any Block 0 or measured run
   (deviation 35). **Superseded 2026-10-05 ~22:00Z:** Nibi's start estimate for that warm-up job slipped to
   2026-10-08 13:00 while all 16 Killarney lanes ran, so the Llama blocks (no run yet, no Nibi job ever started) moved
   to Killarney as well, on step 8's warm Llama caches; every step-9 block runs on Killarney H100s and the Nibi jobs
   were cancelled. Nibi only grades (CPU).
43. **A FlashInfer JIT workspace per Killarney lane (2026-10-05 ~22:45Z).** Six of the first ~110 step-9 servers hung
   in engine warmup (no /health within the startup timeout; the lane retried each item, no run affected). Every vLLM
   server JIT-builds FlashInfer's sampling module into `~/.cache/flashinfer/0.6.14/90a/cached_ops/sampling` under one
   file lock, and the module's `build.ninja` names the building lane's own venv, so with 16 lanes the shared build was
   invalidated and redone by each lane in turn (the directory held fresh object files and never a linked module; this
   rebuild is also why a server start took ~5 min). Each lane now builds into its own workspace
   (`FLASHINFER_WORKSPACE_BASE=/scratch/billxby/step9/flashinfer/<lane>`): the same sources, flags and compiler, built
   once per lane and loaded afterwards. Outputs are unaffected; server starts get shorter.
44. **Step-9 tables and two schema details (2026-10-06).** `tables/step9__<target>__<drafter>.csv` keeps exactly the
   columns of the pair's `step8__` file, with one exception: cmd_step8 writes `time_ratio_same_node` only when some
   row has 10 or more same-node pairs, so the standalone step-8 tables (Llama-3.2-1B rows, Qwen3-1.7B, P-EAGLE) lack
   that column; when a step-9 row of such a pair has it, it is appended last (blank in the step-8 rows of
   `pairs__`). Qwen3-8B + Qwen3-0.6B has no step-8 table (its earlier GSM8K / LiveCodeBench rows are the addendum's
   step 4.3, `tables/lmdraft__*`, another schema): its step-9 table takes the Qwen3-1.7B standalone columns, and its
   `pairs__` file holds the step-9 rows only. Phase 2's LongBench-v2 rows for Qwen3-1.7B, Qwen3-0.6B and P-EAGLE
   draft with 65536-position config copies (as deviation 40; config sha256 1ddb5b89 -> 4df54204, 660db3b7 ->
   8408670b, ea17a342 -> ecabb1e3), each with its own compile cache; Qwen3-0.6B's own cache was warmed first
   (Killarney job 5974366, deviation 35).
45. **MT-Bench judged for steps 8 and 9; HumanEval checked with a defining-block grader (2026-10-06, Bill).** At Bill's
   request after step 9 (the step-9 plan had said no judge spend), every MT-Bench arm of the step-8 and step-9 tables
   was judged exactly as the addendum's step 1.9 (scripts/addendum_mtbench_judge.py unchanged, pointed at the step-8 /
   step-9 run trees by `scripts/step9_mtbench_judge.py`): FastChat single-answer prompts, turn 1, claude-fable-5-1 at
   effort medium on the Message Batches API, batch msgbatch_011ouT5reDRgUyekZvEADp4T, 7,525 requests (12.77M input /
   3.94M output tokens, $162.28), plus 635 runs with no readable answer scored 1 without a request; 63 judge refusals
   are recorded as such. Llama-3.1 answers are the whole completion; Qwen3 / R1-Distill the text outside `<think>`.
   Outputs `step9/mtbench_judge/` (per run, per arm, and `mtbench_vs_lossless.csv`, paired by question). HumanEval:
   the 897 runs (all trees: paper grid 46, addendum 4, step 9 847) whose last code block is not the defining one were
   re-executed on their last DEFINING block (`scripts/humaneval_regrade.py`, grade_humaneval.execute unchanged); 315
   pass. The official tables keep the campaign's grader: the alternative does not make same-target lossless
   accuracies agree better (Qwen3 82.7-84.7% -> 84.0-86.7%, Llama 55.3-58.0% -> 56.0-62.0%; within sampling noise at
   n = 150) and changes no conclusion; the per-run verdicts are in `step9/humaneval_regrade.csv`.
46. **Qwen3-8B + Qwen3-0.6B: spec_casc_opt and r_fuzzy filled in on GSM8K and LiveCodeBench (2026-10-06, Bill).** The
   addendum's step 4.3 ran only mentored_dec 0.75, cactus 0.35 and spec_casc_tok 0.8 for this pair, so the paper's
   0.6B column had two empty cells per dataset. spec_casc_opt 0.05 and r_fuzzy 0.25 (each rule's loosest grid alpha)
   ran with the addendum's own step-4.3 item definition (`scripts/step9_lmdraft_fill.py`; Killarney jobs 5987261 /
   5987262, 2.4 GPU-h) into `runs/addendum/lmdraft`, paired with the same step-4.3 lossless reference, graded with the
   campaign's graders (`step9/grades_lmdraft.csv`). `tables/lmdraft__*_qwen3.csv` gain two rows each; the three
   step-4.3 rows are byte-identical (the new rows draw their bootstrap from a stream of their own, seed 20261002).
