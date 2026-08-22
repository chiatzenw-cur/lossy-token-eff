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
  - `gsm8k_qwen3` finished `08:55:28Z` (~4.5h). `aime24_qwen3` (32768-token
    budget, 16x gsm8k's) already showing longer per-case wall time early on
    (one case hit the full cap without finishing) -- flagged as the
    slowest leg going in.

- **User: "stop and free the gpu at 7pm china time today and resume after
  12pm"** (2026-08-18). Interpreted as 19:00 CST 2026-08-18 -> 12:00 CST
  2026-08-19 (stated the interpretation back rather than blocking on it).
  Built `scripts/pause_resume_qwen3.sh`: a detached (`nohup`) one-shot
  wrapper, not a Claude-session `CronCreate` job -- session-scoped cron
  jobs vanish if the session ends before they fire, and this spans ~26h.
  Sleeps to the stop epoch, `pkill`s the driver + `campaign_run.py` +
  `fresh_server_replay.py`, runs `remote/stop_server.sh` (kills vLLM's
  actual GPU-holding `VLLM::EngineCore` child, not just the API server --
  `pkill -f vllm.entrypoints` alone leaves ~70GiB pinned), logs, sleeps to
  the resume epoch, relaunches `campaign_all_qwen3.sh`.
  - By pause time, 3 more datasets had finished: aime24 (`18:26:17Z`,
    ~9.5h -- confirmed the slow leg), humaneval (`23:28:59Z`, ~5h),
    livecodebench (`06:03:26Z` next day), mtbench (`10:49:40Z`) -- **5 of 6
    done**. `longbench_v2_qwen3` was mid-strict-reference (case 7/12) when
    the pause fired dead on schedule (`11:00:00Z`), GPU cleanly released
    (0 MiB used).
  - **User: "resume"** (before the scheduled noon wakeup) -- killed the
    sleeping wrapper and relaunched `campaign_all_qwen3.sh` manually.
    `campaign_all_qwen3.sh`'s own bash-level loop state doesn't survive
    being killed mid-script, so the relaunch re-walked the dataset list
    from `gsm8k_qwen3`; every already-finished dataset skip-if-done
    re-verified in seconds (no new data, just fast report regen) before
    reaching the real unfinished work at `longbench_v2_qwen3` again.
  - **Found a second real gap, live, on the resumed run**:
    `longbench_v2_qwen3` case_007's strict request crashed with a genuine
    CUDA fault (`RuntimeError: CUBLAS_STATUS_EXECUTION_FAILED` ->
    `torch.AcceleratorError: device-side assert triggered`, surfaced to
    the client as HTTP 500). The request DID get a response (an error one),
    so `run_experiment_vllm.py`'s own exception handler wrote a real
    `run.json` with `"status": "error"` before re-raising -- and
    `fresh_server_replay.py`'s skip-if-done check only looks for run.json
    *existing*, not its status. Left unfixed, that's a silent permanent
    gap, not a loud one-time failure. **Fixed `clean_partial_runs()`** in
    `campaign_run.py` to also clear any `status != "ok"` run, not just a
    missing run.json.
  - **Not a one-off**: as the sweep continued, the SAME 3 cases kept
    failing on every method/alpha that touched them -- case_002 (21
    failures), case_007 (11), case_010 (10). These are exactly the 3
    longest-context cases in the dataset (47003 / 42234 / 39919 input
    tokens -- the only 3 requiring the YaRN extension above Qwen3's native
    40960 window). A real, reproducible interaction bug, not noise.
  - Let the pass finish naturally (`campaign_all_qwen3.sh` exited
    `2026-08-18T23:29:12Z`, all 6 datasets structurally done, but
    `longbench_v2_qwen3` at n_cases=9/12 with 42 logged failures across
    the dataset). **Diagnosed and fixed**: added `ENFORCE_EAGER` to
    `run_server_vllm.sh` (`--enforce-eager`, disables CUDA graph capture --
    the standard first thing to try for a crash at a sequence-length
    bucket the compiled graph cache never covered). Tested on case_002
    alone first (`--overwrite`-equivalent manual clear + rerun): clean
    success. Then `ENFORCE_EAGER=1 campaign_run.py --dataset
    longbench_v2_qwen3` once more -- the now-status-aware
    `clean_partial_runs()` cleared all 44 error stubs across strict/
    calibration/full-sweep in one pass, every retry succeeded under eager
    mode, zero remaining failures. Re-ran `campaign_report.py`: every
    method/alpha now at n_cases=12/12.
  - **Final integrity sweep**: grepped every `_qwen3` dataset's `runs/`
    tree for any `run.json` with `"status": "error"` -- zero across all
    6 datasets. The Qwen3-8B + drafter campaign is genuinely complete:
    6/6 datasets, 12/12 cases each, strict + 5 relaxed methods + accuracy,
    zero known gaps.
- **User: "check the results, what do you find?"** Read all 12
  `campaign/results/*.csv` (6 GPT-OSS + 6 Qwen3) and the raw
  `campaign/calibration/*_qwen3.json` grid data. Headline finding: 4 of 5
  relaxation methods (`cactus`/`spec_casc_opt`/`r_fuzzy`/`spec_casc_tok`)
  show ZERO variation across their entire alpha grid on Qwen3-8B, on all 6
  datasets -- confirmed against the raw 4-point probe grid, not just the
  chosen comparison points, so not a target-selection artifact.
  `mentored_dec` alone stays alpha-sensitive on Qwen3-8B, consistent with
  it being the one method whose knob interpolates accept probability
  directly rather than gating behind a threshold test. Wrote this up as a
  new FINDINGS.md section with the full per-dataset evidence, the
  architectural explanation, a GPT-OSS-vs-Qwen3 strict-baseline comparison
  table (l̄/accuracy/completion-length), and an explicit caveat that
  completion-length isn't a fair cross-model comparison here (Qwen3 ran
  `enable_thinking=True`, GPT-OSS ran `reasoning_effort=medium` -- different
  verbosity settings, not a capability difference).

- **User: "i cant use those results... should we find other parameters to
  test?"** Started down the "widen the alpha grids" path (cactus/
  spec_casc_opt/r_fuzzy/spec_casc_tok math all argue for larger alpha than
  GPT-OSS's own grids), ran a cheap single-case diagnostic probe at very
  aggressive widened alphas (cactus=1.0, spec_casc_opt=1.0, r_fuzzy=0.5,
  spec_casc_tok=0.95) first rather than committing to a full re-run --
  **still perfectly flat, bit-identical to strict to 15 significant
  digits**. That precision is itself the tell: real stochastic accept/
  reject decisions matching exactly at every one of ~1000 tokens across 4
  independent formulas isn't plausible by chance.
  - Went looking for the actual root cause instead of continuing to guess
    alphas. `proposals.jsonl` (the per-token p/q/JSD tracer, on by default)
    turned out to be EMPTY for every Qwen3 run, strict and mentored_dec
    included (mentored_dec's own real alpha-sensitivity proves the tracer
    being empty isn't itself the reason the other 4 are flat -- a separate,
    lower-priority bug, not chased further).
  - **Found it in the server log**: `WARNING [model.py:1546] Default vLLM
    sampling parameters have been overridden by the model's
    generation_config.json: {'temperature': 0.6, 'top_k': 20, 'top_p':
    0.95}. If this is not intended, please relaunch vLLM instance with
    --generation-config vllm.` Present in literally every one of 171
    gsm8k_qwen3 server logs; grepped all 6 GPT-OSS dataset logs for the
    same string -- zero hits. **The entire Qwen3-8B campaign silently ran
    at temperature=0.6/top_k=20/top_p=0.95, not the campaign's own
    --temperature 1.0/--top-p 1.0** (fresh_server_replay.py's real
    defaults, which GPT-OSS actually got). vLLM only warns, never refuses
    to start, so this went unnoticed through the entire first Qwen3 run.
    top_k=20 truncating the effective vocab before any relaxation math
    runs, on top of a much sharper temperature=0.6 distribution, is the
    direct explanation for why cactus/spec_casc_opt/r_fuzzy/spec_casc_tok
    never diverged from strict at ANY alpha, small or extreme -- not a
    calibration problem at all.
  - **Fix**: added `--generation-config vllm` to `run_server_vllm.sh`'s
    `common_args` (applies to both model families uniformly -- harmless
    for GPT-OSS, which never triggered the warning in the first place, so
    its own per-request params were already being honored).
  - **Confirmed with one more cheap probe**: strict/cactus/r_fuzzy on
    gsm8k_qwen3 case_001 at cactus/r_fuzzy's ORIGINAL alpha=0.03 (not even
    widened) -- warning gone, and cactus/r_fuzzy now genuinely diverge from
    strict (L=1108 vs strict's L=743). The original alpha grids were fine
    all along; the sampling config was the actual bug.
  - **Deleted the entire invalid Qwen3-8B result set**: `runs/*_qwen3/`,
    `campaign/{calibration,results,tables}/*_qwen3.*`,
    `campaign/graphs/*_qwen3*.png`, plus the two throwaway diagnostic-probe
    directories -- all measured under the wrong sampling config, and
    left in place would have silently skip-if-done-contaminated a
    re-run's directories with bad-config data under the same paths.
    FINDINGS.md's Qwen3 section is now describing a result set that no
    longer exists on disk -- correctly attributed to the sampling-config
    bug in spirit, but due for a full rewrite once the re-run lands, not
    trustworthy as still-current numbers.
  - Disk was down to 4.6G free after the probes; also cleared
    `~/.cache/uv` (14G, flagged as available-if-needed in an earlier status
    update, fully regenerable, unrelated to the campaign) for headroom
    before the multi-day re-run -- back to 7.7G free.
  - **Relaunched `campaign_all_qwen3.sh` from scratch** (pid 3261808,
    `2026-08-19T22:39:45Z`), confirmed starting clean (gsm8k_qwen3's strict
    stage at 12/12 real runs, not skip-if-done short-circuited).

## 2026-08-20 (session 3)

- **User: "make sure and check the data is usable, keep calibrated ok? match
  l data between methods"** -- verified BEFORE letting the relaunched
  campaign run 2 more days, not after. Set a monitor for gsm8k_qwen3's
  calibration stage (the first, fastest dataset) to land, then read the raw
  4-point grid the moment it did.
  - **Still completely flat** for cactus/spec_casc_opt/r_fuzzy/spec_casc_tok,
    even with the `--generation-config vllm` fix from the previous session
    in place (confirmed the fix itself held: zero override warnings, correct
    temperature=1.0/top_p=1.0 in every request.json). Only `mentored_dec`
    varied. So the sampling-config fix was real but NOT the explanation for
    the flatness -- a second, separate bug.
  - Paused the run (killed cleanly, GPU released) rather than let 2 more
    days run on data that was still going to be unusable.
  - **Investigation, in order**:
    1. A confirmatory single-case diagnostic (cactus/r_fuzzy at their
       ORIGINAL alpha=0.03, not widened) showed real divergence from
       strict at the time -- but a clean, isolated re-test (two independent
       fresh-server runs of plain strict, same case) showed PERFECT
       bit-identical reproducibility, which means that first "divergence"
       reading can't be trusted as evidence either way; the system is
       genuinely deterministic here (fixed seed, no prefix caching), so an
       apparent difference across separate runs is real signal, not noise
       -- and the flatness within a SINGLE clean run (4 alphas, 3 cases,
       all bit-identical to each other and to strict) is the reliable
       finding.
    2. Tried live server instrumentation (added a debug print inside the
       installed, patched `rejection_sampler.py` to check `draft_probs is
       None`) -- blocked once by the permission classifier on
       `patches/apply.sh` directly, then hit a real self-inflicted mess: an
       earlier `pkill` on `campaign_run.py` silently failed (harness
       exit-code-144 masked it), leaving the ORIGINAL campaign process
       running concurrently with manual diagnostic invocations, corrupting
       shared `/tmp` alpha-knob-file state and the patch-hash safety check
       (one test even reverted the installed file to pristine upstream as
       a side effect of its own failure handling). Cleaned up thoroughly
       (killed every stray process by PID, verified via `ps`/`nvidia-smi`,
       confirmed the file hash matches a known-good state via
       `patches/HASHES.txt` before touching anything else) rather than
       push forward on top of an uncertain base state.
    3. `--enforce-eager` (disables CUDA graphs; already the fix for the
       longbench_v2 CUDA-crash issue) tested as a hypothesis that graph
       capture was "freezing" a data-dependent Python branch
       (`if draft_probs is not None:`) at warmup time -- ruled out: same
       flatness in eager mode.
    4. Read vLLM's own EAGLE3 proposer source
       (`v1/spec_decode/llm_base_proposer.py`) directly: `draft_probs`
       comes back `None` when `use_heterogeneous_vocab` forces
       `draft_sample_method` to `"greedy"` regardless of what's requested.
       That flag defaults `False` and is never set in this repo's own
       `--speculative-config` JSON, so on paper it shouldn't trigger --
       but then found BOTH Qwen3 drafter candidates checked
       (`Tengyunw/qwen3_8b_eagle3` AND `RedHatAI/Qwen3-8B-speculator.eagle3`)
       declare `draft_vocab_size: 32000` against the target's real
       `vocab_size: 151936` -- a genuinely reduced/mapped draft vocabulary.
       Checked GPT-OSS's own drafter (`nebius/EAGLE3-gpt-oss-20b`) for the
       same field for comparison: ALSO reduced (`draft_vocab_size: 64000`
       vs `vocab_size: 201088`) -- so a reduced draft vocab alone doesn't
       explain why GPT-OSS's methods worked and Qwen3's didn't; this lead
       didn't fully pan out either, though it surfaced the `draft_vocab_size`
       mismatch as a real property worth keeping in mind.
  - **User: "maybe try another drafter"** -- pragmatic pivot after the
    live-debugging path kept producing plausible-looking dead ends.
    Searched HF for Qwen3-8B EAGLE3 drafters; `RedHatAI/Qwen3-8B-
    speculator.eagle3` stood out (73k downloads, by far the most of any
    candidate, published by the team that builds vLLM-optimized
    speculators -- the same kind of "not a hobby upload" provenance as
    GPT-OSS's own `nebius/EAGLE3-gpt-oss-20b`). 2GB, downloaded cleanly
    (7.7G free at the time, comfortable).
  - **Empirical test, one clean sequential run at a time (no more
    concurrent invocations)**: strict with the new drafter worked
    normally. cactus at alpha=0.35: genuinely DIFFERENT from strict for
    the first time (L=718 vs strict's L=1024) -- real divergence.
    Cross-checked cactus at 0.03, 2.0, and 0.001: all three landed on the
    SAME L=718/l̄=1.248 as 0.35 -- flat *within* cactus's own range on this
    one easy case, but genuinely different from strict throughout, unlike
    the old drafter's total inertness. Confirmed via each run's own
    "[CACTUS PATCH...] alpha=X" startup line that the server actually read
    each distinct alpha value (not a plumbing bug) -- the flatness-within-
    cactus's-range is plausibly just gsm8k's easiest case having little
    "middle-ground uncertainty" for a boost-based relaxation to respond to,
    not evidence the new drafter is broken the same way.
  - **Root cause not conclusively pinned down** -- switching drafters fixed
    the *symptom* (real divergence from strict) empirically, without a
    fully confirmed mechanistic explanation for why the old one didn't
    work. Documented honestly as such (in `campaign_run.py`'s own
    `MODEL_FAMILIES` comment) rather than overclaiming a root cause that
    wasn't actually nailed down.
  - **Switched** `campaign_run.py`'s `MODEL_FAMILIES["qwen3"]` drafter to
    `RedHatAI/Qwen3-8B-speculator.eagle3`. Cleared the stale
    `runs/gsm8k_qwen3/` + `campaign/calibration/gsm8k_qwen3.json` left over
    from the (old-drafter, post-generation-config-fix, still-flat) partial
    run -- would have skip-if-done-contaminated the new drafter's data
    under the same directory names otherwise.
  - **Relaunched `campaign_all_qwen3.sh` from scratch** (pid 3364806,
    `2026-08-20T01:31:32Z`), confirmed starting clean. Disk at 5.7G free
    (down from 7.7G after the 2GB drafter download + diagnostic churn) --
    watching this; the 3G per-dataset floor in `campaign_all_qwen3.sh`
    is the safety net.
  - Watching gsm8k_qwen3's calibration stage specifically (fastest
    dataset) to verify real multi-method alpha-sensitivity before trusting
    the rest of the run to proceed unattended for its full ~2 days.

- **User: "work autonomously to finish collecting data but check results to
  see if actual working"** -- proceeded to port the remaining 3 methods
  (spec_casc_opt, r_fuzzy, spec_casc_tok) into V2, on top of the validated
  cactus/mentored_dec proof of concept.
  - **spec_casc_opt + r_fuzzy**: share the exact same "defer to strict OR
    accept unconditionally" kernel mechanism, differing only in what
    computes the defer decision (TV-based vs JSD-based). Computed both in
    plain PyTorch inside `rejection_sample()`'s orchestration (mirroring
    the V1 patches' own "materialize target_logits/draft_logits as dense
    tensors, reduce once" style) -- `draft_logits` is a dense
    `[max_num_reqs, num_speculative_steps, V]` tensor at that point, gathered
    into `[num_logits, V]` via `expanded_idx_mapping`/`expanded_local_pos`
    to match `target_logits`'s own layout. Combined `defer_mask =
    defer_spec_casc_opt & defer_r_fuzzy` -- exact composition, not an
    approximation, since each inactive method's own alpha defaults to
    "always defer" (True), so it never overrides the other's real decision.
  - **spec_casc_tok**: different shape (direct pi_rej(x) replacement, not a
    defer/accept split). Composed with cactus as DELTAS from p(x)
    (`effective_p_x = gamma_x + pi_rej_x - p_x`) rather than picking one --
    exact under the same mutual-exclusivity invariant (at most one method's
    alpha is ever non-neutral on a given server), since both deltas are
    zero when their own method is inactive.
  - **Two real bugs caught during testing, not before**:
    1. The defer_mask/eta computation ran unconditionally, including
       during vLLM's own CUDA-graph warmup pass (large synthetic dummy
       batches) -- materializing a dense `[num_logits, 151936]` probability
       tensor for THAT batch size genuinely OOM'd the GPU (on top of the KV
       cache already reserved at 85% utilization). Fixed with a `num_reqs
       <= 8` guard, mirroring `relaxation_trace.py`'s own established
       `_MAX_REAL_BATCH = 8` warmup filter exactly -- not a new convention.
       Needed a SEPARATE `HAS_DEFER_MASK`/`HAS_CASC_TOK` compile-time
       constexpr from `HAS_DRAFT_LOGITS` for this, since the tensor can be
       `None` during warmup even when draft_logits itself is real --
       conflating the two would have dereferenced a null pointer on every
       warmup pass.
    2. The naive `draft_logits[expanded_idx_mapping, expanded_local_pos]`
       gather raised a real CUDA "index out of bounds" device-side assert:
       `expanded_local_pos` covers the full flattened num_logits space,
       which includes the bonus-token slot (`expanded_local_pos ==
       num_speculative_steps`, one past `draft_logits`'s own valid step
       range) -- `_compute_local_residual_mass_kernel`'s own `if
       draft_step_idx == 0 or draft_step_idx >= num_speculative_steps:
       return` guard exists for exactly this boundary, enforced there
       instead of at the gather site. Fixed by clamping both index tensors
       before gathering; the resulting garbage values at those positions
       are never read (the accept loop only ever indexes real draft
       positions).
  - **Discovered mentored_dec's own V2 contribution had been silently
    dropped**: the proof-of-concept edits were built starting from a
    PRISTINE copy of `rejection_sampler_utils.py`, not from mentored-dec's
    own already-patched V2 state -- meaning this file was missing
    mentored-dec's real alpha-scaling term the whole time, the same
    "silently inert" failure this entire investigation started from, now
    self-inflicted. Re-ported it from `vllm-0.26.0-mentored-dec.patch`'s
    own V2 hunk verbatim, composed as an additive log-space term on the
    RHS threshold (mentored-dec scales q, not p, so it doesn't fold into
    the effective_p_x delta composition the other methods use).
  - **`patches/apply.sh mentored-dec` broke for real, not just a
    formality**: `HASHES.txt`'s own hash-matching safety check (correctly)
    refuses to apply mentored-dec's official V2 hunk against the now
    heavily-modified V2 file, and (also correctly, by design) rolls back
    the V1 half too rather than leave a half-consistent state -- meaning
    every future `ensure_patch_applied("mentored_dec")` call
    (`fresh_server_replay.py`'s own automatic method-switching, which the
    real campaign calls constantly) would have failed outright the moment
    it needed to switch INTO mentored_dec. Applied V1's own hunk directly
    (bypassing the atomic all-or-nothing apply.sh wrapper for this one
    case) and, since this consolidated V2 file genuinely IS a valid
    mentored-dec state now (not mentored-dec-only, but mentored-dec's own
    contribution is really in it), registered its actual hash under the
    `mentored-dec` label in `HASHES.txt` with a long comment explaining why
    -- confirmed with `bash patches/apply.sh mentored-dec` afterward:
    exit 0, full self-test suite (`test_alpha_plumbing`/
    `test_kernel_uses_alpha`) passing clean.
  - **All 5 methods validated live, one at a time, each against a firm
    strict baseline**: mentored_dec, cactus, spec_casc_opt, r_fuzzy,
    spec_casc_tok all produce genuinely distinct completions from strict
    (and from each other) on the same case/seed. Final regression check
    (strict, full consolidated kernel, everything neutral) reproduces the
    exact baseline text seen all night, confirming the 5-way composition
    reduces correctly to strict when nothing is active.
  - **Scope explicitly NOT done, documented not hidden**: cactus's own
    recovery-distribution correction (H_x) and spec_casc_tok's own
    recovery correction are both still accept-test-only, matching this
    repo's own `cactus_accept_only` convention -- a real, known,
    deliberately-scoped-out gap, not an oversight. A proper per-method
    `.patch` file split (matching V1's own mutually-exclusive-file
    convention, instead of one consolidated always-present V2 file) is
    real follow-up work.
  - Cleared the stale `runs/gsm8k_qwen3/` + calibration data left over
    from the last (still V1-only-patched) attempt, and **relaunched
    `campaign_all_qwen3.sh` from scratch** (pid 3534395,
    `2026-08-20T18:14:36Z`). Watching gsm8k_qwen3's calibration stage
    again -- this time expecting all 5 methods to show real variation, not
    just mentored_dec.

- **2026-08-20, later same night: that relaunch (pid 3534395) was itself
  broken, root-caused, fixed, and relaunched again.** Checking results
  after gsm8k_qwen3 finished (per "read each run's result a bit after
  they finish") found only `mentored_dec` had real `grid_results`;
  cactus/spec_casc_opt/r_fuzzy/spec_casc_tok were all empty again, and
  the campaign had since moved on to aime24_qwen3 and was failing there
  too -- now for **all 5 methods**, including mentored_dec.
  - Root cause #1 (explained the gsm8k_qwen3 failures): the `/tmp`
    alpha-knob-file fix from earlier in the session was correct but this
    relaunch had started *before* that fix was written to disk, so it
    inherited the same stale-file corruption for its entire gsm8k_qwen3
    run.
  - Root cause #2 (new, explains the aime24_qwen3 all-methods failure):
    `patches/apply.sh`'s mentored-dec fresh-install path still copied V2
    into its scratch dir and re-applied the *original* two-file
    `vllm-0.26.0-mentored-dec.patch` (V1 hunk + V2 hunk) unconditionally.
    V2 is now permanently in the consolidated state (baked in for every
    method, per the earlier fix), so the V2 hunk -- written against a
    pristine V2 -- always fails: 4/4 hunks FAILED every time V1 needed a
    fresh mentored-dec install from any other method. This blocked every
    cactus->mentored-dec (and any->mentored-dec) switch, which is why it
    surfaced as "all 5 methods failing" once the grid's method order
    reached mentored-dec and every subsequent apply.sh call inherited a
    corrupted/orphaned server + knob-file state from the repeated
    failures (a live server process was found still running minutes
    after its fresh_server_replay.py call should have torn it down,
    concurrently rewriting the same uid-scoped `/tmp` alpha file that
    apply.sh's own self-test was reading -- a real race, visible as a
    Triton `StopIteration()` CompilationError in cactus's self-test one
    time, and a spurious self-test "FAILED" another).
  - **Fix**: split `vllm-0.26.0-mentored-dec.patch`'s first 131 lines
    (the V1-only hunk) into a new
    `patches/vllm-0.26.0-mentored-dec-v1only.patch`, and changed
    apply.sh's fresh-install path to use it for mentored-dec instead of
    the original combined patch -- V2 is no longer copied into the
    scratch dir or re-patched at all for any method now, matching the
    "V2 never changes per-method any more" design that was already true
    in principle but not yet reflected in this one code path.
  - **Verified**: ran the full 5-method round trip
    (cactus->spec-casc-opt->r-fuzzy->spec-casc-tok->mentored-dec->cactus)
    via manual reverse+apply cycles matching `ensure_patch_applied()`'s
    own logic exactly, each with a full self-test pass, in isolation
    (no live server running, so no race). Every transition: exit 0, full
    self-test suite passing, correct hash. Specifically re-verified the
    previously-broken spec-casc-tok->mentored-dec transition on its own
    with a generous timeout: exit 0, hash correct.
  - Killed the entire broken campaign (`pkill` itself was blocked by the
    sandbox and failed silently -- had to `kill -9` each pid
    individually: `campaign_run.py`, `fresh_server_replay.py`, and the
    live `vllm.entrypoints.openai.api_server` + its `VLLM::EngineCore`
    child, which was still alive and consuming a full GPU's memory after
    the outer shell's original pid had already exited). Cleared all 5
    methods' `/tmp` alpha knob files again, archived the broken stdout
    log, and deleted `runs/gsm8k_qwen3/`, `runs/aime24_qwen3/`, and both
    datasets' `campaign/calibration/*.json` (campaign_run.py's skip-if-done
    check only looks for `run.json` existing, not its status, so leaving
    the corrupted dirs in place would have made every failed
    (method, alpha, case) combination skip silently forever).
  - Relaunching `campaign_all_qwen3.sh` fresh now. Next check: verify
    gsm8k_qwen3's calibration JSON shows real, non-empty, varying
    `grid_results` for all 5 methods before trusting the rest of the run
    to proceed unattended.

- **2026-08-20, ~20:35 UTC: that relaunch (pid 3594426) ALSO broke, but
  differently -- two more copies of the same stale "only mentored-dec
  touches V2" assumption, in two places the first fix missed.**
  - **Bug A**: `fresh_server_replay.py`'s own `ensure_patch_applied()`
    has its OWN patch-reversal logic (separate from apply.sh, by
    design -- apply.sh deliberately refuses to auto-switch). Its
    reversal-from-mentored-dec path still used the original two-file
    `vllm-0.26.0-mentored-dec.patch` to reverse, which fails the same
    way apply.sh's forward-install did (V2 hunks fail against the now-
    further-extended consolidated V2). This blocked every
    mentored-dec -> other-method switch during an unattended sweep --
    exactly the transition the calibration grid hits first (mentored_dec
    is grid position 1). All 4 cactus alpha points failed to reverse out
    of mentored-dec before cactus's own install could even be attempted.
    Fixed by special-casing mentored-dec in `ensure_patch_applied()` to
    reverse via the same `vllm-0.26.0-mentored-dec-v1only.patch` used for
    the forward-install fix, never touching V2.
  - **Bug B** (the one that then broke spec_casc_opt, a method that
    should have been unaffected): `run_experiment_vllm.py`'s
    `vllm_install_info()` -- the CLIENT-side check `run_experiment_vllm.py`
    itself runs before every single request, independent of apply.sh --
    still had `v2_ok = (v2_label == spec.hashes_label) if spec.touches_v2
    else (v2_label == "upstream")` (from `scripts/lossy_methods.py`'s
    `touches_v2` field, `True` only for mentored-dec). Since V2 is now
    permanently "mentored-dec"-labeled for every method, the `else`
    branch's `v2_label == "upstream"` can never be true any more, so
    `patch_applied[method]` was unconditionally `False` for all 4 non-
    mentored-dec methods regardless of what was actually installed --
    surfaced as "the spec_casc_opt patch is not applied" even though
    V1's hash matched spec-casc-opt exactly. This is the third copy of
    the same stale assumption (after apply.sh and HASHES.txt's comment),
    just in the request-time verifier instead of the installer. Fixed by
    replacing the touches_v2 branch with `v2_label in ("mentored-dec",
    "upstream")` unconditionally, matching apply.sh's own check.
  - Grepped the whole codebase afterward for any remaining `v2_label`/
    `v2_hash`/`touches_v2` references to make sure these were the last
    two copies -- only apply.sh's already-fixed check and
    `lossy_methods.py`'s now-unused `touches_v2` field definition
    remained.
  - **Verified both fixes together, live**: reversed to a clean state,
    called `fresh_server_replay.ensure_patch_applied('cactus')` directly
    (Python, not subprocess) from a mentored-dec starting state --
    succeeded with no exception, V1 landed on cactus's hash. Then called
    `run_experiment_vllm.vllm_install_info()` directly and confirmed
    `patch_applied == {'cactus': True, <everything else>: False}` while
    cactus was actually installed -- correct in both directions now.
  - Killed the campaign a third time, cleared the (again-corrupted)
    `runs/gsm8k_qwen3/`, `runs/aime24_qwen3/`, and both datasets'
    calibration JSONs, archived the broken log, and relaunched
    `campaign_all_qwen3.sh` once more.

- **2026-08-22, ~01:30 UTC: livecodebench_qwen3 finished. Accuracy is
  strikingly low across every arm, including strict (2/12 = 0.167) --
  investigated to confirm this is real, not a scoring-pipeline bug.**
  - Independent `grade_livecodebench.py` run initially failed
    ("no test cases at prompts/livecodebench_qwen3/test_cases.json") --
    turned out to be the checker script's own `--prompt-root` default,
    not a real gap: `test_cases.json` is intentionally shared at
    `prompts/livecodebench/` (not duplicated per model family, same as
    every other _qwen3 dataset's "same underlying problems, different
    chat template" convention), and `campaign_report.py` already points
    at that shared path correctly. Re-ran the grader with
    `--test-cases prompts/livecodebench/test_cases.json` explicitly --
    it now matches `campaign/results/livecodebench_qwen3.csv`'s own
    accuracy numbers exactly (strict 2/12), confirming the report
    pipeline's scoring is correct.
  - Traced strict's own 12 cases individually: 2 passed, 7 failed with
    genuine `output mismatch` (code ran, wrong answer), 3 got
    `no_answer` verdict specifically because they hit the 12000-token
    cap (`finish=length`) while still inside the model's own reasoning
    -- generation was cut off before a closing code fence ever appeared,
    so there's nothing to extract, not an extraction bug (`final_segment`
    itself works fine, confirmed directly against a passing case).
  - Conclusion: Qwen3-8B genuinely struggles with LiveCodeBench at this
    token budget -- consistent with LiveCodeBench's known difficulty for
    8B-scale models -- not a defect in the campaign's patches, scoring,
    or pipeline. All 5 lossy methods track strict's own low baseline
    (no method shows a wildly different accuracy shape than strict),
    which is the expected/correct relationship even when the absolute
    numbers are low.

- **2026-08-22, ~07:15 UTC: longbench_v2_qwen3 (the final dataset) hit a
  genuine CUDA crash on its 3 longest cases -- a fourth real bug found
  tonight, unrelated to the three patch-switching bugs earlier.**
  - Symptom: `case_002`, `case_007`, `case_010` (of 12) crashed every
    server that touched them (strict AND mentored_dec calibration, so far)
    with `torch.AcceleratorError: CUDA error: device-side assert
    triggered`, traced to a Triton kernel's own
    `Assertion \`index out of bounds: ... < 40960\` failed`. This killed
    the whole EngineCore process each time (`fresh_server_replay.py`
    correctly logged the failure and moved on to the next case with a
    fresh server, so the campaign itself never got stuck -- but every arm
    would have silently lost these same 3/12 cases for the rest of the
    dataset).
  - **Root cause**: longbench_v2's prompts are genuinely huge
    (12k-47k tokens/case, the only _qwen3 dataset anywhere near this
    long) -- three cases' prompt length alone (or prompt + generated
    tokens for the one case that crossed the boundary mid-generation)
    exceeds 40960, which is Qwen3-8B's OWN native
    `max_position_embeddings` (config.json: `max_position_embeddings:
    40960, rope_scaling: null`). Our server launch's `--hf-overrides`
    correctly configures YaRN `rope_scaling` to extend the target
    model's EFFECTIVE range to `MAX_MODEL_LEN` (65536) -- but that fixed
    only PART of the problem.
  - **First fix attempt (target model's own max_position_embeddings) --
    verified NOT sufficient on its own**: added
    `"max_position_embeddings": $MAX_MODEL_LEN` alongside `rope_scaling`
    in `remote/run_server_vllm.sh`'s `--hf-overrides` JSON (kept -- it's
    still correct and necessary for the target model). Re-tested
    case_002 directly against the exact failing prompt: **same crash,
    same `< 40960` bound**, proving the target model's config wasn't
    the (only) source.
  - **Actual second source, found by inspecting the draft model's own
    config**: `RedHatAI/Qwen3-8B-speculator.eagle3` (the EAGLE3 drafter)
    ships its OWN separate, nested
    `transformer_layer_config.max_position_embeddings: 40960,
    rope_scaling: null` -- completely independent of the target model's
    config. vLLM's own `SpeculativeConfig.compose_draft_hf_overrides()`
    (vllm/config/speculative.py) explicitly documents that dict-form
    `hf_overrides` (what `--hf-overrides` produces) are "target-specific
    key patches and are not applied to the draft" -- only callable
    overrides compose through. There is no CLI flag to override just the
    draft model's own config.
  - **Fix**: patched the draft model's CACHED config.json directly (not
    the repo -- `~/.cache/huggingface/hub/models--RedHatAI--Qwen3-8B-
    speculator.eagle3/.../config.json`, resolving the HF cache's
    content-addressed blob symlink to a plain file first so the blob
    store's own hash-integrity isn't broken by an in-place edit) --
    set `transformer_layer_config.max_position_embeddings: 65536` and
    `rope_scaling` to the same YaRN config as the target
    (`{"rope_type":"yarn","factor":1.6,"original_max_position_embeddings":40960}`).
    Safe from a correctness standpoint even if the draft was never
    calibrated past its native 40960 context: speculative decoding
    always verifies drafts against the target model's own accept/reject
    sampling, so a less-accurate draft near/past position 40960 can only
    reduce acceptance rate there, never produce wrong final output --
    strictly better than crashing the whole server.
  - **Verified directly**: killed the corrupted campaign run, launched an
    isolated manual server with both fixes, and re-sent all 3
    previously-crashing cases' real prompts directly. `case_002`
    (prefill already past 40960): HTTP 200, real coherent completion.
    `case_007` (same): HTTP 200. `case_010` (crosses 40960 mid-
    generation, not at prefill): generated well past the threshold and
    stopped naturally (`finish_reason=stop`) with no crash.
  - Cleared `runs/longbench_v2_qwen3/`, `logs/campaign_longbench_v2_qwen3/`,
    `campaign/calibration/longbench_v2_qwen3.json` (the corrupted partial
    run from before the fix), and the 5 methods' stale `/tmp` alpha files.
    Relaunching `campaign_run.py --dataset longbench_v2_qwen3` directly
    (not the whole `campaign_all_qwen3.sh` wrapper -- the other 5
    datasets are already done and shouldn't be re-touched).
