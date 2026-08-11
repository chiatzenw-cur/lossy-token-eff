"""Per-proposal-token trace, shared by every relaxed-acceptance patch
(mentored-dec, cactus, spec-casc-opt, r-fuzzy, spec-casc-tok, ...). Not
upstream vLLM.

Ported from the sibling lossy-spec-decode-repetition repo's lenience_trace.py
and renamed: that name predated this repo's multi-method taxonomy and no
longer describes what the module does (it was never lenience-specific -- see
the "lam" field history below, which already outgrew the name before this
port). Behaviour is unchanged except where a method-specific counterfactual
branch was added (spec-casc-tok) or a field was generalised (lenience_factor
-> scalar_multiplier).

Why per proposal and not per round
----------------------------------
A speculative round can accept several draft tokens at once, so a per-round mean
acceptance cannot say *which* token started a divergence. Corruption onset has to
be attributed to an individual emitted token, which means recording every
proposal: its target and draft probabilities, the uniform draw it was tested
against, and — critically — whether the strict rule would have rejected it.

`lossy_only` is the whole point. It is computable from a single relaxed run,
because strict acceptance is a deterministic function of the same (p, q, u) the
relaxed rule already used. Three counterfactual shapes are supported, one per
method family:

1. Scalar multiplier on p/q (mentored-dec): computed inline here.
       strict_accept = (p / q)              >= u
       lossy_accept  = (p / (lam*q))        >= u
       lossy_only    = lossy_accept and not strict_accept

2. Binary switch between whole-q (always accept) and whole-p (strict test)
   (spec-casc-opt, r-fuzzy): the caller passes the per-token decision in as
   `defer_mask` directly, computed from the full vocab distributions in the
   patch's own rejection_sample() -- this module combines it with the strict
   test it already computes, rather than re-deriving each method's deferral
   rule here.

3. Full-vocab boost/blend of the drafted token specifically (CACTUS,
   spec-casc-tok): the caller passes the method's own alpha and this module
   recomputes the method's formula for the drafted token's row inline (see
   the `cactus_alpha` and `casc_tok_alpha` branches below). Ensemble (a pure
   elementwise blend of q and p, same shape as CACTUS's boost but with no
   special-casing of the drafted token) would fit here too if added later.

So the strict arm does not need to be instrumented at all; each relaxed run
carries its own counterfactual.

Phase 1 is observation only. Nothing here alters acceptance, because changing
the trajectory while measuring it would destroy the failure being studied.

Enabling
--------
Written by the server launcher, uid-scoped AND repo-scoped like every other
knob this repo passes to EngineCore (which is spawned with a sanitised
environment, so env vars cannot be used -- see rejection_sampler.py's
module-level comment for why this is a file and not an env var):

    /tmp/lossy-token-eff-trace-$UID   ->  destination .jsonl path

Absent or empty disables tracing with near-zero overhead. The path is
repo-scoped (not the sibling repo's lossy-spec-decode-trace- prefix) so a
server from either repo cannot pick up the other's stale trace destination if
both ever run on this box at once.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import threading

import torch

_TRACE_PATH_FILE = pathlib.Path(f"/tmp/lossy-token-eff-trace-{os.getuid()}")
# Flush every round: the engine is SIGKILLed at teardown, so a large buffer
# loses its tail. The first collected run in the sibling repo lost ~65 rows
# this way.
_FLUSH_EVERY = 1  # rounds
_MAX_REAL_BATCH = 8  # above this, the call is a profiling/warmup pass
_EPS = 1e-12
_PLACEHOLDER = -1  # vllm PLACEHOLDER_TOKEN_ID


def _resolve_destination() -> pathlib.Path | None:
    try:
        raw = _TRACE_PATH_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return pathlib.Path(raw) if raw else None


class _Tracer:
    def __init__(self) -> None:
        self.path = _resolve_destination()
        self.enabled = self.path is not None
        self._rows: list[dict] = []
        self._round = 0
        self._emitted = 0  # running output position
        self._skipped_warmup = 0
        self._lock = threading.Lock()
        # Lazily loaded on first decode, not here: importing/loading the
        # o200k_harmony encoding is fast (~tens of ms) but there's no reason
        # to pay it in __init__ if a run somehow never calls record().
        self._encoding = None
        self._encoding_load_failed = False
        if self.enabled:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # Truncate: one engine serves one request under the fresh-server
            # protocol, so a stale file would silently merge two trajectories.
            self.path.write_text("", encoding="utf-8")
            print(
                f"[RELAXATION TRACE] pid={os.getpid()} -> {self.path}",
                file=sys.stderr,
                flush=True,
            )

    def _decode_token(self, token_id: int | None) -> str | None:
        """Best-effort human-readable text for one token id -- gpt-oss-20b's
        own o200k_harmony encoding (hardcoded: every run in this repo serves
        that one model, same assumption analysis/semantic_guard/'s own
        reconstruction scripts already make). Never raises: Phase 1 tracing
        must not be able to take down generation just by trying to decode a
        token for a human to read later (same principle as the trace_anomaly
        handling below, for the same reason -- a single-token decode_utf8
        call can legitimately fail on an orphaned multi-byte lead byte, see
        analysis/semantic_guard/count_relaxed_only_hesitation.py's own note
        on this). Falls back to a lossy per-token decode (replacement
        character for anything that still doesn't stand alone) rather than
        returning None on that specific, expected failure mode; returns None
        only if the encoding itself never loaded or token_id is None.
        """
        if token_id is None:
            return None
        if self._encoding is None:
            if self._encoding_load_failed:
                return None
            try:
                from openai_harmony import HarmonyEncodingName, load_harmony_encoding

                self._encoding = load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)
            except Exception as exc:  # pragma: no cover -- defensive, see docstring
                self._encoding_load_failed = True
                print(f"[RELAXATION TRACE] token-text decoding disabled: {exc}", file=sys.stderr, flush=True)
                return None
        try:
            return self._encoding.decode_utf8([token_id])
        except Exception:
            try:
                return self._encoding.decode([token_id])
            except Exception:
                return None

    def _flush(self) -> None:
        if not self._rows:
            return
        with self.path.open("a", encoding="utf-8") as handle:
            for row in self._rows:
                handle.write(json.dumps(row, separators=(",", ":")) + "\n")
        self._rows.clear()

    @torch.no_grad()
    def record(
        self,
        *,
        draft_token_ids: torch.Tensor,      # [num_tokens]
        draft_probs: torch.Tensor | None,   # [num_tokens, V]
        target_probs: torch.Tensor,         # [num_tokens, V]
        uniform_probs: torch.Tensor,        # [num_tokens]
        recovered_token_ids: torch.Tensor,  # [num_tokens]
        bonus_token_ids: torch.Tensor,      # [batch, 1]
        output_token_ids: torch.Tensor,     # [batch, max_spec_len+1]
        cu_num_draft_tokens: torch.Tensor,  # [batch]
        num_draft_tokens: list[int],
        scalar_multiplier: float,
        # [num_tokens] bool; spec-casc-opt, r-fuzzy. MUST be the BASE
        # method's own decision (e.g. r-fuzzy's JSD test alone), never a
        # mask already OR'd with an on-top guard's contribution (window_guard_mask,
        # or a token-marker guard's own mask) -- lossy_ok below is derived
        # from this parameter as strict_ok | (~defer_mask), which collapses
        # to strict_ok wherever defer_mask is True FOR ANY REASON. Passing a
        # guard-merged mask here makes lossy_would_accept silently equal
        # strict_would_accept at every guarded position by construction,
        # turning "did the guard change anything vs the base method" into an
        # unconditional zero no matter what the guard actually does -- caught
        # once already in r_fuzzy_window_entropy_guard's own patch (see its
        # module comment / git history), worth getting right by convention.
        defer_mask: torch.Tensor | None = None,
        cactus_alpha: float | None = None,
        casc_tok_alpha: float | None = None,
        relaxation_method: str = "mentored_dec",
        window_guard_mask: torch.Tensor | None = None,  # [num_tokens] bool; r_fuzzy_window_entropy_guard only
        # [num_tokens] bool; any token-marker (hesitation-word-id) guard --
        # r_fuzzy_semantic_guard, r_fuzzy_semantic_guard_v2,
        # spec_casc_tok_semantic_guard. Purely informational, same
        # window_guard_mask convention: never fed into strict_ok/lossy_ok
        # above, only recorded so a guard's own effect can be read back
        # later. MUST be the guard's OWN mask alone (e.g.
        # _semantic_guard_mask(draft_token_ids)), never OR'd into whatever
        # was passed as defer_mask/casc_tok_alpha -- see the defer_mask
        # comment above for exactly the failure mode that produces (an
        # r_fuzzy_semantic_guard patch generation predating this parameter
        # did fold its guard into defer_mask directly, which made
        # lossy_would_accept collapse to strict_would_accept at every
        # guarded position by construction; fixed alongside this parameter's
        # introduction, not before).
        token_marker_guard_mask: torch.Tensor | None = None,
    ) -> None:
        if not self.enabled:
            return
        # vLLM profiles and captures CUDA graphs with a large dummy batch before
        # serving anything. Those passes reach this sampler with hundreds of
        # synthetic sequences and would otherwise dominate the trace: the first
        # collected run (sibling repo) had 2048 of its 3570 rows from two
        # warmup calls of 1024 dummy sequences each. Real serving here is one
        # request per engine.
        if len(num_draft_tokens) > _MAX_REAL_BATCH:
            self._skipped_warmup += 1
            return

        dt = draft_token_ids.to(torch.int64)
        p = target_probs.gather(1, dt.unsqueeze(1)).squeeze(1).float()
        if draft_probs is None:
            q = torch.ones_like(p)
        else:
            q = draft_probs.gather(1, dt.unsqueeze(1)).squeeze(1).float()
        u = uniform_probs.float()

        ratio = torch.where(q > 0, p / q, torch.full_like(p, float("inf")))
        strict_ok = (q > 0) & (ratio >= u)
        if defer_mask is not None:
            # spec-casc-opt, r-fuzzy: pi_rej == q (accept unconditionally) at
            # non-deferred positions; the deferred positions run exactly the
            # strict test already computed above. The caller's kernel made
            # this same decision, so this must track it exactly for
            # `actually_accepted` (from output_token_ids, below) to agree
            # with `lossy_would_accept` on every row -- a mismatch would mean
            # the trace and the kernel disagree about what ran.
            lossy_ok = strict_ok | (~defer_mask.to(torch.bool))
        elif cactus_alpha is not None:
            # CACTUS (Hao & Mou 2026): boost the drafted token's own
            # acceptance via gamma_x = min(p(x) + sqrt(2*alpha*p(x)*(1-p(x))), 1),
            # then run the ordinary ratio test with gamma_x in place of p(x).
            # clamp_min guards the sqrt: p*(1-p) is never negative for a valid
            # probability, but the multiply can dip a hair below 0 in fp32.
            gamma = (p + (2.0 * cactus_alpha * p * (1.0 - p)).clamp_min(0.0).sqrt()).clamp(max=1.0)
            gamma_ratio = torch.where(q > 0, gamma / q, torch.full_like(p, float("inf")))
            lossy_ok = (q > 0) & (gamma_ratio >= u)
        elif casc_tok_alpha is not None:
            # spec-casc-tok (Narasimhan et al. 2025 appendix): pi_rej(v) =
            # q(v) + eta*p(v) for v in the trusted top set A = {u: p(u) >=
            # (1-alpha)*max(p)}, else eta*p(v), where eta = 1 - sum_{A} q(u).
            # Only the drafted token x's row of pi_rej is needed for the
            # accept test, but A and eta are full-vocab reductions, computed
            # here the same way the patch's own rejection_sample() does.
            if draft_probs is None:
                # No q to relax against: A/eta collapse to their q==0 limit
                # (eta==1, pi_rej==p everywhere), same as the patch's own
                # NO_DRAFT_PROBS branch -- this is just the strict test.
                lossy_ok = strict_ok
            else:
                target_top1 = target_probs.max(dim=1, keepdim=True).values
                in_top_set = target_probs >= (1.0 - casc_tok_alpha) * target_top1
                eta = 1.0 - (draft_probs * in_top_set).sum(dim=1)
                x_in_top_set = in_top_set.gather(1, dt.unsqueeze(1)).squeeze(1)
                pi_rej_x = torch.where(x_in_top_set, q + eta * p, eta * p)
                casc_tok_ratio = torch.where(
                    q > 0, pi_rej_x / q, torch.full_like(p, float("inf"))
                )
                lossy_ok = (q > 0) & (casc_tok_ratio >= u)
        else:
            lossy_ok = (q > 0) & (ratio / scalar_multiplier >= u)

        # How far down the target's ranking the drafted token sits, and how
        # peaked the target is there. Rank 0 means the target's own argmax.
        rank = (target_probs > p.unsqueeze(1)).sum(dim=1)
        top1 = target_probs.max(dim=1).values.float()

        # Full-distribution features. The per-token p and q say whether *this*
        # proposal was lucky; these say whether the drafter and target disagree
        # about the whole next-token distribution, which is the thing expected
        # to drift before a corruption.
        log_t = torch.log(target_probs.clamp_min(_EPS))
        ent = -(target_probs * log_t).sum(dim=1).float()
        if draft_probs is None:
            # Greedy drafting: q is one-hot, so its entropy is 0 and the KLs are
            # degenerate. Recorded as null rather than a misleading number.
            draft_ent = kl_pq = kl_qp = tv = None
        else:
            log_d = torch.log(draft_probs.clamp_min(_EPS))
            draft_ent = (-(draft_probs * log_d).sum(dim=1)).float().tolist()
            # KL(p||q): how much the drafter misses where the target has mass.
            kl_pq = (target_probs * (log_t - log_d)).sum(dim=1).float().tolist()
            # KL(q||p): how much mass the drafter puts where the target has none
            # -- the direction that produces wrong tokens the verifier must catch.
            kl_qp = (draft_probs * (log_d - log_t)).sum(dim=1).float().tolist()
            # Bounded companion: KL is unstable when either side has near-zero
            # mass, total variation is not, so a spike in one but not the other
            # is informative rather than numerical noise.
            tv = (0.5 * (target_probs - draft_probs).abs().sum(dim=1)).float().tolist()

        dt_l = dt.tolist()
        p_l, q_l, u_l = p.tolist(), q.tolist(), u.tolist()
        s_l, l_l = strict_ok.tolist(), lossy_ok.tolist()
        rank_l, top1_l, ent_l = rank.tolist(), top1.tolist(), ent.tolist()
        rec_l = recovered_token_ids.to(torch.int64).tolist()
        out = output_token_ids.tolist()
        bonus = bonus_token_ids.reshape(-1).tolist()
        wg_l = window_guard_mask.tolist() if window_guard_mask is not None else None
        tmg_l = token_marker_guard_mask.tolist() if token_marker_guard_mask is not None else None

        with self._lock:
            start = 0
            for b, n in enumerate(num_draft_tokens):
                run = 0          # accepted draft tokens so far this round
                rejected = False
                for j in range(n):
                    i = start + j
                    emitted = out[b][j]
                    if emitted == _PLACEHOLDER:
                        # Slot never evaluated (an earlier position was rejected).
                        break
                    accepted = emitted == dt_l[i]
                    if accepted:
                        run += 1
                        source = "accepted_draft"
                    else:
                        rejected = True
                        source = "recovered" if emitted == rec_l[i] else "other"

                    # p/q/target_rank/target_top1_shortfall below ALWAYS describe
                    # the DRAFT PROPOSAL (draft_token_id), not the emitted token
                    # -- that's what the accept/reject test operates on, so it's
                    # the correct thing for THOSE fields to mean. But when
                    # accepted is False, draft_token_id != emitted_token_id: the
                    # proposal was rejected and something else got emitted
                    # (recovery, or "other"). A caller reading p/target_rank off
                    # a non-accepted row as if it characterised the EMITTED
                    # token is reading the rejected proposal's numbers by
                    # mistake -- exactly the conflation that produced a wrong
                    # "recovered tokens are deep in the target's tail" claim
                    # in the sibling repo (the *proposals that got rejected*
                    # were deep in the tail; the recovery kernel then
                    # explicitly excludes that exact token from resampling,
                    # so the recovered token is a different one entirely and
                    # needs its own p/rank). Compute that separately, only
                    # when needed (accepted rows already have draft==emitted,
                    # so it would be redundant there).
                    emitted_p = emitted_rank = emitted_shortfall = None
                    trace_anomaly = None
                    if not accepted:
                        # These two conditions are believed invariant (see the
                        # comments below), but Phase 1 is observation only --
                        # "nothing here alters acceptance" has to also mean
                        # nothing here can ever CRASH generation, or a bug in
                        # this file's own bookkeeping becomes an outage in
                        # the thing it's supposed to be a side-channel on.
                        # First hit: case_033/spec-casc-opt took down its
                        # EngineCore twice in a row on a hard assert here
                        # (fp32 read-back of an emitted token whose Gumbel-max
                        # recovery selection ran in fp64 is the leading
                        # suspect -- a token can be legitimately selected with
                        # a true probability that then rounds to exactly 0.0
                        # in the fp32 tensor this module reads back). Recorded
                        # as an anomaly flag instead of raised, so the run
                        # completes and the anomaly is still visible in the
                        # trace for follow-up, rather than losing the whole
                        # generation to an observation-code bug.
                        if source == "recovered" and emitted == dt_l[i]:
                            # The recovery kernel is supposed to exclude
                            # draft_token_id from its candidate pool (see
                            # sample_recovered_tokens_kernel's NO_DRAFT_PROBS
                            # branch), so this means the trace and the kernel
                            # have desynced.
                            trace_anomaly = "recovered_emitted_rejected_draft_token"
                        emitted_p_t = target_probs[i, emitted]
                        emitted_p = round(float(emitted_p_t), 8)
                        if emitted_p <= 0:
                            trace_anomaly = (trace_anomaly or "") + "|zero_prob_emission"
                            print(
                                f"[RELAXATION TRACE] anomaly: emitted token {emitted} has "
                                f"target_probs()={emitted_p} at output_position={self._emitted} "
                                f"(round={self._round}, batch={b}) -- recording, not raising",
                                file=sys.stderr,
                                flush=True,
                            )
                        emitted_rank = int((target_probs[i] > emitted_p_t).sum())
                        emitted_shortfall = round(top1_l[i] - emitted_p, 6)

                    self._rows.append(
                        {
                            "round": self._round,
                            "batch": b,
                            "pos_in_round": j,
                            # position of THIS token in the final output stream
                            "output_position": self._emitted,
                            "draft_token_id": dt_l[i],
                            "emitted_token_id": emitted,
                            # Human-readable text for the two ids above --
                            # the ORIGINAL drafted proposal and the token
                            # that actually made it into the output (equal,
                            # decoded twice, on accepted rows; different on
                            # recovered/other rows -- exactly the "what was
                            # proposed vs what actually got emitted" pair
                            # for a rejected position). Best-effort, never
                            # raises -- see _decode_token's own docstring.
                            "draft_token_text": self._decode_token(dt_l[i]),
                            "emitted_token_text": self._decode_token(emitted),
                            # p/q/target_rank/target_top1_shortfall: the DRAFT
                            # PROPOSAL's own metrics -- see the comment above.
                            "p": round(p_l[i], 8),
                            "q": round(q_l[i], 8),
                            "p_over_q": round(p_l[i] / q_l[i], 6) if q_l[i] > 0 else None,
                            "u": round(u_l[i], 8),
                            # whatever scalar knob this arm's relaxation used
                            # (mentored-dec's lambda in (0,1], spec-casc-opt's
                            # alpha over all reals, cactus/spec-casc-tok's
                            # alpha >= 0, ...) -- see relaxation_method for
                            # which one it is and rejection_sample() in the
                            # relevant patch for the units.
                            "relaxation_param": scalar_multiplier,
                            "relaxation_method": relaxation_method,
                            "strict_would_accept": bool(s_l[i]),
                            "lossy_would_accept": bool(l_l[i]),
                            "actually_accepted": bool(accepted),
                            # the counterfactual that matters: emitted only
                            # because the bar was lowered
                            "lossy_only_accepted": bool(accepted and l_l[i] and not s_l[i]),
                            # r_fuzzy_window_entropy_guard only; null for every
                            # other method. True iff the rolling entropy window
                            # forced this position to the strict test.
                            # "guard_changed_decision" (whether that forcing
                            # actually flipped the outcome vs plain lossy) is
                            # window_guard_active AND lossy_would_accept AND NOT
                            # strict_would_accept -- derivable from these three
                            # fields together, not stored as its own column.
                            "window_guard_active": None if wg_l is None else bool(wg_l[i]),
                            # any token-marker guard (see the parameter's own
                            # comment above); null for every method without
                            # one. "guard_changed_decision" is derivable the
                            # same way window_guard_active's is: this AND
                            # lossy_would_accept AND NOT strict_would_accept.
                            "token_marker_guard_active": None if tmg_l is None else bool(tmg_l[i]),
                            "emission_source": source,
                            "target_rank": int(rank_l[i]),
                            "target_top1_prob": round(top1_l[i], 6),
                            # top1_prob - p: how far the DRAFT PROPOSAL's own
                            # probability falls short of the target's single
                            # best guess. Exactly 0 when the proposal IS top1
                            # (target_rank == 0). NOT p(1) - p(2) -- this repo
                            # never records the runner-up's probability, so a
                            # "how contested was 1st vs 2nd" reading is not
                            # something this field (or any other) can support.
                            "target_top1_shortfall": round(top1_l[i] - p_l[i], 6),
                            # The EMITTED token's own metrics -- only meaningful
                            # (and only computed) when accepted is False, since
                            # accepted rows already have draft_token_id ==
                            # emitted_token_id (use p/target_rank/
                            # target_top1_shortfall above for those). Null on
                            # accepted rows, not a duplicate of p/target_rank.
                            "emitted_p": emitted_p,
                            "emitted_target_rank": emitted_rank,
                            "emitted_top1_shortfall": emitted_shortfall,
                            "trace_anomaly": trace_anomaly,
                            "target_entropy": round(ent_l[i], 5),
                            "draft_entropy": None if draft_ent is None else round(draft_ent[i], 5),
                            "kl_target_draft": None if kl_pq is None else round(kl_pq[i], 5),
                            "kl_draft_target": None if kl_qp is None else round(kl_qp[i], 5),
                            "tv_distance": None if tv is None else round(tv[i], 5),
                            "consecutive_accepted_length": run,
                        }
                    )
                    self._emitted += 1
                    if rejected:
                        break
                if not rejected and run == n:
                    # Every draft token survived, so the bonus token is emitted.
                    self._rows.append(
                        {
                            "round": self._round,
                            "batch": b,
                            "pos_in_round": n,
                            "output_position": self._emitted,
                            "draft_token_id": None,
                            "emitted_token_id": bonus[b] if b < len(bonus) else None,
                            "draft_token_text": None,
                            "emitted_token_text": self._decode_token(bonus[b] if b < len(bonus) else None),
                            "emission_source": "bonus",
                            "consecutive_accepted_length": run,
                            "relaxation_param": scalar_multiplier,
                            "relaxation_method": relaxation_method,
                        }
                    )
                    self._emitted += 1
                start += n
            self._round += 1
            if self._round % _FLUSH_EVERY == 0:
                self._flush()

    def close(self) -> None:
        if self.enabled:
            with self._lock:
                self._flush()


TRACER = _Tracer()

import atexit  # noqa: E402

atexit.register(TRACER.close)
