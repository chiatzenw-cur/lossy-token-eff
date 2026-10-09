#!/usr/bin/env python3
"""Step 8, Block 0 (campaign/addendum/step8/GOAL.md): load checks as lane work lists.

Every check is an ordinary scripts/addendum_lane.py item (persistent_arm_replay.py, the campaign's
settings), written to its own run root `runs/addendum/step8_block0/<check>/` under a Killarney lane
root, so a check exercises exactly the path the campaign arms will take. Four lists, one per
Killarney lane copy (concurrent jobs never share a venv):

  K1  (a) R1-Distill-Llama-8B + EAGLE-3, (b) + Llama-3.2-1B draft_model   -- incl. grading samples
  K2  (c) Llama-3.1-8B-Instruct + EAGLE-3, and (f) on the V2 path          -- incl. grading samples
  K3  (c) + EAGLE-1, + Medusa, + Llama-3.2-1B draft_model, and (f) on the V1 path
  K4  (d) Qwen3-8B + DFlash / Thinking EAGLE-3 / Qwen3-1.7B, (e) GPT-OSS-20B + RedHatAI EAGLE-3, P-EAGLE

(f) strict-limit: each of the five rules at its strict point (mentored_dec / cactus 0, the other three
-inf) must reproduce the lossless run token for token (same case, seed, server seed); at its loosest
grid alpha it must differ and the server log must carry the patch's alpha line. The yuhuili EAGLE
heads declare max_position_embeddings 2048, so each gets a generation past 2048 positions with the
published config and with a copy whose config allows 65536 (the README deviation 19 fix).

  python3 scripts/step8_block0.py write     # campaign/addendum/step8/block0/K<n>.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from campaign_run import ALPHA_GRIDS, MODEL_FAMILIES, QWEN3_ROPE_SCALING, TOKEN_BUDGETS, model_flags  # noqa: E402

OUT = REPO / "campaign" / "addendum" / "step8" / "block0"
LOCAL = "/home/billxby/projects/aip-hongyanz/billxby/hf/local"
FIVE = ["mentored_dec", "cactus", "spec_casc_opt", "r_fuzzy", "spec_casc_tok"]
STRICT_POINT = {"mentored_dec": "0", "cactus": "0", "spec_casc_opt": "-inf", "r_fuzzy": "-inf", "spec_casc_tok": "-inf"}
LOOSEST = {m: f"{max(ALPHA_GRIDS[m]):g}" for m in FIVE}

R1, R1_E3 = MODEL_FAMILIES["r1llama"][0], MODEL_FAMILIES["r1llama"][1]
L31, L31_E3 = MODEL_FAMILIES["llama31"][0], MODEL_FAMILIES["llama31"][1]
L31_E1, L31_MEDUSA, L32_1B = "yuhuili/EAGLE-LLaMA3.1-Instruct-8B", "nebius/MEDUSA-Llama-3.1-8B-Instruct", "alpindale/Llama-3.2-1B-Instruct"
QWEN3 = MODEL_FAMILIES["qwen3"][0]
GPTOSS = MODEL_FAMILIES["gpt_oss_20b"][0]


def maxpos(repo: str) -> str:
    return f"{LOCAL}/{repo.split('/')[1]}-maxpos65536"


def item(check: str, dataset: str, method: str, alpha: str, cases: list[str], target: str, drafter: str,
         served: str, spec_method: str, max_new_tokens: int | None = None, rope: str = "",
         extra_env: dict | None = None) -> dict:
    env = {"SPEC_METHOD": spec_method, **(extra_env or {})}
    if target == GPTOSS:
        env["MENTORED_DEC_TEST_V1_ONLY"] = "1"  # GPT-OSS is V1-only (README deviation 5)
    return {
        "id": f"b0|{check}|{dataset}|{method}|{alpha}", "step": "8.0", "condition": f"step8_block0/{check}",
        "dataset": dataset, "method": method, "alpha": alpha, "seed": 0, "cases": cases,
        "prompt_root": f"prompts/{dataset}", "runs_subroot": f"runs/addendum/step8_block0/{check}",
        "max_new_tokens": max_new_tokens or TOKEN_BUDGETS[dataset],
        "model_flags": model_flags(target, drafter, served, rope),
        "num_spec": 6, "temperature": 1.0, "top_p": 1.0, "env": env,
    }


def c(*nums: int) -> list[str]:
    return [f"case_{n:03d}" for n in nums]


def strict_limit(check: str, dataset: str, target: str, drafter: str, served: str, spec_method: str,
                 rope: str = "") -> list[dict]:
    """(f): strict on case_001, each rule at its strict point and at its loosest alpha on the same case."""
    out = [item(check, dataset, "strict", "strict", c(1), target, drafter, served, spec_method, rope=rope)]
    for method in FIVE:
        for alpha in (STRICT_POINT[method], LOOSEST[method]):
            out.append(item(check, dataset, method, alpha, c(1), target, drafter, served, spec_method, rope=rope))
    return out


def lists() -> dict[str, list[dict]]:
    r1, l31 = "r1-distill-llama-8b", "llama31-8b-instruct"
    k1 = [
        # (a) + 5 graded GSM8K and 5 graded LiveCodeBench samples (think-block extraction), full budgets
        item("a_r1_eagle3", "gsm8k_r1llama", "strict", "strict", c(1, 2, 3, 4, 5), R1, R1_E3, r1, "eagle3"),
        item("a_r1_eagle3", "livecodebench_r1llama", "strict", "strict", c(1, 2, 3, 4, 5), R1, R1_E3, r1, "eagle3"),
        item("a_r1_eagle3", "gsm8k_r1llama", "mentored_dec", "0.75", c(1), R1, R1_E3, r1, "eagle3"),
        # past 2048 positions with the 65536-position copy (the published config is exercised above: LCB runs long)
        item("a_r1_eagle3_maxpos", "livecodebench_r1llama", "strict", "strict", c(1, 2), R1, maxpos(R1_E3), r1, "eagle3"),
        # (b)
        item("b_r1_llama1b", "gsm8k_r1llama", "strict", "strict", c(1, 2, 3, 4, 5), R1, L32_1B, r1, "draft_model"),
        item("b_r1_llama1b", "gsm8k_r1llama", "mentored_dec", "0.75", c(1), R1, L32_1B, r1, "draft_model"),
    ]
    k2 = [
        item("c_l31_eagle3", "gsm8k_llama31", "strict", "strict", c(1, 2, 3, 4, 5), L31, L31_E3, l31, "eagle3"),
        item("c_l31_eagle3", "livecodebench_llama31", "strict", "strict", c(1, 2, 3, 4, 5), L31, L31_E3, l31, "eagle3"),
        item("c_l31_eagle3_maxpos", "livecodebench_llama31", "strict", "strict", c(1, 2), L31, maxpos(L31_E3), l31, "eagle3"),
        *strict_limit("f_v2_l31_eagle3", "gsm8k_llama31", L31, L31_E3, l31, "eagle3"),
    ]
    k3 = [
        item("c_l31_eagle1", "gsm8k_llama31", "strict", "strict", c(1), L31, L31_E1, l31, "eagle"),
        item("c_l31_eagle1", "livecodebench_llama31", "strict", "strict", c(1, 2), L31, L31_E1, l31, "eagle"),
        item("c_l31_eagle1_maxpos", "livecodebench_llama31", "strict", "strict", c(1, 2), L31, maxpos(L31_E1), l31, "eagle"),
        item("c_l31_medusa", "gsm8k_llama31", "strict", "strict", c(1), L31, L31_MEDUSA, l31, "medusa"),
        item("c_l31_medusa", "livecodebench_llama31", "strict", "strict", c(1), L31, L31_MEDUSA, l31, "medusa"),
        item("c_l31_medusa", "gsm8k_llama31", "mentored_dec", "0.75", c(1), L31, L31_MEDUSA, l31, "medusa"),
        item("c_l31_llama1b", "gsm8k_llama31", "strict", "strict", c(1), L31, L32_1B, l31, "draft_model"),
        *strict_limit("f_v1_l31_llama1b", "gsm8k_llama31", L31, L32_1B, l31, "draft_model"),
    ]
    q, g = "qwen3-8b", "gpt-oss-20b"
    k4 = [
        item("d_q3_dflash", "gsm8k_qwen3", "strict", "strict", c(1), QWEN3, "RedHatAI/Qwen3-8B-speculator.dflash", q, "dflash", rope=QWEN3_ROPE_SCALING),
        item("d_q3_dflash", "gsm8k_qwen3", "mentored_dec", "0.75", c(1), QWEN3, "RedHatAI/Qwen3-8B-speculator.dflash", q, "dflash", rope=QWEN3_ROPE_SCALING),
        item("d_q3_thinking_eagle3", "gsm8k_qwen3", "strict", "strict", c(1), QWEN3, "RedHatAI/Qwen3-8B-Thinking-speculator.eagle3", q, "eagle3", rope=QWEN3_ROPE_SCALING),
        item("d_q3_thinking_eagle3", "gsm8k_qwen3", "mentored_dec", "0.75", c(1), QWEN3, "RedHatAI/Qwen3-8B-Thinking-speculator.eagle3", q, "eagle3", rope=QWEN3_ROPE_SCALING),
        item("d_q3_qwen17b", "gsm8k_qwen3", "strict", "strict", c(1), QWEN3, "Qwen/Qwen3-1.7B", q, "draft_model", rope=QWEN3_ROPE_SCALING),
        item("d_q3_qwen17b", "gsm8k_qwen3", "mentored_dec", "0.75", c(1), QWEN3, "Qwen/Qwen3-1.7B", q, "draft_model", rope=QWEN3_ROPE_SCALING),
        item("e_gptoss_rh_eagle3", "gsm8k", "strict", "strict", c(1), GPTOSS, "RedHatAI/gpt-oss-20b-speculator.eagle3", g, "eagle3"),
        item("e_gptoss_rh_eagle3", "gsm8k", "mentored_dec", "0.75", c(1), GPTOSS, "RedHatAI/gpt-oss-20b-speculator.eagle3", g, "eagle3"),
        # block 7's drafter, checked now while the node is warm (P-EAGLE drafts in parallel: V1 runner)
        item("p_q3_peagle", "gsm8k_qwen3", "strict", "strict", c(1), QWEN3, "RedHatAI/Qwen3-8B-speculator.peagle", q, "eagle3", rope=QWEN3_ROPE_SCALING,
             extra_env={"PARALLEL_DRAFTING": "true"}),
    ]
    # retest (2026-10-03 17:30Z): Qwen3-1.7B as draft_model crashed in the drafter's CUDA-graph capture right after
    # loading an AOT-compiled graph from the shared compile cache (illegal memory access); the same architecture's
    # Qwen3-0.6B (addendum step 4.3) compiled into that cache. Same items with a compile cache of their own.
    own = {"VLLM_CACHE_ROOT": "/scratch/billxby/vllm_cache_step8/qwen3-8b__qwen3-1.7b"}
    k1r = [
        item("d_q3_qwen17b_owncache", "gsm8k_qwen3", "strict", "strict", c(1), QWEN3, "Qwen/Qwen3-1.7B", q, "draft_model",
             rope=QWEN3_ROPE_SCALING, extra_env=own),
        item("d_q3_qwen17b_owncache", "gsm8k_qwen3", "mentored_dec", "0.75", c(1), QWEN3, "Qwen/Qwen3-1.7B", q, "draft_model",
             rope=QWEN3_ROPE_SCALING, extra_env=own),
    ]
    # acceptance vs position (2026-10-03 17:45Z): R1 + its EAGLE-3 head gave l_bar 2.4-3.3 on GSM8K (<= 717 tokens) but
    # 1.17 at 4139 tokens and 0.40 at 12000 (LiveCodeBench). The head's published config stops at 2048 positions. Same
    # case and seed at four budgets (fresh server each: lossless decoding with a fixed seed repeats the prefix), so the
    # differences between budgets give accepted tokens per position segment.
    k1p = []
    for ds, case in (("livecodebench_r1llama", 2), ("aime24_r1llama", 1)):
        for budget in (1024, 2048, 4096, 8192):
            it = item(f"prof_r1_eagle3_maxpos_{budget}", ds, "strict", "strict", c(case), R1, maxpos(R1_E3), r1, "eagle3",
                      max_new_tokens=budget)
            it["env"]["VLLM_CACHE_ROOT"] = "/scratch/billxby/vllm_cache_step8/r1-distill-llama-8b__eagle3"
            k1p.append(it)
    # rerun of every R1 check with the tokenizer fix (README deviation 33): R1's declared tokenizer class dropped the
    # spaces of every prompt under transformers 5.18 (0 of 350 prompts matched tokenizer.json), so a_* / b_* / prof_*
    # above ran on mis-encoded prompts and are kept only as the record of that bug
    tok = {"TOKENIZER": f"{LOCAL}/DeepSeek-R1-Distill-Llama-8B-tokenizer-fast",
           "VLLM_CACHE_ROOT": "/scratch/billxby/vllm_cache_step8/r1-distill-llama-8b__eagle3"}
    tok1b = {**tok, "VLLM_CACHE_ROOT": "/scratch/billxby/vllm_cache_step8/r1-distill-llama-8b__llama32-1b"}
    k1t = [
        item("a2_r1_eagle3_maxpos", "gsm8k_r1llama", "strict", "strict", c(1, 2, 3, 4, 5), R1, maxpos(R1_E3), r1, "eagle3", extra_env=tok),
        item("a2_r1_eagle3_maxpos", "livecodebench_r1llama", "strict", "strict", c(1, 2, 3, 4, 5), R1, maxpos(R1_E3), r1, "eagle3", extra_env=tok),
        item("a2_r1_eagle3_maxpos", "gsm8k_r1llama", "mentored_dec", "0.75", c(1), R1, maxpos(R1_E3), r1, "eagle3", extra_env=tok),
        item("b2_r1_llama1b", "gsm8k_r1llama", "strict", "strict", c(1, 2, 3, 4, 5), R1, L32_1B, r1, "draft_model", extra_env=tok1b),
        item("b2_r1_llama1b", "gsm8k_r1llama", "mentored_dec", "0.75", c(1), R1, L32_1B, r1, "draft_model", extra_env=tok1b),
    ]
    for ds, case in (("livecodebench_r1llama", 2), ("aime24_r1llama", 1)):
        for budget in (1024, 2048, 4096, 8192):
            k1t.append(item(f"prof2_r1_eagle3_maxpos_{budget}", ds, "strict", "strict", c(case), R1, maxpos(R1_E3), r1,
                            "eagle3", max_new_tokens=budget, extra_env=tok))
    # rerun (2026-10-03 17:50Z): (1) the -inf arms exited 2 -- the lane passed "--x-alpha -inf" and argparse took
    # "-inf" for an option (now "--x-alpha=-inf"); (2) cactus 0.35 / r_fuzzy 0.25 on Llama-3.1 + EAGLE-3 crashed with
    # the published 2048-position head config (README deviation 31): the V2-path checks again with the 65536 copy and
    # the pair's own compile cache; (3) the GPT-OSS check needed prompts/gsm8k on Killarney (copied).
    l31c = {"VLLM_CACHE_ROOT": "/scratch/billxby/vllm_cache_step8/llama31-8b-instruct__eagle3"}
    k2f = [dict(i, env={**i["env"], **l31c}) for i in
           strict_limit("f2_v2_l31_eagle3_maxpos", "gsm8k_llama31", L31, maxpos(L31_E3), l31, "draft_model")]
    for i in k2f:
        i["env"]["SPEC_METHOD"] = "eagle3"
    k2f += [i for i in k3 if i["id"].startswith("b0|f_v1_l31_llama1b")]  # skip-if-done: only the failed ones run
    k2f += [i for i in k4 if i["id"].startswith("b0|e_gptoss")]
    # the V2 check job (cascade/cluster/step8_v2_check.sbatch, 5914176) passed "-inf" as a separate argument for the two
    # new rules' strict points; those two arms, with a lossless run in the same job, on the lane left on the 796e3c85 file
    q3 = ("Qwen/Qwen3-8B", "RedHatAI/Qwen3-8B-speculator.eagle3", "qwen3-8b")
    k4v = [item("v2fix_strict_point", "gsm8k_qwen3", "strict", "strict", c(1), *q3, "eagle3", max_new_tokens=2048,
                rope=QWEN3_ROPE_SCALING),
           item("v2fix_strict_point", "gsm8k_qwen3", "spec_casc_tok_lt", "-inf", c(1), *q3, "eagle3", max_new_tokens=2048,
                rope=QWEN3_ROPE_SCALING)]
    oh = item("v2fix_strict_point", "gsm8k_qwen3", "spec_casc_opt_head", "-inf", c(1), *q3, "eagle3", max_new_tokens=2048,
              rope=QWEN3_ROPE_SCALING)
    oh["id"] += "|b0.15"
    oh["extra_flags"] = ["--spec-casc-opt-head-beta=0.15"]
    oh["params_dir"] = "alphaneginf_beta0.15"
    k4v.append(oh)
    # determinism check (2026-10-03 19:35Z): on the V2 path the lossless arm gave 166 tokens when its server compiled
    # cold (first item on a fresh compile cache) and 142 when it loaded the cache, the same 142 as all five rules at
    # their strict points. Lossless again, twice, on the now-warm cache of f2_v2: both must give the 142-token output.
    k3w = []
    for rep in (1, 2):
        it = dict(next(i for i in k2f if i["id"] == "b0|f2_v2_l31_eagle3_maxpos|gsm8k_llama31|strict|strict"))
        it = {**it, "id": f"b0|f3_v2_strict_warm{rep}|gsm8k_llama31|strict|strict",
              "condition": f"step8_block0/f3_v2_strict_warm{rep}",
              "runs_subroot": f"runs/addendum/step8_block0/f3_v2_strict_warm{rep}", "env": dict(it["env"])}
        k3w.append(it)
    # Block 6 check (2026-10-04 13:40Z): spec_casc_tok_lt 0.15 and 0.2 gave byte-identical outputs on all 240 cases
    # (spec_casc_opt_head on 238). Plausible for a drafter whose drafts are almost always the target's argmax or far
    # below it (lossless l_bar 1.5), but the mask must be shown live: much wider heads (0.55, 0.8) on case_001-030
    # must change the outputs and raise l_bar.
    fixenv = {"VLLM_CACHE_ROOT": "/scratch/billxby/vllm_cache_step8/qwen3-8b__eagle3-fix"}
    k3x = [item(f"fixcheck_tok_lt_{a}", "gsm8k_qwen3", "spec_casc_tok_lt", a, [f"case_{n:03d}" for n in range(1, 31)],
                *q3, "eagle3", rope=QWEN3_ROPE_SCALING, extra_env=fixenv) for a in ("0.55", "0.8")]
    return {"K1": k1, "K2": k2, "K3": k3, "K4": k4, "K1r": k1r, "K1p": k1p, "K1t": k1t, "K2f": k2f, "K4v": k4v,
            "K3w": k3w, "K3x": k3x}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cmd", choices=["write"])
    parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for lane, items in lists().items():
        (OUT / f"{lane}.json").write_text(json.dumps({"items": items, "hold_minutes": 0}, indent=1) + "\n", encoding="utf-8")
        print(f"{lane}: {len(items)} items, {sum(len(i['cases']) for i in items)} runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
