# V2 model-runner base (recorded 2026-10-05)

Verbatim copies of the three vLLM 0.26.0 V2 (`vllm/v1/worker/gpu/`) files as they were installed in `.venv-vllm` when the Qwen3 force-commit port began. They are the base that `patches/vllm-0.26.0-qwen3-force-commit-v2.patch` applies to.

| file here | installed path (under `vllm/v1/worker/gpu/`) | sha256 |
|---|---|---|
| `gpu_model_runner_v2.py` | `model_runner.py` | 49ba999e6ba5661365c65c3f71bea75f7182cc5583252c8f16b71baf9ac3f670 |
| `spec_decode_rejection_sampler.py` | `spec_decode/rejection_sampler.py` | 63d52ec3a453be6733f8efe699b03260d0ee43633c4da52031ec0110383a0825 |
| `spec_decode_rejection_sampler_utils.py` | `spec_decode/rejection_sampler_utils.py` | 68d0a904230a82d7aa90916e9ed60297e3c725eeb0188b633893e03fb5b9f938 |

## Origin, stated plainly

- Upstream vLLM 0.26.0 has no lossy-verification code in these files. Everything beyond upstream was added by this repo's V2 ports, which were applied to the files directly and not recorded as patch files.
- `rejection_sampler_utils.py` is the consolidated V2 kernel shared by the spec-casc-tok, mentored-dec, cactus, spec-casc-opt and r-fuzzy arms. Its hash is recorded in campaign configs as `vllm.v2_sha256`. Origin: `campaign/JOURNAL.md`, the entry on "port the remaining 3 methods into V2" (2026-08-20 to 21).
- `gpu_model_runner_v2.py` carries lossy-verification markers, including a comment for an "hsr-guard V2 port" (2026-08-22). No patch file in `patches/` produces them. This is the part with the weakest provenance.
- `spec_decode_rejection_sampler.py` is the sampler `__call__` that calls the consolidated kernel. Its edits are not separately documented either.

Consequence: the base cannot be rebuilt from upstream plus a patch. It can only be reproduced by copying these files. Any future V2 change must be a patch against these copies, and the installed hashes must match this table before applying.
