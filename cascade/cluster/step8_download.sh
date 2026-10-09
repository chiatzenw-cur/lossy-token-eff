#!/bin/bash
# Step 8 (campaign/addendum/step8/GOAL.md) model downloads on a login node:
# weights, configs and tokenizers only (no optimizer/scheduler states, no
# original/*.pth). The unsloth repos are fetched for their config/tokenizer
# files only: they are the independent copies the Meta mirrors are hashed
# against (README deviation 29).
#   PROJECT_DIR=~/projects/aip-hongyanz/billxby bash cascade/cluster/step8_download.sh [repo ...]
set -uo pipefail
PROJECT_DIR="${PROJECT_DIR:?PROJECT_DIR}"
export HF_HOME="${HF_HOME:-$PROJECT_DIR/hf}"
unset HF_HUB_OFFLINE TRANSFORMERS_OFFLINE
PY="${PY:-$PROJECT_DIR/lossy-token-eff/.venv-vllm/bin/python}"
MODELS=("$@")
if [[ ${#MODELS[@]} -eq 0 ]]; then
  MODELS=(yuhuili/EAGLE3-DeepSeek-R1-Distill-LLaMA-8B deepseek-ai/DeepSeek-R1-Distill-Llama-8B
          alpindale/Llama-3.2-1B-Instruct NousResearch/Meta-Llama-3.1-8B-Instruct
          yuhuili/EAGLE3-LLaMA3.1-Instruct-8B yuhuili/EAGLE-LLaMA3.1-Instruct-8B nebius/MEDUSA-Llama-3.1-8B-Instruct
          RedHatAI/Qwen3-8B-speculator.dflash RedHatAI/Qwen3-8B-Thinking-speculator.eagle3 Qwen/Qwen3-1.7B
          RedHatAI/gpt-oss-20b-speculator.eagle3 openai/gpt-oss-20b RedHatAI/Qwen3-8B-speculator.peagle
          unsloth/Llama-3.1-8B-Instruct unsloth/Llama-3.2-1B-Instruct)
fi
for m in "${MODELS[@]}"; do
  echo "=== $m $(date -u +%FT%TZ)"
  "$PY" - "$m" <<'PY' || echo "FAILED $m"
import sys
from huggingface_hub import snapshot_download
m = sys.argv[1]
pats = ["*.json", "*.safetensors", "*.py", "*.jinja", "*.txt", "*.model", "tokenizer*"]
if m.startswith("unsloth/"):
    pats = ["*.json", "*.jinja"]
if m.startswith("yuhuili/"):
    pats.append("pytorch_model.bin")
if m == "openai/gpt-oss-20b":
    pats = ["*.json", "model-*.safetensors", "*.jinja", "*.txt"]
p = snapshot_download(m, allow_patterns=pats, ignore_patterns=["original/*", "metal/*", "*optimizer*", "*scheduler*"])
print("OK", m, p)
PY
done
echo "=== ALL DONE $(date -u +%FT%TZ)"
