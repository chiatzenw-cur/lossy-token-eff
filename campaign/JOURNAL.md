# Campaign journal

Append-only. One entry per work session. See `campaign/PLAN.md` for the design.

## 2026-08-15 (session 1)

- Explored the repo (`runs/readme.md`, `patches/README.md`, `remote/ENVIRONMENT.md`,
  `scripts/run_experiment_vllm.py`, `scripts/fresh_server_replay.py`,
  `scripts/lossy_methods.py`) to understand the existing fresh-server-per-
  measurement infrastructure before building anything new on top of it.
  `scripts/fresh_server_replay.py` already does everything the "run the
  sweep" half of this task needs (server lifecycle, patch switching, per-run
  alpha via CLI, resumable skip-if-done, trace on/off) -- reused as-is, not
  reimplemented.
- Found disk at 96% full / 4.2G free on the root filesystem (pre-existing,
  not caused by this task). Initially planned to route new run data to
  `/srv/data` (934G free) but that's root-owned with no write access for
  this user and no sudo available -- worked around it instead by disabling
  per-token tracing (`--no-trace-proposals`), which was never needed for
  this deliverable anyway (only `run.json`'s summary fields are), dropping
  per-run disk cost from ~1-1.5MB to ~25KB. Full campaign now costs ~30MB.
  Flagged in `campaign/PLAN.md`; no user action needed unless a future task
  here genuinely needs the trace files at scale.
- `git mv runs old_runs` (13,585 tracked files, clean rename, all existing
  AIME24/HumanEval data including the guard-variant pilots preserved).
  Fresh `runs/` created, added to `.gitignore` (not tracked going forward --
  avoids growing the already-full root disk's `.git`, and the data is
  regeneratable from `campaign/` scripts + `prompts/`). Committed as
  `172e755b`.
- Checked the sibling repo `~/lossy-spec-decode-repetition` for LiveCodeBench/
  MT-Bench/LongBench-v2: it already has `build_livecodebench_prompts.py`,
  `build_mtbench_prompts.py`, `build_longbench_v2_prompts.py` and their
  fetched output (90/80/153 cases respectively). Verified completeness
  directly (per the user's ask): `candidate_index.jsonl` line counts match
  case-dir counts exactly for all three (90/90, 80/80, 153/153), every case
  dir has all 4 required files non-empty, and a sampled `rendered_prompt.txt`
  (livecodebench case_001) ends cleanly at `<|start|>assistant` with no
  truncation. No GSM8K there -- building it fresh here.
- Wrote `campaign/PLAN.md`: case counts (12 full-sweep + 3 calibration-probe
  cases per dataset), per-method alpha calibration grids (4 points each,
  anchored to the existing single-alpha reference table), target-selection
  rule (nearest-grid-point to 3 percentiles of the cross-method-achievable
  l̄ band), and per-dataset `--max-new-tokens` budgets (gsm8k 2048, aime24
  32768, humaneval 9000, livecodebench 12000, mtbench 4096, longbench_v2
  8192) -- picked from each task's output-length character, not copied
  from one dataset to all. Time budget self-estimate: ~1,170 runs total,
  ~2-2.5 days of continuous single-GPU wall time (no parallelism possible --
  fresh-server-per-measurement is a hard requirement here, see
  `remote/ENVIRONMENT.md`).
- Next: build `scripts/build_gsm8k_prompts.py`, copy+subset the 3 borrowed
  prompt sets, write `scripts/campaign_run.py` (calibrate -> pick targets ->
  full sweep, resumable, one dataset at a time) and
  `scripts/campaign_report.py` (tables + graphs), then kick off the actual
  GPU campaign in the background.
- Built `scripts/build_gsm8k_prompts.py` (12 cases, `openai/gsm8k`), and
  `scripts/subset_borrowed_prompts.py` to evenly-stride 12 cases each out of
  the sibling repo's livecodebench/mtbench/longbench_v2 sets. All 6 prompt
  sets now have exactly 12 `case_NNN` dirs available (aime24/humaneval reuse
  their own first 12 of their larger existing sets).
- Wrote `scripts/campaign_run.py` and `scripts/campaign_report.py`, dry-run
  validated the plumbing, then ran a real 2-case smoke test on gsm8k/
  spec_casc_tok. Caught a real resumability bug this way: a run killed
  mid-flight (by the smoke test's own `timeout 300` wrapper) leaves a
  partial run directory (config/request/server_info.json but no run.json),
  and `run_experiment_vllm.py`'s own overwrite guard would make every future
  retry of that exact (method, alpha, case) fail identically forever --
  silently, since `fresh_server_replay.py` logs a failure and moves on
  rather than stopping. Fixed by adding `clean_partial_runs()` to
  `campaign_run.py`, run automatically before every dataset's stage 1 --
  confirmed it correctly cleaned up the smoke test's own leftover partial
  dir on the very next invocation. The 2 completed smoke-test runs
  (gsm8k/spec_casc_tok/alpha0.15, case_001+case_002) produced well-formed
  `run.json` (l_bar 3.57/3.23, output_tokens 160/144, status ok) and are
  real data, not discarded -- alpha 0.15 is genuinely part of
  spec_casc_tok's real calibration grid, so they count toward the real
  campaign's calibration mean.
- No `matplotlib` in either `.venv-vllm` or system python3, and system pip3
  is PEP-668-externally-managed with no `python3-venv` package installed (no
  sudo to fix that). Built a separate `.venv-report` via `uv venv` (avoids
  needing the broken system `ensurepip`) with matplotlib -- kept fully
  separate from `.venv-vllm` on purpose, since that env's exact package set
  is load-bearing for the patched-kernel tests (see `remote/ENVIRONMENT.md`'s
  hardlink-trap warning) and has no reason to carry plotting deps.
  `campaign_report.py` verified against the smoke-test data (writes
  `campaign/tables/gsm8k.csv` correctly; correctly no-ops on the graph until
  a `campaign/calibration/<dataset>.json` exists).
- Loaded the `dataviz` skill before writing the graph code. Static
  matplotlib PNG, not an interactive artifact, so only the medium-agnostic
  rules apply: fixed categorical color order (skill's validated slots 1-5,
  never cycled), and since 5 series exceeds the palette's own 3-series
  all-pairs-safe cap, added marker shape + linestyle as secondary encoding
  per method plus direct end-of-line labels, not color/legend alone.
- **Launched the real campaign**: `nohup bash scripts/campaign_all.sh` (all
  6 datasets, sequential, detached from this session so it survives
  independent of this conversation) ->
  `logs/campaign_all_stdout.log`. Started with gsm8k (fastest dataset --
  short completions, ~1-2s generation per run, so wall time is almost
  entirely the ~90-100s fresh-server overhead). Order: gsm8k, aime24,
  humaneval, livecodebench, mtbench, longbench_v2.
- Set up a self-paced `/loop` to check in periodically (aiming for
  20-30 min between checks while runs are actively landing), update this
  journal, and run `campaign_report.py` for any dataset whose full sweep
  finishes, until all 6 are done.
- User asked for the per-token trace after all: turned tracing back on
  (dropped `--no-trace-proposals` from `campaign_run.py`'s
  `fresh_server_replay.py` invocation -- tracing is that script's own
  default). At that point gsm8k's `mentored_dec` calibration grid had
  finished (14 runs) and `cactus` calibration had just started -- cleanly
  killed the running driver + server (`kill -TERM` on `campaign_run.py`/
  `fresh_server_replay.py`, then `remote/stop_server.sh`, confirmed 0MiB GPU
  used afterwards), deleted `runs/gsm8k` entirely (14 small untraced runs,
  ~110s/run to redo -- cheaper and cleaner than leaving a traced/untraced
  split in the same dataset's table), and relaunched
  `scripts/campaign_all.sh` from a clean gsm8k start. Disk was still 4.1G
  free at this point (the untraced runs cost ~25KB each, negligible either
  way) -- re-checked the contingency plan (`runs_old_backup/`, 2.3G, is the
  first thing to recycle if tracing's real disk cost turns out to matter)
  and documented it in `campaign/PLAN.md`, but haven't needed to touch it
  yet.
- **Session recovered after SSH disconnect**: the monitoring session died
  around 2026-08-15T04:42Z mid-check-in (last message was confirming the
  first traced `proposals.jsonl` landed). `scripts/campaign_all.sh` itself
  was launched via `nohup` and kept running the whole time, unaffected --
  at recovery it was still on gsm8k's `spec_casc_tok` calibration sweep
  (alpha0.8, case_007/9), ~5h20m of continuous uptime. gsm8k run counts at
  recovery: cactus 39, mentored_dec 39, r_fuzzy 39, spec_casc_opt 39,
  spec_casc_tok 27 (of 39) -- no dataset has a finished calibration+sweep
  yet, so nothing new for `campaign_report.py` to do this check-in.
  Restarted the self-paced check-in loop (same ~20-30 min cadence as
  before) to pick back up where it left off.
- **Added the lossless (`strict`) reference back in** (user request,
  reversing the original scoping decision in `campaign/PLAN.md`). Reused
  `fresh_server_replay.py`'s existing `strict` arm (no new plumbing there)
  -- `campaign_run.py` gained a Stage 0 that runs `--arms strict` once per
  full 12-case set (no alpha axis, `--skip-strict` to opt out), and
  `campaign_report.py` now aggregates any `method=strict` run.json rows
  into `results/<dataset>.csv` and plots them as a single reference point
  (neutral `X` marker + dashed guide lines, not a 6th palette color -- see
  `STRICT_STYLE`'s comment). Verified with `--dry-run` on humaneval (writes
  to `humaneval/strict/strict/`, correct) and a live re-run of
  `campaign_report.py --dataset gsm8k` (186/14 rows unchanged, since gsm8k
  has no strict data yet -- confirms no regression for datasets without it).
  Did **not** touch `campaign_all.sh` while it's the live process (PID
  598170, editing a running bash script mid-execution is a real footgun --
  seek/buffering can read the wrong bytes after an edit); it stays as-is
  and picks up the new `campaign_run.py` automatically on its next fresh
  subprocess invocation (humaneval onward). **gsm8k (done) and aime24
  (mid-sweep) still need a strict backfill** -- can't run it now, GPU is
  busy with the live aime24 sweep and this setup has no parallelism; queued
  for whenever the GPU is next free (watching for it in the check-in loop).
- **Disk cleanup** (user request, root disk hit 97% full / 3.6G free):
  removed `runs_old_backup/` (2.3G, already in git history), 5 unused
  HuggingFace model/dataset cache entries not touched by this campaign's
  server (~7.65G), and `~/deferred-window-trace-label`'s gitignored
  `.venv/` (8.8G, regenerable, unrelated sibling repo) -- 20G reclaimed,
  disk now 77% full / 23G free. Left `old_runs/` and the other sibling
  repos alone (real uncommitted/live-session risk found there -- see chat
  for the full audit). Also removed a stale `backup-pre-rewrite` git branch
  in that sibling repo after confirming its "2 unpushed commits" were
  identical-content leftovers from a prior history rewrite, not new work.
- **`campaign/FINDINGS.md` added** (user request: "record the trails and
  restrictions of different methods"): cross-dataset per-method behaviour
  -- achievable l̄ range, monotonicity, chosen-alpha collapse pattern.
  Headline: `cactus` and `spec_casc_tok` have set the shared
  cross-method l̄ band's floor and ceiling respectively on every one of the
  3 finished datasets so far (gsm8k, aime24, humaneval) -- not a fluke,
  same two methods both times. `spec_casc_tok` also non-monotonic in alpha
  on 2/3 datasets. See that file for the full tables; update it as
  livecodebench/mtbench/longbench_v2 land to see if the pattern holds.
- **Added statistical backing to the headline finding** (user: this may go
  in the survey paper, needs data backing). Raw per-case l̄ std (~0.2-0.5)
  is comparable to the between-method mean gaps, so mean-vs-mean alone
  wasn't strong enough -- ran a **paired per-case sign test** instead
  (same 12 prompts under every method, so per-prompt variance cancels out
  of the comparison). Result: cactus's floor beats every other method's
  floor in 131/144 (91.0%) paired case comparisons pooled across the 3
  finished datasets, and every other method's ceiling beats spec_casc_tok's
  ceiling in 139/144 (96.5%) -- all 24 dataset x method-pair cells directionally
  unanimous, 22/24 individually significant at p<.05 (n=12 each). The 2
  non-significant cells are both `spec_casc_opt` vs `cactus` on the floor
  claim (9/12), consistent with it having the next-highest floor, not a
  contradiction. Full tables + reproduction pointer in
  `campaign/FINDINGS.md`'s new "Statistical backing" section -- no new
  runs needed, reused existing sweep data (`campaign/tables/*.csv`).
- **gsm8k finished** (2026-08-15T10:05:08Z, ~5h25m total for this dataset).
  `campaign_report.py --dataset gsm8k` ran automatically at the end of
  `campaign_all.sh`'s gsm8k stage: `campaign/tables/gsm8k.csv` (186 rows,
  raw per-run data across all 5 methods' calibration grids),
  `campaign/results/gsm8k.csv` (14 rows -- the picked 3-target-alpha
  comparison points per method), and `campaign/graphs/gsm8k.png` (the
  5-line mean-accept-length-vs-completion-length graph) all written, report
  script exited 0. Campaign auto-advanced straight into **aime24**
  (started same second, mentored_dec calibration alpha0.15/0.35 first --
  aime24's 32768-token budget makes each run much slower than gsm8k's,
  e.g. case_002/alpha0.15 alone took 231s of generation).
- **Accuracy grading added** (user: "we should also produce score accuracy
  of final result graph"). Found `scripts/grade_aime.py` and
  `scripts/grade_humaneval.py` already existed and work as-is against this
  campaign's run tree (same `<method>/<params>/<case>/seed_N/` layout) --
  reused directly. Wrote `scripts/grade_gsm8k.py` (numeric `####` marker,
  adapted from grade_aime.py) and `scripts/grade_longbench.py`
  (`\boxed{<letter>}` MC match, ditto). `scripts/campaign_report.py` now
  imports whichever grader applies (new `GRADERS` dict) and writes a
  6th `accuracy` column into `results/<dataset>.csv` plus a second graph,
  `graphs/<dataset>_accuracy.png` (same method colors/styles, x=l̄ again,
  y=accuracy, `strict` reference point included) -- ran it for gsm8k,
  aime24, humaneval (all 3 already-finished datasets): humaneval's
  accuracy graph is a real finding on its own, `r_fuzzy` drops to 50% pass@1
  at its highest tested alpha while `mentored_dec`/`spec_casc_tok` hold
  100% across their whole range. **livecodebench and mtbench have no
  grader yet** -- livecodebench needs its real test cases re-fetched
  (`build_livecodebench_prompts.py` deliberately skipped the ~1.25GB
  test-case blobs when building prompts) plus a stdin/stdout execution
  harness (HumanEval's `check()`-function harness doesn't apply); mtbench
  needs an LLM-judge, no infra exists anywhere on this machine. Neither
  built yet -- flagged to the user rather than assumed, given the
  data-fetch + engineering + (for mtbench) extra GPU-time cost involved.
- **Qwen3-8B + drafter feasibility checked** (user: "if we have space").
  Qwen3-8B itself is 16.4G, cheapest available drafter
  (`Tengyunw/qwen3_8b_eagle3`) is 0.8G -> ~17.2G to download, against
  20G currently free. Fits, barely -- would leave near-zero headroom while
  longbench_v2 is still writing to `runs/` and the gsm8k/aime24 strict
  backfill (Task #1) hasn't run yet. Not started; GPU is also single and
  fully booked by the live campaign regardless of disk, so this is
  necessarily a next-phase item, not something to interleave now.
- **More disk cleanup, user request ("clean old_runs we need the space")**:
  removed `old_runs/` (6.7G) after confirming it's fully tracked in git
  (13,796 files, commit `172e755b`, clean working tree) -- nothing lost,
  recoverable with `git checkout 172e755b -- old_runs` any time. This
  reverses the "keep it" call from earlier the same day; the Qwen3-8B
  download below is why the extra headroom was needed. Disk now 27G free
  / 73% used.
- **Qwen3-8B + drafter: proceeding** (user: "start downloading the models
  now"). `Qwen/Qwen3-8B` (16.4G) + `Tengyunw/qwen3_8b_eagle3` (0.8G) via
  `huggingface_hub.snapshot_download`, disk-only (no GPU needed for the
  download itself) -- see JOURNAL for completion/next steps.
- **livecodebench grading: starting** (user: "build it"). Needs the real
  test cases re-fetched (`build_livecodebench_prompts.py` skipped them
  originally) for just the 12 cases actually in `prompts/livecodebench/`,
  not the full ~1.25GB file, plus a new stdin/stdout execution harness --
  see JOURNAL for how the fetch was actually done and what it found.
- **Qwen3-8B + drafter download: done.** `Qwen/Qwen3-8B` (16G) and
  `Tengyunw/qwen3_8b_eagle3` (764M) both landed in the HF cache in under a
  minute (fast link). Disk-only step, as scoped -- actually running any of
  the campaign against this model pair still needs the GPU, which is still
  fully committed to the live 6-dataset campaign; that part is a genuinely
  separate next step, not started.
- **livecodebench test cases fetched**: streamed `test.jsonl` (~1.25GB on
  HF, never written to disk in full -- read in 1MB chunks, matched by
  `question_id` against the 12 IDs actually in `prompts/livecodebench/`,
  discarded everything else) into `prompts/livecodebench/test_cases.json`
  (12 rows, all found). **Public test cases only, deliberately**: the
  `private_test_cases` field is a base64+zlib+pickle blob, and unpickling
  data fetched from a URL is a real code-execution risk regardless of the
  host's trustworthiness -- the permission classifier actually caught me
  reaching for `pickle.loads` on it during a format-probe and blocked it,
  which was the right call, not worked around.
- **`scripts/grade_livecodebench.py` written**: same Harmony-final-channel
  + fenced-```python-block extraction as `grade_humaneval.py`, but a
  stdin/stdout execution harness (candidate run as a whole program, each
  public test case's `input` piped in, `output` compared
  line-by-line/trailing-whitespace-insensitive) instead of HumanEval's
  `check()`-function style, since LiveCodeBench problems are competitive-
  programming programs, not single functions. Wired into
  `campaign_report.py`'s `GRADERS` (one extra required kwarg,
  `test_cases_by_qid`, handled via a lazy callable since it's the only
  grader that needs one). Result: **35/189 (18.5%) pass@1 pooled**,
  spot-checked a sample of the "error" verdicts and they're real candidate
  bugs (SyntaxError/NameError/IndexError in the model's own generated
  code, not harness bugs) -- one was literally `NameError: name
  '__namename__' is not defined`, a garbled duplicated token, which given
  this whole repo studies decoding pathologies under lossy speculative
  decoding is a fairly on-the-nose failure mode to have caught.
  `strict` (lossless) itself only passes 1/12 -- LiveCodeBench is
  genuinely hard for this model at this scale, not an artifact of the
  relaxed methods. Re-ran `campaign_report.py --dataset livecodebench`:
  accuracy column + `graphs/livecodebench_accuracy.png` both written.
- **Fixed a label-collision bug in `render_graph()`** while looking at the
  livecodebench accuracy graph: with n=12 cases, accuracy is coarsely
  quantized (multiples of ~8.3%), so multiple methods' end-labels landed on
  the exact same point and rendered as garbled overlapping text (spotted
  "spec_casc_optr_fuzzy" as one string). Fixed with a small per-method
  vertical offset cycle instead of a fixed offset for every label;
  re-rendered all 4 finished datasets' graphs with the fix (gsm8k, aime24,
  humaneval, livecodebench) -- no data changed, cosmetic only.

## 2026-08-17 (session 2)

- **campaign_all.sh finished overnight**: all 6 datasets done as of
  `2026-08-16T23:49:24Z` (longbench_v2 was last), zero errors across the
  whole 1d14h+ run. GPU free.
- **Strict backfill for gsm8k + aime24** (Task #1, deferred from session 1):
  launched `campaign_run.py --dataset {gsm8k,aime24}` + `campaign_report.py`
  for each in the background; both datasets' `results/*.csv` had 0 strict
  rows going in, confirming the backfill was real (not already covered).
- **Qwen3-8B + drafter run: scoped and built** (user: "after backfill do the
  same data collection on qwen 8b", then "full 6-dataset parity" when asked
  about scope given a real compatibility gap -- see below).
  - **Found the pipeline is not model-agnostic** the way
    `run_server_vllm.sh`'s `MODEL_PATH`/`DRAFT_MODEL_PATH` env vars make it
    look: prompts are pre-rendered through `openai_harmony`'s
    `HARMONY_GPT_OSS` encoding (GPT-OSS's own chat format), and every
    `grade_*.py` extracts answers by splitting on Harmony's
    `<|channel|>final<|message|>` marker -- neither means anything to
    Qwen3, which uses ChatML (`<|im_start|>`/`<|im_end|>`) and
    `<think>...</think>` instead. The 5 relaxation methods themselves are
    fine as-is (threshold on p/q probabilities, no GPT-OSS-specific token
    IDs in the plain variants this campaign uses).
  - **`scripts/build_prompts_qwen3.py`** (new): converts an existing
    Harmony prompt set into a Qwen3 one by extracting the
    `<|start|>user<|message|>...<|end|>` block from each case's already-
    rendered `rendered_prompt.txt` (confirmed single-turn for all 6
    datasets first) and re-rendering that same content through
    `AutoTokenizer.apply_chat_template` (Qwen/Qwen3-8B, enable_thinking=
    True). One generic script instead of six per-dataset builders --
    exact content parity (including longbench_v2's ~35k-token source
    document, which lives ONLY inside `rendered_prompt.txt`, not in
    `source.json`/`metadata.json`) without reconstructing each dataset's
    wrapper wording by hand. Ran for all 6 datasets, 12 cases each, into
    `prompts/<dataset>_qwen3/`.
  - **`scripts/answer_extraction.py`** (new): shared `final_segment(text)`
    used by all 5 `grade_*.py` scripts (gsm8k/aime/humaneval/longbench/
    livecodebench) -- Harmony marker first, else split on `</think>`, else
    (non-thinking response) the whole text is already the answer segment.
    One function instead of patching each grader's own copy of the same
    `if FINAL_MARKER not in text` check independently; `grade_humaneval.py`
    also now trims either `<|end|>` or `<|im_end|>` if one leaks into the
    segment. mtbench still has no grader either way (unaffected).
  - **Model plumbing**: `run_server_vllm.sh`'s `--served-model-name
    gpt-oss-20b` was a hardcoded literal -- parametrized via a new
    `SERVED_MODEL_NAME` env var. `fresh_server_replay.py` gained
    `--model-path`/`--draft-model-path`/`--served-model-name` (defaults =
    GPT-OSS-20B's own values, so a plain invocation is unchanged), wired
    into both the server's env and `run_experiment_vllm.py`'s
    `--model`/`--draft-model` (the client's `request_payload["model"]` must
    match the server's `--served-model-name` or vLLM 400s).
  - **`campaign_run.py`**: `TOKEN_BUDGETS` extended with `<dataset>_qwen3`
    entries (same budgets as the GPT-OSS datasets), `model_family_for()`
    picks the GPT-OSS or Qwen3 (`Qwen/Qwen3-8B` + `Tengyunw/qwen3_8b_eagle3`
    + served name `qwen3-8b`) triple by dataset-name suffix and threads it
    through both `run_fresh_server_replay()` and `run_strict_reference()`.
    `campaign_report.py`'s `grade_accuracy()` strips the `_qwen3` suffix
    when looking up `GRADERS` (same grading rules apply to either model
    family now that `answer_extraction.py` handles both formats) while
    keeping `prompts/<dataset>_qwen3`/`runs/<dataset>_qwen3` as real,
    separate directories from the GPT-OSS ones.
  - **`scripts/campaign_all_qwen3.sh`** (new): `campaign_all.sh`'s shape
    over the 6 `_qwen3` dataset names, with a free-space check (`df`) before
    EVERY dataset, not just once at the top -- disk sat at 10G free when
    this was written and Qwen3-8B's hybrid-thinking traces are unknown
    territory length-wise (unlike the GPT-OSS run, which started with more
    headroom). Stops (does not skip) the moment free space drops under
    `MIN_FREE_GB` (default 3G), leaving whatever datasets already finished
    intact.
  - All changes verified with `py_compile` + `--dry-run` (both
    `fresh_server_replay.py` and `campaign_run.py` against
    `gsm8k_qwen3`) before touching the GPU. Launch itself waits for the
    strict backfill above to finish (one GPU, inherently serial).
  - **Backfill finished** (`2026-08-17T04:19:01Z`); GPU free. Ran a real
    sanity check before committing to an unattended multi-hour run
    (`--arms strict --cases case_001`, small 512-token budget, foreground):
    caught a genuine hard blocker on the first try -- Qwen3-8B's native
    `max_position_embeddings` is 40960 (its own `config.json`:
    `rope_scaling: null`), but `MAX_MODEL_LEN` defaulted to 65536
    (GPT-OSS-20B's own value); vLLM correctly refused to start rather than
    silently truncating. Checked the actual damage: `longbench_v2_qwen3`'s
    own `case_002` is 47003 input tokens ALONE, already past 40960 with
    zero completion budget -- not a corner case, a real ceiling 3 of 12
    longbench_v2 cases would have hit.
    - **Fix**: YaRN RoPE scaling (Qwen's own documented context-extension
      mechanism -- explicitly NOT `VLLM_ALLOW_LONG_MAX_MODEL_LEN`, which
      vLLM's own error message warns can produce NaN/OOB instead of an
      error). Added `ROPE_SCALING_JSON` env var to `run_server_vllm.sh`
      (empty by default, becomes vLLM's `--hf-overrides
      '{"rope_scaling":...}'` when set), `--rope-scaling-json` on
      `fresh_server_replay.py`, and a 4th tuple element on
      `campaign_run.py`'s `MODEL_FAMILIES`: factor 1.6,
      `original_max_position_embeddings: 40960` -> effective window 65536,
      matching GPT-OSS-20B's own `MAX_MODEL_LEN` exactly. Applied
      uniformly to all 6 `_qwen3` datasets (not just longbench_v2) for the
      same reason GPT-OSS's own `MAX_MODEL_LEN` is one fixed value across
      its 6 datasets, not tuned per-dataset.
    - Re-ran the same sanity check with the fix: server started clean,
      request succeeded, output was **coherent, correct reasoning inside
      `<think>...</think>`, right answer ($18 for the Janet's-ducks
      problem)** -- just didn't finish inside the deliberately tiny
      512-token test budget (real gsm8k budget is 2048, plenty per the
      partial trace's own pace). Confirms the whole pipeline end-to-end:
      Qwen3 chat-template prompts, EAGLE3 draft, YaRN-extended context,
      `answer_extraction.py`'s `</think>` handling, all working together.
  - **Launched**: `nohup bash scripts/campaign_all_qwen3.sh` (pid 1956838,
    `2026-08-17T04:24:59Z`), same background+journal monitoring discipline
    as the GPT-OSS run. First dataset (`gsm8k_qwen3`) confirmed underway
    (strict reference, case 1/12) with no errors in an early check.
    6-dataset order: gsm8k, aime24, humaneval, livecodebench, mtbench,
    longbench_v2 (all `_qwen3`). Disk at 9.8G free going in -- the script's
    own per-dataset free-space floor (3G, see above) is the safety net if
    Qwen3's `runs/` tree turns out bigger than GPT-OSS's 3.2G total.
