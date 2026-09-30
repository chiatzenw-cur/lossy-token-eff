# Running this repo on the Alliance cluster (Nibi)

Everything the campaign does is "start one vLLM server on one GPU, send it
one request, read `/metrics`, stop it" — plain bash/Python on a single box.
On the cluster that maps to **one Slurm job = one H100 for N hours running
the same scripts**, with the server and client on the same node. This
directory holds the environment recipe, the job wrappers, and what was
learned running ~60 GPU-hours here in September 2026.

## Account and cluster facts

| | |
|---|---|
| Slurm account, general-purpose clusters | **`def-hongyanz_gpu`** (`sshare -U` shows the `_gpu`/`_cpu` split; `def-hongyanz` also resolves) |
| Slurm account, AI clusters (Killarney / Vulcan / TamIA) | `aip-hongyanz` |
| cluster used | Nibi, `nibi.alliancecan.ca` (Waterloo; H100 SXM 80 GB nodes `g1–g28`, 8 GPUs each, `--gpus-per-node=h100:1`; no `--partition`, it is chosen by walltime) |
| login | `ssh nibi` via an `~/.ssh/config` entry (user, key, `ControlMaster` multiplexing so one Duo approval covers a session); the multiplexed connection is closed server-side after ~10 idle minutes, so batch work per login |
| storage | home 50 GiB (small: no venvs); `$SCRATCH` 1 TiB (60-day purge); project `~/projects/def-hongyanz` 931 GiB shared with the group — repo, venvs and model cache live there |
| software | `module load StdEnv/2023 python/3.12 cuda/12.9` — modules load only in login shells (`bash -l`); driver 580.82 on the GPU nodes; compute nodes have internet, jobs still run with `HF_HUB_OFFLINE=1` |
| limits | no per-user GPU cap under QOS `normal` (interactive QOS: 3 jobs); fair-share priority is the only constraint |

**Getting access, the part that cost a day:** CCDB → Resources → *Access
Systems* is opt-in **per system**. Until "I request access" is selected
for a cluster, the public key and Duo both succeed and the cluster then
refuses the session (`Connection closed` on Nibi/Fir/Killarney;
`Permission denied (keyboard-interactive)` after three Duo successes on
Rorqual/Narval). Request access, wait up to an hour, log in. Not a
provisioning bug, not a support ticket.

## First-login checklist (do once)

```bash
sshare -U                               # confirm the def-hongyanz_gpu association
sinfo -o "%P %G %D %t" | grep -i gpu    # GPU gres names
diskusage_report                        # home / project / scratch quotas
module spider python cuda               # module versions -> setup_nibi.sh
ls -la ~/projects/                      # def-hongyanz symlink
```

## Layout on the cluster

| what | where | why |
|---|---|---|
| repo + venvs | `~/projects/def-hongyanz/$USER/lossy-token-eff` | project space: large, not purged, group-shared |
| HF model cache | `~/projects/def-hongyanz/$USER/hf` | GPT-OSS-20B + EAGLE3 (~40 GB with all formats); pre-downloaded on a login node |
| runs/ logs/ | inside the repo (default `--runs-root`) | ~25 KB per run without traces; `campaign_report.py` finds them there |
| vLLM / Triton / Inductor caches | `$SCRATCH/{vllm,triton,inductor}_cache` | persistent, so servers start in ~5 min instead of ~11 (cold compile) |
| `/tmp` knob files | node-local `/tmp` | the patched sampler reads them; server and client share the node |

**Rule: concurrent jobs must never share a venv.** Every arm switches the
installed vLLM patch in its venv (the patches are mutually exclusive on
one file); two jobs doing that in one venv crash each other. Run one job
per venv copy (`lossy-token-eff-lane2/` is such a copy) and keep lanes on
disjoint nodes (`--exclude=g[15-28]` / `--exclude=g[1-14]`) because the
`/tmp` knob files are per node. When copying a venv with rsync, anchor the
excludes (`--exclude /runs/`, not `runs/`), or directories named `runs`
inside site-packages get dropped too.

## Environment build (login node, once): `setup_nibi.sh`

Mirrors `remote/ENVIRONMENT.md` (vLLM 0.26.0 + torch 2.11 cu129, a
matplotlib venv for reports) with `pip`, then downloads the GPT-OSS pair
(`MODELS=` to change). Two Nibi-specific fixes are baked in: the Python
module re-sets `PIP_CONFIG_FILE` after `module load` (its wheelhouse would
silently substitute `torch+computecanada` for the cu129 wheel), so the
override and `unset PYTHONPATH` come after the load; and `torchcodec`
(linked against CUDA 13) is uninstalled because its import breaks the
patched sampler. Verify on a GPU node with `bash cascade/run.sh E0`
(`cluster/patch_cycle_test.sh`: installs and self-tests every patch in
turn, reversing the previous one — `patches/apply.sh` refuses to switch on
its own).

**Qwen3 caveat:** Qwen3-8B uses vLLM's V2 runner, whose consolidated
multi-method file exists only on the original H100 box
(`../DIRECTIONS.md` D8). On a fresh install every Qwen3 arm would silently
run strict; `nibi_campaign.sbatch` refuses `*_qwen3` datasets.

## Submitting

- `bash cascade/run.sh <id> --target nibi` builds the command for an
  experiment id (`../EXPERIMENTS.md`) and submits it through
  `nibi_run.sbatch` (one H100, modules, offline HF cache, persistent
  compile caches, a port derived from the job id). `--dry-run` prints the
  command. `SBATCH_EXTRA="--dependency=afterany:<jobid> --exclude=g[15-28]"`
  passes extra sbatch flags (chaining, node pinning). `REPO_DIR` selects
  the repo copy the job runs in (default `~/projects/def-hongyanz/$USER/lossy-token-eff`).
- `nibi_campaign.sbatch <dataset> "<methods>" [cases] [calib]` is the same
  wrapper specialised to one `campaign_run.py` call.
- `nibi_interactive.sh` gives a short one-GPU `salloc` for debugging.
- `nibi_after_build.sh` waits for `setup_nibi.sh` to finish, then submits
  E0 and the sample run chained.

Timings on the H100 SXM (warm server per arm; per-answer generation is
~3× faster than the old box's PCIe card): gsm8k 150 problems × 3 seeds ×
7 arms ≈ 1 h; humaneval ≈ 3.5 h; mtbench ≈ 3 h; livecodebench ≈ 5 h;
aime24 30 × 3 × 7 ≈ 8 h; longbench_v2 30 × 3 × 7 ≈ 1 h. A fresh server
start is ~5 min, so fresh-server-per-measurement sweeps are ~10× dearer
than on the old box; persistent mode is the practical default here.

## After a failed job

Delete the failed placeholder records before resubmitting — skip-if-done
treats any `run.json` as done, including ones with `status != ok`:

```bash
python3 - <<'PY'
import json, pathlib, shutil
for rj in pathlib.Path("runs/<dataset>").glob("*/*/case_*/seed_*/run.json"):
    if json.loads(rj.read_text()).get("status") != "ok": shutil.rmtree(rj.parent)
PY
```

`remote/stop_server.sh` waits for the GPU to be released, not for the
previous API server's socket; `fresh_server_replay.start_server` now waits
for the port to be free before launching the next server.

## Syncing code and results

`git clone` the repo on the cluster, or push the working tree with
`sync_to_nibi.sh` (rsync; excludes runs, logs, venvs, `.git`). Results
come back with `rsync -avz nibi:projects/def-hongyanz/$USER/lossy-token-eff/campaign/ campaign/`;
note that `campaign/results/<ds>.csv` and `campaign/tables/<ds>.csv` share
a filename, so pull them under distinct local names.
