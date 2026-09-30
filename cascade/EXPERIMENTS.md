# Experiment registry

Every experiment this workspace wants to run, why, exactly what runs, what
it costs, where the output lands, and how to decide what it means. Each has
an id; `bash cascade/run.sh <id>` runs it (see "Running" at the bottom).
Cross-references: `DIRECTIONS.md` (the reasoning behind the list),
`METHODS.md` (every rule's formula and knobs), `METRICS.md` (every number's
definition), `SETUP.md` (what must be true before anything runs).

## Overview

| id | question | arms | datasets | cases | cost (fresh / persistent) | status |
|---|---|---|---|---|---|---|
| E0 | do the five new patches install and pass their tests on this box? | all cascade variants | -- | 1 dry run | 10 min | **passed on Nibi 2026-09-11** (all 5, kernel tests included) |
| E1 | does removing tok's out-of-head penalty raise l̄ *without* inflation? (mechanism) | `spec_casc_tok_lt`, `spec_casc_tok` | gsm8k -> humaneval -> aime24 | 30 | 5 h / 0.6 h (gsm8k); ~1 day / 2.5 h (aime24, Nibi) | **quick looks done** gsm8k 09-11, aime24 09-12: tok_lt α=0.15 is the clean best point (1.08×, no loops, acc 0.83); α ≥ 0.35 inflates like tok — head must stay narrow (JOURNAL 09-12) |
| E1F | where exactly does inflation begin? fine α ∈ {0.05,0.1,0.15,0.2,0.25} × 3 seeds | `spec_casc_tok_lt`, `spec_casc_tok`, `strict` | aime24 | 30 × 3 seeds | 8 h (persistent, Nibi) | **done 2026-09-13**: tok_lt +11–14% l̄ at every α, no inflation (typical answers ±10% of strict, loops = strict's), acc intact ≤0.2, end-to-end **~1.05–1.08×**; no clean α cliff — see JOURNAL |
| E1P | the AIME24 protocol on every other campaign benchmark: `tok_lt` and `tok` at α ∈ {0.15, 0.2, 0.25} × 3 seeds + strict × 3 seeds | `spec_casc_tok_lt`, `spec_casc_tok`, `strict` | gsm8k (150), humaneval (150), mtbench (80), livecodebench (90), longbench_v2 (30) | campaign case counts × 3 seeds | ≈4 / 7 / 6 / 15 / 15 h (persistent, one GPU, chained) | staged — `bash cascade/run.sh E1P-<ds> --target nibi`; reports to `campaign/*/<ds>_proper.*` |
| E2 | does an entropy trigger fix opt's rambling? | `spec_casc_opt_ent`, `spec_casc_opt` | aime24, humaneval | 30 | 9 h / 5 h (aime24) | ready |
| E3 | what is the *measured* wall-clock speedup, and this stack's drafter cost c_rel? | `baseline`, `strict`, `spec_casc_tok` a=0.8 | gsm8k, aime24 | 10 | 1 h / -- (fresh only) | ready |
| E4 | does tuning draft length under strict beat any relaxation? (Xia Finding 2) | `strict`, `spec_casc_tok` a=0.8 at N in {3,4,6,8,10} | gsm8k, aime24 | 20 | 6 h / 1 h (gsm8k) | ready |
| E5 | how do the source paper's other deferral rules (Diff, Chow) compare at matched l̄? | `spec_casc_diff`, `spec_casc_chow` | gsm8k, aime24 | 30 | 5 h / 0.4 h (gsm8k) | ready |
| E6 | does restricting opt's free pass to the verifier's head remove its inflation while keeping its gain? | `spec_casc_opt_head` beta in {0.15, 0.35} x opt's alpha grid | aime24 | 30 (seed 0) | 2 h (persistent, Nibi) | **done 2026-09-13**: removes the inflation (loops 1–5/30 vs opt's 13) **and** the gain (l̄ 2.45–2.53 = tok_lt's, not opt's 2.71–3.38); end-to-end 0.84–1.07× — no bigger prize; see JOURNAL |
| E7 | do relaxed rules' *out-of-head* commits explain inflation? (trace analysis, no GPU) | existing traces | old_runs humaneval + aime24 | all | 20 s | **done** — see below |
| SAMPLE-<ds> | does the whole pipeline run on this box? one case, `strict` vs `spec_casc_tok_lt` α=0.55, fresh servers | 2 arms | any | 1 | ~17 min on Nibi (cold compile) | **passed on Nibi 2026-09-11** (job 21760344) |
| E8 | recover the Qwen3 (V2 runner) consolidated sampler so Qwen3 experiments are possible | -- | -- | -- | 30 min on the old box | blocked on old-box access |

Cost model (from the campaign's own logs): a fresh server costs ~100 s per
measurement; generation averages ~2 s (gsm8k), ~4 s (humaneval), ~73 s
(aime24). A `campaign_run.py` invocation with 2 methods and 30 cases is
~186 runs (4-point calibration on 3 cases + 3 chosen alphas on the rest).
"persistent" = one warm server per arm (`scripts/persistent_arm_replay.py`),
fixed 4-point alpha grid, no matched-l̄ selection, and the documented
request-ordinal confound (`remote/ENVIRONMENT.md`). Use fresh for anything
that goes in the paper; persistent to find out fast whether an idea is dead.
Persistent-mode reports go to `campaign/{calibration,tables,results}/<ds>_quick.*`
and `campaign/graphs/<ds>_quick*.png` (all grid points graded and plotted),
leaving the campaign's own files untouched; `speed_ignoring_accuracy.py`
then shows them as dataset `<ds>_quick`. On Nibi each server start is ~5 min
(cold compile ~11 min), so a 9-arm quick look is ~1 h, not 25 min.

## E7 (done): out-of-head commits and inflation — `results/trace_rank_analysis.md`

Ran on the 1,226 traced runs in `old_runs/` (HumanEval 164 cases x 6 arms,
AIME24 30 cases x 6 arms plus `spec_casc_tok` at a = 0.5, 0.7, 1.0). A
*lossy-only accept* is a token committed only because the relaxed rule
lowered the bar (strict would have rejected it); *out-of-head (ooh80)* means
its verifier probability was below 0.2 x the verifier's top-1, i.e. outside
`spec_casc_tok`'s trusted set at a = 0.8.

| arm (AIME24) | lossy-only /1k emitted | ooh80 share of those | ooh80 /1k | len vs strict | budget-hit |
|---|---:|---:|---:|---:|---:|
| `spec_casc_tok` a=0.3 / 0.5 / 0.7 | 26 / 33 / 47 | **0.00 / 0.00 / 0.00** | 0 | 0.94 / 1.04 / 1.03 | 7% / 13% / 17% |
| `mentored_dec` a=0.37 | 53 | 0.31 | 16 | 1.23 | 7% |
| `spec_casc_opt` a=0.05 | 124 | 0.52 | 65 | 2.13 | 50% |
| `r_fuzzy` a=0.3 | 204 | 0.69 | 141 | 1.94 | 17% |
| `cactus` a=0.25 | 219 | 0.71 | 155 | 1.86 | 27% |
| `spec_casc_tok` a=1.0 (whole vocab trusted, 1 run) | 249 | 0.69 | 172 | **19.15** | 100% |

HumanEval shows the same ordering (tok 0 ooh80, length 0.96x; opt 56/1k,
1.62x; r_fuzzy 118/1k, 1.87x; cactus 122/1k, 1.57x). Strict itself commits
~50 "out-of-head" tokens per 1k under the lossless rule without inflating —
so the harmful set is specifically *out-of-head tokens strict would have
rejected*, which is exactly what ooh80 counts.

Read-out: the mechanism hypothesis holds **at the rule level** — the one
rule with zero out-of-head lossy-only accepts is the one rule that never
inflates, and letting it accept out-of-head (a = 1) produces the worst
inflation in the dataset. It does **not** hold as a per-token trigger:
within an arm, cases with a higher ooh80 rate are not the cases that loop
(Pearson r = 0.06–0.38 on HumanEval, negative on AIME24, where looping
runs fill up with in-head repeats). Design consequence: restrict *where*
relaxation may commit (E1, E6), don't try to detect bad tokens one at a
time (which is what the guard line already found).

Predictions this makes for the GPU experiments:
- E1: `spec_casc_tok_lt`'s lossy-only accepts are in-head by construction ->
  no inflation; l̄ rises by roughly strict's out-of-head acceptance share.
- E6: at beta = 0.8, `spec_casc_opt_head` keeps the ~48% of opt's lossy-only
  accepts that were in-head and drops the rest -> l̄ about half-way between
  strict and opt, length ratio near 1.0 instead of 2.13.

## E0 — smoke test (run first on any new box)

`bash cascade/run.sh E0`. Runs `cascade/cluster/patch_cycle_test.sh`:
installs each new patch in turn through `patches/apply.sh` (hash-verified,
then its `test_<method>.py`: knob plumbing, formula, and — with a GPU — the
Triton kernel), reversing the previously installed patch before each one
(`apply.sh` refuses to switch on its own), then a `campaign_run.py
--dry-run`. Pass = five "all ... checks passed" lines. First run on Nibi
2026-09-11: `spec-casc-tok-lt` passed all checks including the kernel test.
Fail on the hash step means the vLLM install is not pristine 0.26.0; fail
on the kernel step means stop and read the test's output — the kernel hunk
is shared with `spec_casc_opt`, so a failure there would be an environment
problem, not a variant problem.

## E1 — mechanism test: `spec_casc_tok_lt` vs `spec_casc_tok` (DIRECTIONS D1)

**Why.** E7 says tok is safe *because* it never commits out-of-head tokens
strict would reject, and expensive *because* outside the head it is
stricter than lossless (`eta*p/q`). tok_lt keeps the first property and
drops the second. If it gains l̄ with no inflation, "relax freely inside
the verifier's head, never outside" is the design rule.

**Runs.** `bash cascade/run.sh E1-gsm8k`, then `E1-humaneval`, then
`E1-aime24`. Each: `campaign_run.py --methods spec_casc_tok_lt spec_casc_tok
--full-cases 30` (calibration on 3 probe cases over `[0.15, 0.35, 0.55,
0.8]`, then 3 matched-l̄ alphas on all 30), `campaign_report.py`, and
`speed_ignoring_accuracy.py`. The strict reference for each dataset already
exists on the old box (`runs/<dataset>/strict/`); on a fresh box
`campaign_run.py` runs it first (30 more runs).

**Outputs.** `runs/<dataset>/spec_casc_tok_lt/alpha*/`, tables in
`campaign/tables|results/<dataset>.csv`, graphs in `campaign/graphs/`,
ranked speed table in `cascade/results/speed_ignoring_accuracy.md`.
The dataset's `campaign/calibration/<dataset>.json` is **merged**, not
overwritten: the five paper methods keep their chosen alphas, and tok_lt is
matched to the l̄ targets already on file (so it lands on the same band as
the paper's methods). Pass `--retarget` to `campaign_run.py` only if you
deliberately want a new band computed from this run alone. The regenerated
`results/<dataset>.csv` and graphs then contain the paper's five methods
plus the new one (grey fallback line, labelled).

**Decision.** Compare at matched l̄ (the graphs' x-axis). Support: tok_lt
reaches a higher l̄ than tok's max with `len_ratio` <= 1.05 and
`budget_hit` within 5 points of strict. Refute: tok_lt inflates (len_ratio
> 1.15 at any alpha) — then the eta penalty was load-bearing and E6's
prediction is in doubt. Null: tok_lt's l̄ band equals tok's — the drafter
rarely proposes out-of-head tokens at all on this data (check
`accepted_ooh80_per_1k` for strict in E7's table: ~50/1k, so a null would
be surprising).

## E2 — `spec_casc_opt_ent` vs `spec_casc_opt` (D3)

**Why.** opt is the worst method on long-form tasks (2.13x length, 50%
budget hits on AIME24) and E7 shows its lossy-only accepts are less
extreme (median verifier rank 2 vs cactus's 7) yet it inflates most — its
failure is in *when* it trusts the drafter, not only *what* it lets
through. With a > 0 its threshold `max p - a*TV` drops exactly where the
two models disagree most. The entropy plug-in (the paper's own App. C.2)
compares whole-distribution sharpness instead of two argmaxes.

**Runs.** `bash cascade/run.sh E2-aime24` (opt's full sweep already
exists; the run adds opt_ent on the same 30 cases), then `E2-humaneval`.
Grid `[-2, -0.5, 0, 0.5]` is a first guess in nats — inspect
`campaign/calibration/<dataset>.json` before trusting the chosen alphas;
widen the grid in `scripts/campaign_run.py` if opt_ent's l̄ band does not
overlap opt's.

**Decision.** At matched l̄: opt_ent len_ratio and budget_hit below opt's
-> the trigger matters; equal -> the trigger is irrelevant and only head
restriction (E6) can fix opt. Either way the result feeds the paper's
"why cascades" paragraph.

## E3 — measured throughput and c_rel (D4)

**Why.** The paper draft has no measured wall-clock number; Xia et al.
found vLLM's spec-dec overhead dominates realisable gains (their c_rel
0.85 vs an ideal 0.27). Every speedup formula in the paper needs this
stack's c_rel, and "1.21x fewer rounds" needs a "1.1x wall-clock" next to
it to be believed.

**Runs.** `bash cascade/run.sh E3-gsm8k` then `E3-aime24`: 10 cases each
of `baseline` (no drafter), `strict`, `spec_casc_tok` a=0.8, one fresh
server per measurement, tracing off (tracing changes timing). Then
`cascade/analysis/timing_report.py` -> `cascade/results/timing_<dataset>.md`.

**Decision.** Report tok/s per arm, `tok/s vs strict`, `tok/s vs
baseline`, and the c_rel estimate `((l̄_strict+1)/S_strict - 1)/N`. If
c_rel > 0.5 on this stack, say so in the paper: it caps every method's
realisable speedup regardless of acceptance. Fresh servers only — warm
engines change per-request timing.

## E4 — draft-length sweep under strict and tok (D6)

**Why.** Xia Finding 2: choosing `N_draft` under lossless verification
gives gains comparable to relaxation, with zero accuracy risk. The entire
campaign used `NUM_SPEC=6`. If strict at N=4 matches tok at N=6, the paper's
"cascades are the exception" becomes "nothing beats tuning the draft
length", which is a stronger and simpler claim.

**Runs.** `bash cascade/run.sh E4-gsm8k` (`--mode persistent` is
acceptable here: throughput per arm is what matters, and each N gets its
own `runs_nspec<N>/` root so the run directories never collide), then
`E4-aime24`. Report: `cascade/results/nspec_<dataset>.md` (tok/s,
rounds/s, l̄ per N per arm).

**Decision.** Best N for strict by tok/s; compare strict@bestN with
tok@6 and tok@bestN. Rounds/s should be ~constant across N (one target
pass per round) while tok/s peaks where l̄ saturates.

## E5 — Diff and Chow deferral rules (D5, paper completeness)

**Why.** The source paper's OPT rule was measured against the
confidence-difference (Eq. 5) and Chow (Eq. 2) rules; the campaign only
has OPT. Both are one-line mask changes and give the method table its
baselines. Chow is also the only cascade rule that never consults the
verifier for the decision — a useful contrast for the "trust the target"
story.

**Runs.** `bash cascade/run.sh E5-gsm8k`, then `E5-aime24`
(`campaign_run.py --methods spec_casc_diff spec_casc_chow`; grids in
`scripts/campaign_run.py`).

**Decision.** At matched l̄, do Diff/Chow inflate like opt (expected: yes,
both trust the drafter wholesale) — and does Chow, which ignores p
entirely, inflate more? Their ooh80 rates from a traced run (tracing is on
by default in fresh mode) make the E7 table complete.

## E6 — `spec_casc_opt_head`: opt's trigger, tok's head restriction (D5)

**Why.** The direct test of E7's design consequence on the worst method:
keep opt's deferral, but grant the free pass only inside the verifier's
head. Two knobs: opt's alpha (grid `[-0.3, -0.1, -0.02, 0.05]`) and head
width beta in {0.5, 0.8}. beta = 1 is plain opt (control already exists).

**Runs.** `bash cascade/run.sh E6-gsm8k --mode persistent` first (25
min) to see whether the effect is there; then `E6-aime24` fresh (12 h) if
it is. Runs land in `runs/<dataset>/spec_casc_opt_head/alpha<a>_beta<b>/`;
`campaign_report.py --include-uncalibrated` (which `run.sh` passes for E6)
reports them as separate rows keyed `spec_casc_opt_head_beta<b>` with the
alpha column set, alongside the calibrated methods; without the flag the
campaign's results/graphs ignore uncalibrated arms.

**Decision.** Prediction: at beta = 0.8, len_ratio ~1.0 and l̄ about half
of opt's gain over strict at the same alpha. Support: len_ratio <= 1.1
with l̄ >= strict + 0.3 at some alpha. Refute: same inflation as opt ->
opt's damage is not in its out-of-head commits, and the trigger (E2) is
the only remaining lever.

## E8 — recover the V2 runner file (needed for anything Qwen3)

On the old H100 box:
```
cp .venv-vllm/lib/python3.12/site-packages/vllm/v1/worker/gpu/spec_decode/rejection_sampler_utils.py /tmp/v2_consolidated.py
# pristine copy: https://raw.githubusercontent.com/vllm-project/vllm/v0.26.0/vllm/v1/worker/gpu/spec_decode/rejection_sampler_utils.py
diff -u --label a/vllm/v1/worker/gpu/spec_decode/rejection_sampler_utils.py --label b/vllm/v1/worker/gpu/spec_decode/rejection_sampler_utils.py pristine.py /tmp/v2_consolidated.py > patches/vllm-0.26.0-v2-consolidated.patch
sha256sum /tmp/v2_consolidated.py   # must equal HASHES.txt's current V2 "mentored-dec" line
```
Then teach `apply.sh` to install it (V2 block) and note in the paper that
cactus/tok on Qwen3 are accept-test-only ports. Until this is done, do not
run `*_qwen3` datasets on a fresh install.

## Running

```
bash cascade/run.sh <id> [--target box|nibi] [--mode fresh|persistent] [--cases N] [--dry-run]
```
- `--target box` (default) runs in the foreground from the repo root on
  the machine you are on (the old H100 box, or inside a Nibi `salloc`).
- `--target nibi` submits the identical command through
  `cascade/cluster/nibi_run.sbatch` (one H100, 12 h default; the job sets
  `PORT` from its id so two jobs on a node never collide).
- `--dry-run` prints the exact command(s). Every id above was dry-run
  checked; the commands are ordinary `campaign_run.py` /
  `fresh_server_replay.py` / `persistent_arm_replay.py` calls, so anything
  can also be typed by hand.
- Recommended order on a new GPU: `E0` -> `E1-gsm8k` -> `E3-gsm8k` ->
  `E6-gsm8k --mode persistent` -> `E1-aime24` -> the rest as time allows.
  Each result should be logged in `JOURNAL.md` with the date and the
  command used.
