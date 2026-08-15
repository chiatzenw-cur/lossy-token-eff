#!/usr/bin/env python3
"""Render GSM8K problems into Harmony prompts for trace collection.

Mirrors scripts/build_humaneval_prompts.py's structure and artifact contract
(same rendered_prompt.txt / candidate_index.jsonl / metadata.json /
source.json shape, same HF datasets-server rows API mechanism) -- new for
campaign/PLAN.md's 6-dataset sweep; openai/gsm8k has no custom loading
script either, so the datasets-server preview works directly, same as
HumanEval and AIME24 here.

GSM8K's reference answer is the trailing "#### <int>" line in the dataset's
own `answer` field (the full worked solution precedes it) -- extracted here
into metadata.json's reference_answer for anyone who wants to grade later;
this campaign's own scripts never read it (see campaign/PLAN.md's
"Grading / correctness" section -- out of scope for this deliverable).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import urllib.parse
import urllib.request

from openai_harmony import (
    Conversation,
    HarmonyEncodingName,
    Message,
    ReasoningEffort,
    Role,
    SystemContent,
    load_harmony_encoding,
)

FINAL_ANSWER_RE = re.compile(r"####\s*(-?[0-9][0-9,]*(?:\.[0-9]+)?)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", default="openai/gsm8k")
    parser.add_argument("--config", default="main")
    parser.add_argument("--split", default="test")
    parser.add_argument("--limit", type=int, default=0, help="Number of cases to render; 0 renders every fetched row.")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--conversation-date", default="2026-08-15")
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path("prompts/gsm8k"))
    parser.add_argument("--replace-output", action="store_true")
    parser.add_argument("--rows-json", type=pathlib.Path, default=None, help="Read rows from this file instead of fetching them.")
    parser.add_argument("--save-rows-json", type=pathlib.Path, default=None)
    parser.add_argument("--page-size", type=int, default=100, help="datasets-server rows-per-request cap.")
    return parser.parse_args()


def load_rows(args: argparse.Namespace) -> list[dict]:
    if args.rows_json is not None:
        text = args.rows_json.read_text(encoding="utf-8")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return [json.loads(line) for line in text.splitlines() if line.strip()]
        if isinstance(payload, list):
            return payload
        rows = payload["rows"]
        return [entry["row"] if isinstance(entry, dict) and "row" in entry else entry for entry in rows]

    rows: list[dict] = []
    offset = 0
    total = None
    while total is None or offset < total:
        if args.limit > 0 and offset >= args.limit:
            break
        query = urllib.parse.urlencode(
            {
                "dataset": args.dataset,
                "config": args.config,
                "split": args.split,
                "offset": offset,
                "length": args.page_size,
            }
        )
        url = f"https://datasets-server.huggingface.co/rows?{query}"
        with urllib.request.urlopen(url, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
        page = [entry["row"] if isinstance(entry, dict) and "row" in entry else entry for entry in payload["rows"]]
        rows.extend(page)
        total = payload.get("num_rows_total", len(rows))
        offset += len(page)
        if not page:
            break  # avoid an infinite loop if the server returns nothing further

    if args.save_rows_json:
        args.save_rows_json.parent.mkdir(parents=True, exist_ok=True)
        args.save_rows_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rows


def extract_reference(answer: str) -> str | None:
    match = FINAL_ANSWER_RE.search(answer or "")
    if not match:
        return None
    return match.group(1).replace(",", "")


def make_user_prompt(row: dict) -> str:
    question = str(row.get("question") or "").strip()
    return (
        f"{question}\n\n"
        "Please reason step by step, then give the final numeric answer on its "
        "own line as: #### <answer>"
    )


def make_conversation(prompt: str, reasoning_effort: str, conversation_date: str) -> Conversation:
    effort = ReasoningEffort(reasoning_effort.capitalize())
    system = SystemContent.new().with_reasoning_effort(effort).with_conversation_start_date(conversation_date)
    return Conversation.from_messages(
        [Message.from_role_and_content(Role.SYSTEM, system), Message.from_role_and_content(Role.USER, prompt)]
    )


def main() -> int:
    args = parse_args()
    if args.output.exists():
        if not args.replace_output:
            raise SystemExit(f"Output already exists: {args.output} (use --replace-output)")
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)

    encoding = load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)
    rows = load_rows(args)
    print(f"fetched {len(rows)} rows from {args.dataset}")

    count = len(rows) if args.limit <= 0 else min(args.limit, len(rows))
    index_rows = []
    for position in range(count):
        row = rows[position]
        if not row.get("question") or not row.get("answer"):
            continue
        reference = extract_reference(row["answer"])
        user_prompt = make_user_prompt(row)
        conversation = make_conversation(user_prompt, args.reasoning_effort, args.conversation_date)
        tokens = encoding.render_conversation_for_completion(conversation, Role.ASSISTANT)
        rendered = encoding.decode(tokens)

        case = f"case_{position + 1:03d}"
        case_dir = args.output / case
        case_dir.mkdir()

        metadata = {
            "source": "GSM8K",
            "source_dataset": args.dataset,
            "source_config": args.config,
            "source_split": args.split,
            "source_id": f"{args.dataset}:{args.split}:{position}",
            "tokenizer": "o200k_harmony",
            "harmony_encoding": "HARMONY_GPT_OSS",
            "reasoning_effort": args.reasoning_effort,
            "conversation_start_date": args.conversation_date,
            "input_tokens": len(tokens),
            "reference_answer": reference,
            "selected_for_pilot": True,
        }
        (case_dir / "rendered_prompt.txt").write_text(rendered, encoding="utf-8")
        (case_dir / "token_count.txt").write_text(f"{len(tokens)}\n", encoding="utf-8")
        (case_dir / "reference_output.txt").write_text(f"{reference or ''}\n", encoding="utf-8")
        (case_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (case_dir / "source.json").write_text(
            json.dumps(
                {"problem": user_prompt, "answer": reference, "full_solution": row.get("answer")},
                ensure_ascii=False, indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        index_rows.append({"case": case, **metadata})
        print(f"{case}: {len(tokens):>4} input tokens  answer={reference}")

    if not index_rows:
        raise SystemExit("no rows selected -- check the fetch")

    with (args.output / "candidate_index.jsonl").open("w", encoding="utf-8") as handle:
        for row in index_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    counts = [row["input_tokens"] for row in index_rows]
    (args.output / "selection_summary.json").write_text(
        json.dumps(
            {
                "dataset": args.dataset,
                "config": args.config,
                "split": args.split,
                "selected": len(index_rows),
                "reasoning_effort": args.reasoning_effort,
                "tokenizer": "o200k_harmony",
                "harmony_encoding": "HARMONY_GPT_OSS",
                "min_input_tokens": min(counts),
                "max_input_tokens": max(counts),
            },
            ensure_ascii=False, indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"\nwrote {len(index_rows)} cases to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
