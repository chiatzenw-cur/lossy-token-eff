#!/bin/bash
#SBATCH --account=aip-hongyanz
#SBATCH --gpus-per-node=h100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=3:00:00
#
# Step 8 block 6 (campaign/addendum/step8/GOAL.md): GPU check of the V2 port of spec_casc_tok_lt /
# spec_casc_opt_head (patches/vllm-0.26.0-v2-consolidated-step8.patch), Qwen3-8B + its EAGLE-3 head,
# gsm8k_qwen3 case_001, seed 0, in one job on one node:
#   old  = consolidated V2 68d0a904: strict + the five rules (mentored_dec 0.75, cactus 0.35, spec_casc_opt 0.05,
#          r_fuzzy 0.25, spec_casc_tok 0.8)
#   new  = 796e3c85: the same six arms (must be bit-identical to old), then tok_lt -inf / 0.15 / 0.2 and
#          opt_head (-inf, 0.15) / (0.05, 0.15): the -inf arms must equal strict, the others must not
# The lane venv is left on the new file afterwards (it supersedes 68d0a904, HASHES.txt).
#   REPO_DIR=<lane repo> V2_DIR=/scratch/billxby/step8/v2 OUT=/scratch/billxby/step8/v2check sbatch ... this file
set -euo pipefail
REPO_DIR="${REPO_DIR:?}"; V2_DIR="${V2_DIR:?}"; OUT="${OUT:?}"
PROJECT_DIR="${PROJECT_DIR:-$HOME/projects/aip-hongyanz/$USER}"
for _ in 1 2 3; do "$REPO_DIR/.venv-vllm/bin/python" -c pass 2>/dev/null && break; sleep 10; done
module load StdEnv/2023 python/3.12 cuda/12.9
unset PYTHONPATH
cd "$REPO_DIR"
export HF_HOME="$PROJECT_DIR/hf" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export CUDA_HOME="${EBROOTCUDA:-/usr/local/cuda}" VLLM_CACHE_ROOT="$SCRATCH/vllm_cache" TRITON_CACHE_DIR="$SCRATCH/triton_cache"
export TORCHINDUCTOR_CACHE_DIR="$SCRATCH/inductor_cache" APPLY_SKIP_TEST_IF_APPLIED=1
PORT=$((30000 + SLURM_JOB_ID % 20000))
PY="$REPO_DIR/.venv-vllm/bin/python"
DST="$REPO_DIR/.venv-vllm/lib/python3.12/site-packages/vllm/v1/worker/gpu/spec_decode/rejection_sampler_utils.py"
echo "=== v2 check job $SLURM_JOB_ID on $(hostname) $(date -u +%FT%TZ) ==="
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader

install() {  # $1 = file, $2 = expected sha256 prefix
  local got; cp "$1" "$DST"; got=$(sha256sum "$DST" | cut -c1-8)
  [[ "$got" == "$2" ]] || { echo "V2 install failed: $got != $2" >&2; exit 1; }
  echo "V2 file now $got"
}
run() {  # $1 = label, rest = persistent_arm_replay args
  local label="$1"; shift
  "$PY" scripts/persistent_arm_replay.py --cases case_001 --seeds 0 --prompt-root prompts/gsm8k_qwen3 \
    --runs-root "$OUT/$label/runs" --log-root "$OUT/$label/logs" --max-new-tokens 2048 --num-spec 6 \
    --temperature 1.0 --top-p 1.0 --server-seed 0 --port "$PORT" --no-trace-proposals \
    --model-path Qwen/Qwen3-8B --draft-model-path RedHatAI/Qwen3-8B-speculator.eagle3 --served-model-name qwen3-8b \
    --rope-scaling-json '{"rope_type":"yarn","factor":1.6,"original_max_position_embeddings":40960}' "$@" \
    || echo "run $label exited nonzero"  # one failed arm must not stop the rest (set -e)
}
SIX=(--arms strict mentored_dec cactus spec_casc_opt r_fuzzy spec_casc_tok --mentored-dec-alpha 0.75
     --cactus-alpha 0.35 --spec-casc-opt-alpha 0.05 --r-fuzzy-alpha 0.25 --spec-casc-tok-alpha 0.8)
install "$V2_DIR/v2_consolidated.py" 68d0a904
run old "${SIX[@]}"
install "$V2_DIR/v2_step8.py" 796e3c85
run new "${SIX[@]}"
for a in -inf 0.15 0.2; do run new --arms spec_casc_tok_lt --spec-casc-tok-lt-alpha="$a"; done
for a in -inf 0.05; do run new --arms spec_casc_opt_head --spec-casc-opt-head-alpha="$a" --spec-casc-opt-head-beta=0.15; done

# ---- block 0(d) and the q probe of every other drafter (Bill, 2026-10-03): a drafter passes only if its per-position
# draft probabilities q reach the patched sampler and are not one-hot. V2 drafters: the [Q-PROBE V2] line of the
# 796e3c85 file; V1 drafters: a traced strict run (patches/relaxation_trace.py records q(x) and the draft entropy).
probe() {  # $1 = label, $2 = prompt set, $3 = target, $4 = drafter, $5 = served name, $6 = spec method, $7 = rope json, $8 = trace?
  local label="$1" ds="$2" target="$3" drafter="$4" served="$5" spec="$6" rope="$7" trace="$8"
  local extra=(--no-trace-proposals); [[ "$trace" == trace ]] && extra=()
  local ropeargs=(); [[ -n "$rope" ]] && ropeargs=(--rope-scaling-json "$rope")
  SPEC_METHOD="$spec" "$PY" scripts/fresh_server_replay.py --arms strict --cases case_001 --seeds 0 \
    --prompt-root "prompts/$ds" --runs-root "$OUT/q/$label/runs" --log-root "$OUT/q/$label/logs" --max-new-tokens 1024 \
    --num-spec 6 --temperature 1.0 --top-p 1.0 --server-seed 0 --port "$PORT" "${extra[@]}" \
    --model-path "$target" --draft-model-path "$drafter" --served-model-name "$served" "${ropeargs[@]}" \
    > "$OUT/q/$label.out" 2>&1 || echo "probe $label: replay exited nonzero"
  echo "--- probe $label ($spec, $drafter)"
  grep -rh "Q-PROBE V2" "$OUT/q/$label/logs" 2>/dev/null | head -3 || true
  find "$OUT/q/$label/runs" -name proposals.jsonl -exec "$PY" -c '
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1])]
qs = [r.get("q") for r in rows]
real = [q for q in qs if q is not None]
ent = [r.get("draft_entropy") for r in rows if r.get("draft_entropy") is not None]
print(f"[Q-PROBE V1 trace] proposals={len(rows)} q_present={len(real)} q_lt_0.999={sum(q < 0.999 for q in real)} "
      f"mean_draft_entropy={sum(ent) / len(ent) if ent else -1.0:.4f}")' {} \; 2>/dev/null || true
  find "$OUT/q/$label/runs" -name run.json -exec grep -l '"status": "ok"' {} \; | head -1 | sed 's/^/ok run: /'
}
Q3ROPE='{"rope_type":"yarn","factor":1.6,"original_max_position_embeddings":40960}'
mkdir -p "$OUT/q"
# (d) in Bill's order, stop at the first that passes (q present, frac_one_hot < 0.5, run ok)
for spec_drafter in dspark:deepseek-ai/dspark_qwen3_8b_block7 dflash:RedHatAI/Qwen3-8B-speculator.dflash \
                    eagle3:RedHatAI/Qwen3-8B-Thinking-speculator.eagle3; do
  spec="${spec_drafter%%:*}"; drafter="${spec_drafter#*:}"; label="d_${spec}"
  probe "$label" gsm8k_qwen3 Qwen/Qwen3-8B "$drafter" qwen3-8b "$spec" "$Q3ROPE" notrace
  if grep -rh "Q-PROBE V2" "$OUT/q/$label/logs" 2>/dev/null | grep -q "draft_logits=present" && \
     grep -rh "Q-PROBE V2" "$OUT/q/$label/logs" | head -1 | "$PY" -c 'import re,sys; v=float(re.search(r"frac_one_hot=([0-9.]+)", sys.stdin.read()).group(1)); sys.exit(0 if v < 0.5 else 1)' && \
     find "$OUT/q/$label/runs" -name run.json -exec grep -q '"status": "ok"' {} \; ; then
    echo "=== block 0(d): $drafter ($spec) PASSES"; break
  fi
  echo "=== block 0(d): $drafter ($spec) fails"
done
VLLM_CACHE_ROOT=/scratch/billxby/vllm_cache_step8/qwen3-8b__qwen3-1.7b probe d_qwen17b gsm8k_qwen3 Qwen/Qwen3-8B Qwen/Qwen3-1.7B qwen3-8b draft_model "$Q3ROPE" trace
probe q_q3_eagle3 gsm8k_qwen3 Qwen/Qwen3-8B RedHatAI/Qwen3-8B-speculator.eagle3 qwen3-8b eagle3 "$Q3ROPE" notrace
L="$PROJECT_DIR/hf/local"
probe q_r1_eagle3 gsm8k_r1llama deepseek-ai/DeepSeek-R1-Distill-Llama-8B "$L/EAGLE3-DeepSeek-R1-Distill-LLaMA-8B-maxpos65536" r1-distill-llama-8b eagle3 "" notrace
probe q_r1_llama1b gsm8k_r1llama deepseek-ai/DeepSeek-R1-Distill-Llama-8B alpindale/Llama-3.2-1B-Instruct r1-distill-llama-8b draft_model "" trace
probe q_l31_eagle3 gsm8k_llama31 RedHatAI/Llama-3.1-8B-Instruct "$L/EAGLE3-LLaMA3.1-Instruct-8B-maxpos65536" llama31-8b-instruct eagle3 "" notrace
probe q_l31_eagle1 gsm8k_llama31 RedHatAI/Llama-3.1-8B-Instruct "$L/EAGLE-LLaMA3.1-Instruct-8B-maxpos65536" llama31-8b-instruct eagle "" notrace
probe q_l31_medusa gsm8k_llama31 RedHatAI/Llama-3.1-8B-Instruct nebius/MEDUSA-Llama-3.1-8B-Instruct llama31-8b-instruct medusa "" trace
probe q_l31_llama1b gsm8k_llama31 RedHatAI/Llama-3.1-8B-Instruct alpindale/Llama-3.2-1B-Instruct llama31-8b-instruct draft_model "" trace
MENTORED_DEC_TEST_V1_ONLY=1 probe q_gptoss_rh gsm8k openai/gpt-oss-20b RedHatAI/gpt-oss-20b-speculator.eagle3 gpt-oss-20b eagle3 "" trace
bash remote/stop_server.sh > /dev/null 2>&1 || true
echo "=== done $(date -u +%FT%TZ) ==="
