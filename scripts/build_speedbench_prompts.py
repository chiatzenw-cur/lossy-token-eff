#!/usr/bin/env python3
"""Build the SPEED-Bench qualitative prompt set for GPT-OSS (addendum step 7; campaign/addendum/README.md).

Source: nvidia/SPEED-Bench (Abramovich et al., ICML 2026, arXiv:2604.09557), config `qualitative`:
880 prompts, 80 in each of 11 categories. The parquet is read from --parquet (downloaded at the pinned
--revision; its sha256 goes into selection_summary.json). 494 of its rows ship as placeholders
("FULL BENCHMARK DATA SHOULD BE FETCHED FROM THE SOURCE USING SPECDEC_BENCH"); they are resolved with
NVIDIA's own code, `SPEEDBench._fetch_all_turns_data` from Model-Optimizer's examples/specdec_bench
(--specdec-bench points at a checkout of it), exactly as its prepare_data.py would. The 208 rows from
`cais/hle` need a Hugging Face token with access to that gated dataset; without one they are skipped
and listed as pending in cases.csv, and a rerun with a token adds them (existing case dirs are kept).

Case order: SPEED-Bench's own stratified interleaving (specdec_bench `_stratified_select`: round-robin
over the categories in first-appearance order, the dataset's order within a category), so
case_001..case_{11k} hold exactly k prompts of every category. The first 40 cases are the per-arm time
estimate sample; the first 440 are the 40-per-category subset.

Like the repo's MT-Bench prompts: turn 1 only (the later turns of the 167 multi-turn rows are kept in
metadata.json as `later_turns`), rendered as a Harmony conversation (o200k_harmony, reasoning effort
medium, conversation start date 2026-08-01, default system message; SPEED-Bench's own system_prompt is
None). Output mirrors the other prompt roots (rendered_prompt.txt / metadata.json / source.json /
reference_output.txt / token_count.txt / candidate_index.jsonl / selection_summary.json), with the
SPEED-Bench category in metadata.json.

The prompt texts are NOT committed: the repo is public, SPEED-Bench is under the NVIDIA Evaluation
Dataset License, and its rows come from third-party sources (HLE asks that its questions stay off the
open web). prompts/speedbench*/ is gitignored; --cases-csv (committed) records case -> question_id,
category, source, src_id, sha256 of rendered_prompt.txt and token counts, so a rebuild can be checked.

  python scripts/build_speedbench_prompts.py --parquet qualitative.parquet \\
      --specdec-bench Model-Optimizer/examples/specdec_bench --output prompts/speedbench \\
      --cases-csv campaign/addendum/speedbench/cases.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
import sys

from openai_harmony import (
    Conversation,
    HarmonyEncodingName,
    Message,
    ReasoningEffort,
    Role,
    SystemContent,
    load_harmony_encoding,
)

PLACEHOLDER = "FULL BENCHMARK DATA SHOULD BE FETCHED FROM THE SOURCE USING SPECDEC_BENCH"
HLE = "cais/hle"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--parquet", type=pathlib.Path, required=True, help="qualitative/test-00000-of-00001.parquet")
    parser.add_argument("--revision", default="454f88454792dfa3ccfd7ef15fff248efde44cd1", help="nvidia/SPEED-Bench revision the parquet came from.")
    parser.add_argument("--specdec-bench", type=pathlib.Path, required=True, help="Model-Optimizer/examples/specdec_bench checkout.")
    parser.add_argument("--specdec-bench-commit", default="", help="Model-Optimizer commit, recorded in selection_summary.json.")
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path("prompts/speedbench"))
    parser.add_argument("--cases-csv", type=pathlib.Path, default=pathlib.Path("campaign/addendum/speedbench/cases.csv"))
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--conversation-date", default="2026-08-01")
    parser.add_argument("--skip-hle", action="store_true", help="Do not try the gated cais/hle rows (no token).")
    return parser.parse_args()


def stratified_order(rows: list[dict]) -> list[dict]:
    """specdec_bench SPEEDBench._stratified_select with n = len(rows)."""
    by_cat: dict[str, list[dict]] = {}
    for row in rows:
        by_cat.setdefault(row["category"], []).append(row)
    lists = list(by_cat.values())
    out = []
    for i in range(max(len(c) for c in lists)):
        for c in lists:
            if i < len(c):
                out.append(c[i])
    return out


def render(encoding, prompt: str, effort: str, date: str) -> tuple[str, int]:
    system = SystemContent.new().with_reasoning_effort(ReasoningEffort(effort.capitalize())).with_conversation_start_date(date)
    conversation = Conversation.from_messages(
        [Message.from_role_and_content(Role.SYSTEM, system), Message.from_role_and_content(Role.USER, prompt)]
    )
    tokens = encoding.render_conversation_for_completion(conversation, Role.ASSISTANT)
    return encoding.decode(tokens), len(tokens)


def main() -> int:
    args = parse_args()
    import pyarrow.parquet as pq

    sys.path.insert(0, str(args.specdec_bench.resolve()))
    from specdec_bench.datasets.speed import SPEEDBench  # NVIDIA's resolver (Apache-2.0)

    resolver = SPEEDBench.__new__(SPEEDBench)  # skip __init__: it loads and resolves the whole split at once
    resolver.external_datasets = {}

    rows = pq.read_table(args.parquet).to_pylist()
    ordered = stratified_order(rows)
    encoding = load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)
    args.output.mkdir(parents=True, exist_ok=True)

    index_rows, csv_rows, pending = [], [], []
    for i, row in enumerate(ordered, start=1):
        case = f"case_{i:03d}"
        masked = row["turns"][0].startswith(PLACEHOLDER)
        info = {
            "case": case, "question_id": row["question_id"], "category": row["category"],
            "sub_category": row["sub_category"], "source": row["source"], "src_id": row["src_id"],
            "difficulty": row["difficulty"], "multiturn": bool(row["multiturn"]), "n_turns": len(row["turns"]),
            "resolved_by": "specdec_bench" if masked else "parquet",
        }
        case_dir = args.output / case
        if masked and HLE in row["source"] and args.skip_hle and not (case_dir / "rendered_prompt.txt").is_file():
            pending.append(case)
            csv_rows.append({**info, "status": "pending_hle_token", "input_tokens": "", "sha256_rendered": ""})
            continue
        if (case_dir / "rendered_prompt.txt").is_file():
            rendered = (case_dir / "rendered_prompt.txt").read_text(encoding="utf-8")
            meta = json.loads((case_dir / "metadata.json").read_text(encoding="utf-8"))
            if meta["question_id"] != row["question_id"]:
                raise SystemExit(f"{case_dir} holds question {meta['question_id']}, expected {row['question_id']}")
            n_tokens = meta["input_tokens"]
        else:
            turns = list(row["turns"])
            if masked:
                try:
                    turns = resolver._fetch_all_turns_data(dict(row, turns=turns), "qualitative")["turns"]
                except Exception as exc:  # gated dataset without a token, network errors
                    if HLE in row["source"]:
                        pending.append(case)
                        csv_rows.append({**info, "status": f"pending_hle_token ({type(exc).__name__})", "input_tokens": "", "sha256_rendered": ""})
                        continue
                    raise
                if any(t.startswith(PLACEHOLDER) for t in turns):
                    raise SystemExit(f"{row['question_id']}: placeholder left after resolution")
            rendered, n_tokens = render(encoding, turns[0], args.reasoning_effort, args.conversation_date)
            meta = {
                "source": "SPEED-Bench",
                "source_dataset": "nvidia/SPEED-Bench",
                "source_config": "qualitative",
                "source_revision": args.revision,
                "source_id": f"nvidia/SPEED-Bench:qualitative:{row['question_id']}",
                **{k: info[k] for k in ("question_id", "category", "sub_category", "difficulty", "multiturn", "n_turns", "resolved_by")},
                "speed_source": row["source"],
                "speed_src_id": row["src_id"],
                "turn_used": 1,
                "later_turns": turns[1:],
                "tokenizer": "o200k_harmony",
                "harmony_encoding": "HARMONY_GPT_OSS",
                "reasoning_effort": args.reasoning_effort,
                "conversation_start_date": args.conversation_date,
                "input_tokens": n_tokens,
                "reference_answer": None,
            }
            case_dir.mkdir(parents=True, exist_ok=True)
            (case_dir / "rendered_prompt.txt").write_text(rendered, encoding="utf-8")
            (case_dir / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            (case_dir / "source.json").write_text(json.dumps({"problem": turns[0], "answer": None}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            (case_dir / "reference_output.txt").write_text("\n", encoding="utf-8")
            (case_dir / "token_count.txt").write_text(f"{n_tokens}\n", encoding="utf-8")
        sha = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        index_rows.append({"case": case, **{k: v for k, v in meta.items() if k != "later_turns"}})
        csv_rows.append({**info, "status": "built", "input_tokens": n_tokens, "sha256_rendered": sha})

    with (args.output / "candidate_index.jsonl").open("w", encoding="utf-8") as handle:
        for r in index_rows:
            handle.write(json.dumps(r, ensure_ascii=False) + "\n")
    parquet_sha = hashlib.sha256(args.parquet.read_bytes()).hexdigest()
    (args.output / "selection_summary.json").write_text(json.dumps({
        "dataset": "nvidia/SPEED-Bench", "config": "qualitative", "revision": args.revision,
        "parquet_sha256": parquet_sha, "specdec_bench_commit": args.specdec_bench_commit,
        "order": "specdec_bench _stratified_select interleaving (round-robin over categories, first-appearance order)",
        "turn_used": 1, "reasoning_effort": args.reasoning_effort, "conversation_start_date": args.conversation_date,
        "tokenizer": "o200k_harmony", "harmony_encoding": "HARMONY_GPT_OSS",
        "n_rows": len(ordered), "n_built": len(index_rows), "pending_hle_token": pending,
    }, indent=2) + "\n", encoding="utf-8")
    args.cases_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.cases_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"{len(index_rows)} built, {len(pending)} pending (cais/hle token) of {len(ordered)}; parquet sha256 {parquet_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
