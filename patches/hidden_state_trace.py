"""Per-round TARGET hidden-state capture, for the latent-trajectory-
recurrence pilot (analysis/semantic_guard/README.md). Not upstream vLLM.

Companion to relaxation_trace.py, deliberately a SEPARATE module: that one
records scalar decode-time quantities (p, q, rank, entropy, ...) computed
downstream of the model forward pass, in rejection_sampler.py; this one
records the target model's own hidden state, upstream, at the one place in
vllm/v1/worker/gpu_model_runner.py where it's already computed and about to
be handed to the EAGLE3 drafter (see the patch's own diff --
`target_hidden_states`, right before `self.drafter.propose(...)`, in the
EAGLE/aux-hidden-states branch of `propose_draft_token_ids`). Note this is
`gpu_model_runner.py`, the FLAT file -- vLLM's "V1" model runner, confirmed
active by default in this config (`use_v2_model_runner` unset; same
distinction patches/README.md's mentored-dec section already hit from a
different angle). `vllm/v1/worker/gpu/model_runner.py` under the `gpu/`
subdirectory is "V2" and is never instantiated here; an earlier version of
this patch targeted that file by mistake and silently captured nothing (a
genuinely dead code path in this config) -- caught only by an empty output
file after a real test run, not by any test run against the (correctly
behaving, just never-invoked) V2 code. Kept separate from
relaxation_trace.py because the write volume and cadence are different
(hidden states are large; this is meant to be switched on for a handful of
short diagnostic runs, not left on by default the way scalar tracing is)
and because this file is a genuinely different, more architecturally
sensitive patch site (CUDA-graph-adjacent orchestration code, five parallel
per-drafter-type branches to navigate) than rejection_sampler.py -- if this
ever needs reverting independently of the scalar tracer, it should be able
to.

For this repo's config specifically (`use_aux_hidden_state_outputs=True`,
EAGLE3's own design), `target_hidden_states` is NOT only the target's final
layer -- it's the concatenation of several intermediate layers EAGLE3
itself uses as its drafting input (`eagle_aux_hidden_state_layer_ids`).
That's a real, load-bearing difference from "the target's own last hidden
state" as originally scoped (patch/analysis discussion in this repo's
commit history) -- worth remembering when interpreting a captured vector:
it's "what EAGLE3 sees," which happens to also be a legitimate target-side
representation, but isn't necessarily the single last-layer vector a
from-scratch capture would have chosen.

Row alignment with proposals.jsonl: this module's own `round` counter
increments once per call to `record(...)`, which happens once per verify
round from `gpu_model_runner.py`'s speculative-proposal path --
chronologically right after that SAME round's rejection_sample() call (and
therefore right after relaxation_trace.py's own `self._round` increments
for that round), so round numbers here are expected to line up 1:1 with
`proposals.jsonl`'s own `round` field for the same run. This is NOT
verified by construction (the two counters are independent, on purpose --
this module must not import from or depend on relaxation_trace.py, so a
bug in one can't corrupt the other) -- validate it empirically per run
(row counts, or a handful of spot checks) before trusting a join, and see
analysis/semantic_guard/join_hidden_states.py for the join itself.

`hidden_states` here covers every position PROCESSED in the round's target
forward pass (all K draft positions, whether later accepted, rejected, or
never reached by the round's own accept/reject walk) -- rejection doesn't
change what the target forward pass computed, only which of its outputs get
used downstream, so capturing everything and filtering at join/analysis
time (against proposals.jsonl's own per-position emission_source) is
simpler and safer than trying to replicate the accept/reject walk here.

Storage: NOT full hidden vectors (hidden_size is in the thousands; a 30k-
token AIME run would be gigabytes). A fixed random projection (m=128,
FIXED SEED so re-running is reproducible and multiple runs are directly
comparable) down to a small dimension, L2-normalized, stored as float16 --
enough to recover both cosine similarity (dot product of normalized
vectors) and a SimHash-style bit signature (sign bits of the SAME vector,
no separate computation or storage needed) for the recurrence-detection
pilot this exists to support. ~256 bytes/token (128 x fp16) -- a 30k-token
run is ~7.5MB, not gigabytes.

Phase 1 discipline, same as relaxation_trace.py: observation only, must
never influence generation, must never be able to crash it. Every public
entry point is wrapped so a bug here degrades to "this run has no hidden-
state trace," never to a crashed EngineCore.
"""

from __future__ import annotations

import os
import pathlib
import struct
import sys
import threading

import torch

_UID = os.getuid()
_DEST_FILE = pathlib.Path(f"/tmp/lossy-token-eff-hidden-state-trace-{_UID}")
_PROJECTION_DIM = 128
_PROJECTION_SEED = 20260810  # fixed: re-running reproduces the identical R, runs stay comparable
_MAX_REAL_BATCH = 8  # same warmup-filter threshold relaxation_trace.py uses, same reason

# Row format: round(uint32) pos_in_round(uint16) num_tokens_in_row(uint16,
# always 1 here -- one row per position) then _PROJECTION_DIM x float16.
# Fixed-width, not JSON: this is meant to hold tens of thousands of rows of
# a 128-float vector each; JSON per row would be both slower to write and
# ~4x the size for no benefit (nothing here needs to be human-read directly
# -- see join_hidden_states.py for turning it into something readable).
_ROW_HEADER = struct.Struct("<IH")  # round, pos_in_round


def _resolve_destination() -> pathlib.Path | None:
    try:
        raw = _DEST_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return pathlib.Path(raw) if raw else None


class _HiddenStateTracer:
    def __init__(self) -> None:
        self.path = _resolve_destination()
        self.enabled = self.path is not None
        self._round = 0
        self._lock = threading.Lock()
        self._projection: torch.Tensor | None = None  # lazily moved to the right device/dtype
        self._file = None
        if self.enabled:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self._file = self.path.open("wb")
                print(
                    f"[HIDDEN STATE TRACE] pid={os.getpid()} -> {self.path} "
                    f"(dim={_PROJECTION_DIM}, seed={_PROJECTION_SEED})",
                    file=sys.stderr,
                    flush=True,
                )
            except OSError as exc:
                print(f"[HIDDEN STATE TRACE] failed to open {self.path}: {exc}", file=sys.stderr, flush=True)
                self.enabled = False
                self._file = None

    def _get_projection(self, hidden_size: int, device: torch.device, dtype: torch.dtype) -> torch.Tensor:
        if self._projection is None or self._projection.shape[1] != hidden_size:
            gen = torch.Generator(device="cpu").manual_seed(_PROJECTION_SEED)
            r = torch.randn((_PROJECTION_DIM, hidden_size), generator=gen)
            self._projection = r.to(device=device, dtype=torch.float32)
        return self._projection.to(device=device, dtype=dtype)

    @torch.no_grad()
    def record(self, hidden_states: torch.Tensor) -> None:
        """hidden_states: [num_tokens, hidden_size], this round's target
        forward-pass output, one row per position processed (see module
        docstring -- includes positions later rejected/never-reached; that
        filtering happens at join time against proposals.jsonl)."""
        if not self.enabled:
            return
        try:
            num_tokens = hidden_states.shape[0]
            if num_tokens > _MAX_REAL_BATCH * 32:
                # A single real round is at most num_speculative_tokens+1
                # (7 here); anything far larger is a warmup/profiling pass
                # with synthetic sequences, same class of pass
                # relaxation_trace.py's own _MAX_REAL_BATCH check exists to
                # skip. Heuristic, not exact (no direct batch-size signal
                # at this call site the way relaxation_trace.py has via
                # num_draft_tokens) -- generous multiplier to avoid
                # accidentally skipping a real, unusually large round.
                return
            proj = self._get_projection(hidden_states.shape[-1], hidden_states.device, hidden_states.dtype)
            z = hidden_states.float() @ proj.float().T  # [num_tokens, _PROJECTION_DIM]
            z = torch.nn.functional.normalize(z, dim=-1)
            z16 = z.to(torch.float16).cpu().numpy()

            with self._lock:
                assert self._file is not None
                for pos in range(num_tokens):
                    self._file.write(_ROW_HEADER.pack(self._round, pos))
                    self._file.write(z16[pos].tobytes())
                self._file.flush()
                self._round += 1
        except Exception as exc:  # pragma: no cover -- Phase 1: never take down generation
            print(f"[HIDDEN STATE TRACE] record() failed, disabling: {exc}", file=sys.stderr, flush=True)
            self.enabled = False


TRACER = _HiddenStateTracer()
