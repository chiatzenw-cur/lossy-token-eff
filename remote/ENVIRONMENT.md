# Environment

Same box as `lossy-spec-decode-repetition` (H100 PCIe, driver 570.195.03 / CUDA
12.8), so the same forced deviation applies: cu130 needs driver 580+, this
driver is 570, so we install the cu129 build of both torch and vLLM — a minor
version step, which CUDA's minor-version compatibility covers. Verified below
with a real GPU matmul, not just an import.

| | here |
|---|---|
| vLLM | **0.26.0+cu129** |
| torch | **2.11.0+cu129** |
| GPU | H100 PCIe |
| parallelism | none (`--tensor-parallel-size 1 --pipeline-parallel-size 1`) |

`lossy-spec-decode-repetition` started on vLLM 0.20.1 (matching the paper
exactly) and moved to 0.26.0 partway through; its patches now target 0.26.0
(see its `patches/README.md`). We start directly on 0.26.0.

## Install

Order matters: installing vLLM pulls PyPI's default cu130 torch, so torch is
restored from the cu129 index afterwards. Same for torchvision/torchaudio.

```bash
uv venv --python 3.12 .venv-vllm
uv pip install --python .venv-vllm/bin/python \
  --index-url https://download.pytorch.org/whl/cu129 torch==2.11.0
uv pip install --python .venv-vllm/bin/python "vllm==0.26.0+cu129" \
  --extra-index-url https://wheels.vllm.ai/0.26.0/cu129/ --index-strategy unsafe-best-match
uv pip install --python .venv-vllm/bin/python \
  --index-url https://download.pytorch.org/whl/cu129 \
  --reinstall-package torch --reinstall-package torchvision --reinstall-package torchaudio \
  torch==2.11.0 torchvision==0.26.0 torchaudio==2.11.0
```

Done 2026-08-08. `uv`'s package cache (`~/.cache/uv`) already held these exact
cu129 wheels from the sibling repo's install, so every step above resolved via
hardlink — net new disk cost was ~1G against an 11G venv (`du` counts each
hardlink at full size; `df` is the number that's real). If this is ever
rebuilt on a box without that warm cache, budget real download time and space
for it.

## Verify

```bash
.venv-vllm/bin/python -c "
import torch
print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))
x = torch.randn(1024,1024, device='cuda') @ torch.randn(1024,1024, device='cuda')
print('finite:', torch.isfinite(x).all().item())
"
```

Confirmed: `2.11.0+cu129 True NVIDIA H100 PCIe`, matmul finite.

Check for stray CUDA-13-linked extensions:

```bash
cd .venv-vllm/lib/python3.12/site-packages
for so in $(find . -name "*.so" -not -path "./torch/*" -not -path "./nvidia/*"); do
  strings "$so" 2>/dev/null | grep -q "libcudart\.so\.13" && echo "CU13: $so"
done
```

This prints six hits, three more than the sibling repo's two
(`cudnn/_compiled_module`, `tilelang/lib/libcudart_stub.so`): vLLM 0.26.0 pulls
in `torchcodec` as a new transitive dependency (video/audio decoding,
0.20.1-era vLLM didn't have it), contributing four `libtorchcodec_core*.so`
hits. Confirmed harmless the same way — `import vllm` does not put
`torchcodec` in `sys.modules`, so it's dormant weight on disk, not on the
serving path, for a text-only model.

## Checkpoints

Reusing the sibling repo's shared Hugging Face cache (`~/.cache/huggingface`,
user-level, not repo-scoped) — no re-download needed:

| Role | Repo | Local size |
|---|---|---|
| Target | `openai/gpt-oss-20b` | 13G |
| Draft | `nebius/EAGLE3-gpt-oss-20b` | 669M |

**This is a real constraint, not just a convenience.** The box has 16G free.
The taxonomy paper's own pairs (Qwen3-32B verifier, tens of GB) don't fit
without freeing space first, so GPT-OSS-20B+EAGLE3 is effectively the only
target/drafter pair available right now unless that changes.

## Fresh server per measurement — not optional

**Yes, shut down and start a new server for every measurement.** This isn't
caution for its own sake; the sibling repo measured the alternative failing.

`--seed` and prompt/sampling params being identical is not enough to make two
requests comparable if they land on a server that has already served other
requests. Two failure modes compound:

1. **Prefix-cache reuse takes a different numeric path than a cold
   compute**, even with the *same* prompt+seed (`--no-enable-prefix-caching`
   above exists because of this — see that section).
2. **Continuous batching and RNG state carry over between requests on the
   same engine.** The sibling repo's `case_001` gave 1,711 output tokens as a
   server's *first* request and 2,485 tokens as its *second* — same prompt,
   same seed, same everything except how many prior requests that engine had
   already served.

The naive fix — run each arm as its own fresh server, but issue all N cases
to it in the same order — is **not** sufficient either. "Same ordinal
position" is not "same engine state": by case 2, the two arms have already
produced different numbers of tokens and consumed different numbers of RNG
draws, so anything downstream of the first case in a shared run still carries
a request-history confound.

The sibling repo hit this directly: a 10-problem pilot sharing one server per
arm reported strict 9/10 → lossy 6/10. Re-run with one fresh server per
*(arm, case, seed)* triple — every request the first thing its engine ever
sees — the same ten problems gave strict 7/10 → lossy 7/10, and the one case
that happened to be ordinal-1 in both runs (`case_001`) reproduced
**bit-for-bit** (1,711 / 1,587 tokens, same for both). That agreement is also
useful on its own: it confirms the pipeline is deterministic and the pilot
and fresh datasets are directly comparable once position is controlled — the
gap was the confound, not noise.

**So: one server per `(arm, config, case, seed)` tuple, every request
ordinal 1.** This costs a full server start per measurement (the sibling repo
priced 60 runs at ~1.5h), which is real but small next to the alternative of
a dataset with an uncontrolled confound baked in. `scripts/run_experiment_vllm.py`
in the sibling repo asserts ordinal-1 from `/metrics` and refuses to write a
run directory otherwise (`--assert-fresh-server`) — port that assertion, not
just the discipline, when the data-collection runner exists here; a policy
enforced only by remembering to follow it is the exact way the pilot's
confound got in.

## Patching rejection_sampler.py — the hardlink trap

`lossy-spec-decode-repetition/patches/README.md` flags this and it applies
here too: `uv` installs via hardlink from `~/.cache/uv/archive-v0`. A plain
`cp` onto an installed file writes *through* the hardlink and silently
corrupts that cached wheel for every other venv built from it — including the
sibling repo's already-verified `.venv-vllm`. Always `cp --remove-destination`
(or write-then-`mv`) when patching installed files, never a bare `cp`.
