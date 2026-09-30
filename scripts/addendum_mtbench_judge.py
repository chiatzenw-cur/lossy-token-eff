#!/usr/bin/env python3
"""Addendum step 1.9 (campaign/addendum/README.md): MT-Bench single-answer
grading of the campaign's MT-Bench completions, turn 1 only, with the
FastChat llm_judge prompts (prompts/mtbench_judge/, fetched 2026-09-29 from
lm-sys/FastChat main: judge_prompts.jsonl, mt_bench/question.jsonl,
mt_bench/reference_answer/gpt-4.jsonl). Categories math/reasoning/coding use
`single-math-v1` with the GPT-4 reference answer (FastChat's NEED_REF_CATS),
every other category `single-v1`; the rating is parsed from `[[rating]]`.

Judge: the strongest Claude model (claude-fable-5-1) through the Message
Batches API (50% price, asynchronous). Differences from FastChat's GPT-4
judge, recorded in every output row: no temperature (Claude Fable 5.1 rejects
sampling parameters; thinking is always on, depth set by --effort), and no
server-side refusal fallback (the Batches API rejects it): a refused request
is recorded as verdict=refusal, not re-routed to another model.

  python3 scripts/addendum_mtbench_judge.py plan      # runs to judge, question mapping check, cost estimate; no API call
  python3 scripts/addendum_mtbench_judge.py submit    # create the batch (needs ANTHROPIC_API_KEY)
  python3 scripts/addendum_mtbench_judge.py collect   # wait for it, parse ratings, write the CSVs
  python3 scripts/addendum_mtbench_judge.py direct [--cancel-batch]  # same requests through the Messages API
                                                      # (standard price), then the CSVs; resumable

"Every arm" = strict and the five campaign rules at every alpha that has
runs (single-knob parameter directories), both targets, every seed present.
A run whose output never reaches an answer (GPT-OSS: no final channel;
Qwen3: no text outside <think> blocks) is not sent to the judge: it gets
score 1 and verdict=no_answer (the reader saw nothing); summaries report the
mean with and without those runs.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import sys
import time

REPO = pathlib.Path(__file__).resolve().parent.parent
RUNS = REPO / "runs"
JUDGE_DIR = REPO / "prompts" / "mtbench_judge"
OUT = REPO / "campaign" / "addendum" / "analysis"
STATE = OUT / "mtbench_judge_batches.json"
FIVE = ["mentored_dec", "cactus", "spec_casc_opt", "r_fuzzy", "spec_casc_tok"]
NEED_REF_CATS = {"math", "reasoning", "coding"}
SPECIAL = re.compile(r"<\|[^|>]*\|>")
# Claude Fable 5.1 on the Batches API: $10/$50 per MTok standard, half in a batch.
PRICE_IN, PRICE_OUT = 5.0, 25.0


def answer_text(text: str, target: str) -> str:
    """The part of the completion a user would read (same split as scripts/addendum_analysis.py)."""
    if target == "gpt-oss-20b":
        i = text.find("<|channel|>final")
        if i < 0:
            return ""
        tail = text[i:]
        tail = tail.split("<|message|>", 1)[1] if "<|message|>" in tail else ""
        return SPECIAL.sub("", tail).strip()
    if "</think>" not in text:
        return ""
    parts, inside, pos = [], False, 0
    first_open, first_close = text.find("<think>"), text.find("</think>")
    inside = first_close >= 0 and (first_open < 0 or first_close < first_open)
    for m in re.finditer(r"</?think>", text):
        if not inside:
            parts.append(text[pos:m.start()])
        inside = m.group(0) == "<think>"
        pos = m.end()
    if not inside:
        parts.append(text[pos:])
    return SPECIAL.sub("", "".join(parts)).strip()


def load_judge_data():
    prompts = {d["name"]: d for d in map(json.loads, (JUDGE_DIR / "judge_prompts.jsonl").open())}
    questions = [json.loads(l) for l in (JUDGE_DIR / "question.jsonl").open()]
    refs = {d["question_id"]: d["choices"][0]["turns"][0]
            for d in map(json.loads, (JUDGE_DIR / "reference_answer_gpt-4.jsonl").open())}
    by_text = {q["turns"][0].strip(): q for q in questions}
    return prompts, by_text, refs


def collect_runs(seeds: list[str] | None = None) -> list[dict]:
    prompts, by_text, refs = load_judge_data()
    runs = []
    for ds, target in (("mtbench", "gpt-oss-20b"), ("mtbench_qwen3", "qwen3-8b")):
        for run_json in sorted((RUNS / ds).glob("*/*/case_*/seed_*/run.json")):
            run_dir = run_json.parent
            case, params, method = run_dir.parent.name, run_dir.parent.parent.name, run_dir.parent.parent.parent.name
            if method != "strict" and (method not in FIVE or "_" in params):
                continue
            run = json.loads(run_json.read_text(encoding="utf-8"))
            if run.get("status") != "ok":
                continue
            if seeds is not None and run_dir.name.removeprefix("seed_") not in seeds:
                continue
            case_dir = REPO / "prompts" / ds / case
            question = json.loads((case_dir / "source.json").read_text(encoding="utf-8"))["problem"]
            category = json.loads((case_dir / "metadata.json").read_text(encoding="utf-8"))["category"]
            q = by_text.get(question.strip())
            if q is None:
                # HuggingFaceH4/mt_bench_prompts carries a typo in case_007 ("reprompt top-5 words" for
                # FastChat q121's "returns top-5 words"): match by similarity for the id/reference only;
                # the judge still sees the question text the model was asked.
                import difflib
                best = max(by_text, key=lambda t: difflib.SequenceMatcher(None, t, question.strip()).ratio())
                if difflib.SequenceMatcher(None, best, question.strip()).ratio() < 0.95:
                    raise SystemExit(f"no FastChat question matches {ds}/{case}")
                q = by_text[best]
            alpha = "strict" if method == "strict" else f"{float(params.removeprefix('alpha').replace('neg', '-')):g}"
            answer = answer_text((run_dir / "output.txt").read_text(encoding="utf-8", errors="replace"), target)
            version = "single-math-v1" if category in NEED_REF_CATS else "single-v1"
            fields = {"question": question, "answer": answer}
            if version == "single-math-v1":
                fields["ref_answer_1"] = refs[q["question_id"]]
            runs.append({
                "relpath": str(run_dir.relative_to(RUNS)), "target": target, "method": method, "alpha": alpha,
                "case": case, "seed": run_dir.name.removeprefix("seed_"), "category": category,
                "question_id": q["question_id"], "prompt_version": version, "answer_chars": len(answer),
                "finish_reason": run.get("finish_reason"),
                "system": prompts[version]["system_prompt"],
                "user": prompts[version]["prompt_template"].format(**fields),
            })
    return runs


def custom_id(i: int) -> str:
    return f"r{i:06d}"


KEY_FILE = pathlib.Path.home() / ".config" / "lossy-token-eff" / "judge.env"


def load_key_file() -> None:
    """KEY=VALUE lines from ~/.config/lossy-token-eff/judge.env into the environment (values never printed;
    a variable already set in the environment wins)."""
    import os
    if not KEY_FILE.is_file():
        return
    for line in KEY_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip().removeprefix("export ").strip()
        os.environ.setdefault(name, value.strip().strip('"').strip("'"))


def cmd_plan(args) -> int:
    runs = collect_runs(args.seeds)
    to_judge = [r for r in runs if r["answer_chars"] > 0]
    chars_in = sum(len(r["system"]) + len(r["user"]) for r in to_judge)
    tok_in = chars_in / 3.5
    tok_out = len(to_judge) * args.est_output_tokens
    cost = tok_in / 1e6 * PRICE_IN + tok_out / 1e6 * PRICE_OUT
    by = {}
    for r in runs:
        by.setdefault((r["target"], r["seed"]), 0)
        by[(r["target"], r["seed"])] += 1
    print(f"{len(runs)} MT-Bench runs (all 160 cases map to a FastChat question); {len(runs) - len(to_judge)} have no answer")
    print("runs per (target, seed):", by)
    print(f"to judge: {len(to_judge)} requests, ~{tok_in / 1e6:.1f}M input tokens, ~{tok_out / 1e6:.1f}M output tokens "
          f"(assumed {args.est_output_tokens}/request incl. thinking) -> ~${cost:.0f} with {args.model} on the Batches API")
    return 0


def cmd_submit(args) -> int:
    load_key_file()
    import anthropic
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    runs = [r for r in collect_runs(args.seeds) if r["answer_chars"] > 0]
    state = json.loads(STATE.read_text()) if STATE.is_file() else {"batches": []}
    done = {rel for b in state["batches"] for rel in b["ids"].values()}
    runs = [r for r in runs if r["relpath"] not in done]
    if not runs:
        print("nothing new to judge")
        return 0
    client = anthropic.Anthropic()
    ids, requests = {}, []
    start = sum(len(b["ids"]) for b in state["batches"])
    for i, r in enumerate(runs, start=start):
        cid = custom_id(i)
        ids[cid] = r["relpath"]
        requests.append(Request(custom_id=cid, params=MessageCreateParamsNonStreaming(
            model=args.model, max_tokens=16000, system=r["system"],
            output_config={"effort": args.effort},
            messages=[{"role": "user", "content": r["user"]}],
        )))
    batch = client.messages.batches.create(requests=requests)
    state["batches"].append({"id": batch.id, "model": args.model, "effort": args.effort,
                             "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "ids": ids})
    STATE.write_text(json.dumps(state, indent=1) + "\n")
    print(f"created batch {batch.id} with {len(requests)} requests ({args.model}, effort {args.effort})")
    return 0


RATING = re.compile(r"\[\[(\d+\.?\d*)\]\]")
RATING_LOOSE = re.compile(r"\[(\d+\.?\d*)\]")
DIRECT_CACHE = OUT / "mtbench_judge_direct.jsonl"  # one line per run judged by `direct`


def verdict_of(msg, model: str, effort: str, api: str) -> dict:
    row = {"judge_model": model, "judge_effort": effort, "judge_api": api,
           "judge_model_served": msg.model, "stop_reason": msg.stop_reason}
    if msg.stop_reason == "refusal":
        row.update(verdict="refusal", score=None)
    else:
        text = "".join(block.text for block in msg.content if block.type == "text")
        m = RATING.search(text) or RATING_LOOSE.search(text)
        row.update(verdict="ok" if m else "parse_error", score=float(m.group(1)) if m else None, judge_text=text[-600:])
    return row


def direct_results() -> dict[str, dict]:
    out = {}
    if DIRECT_CACHE.is_file():
        for line in DIRECT_CACHE.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                out[row["relpath"]] = row
    return out


def cmd_direct(args) -> int:
    """Judge through the Messages API (streamed, --workers at a time) every run not scored yet by a batch
    or an earlier direct call; --cancel-batch first cancels unfinished batches in the state file. Same
    prompts, model and effort as `submit`; standard (not batch) price. Resumable."""
    load_key_file()
    import anthropic
    from concurrent.futures import ThreadPoolExecutor, as_completed

    client = anthropic.Anthropic(max_retries=8)
    state = json.loads(STATE.read_text()) if STATE.is_file() else {"batches": []}
    if args.cancel_batch:
        for b in state["batches"]:
            if b.get("canceled"):
                continue
            if client.messages.batches.retrieve(b["id"]).processing_status != "ended":
                client.messages.batches.cancel(b["id"])
                b["canceled"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                print(f"canceled batch {b['id']}", flush=True)
        STATE.write_text(json.dumps(state, indent=1) + "\n")
    done = direct_results()
    runs = [r for r in collect_runs(args.seeds) if r["answer_chars"] > 0 and r["relpath"] not in done]
    print(f"{len(runs)} run(s) to judge directly ({len(done)} already in {DIRECT_CACHE.name})", flush=True)

    def judge(r: dict) -> dict:
        with client.messages.stream(model=args.model, max_tokens=16000, system=r["system"],
                                    output_config={"effort": args.effort},
                                    messages=[{"role": "user", "content": r["user"]}]) as stream:
            msg = stream.get_final_message()
        return {"relpath": r["relpath"], **verdict_of(msg, args.model, args.effort, "messages"),
                "input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens,
                "t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    tok_in = tok_out = failed = 0
    with ThreadPoolExecutor(args.workers) as pool, DIRECT_CACHE.open("a", encoding="utf-8") as out:
        futures = {pool.submit(judge, r): r for r in runs}
        for i, fut in enumerate(as_completed(futures), start=1):
            try:
                row = fut.result()
            except anthropic.APIError as exc:  # after the SDK's own retries; rerun `direct` to retry
                failed += 1
                print(f"{futures[fut]['relpath']}: {type(exc).__name__}: {str(exc)[:160]}", flush=True)
                continue
            out.write(json.dumps(row) + "\n")
            out.flush()
            tok_in += row["input_tokens"]
            tok_out += row["output_tokens"]
            if i % 50 == 0 or i == len(runs):
                cost = tok_in / 1e6 * 2 * PRICE_IN + tok_out / 1e6 * 2 * PRICE_OUT
                print(f"{i}/{len(runs)} judged, {failed} failed, ~${cost:.2f} so far", flush=True)
    if failed:
        print(f"{failed} request(s) failed; run `direct` again to retry them")
        return 1
    args.no_wait = True
    return cmd_collect(args)


def cmd_collect(args) -> int:
    load_key_file()
    import anthropic
    import numpy as np

    client = anthropic.Anthropic()
    state = json.loads(STATE.read_text())
    runs = {r["relpath"]: r for r in collect_runs(args.seeds)}
    scored = {}
    def retrying(fn, what: str):
        """Transient API trouble (5xx, e.g. a 503 'credential validation failed', or a dropped network) must
        not lose a submitted batch: keep retrying for up to 6 hours; 4xx errors still raise."""
        deadline = time.time() + 6 * 3600
        while True:
            try:
                return fn()
            except (anthropic.APIConnectionError, anthropic.InternalServerError) as exc:
                if time.time() > deadline:
                    raise
                print(f"{what}: transient {type(exc).__name__}: {str(exc)[:120]} -- retrying in 60 s", flush=True)
                time.sleep(60)
            except anthropic.APIStatusError as exc:
                if exc.status_code < 500 or time.time() > deadline:
                    raise
                print(f"{what}: HTTP {exc.status_code} {str(exc)[:120]} -- retrying in 60 s", flush=True)
                time.sleep(60)

    for b in state["batches"]:
        while True:
            batch = retrying(lambda: client.messages.batches.retrieve(b["id"]), "retrieve")
            if batch.processing_status == "ended":
                break
            if getattr(args, "no_wait", False) and not b.get("canceled"):
                batch = None  # still running: use what `direct` judged instead
                break
            print(f"batch {b['id']}: {batch.processing_status}, {batch.request_counts.processing} processing", flush=True)
            time.sleep(60)
        if batch is None:
            continue
        for result in retrying(lambda: list(client.messages.batches.results(b["id"])), "results"):
            rel = b["ids"][result.custom_id]
            if result.result.type != "succeeded":
                row = {"judge_model": b["model"], "judge_effort": b["effort"], "judge_api": "batch",
                       "judge_model_served": "", "stop_reason": "", "verdict": f"batch_{result.result.type}", "score": None}
            else:
                row = verdict_of(result.result.message, b["model"], b["effort"], "batch")
            scored[rel] = row
    for rel, row in direct_results().items():  # direct calls fill whatever the batches did not score
        if rel not in scored or scored[rel].get("score") is None:
            scored[rel] = row
    rows = []
    for rel, r in sorted(runs.items()):
        s = scored.get(rel)
        if r["answer_chars"] == 0:
            s = {"verdict": "no_answer", "score": 1.0, "judge_model": "", "judge_effort": "", "judge_api": "",
                 "judge_model_served": "", "stop_reason": ""}
        if s is None:
            continue
        rows.append({k: r[k] for k in ("relpath", "target", "method", "alpha", "case", "seed", "category",
                                        "question_id", "prompt_version", "answer_chars", "finish_reason")} | s)
    fields = ["relpath", "target", "method", "alpha", "case", "seed", "category", "question_id", "prompt_version",
              "answer_chars", "finish_reason", "judge_model", "judge_effort", "judge_api", "judge_model_served",
              "stop_reason", "verdict", "score"]
    with (OUT / "mtbench_judge.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    rng = np.random.default_rng(20261001)
    summary = []
    arms = sorted({(r["target"], r["method"], r["alpha"], r["seed"]) for r in rows})
    for target, method, alpha, seed in arms:
        cell = [r for r in rows if (r["target"], r["method"], r["alpha"], r["seed"]) == (target, method, alpha, seed)]
        scores = np.array([r["score"] for r in cell if r["score"] is not None], float)
        answered = np.array([r["score"] for r in cell if r["score"] is not None and r["verdict"] == "ok"], float)
        row = {"target": target, "method": method, "alpha": alpha, "seed": seed, "n_runs": len(cell),
               "n_scored": len(scores), "n_no_answer": sum(r["verdict"] == "no_answer" for r in cell),
               "n_refusal": sum(r["verdict"] == "refusal" for r in cell),
               "n_parse_error": sum(r["verdict"] == "parse_error" for r in cell)}
        for name, x in (("mean_score", scores), ("mean_score_answered_only", answered)):
            if len(x):
                boot = x[rng.integers(0, len(x), size=(10000, len(x)))].mean(axis=1)
                row[name] = round(float(x.mean()), 4)
                row[f"{name}_ci_lo"] = round(float(np.percentile(boot, 2.5)), 4)
                row[f"{name}_ci_hi"] = round(float(np.percentile(boot, 97.5)), 4)
        summary.append(row)
    with (OUT / "mtbench_judge_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(dict.fromkeys(k for r in summary for k in r)), lineterminator="\n")
        writer.writeheader()
        writer.writerows(summary)
    print(f"wrote mtbench_judge.csv ({len(rows)} rows) and mtbench_judge_summary.csv ({len(summary)} arms)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default="claude-fable-5-1")
    parser.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--est-output-tokens", type=int, default=1500)
    parser.add_argument("--seeds", nargs="+", default=["0"], help="Request seeds to judge (default: 0, the campaign's runs).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, fn in (("plan", cmd_plan), ("submit", cmd_submit), ("collect", cmd_collect)):
        sub.add_parser(name).set_defaults(fn=fn)
    p = sub.add_parser("direct")
    p.add_argument("--cancel-batch", action="store_true", help="Cancel unfinished batches in the state file first.")
    p.add_argument("--workers", type=int, default=16)
    p.set_defaults(fn=cmd_direct)
    args = parser.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
