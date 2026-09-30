#!/usr/bin/env bash
# One-time environment build on an Alliance LOGIN node (needs internet).
# Mirrors remote/ENVIRONMENT.md (vLLM 0.26.0, torch 2.11, cu129 wheels) with
# pip instead of uv, then pre-downloads the checkpoints so GPU jobs can run
# with HF_HUB_OFFLINE=1.
#
#   bash cascade/cluster/setup_nibi.sh            # after cloning the repo into $PROJECT_DIR
#
# Three things to confirm from the first-login checklist (cluster/README.md)
# before running: the module names, the wheel flavour for the GPU node's
# driver, and the project directory.
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$HOME/projects/def-hongyanz/$USER}"
REPO_DIR="${REPO_DIR:-$PROJECT_DIR/lossy-token-eff}"
export HF_HOME="${HF_HOME:-$PROJECT_DIR/hf}"
# `module spider python` / `module spider cuda` list what exists; these are
# the usual StdEnv/2023 names on 2025 clusters.
MODULES="${MODULES:-StdEnv/2023 python/3.12 cuda/12.9}"
# Checkpoints to pre-download. Default: the GPT-OSS pair only -- the Qwen3
# pair (Qwen/Qwen3-8B RedHatAI/Qwen3-8B-speculator.eagle3) is unusable on a
# fresh install until the V2 sampler is recovered (cascade/DIRECTIONS.md D8).
MODELS="${MODELS:-openai/gpt-oss-20b nebius/EAGLE3-gpt-oss-20b}"
# cu129 matches remote/ENVIRONMENT.md (driver 570 on the old box). If
# nvidia-smi on a GPU node reports driver >= 580, cu130 (PyPI defaults) is
# fine too: WHEEL_FLAVOUR=cu130 skips the torch re-pin below.
WHEEL_FLAVOUR="${WHEEL_FLAVOUR:-cu129}"

if [[ ! -d "$REPO_DIR/patches" ]]; then
  echo "repo not found at $REPO_DIR -- git clone it there first (or set REPO_DIR)" >&2
  exit 1
fi
mkdir -p "$HF_HOME"

# shellcheck disable=SC2086
module load $MODULES
# AFTER module load, which (re)sets both of these: the Alliance python
# module points pip at its own wheelhouse (whose torch-2.11.0+computecanada
# would silently replace the PyTorch cu129 wheel the vLLM cu129 wheel is
# built against) and puts a site-packages dir on PYTHONPATH that would
# shadow the venv's packages. The campaign environment is pinned to PyPI /
# the PyTorch cu129 index / the vLLM index (remote/ENVIRONMENT.md).
export PIP_CONFIG_FILE=/dev/null
unset PYTHONPATH
cd "$REPO_DIR"

if [[ ! -x .venv-vllm/bin/python ]]; then
  python -m venv .venv-vllm
fi
PY=.venv-vllm/bin/python
"$PY" -m pip install --upgrade pip wheel

if [[ "$WHEEL_FLAVOUR" == "cu129" ]]; then
  # Order matters (remote/ENVIRONMENT.md): vLLM pulls PyPI's default torch,
  # so torch/torchvision/torchaudio are re-pinned from the cu129 index after.
  "$PY" -m pip install --index-url https://download.pytorch.org/whl/cu129 torch==2.11.0
  "$PY" -m pip install "vllm==0.26.0+cu129" --extra-index-url https://wheels.vllm.ai/0.26.0/cu129/
  "$PY" -m pip install --index-url https://download.pytorch.org/whl/cu129 --force-reinstall --no-deps \
    torch==2.11.0 torchvision==0.26.0 torchaudio==2.11.0
else
  "$PY" -m pip install "vllm==0.26.0"
fi
"$PY" -m pip install huggingface_hub
# torchcodec (a video-decoding dependency vLLM 0.26 pulls in) ships linked
# against CUDA 13 libraries (libcudart.so.13, libnvrtc.so.13) that the cu129
# environment does not have, so importing it raises OSError -- and the
# patched sampler's import chain reaches it. Text-only serving never uses it
# (remote/ENVIRONMENT.md); removing it makes the import fall back cleanly.
# Found on Nibi 2026-09-11: the patch self-test failed with exactly this.
"$PY" -m pip uninstall -y torchcodec 2>/dev/null || true

if [[ ! -x .venv-report/bin/python ]]; then
  python -m venv .venv-report
fi
.venv-report/bin/python -m pip install --upgrade pip
.venv-report/bin/python -m pip install matplotlib

echo "--- versions ---"
"$PY" -c "import vllm, torch; print('vllm', vllm.__version__, '| torch', torch.__version__)"

echo "--- checkpoints -> $HF_HOME: $MODELS ---"
for repo in $MODELS; do
  "$PY" -c "from huggingface_hub import snapshot_download; print(snapshot_download('$repo'))"
done

echo "--- patch sanity (no GPU: kernel tests skip, plumbing + formula tests run) ---"
bash patches/apply.sh spec-casc-tok-lt

cat <<EOF

done. Next:
  bash cascade/cluster/nibi_interactive.sh          # GPU shell; nvidia-smi; re-run 'bash patches/apply.sh spec-casc-tok-lt' for the kernel test
  sbatch cascade/cluster/nibi_campaign.sbatch gsm8k spec_casc_tok_lt 30 3
EOF
