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
