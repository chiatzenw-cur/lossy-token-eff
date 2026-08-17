#!/usr/bin/env python3
"""Convert an already-built GPT-OSS/Harmony prompt set into a Qwen3 prompt
set, re-rendered through Qwen3's own chat template instead of Harmony.

Why re-render from rendered_prompt.txt rather than write 6 new per-dataset
builders: every dataset's *real* user-facing content (including
longbench_v2's ~35k-token source document, which is NOT preserved anywhere
in source.json/metadata.json -- only baked into the Harmony rendering) is
already sitting in prompts/<dataset>/case_*/rendered_prompt.txt, wrapped in
Harmony's own literal-text markup (`<|start|>system<|message|>...<|end|>
<|start|>user<|message|>{content}<|end|><|start|>assistant`). Extracting the
user message and feeding it through Qwen3's chat_template is exact (same
question, same instructions, same wrapper text each dataset's own builder
wrote) and dataset-agnostic -- one script instead of six, and no risk of
drifting from the original wrapper wording. Confirmed single-turn (one
`<|start|>user<|message|>` block) for all 6 datasets before writing this.

Output mirrors the original artifact contract (rendered_prompt.txt /
metadata.json / source.json / reference_output.txt / token_count.txt /
candidate_index.jsonl / selection_summary.json) so campaign_run.py /
campaign_report.py / the grade_*.py scripts work against a Qwen3 prompt root
exactly like a Harmony one -- only tokenizer/harmony_encoding/input_tokens
in metadata.json (and the qwen3-specific `chat_format`/`enable_thinking`
fields) differ from the source.

enable_thinking=True by default: GPT-OSS's own prompts used
reasoning_effort=medium (real chain-of-thought before the answer), so
leaving Qwen3's hybrid-thinking mode on is the comparable setting, not the
odd one out. Qwen3's template does not force an opening `<think>` tag into
the rendered text either way -- the model opens it itself if it reasons.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil

USER_MESSAGE = re.compile(r"<\|start\|>user<\|message\|>(.*?)<\|end\|><\|start\|>assistant", re.DOTALL)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=pathlib.Path, required=True, help="Existing Harmony prompt root, e.g. prompts/gsm8k.")
    parser.add_argument("--dest", type=pathlib.Path, required=True, help="Output Qwen3 prompt root, e.g. prompts/gsm8k_qwen3.")
    parser.add_argument("--tokenizer", default="Qwen/Qwen3-8B")
    parser.add_argument("--count", type=int, default=12, help="Convert case_001..case_{count:03d} only (campaign never uses more).")
    parser.add_argument("--enable-thinking", dest="enable_thinking", action="store_true", default=True)
    parser.add_argument("--no-enable-thinking", dest="enable_thinking", action="store_false")
    parser.add_argument("--replace-dest", action="store_true")
    return parser.parse_args()


def extract_user_message(rendered: str) -> str:
    match = USER_MESSAGE.search(rendered)
    if not match:
        raise ValueError("no <|start|>user<|message|>...<|end|><|start|>assistant block found -- not a single-turn Harmony render")
    return match.group(1)


def main() -> int:
    args = parse_args()
    if args.dest.exists():
        if not args.replace_dest:
            raise SystemExit(f"{args.dest} already exists (use --replace-dest)")
        shutil.rmtree(args.dest)
    args.dest.mkdir(parents=True)

    from transformers import AutoTokenizer  # deferred: slow import, only needed once we're committed to running

    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)

    index_rows = []
    for i in range(1, args.count + 1):
        case = f"case_{i:03d}"
        src_dir = args.source / case
        if not src_dir.is_dir():
            print(f"skip {case}: not present in {args.source}")
            continue
        rendered_src = (src_dir / "rendered_prompt.txt").read_text(encoding="utf-8")
        user_content = extract_user_message(rendered_src)

        rendered = tokenizer.apply_chat_template(
            [{"role": "user", "content": user_content}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=args.enable_thinking,
        )
        token_count = len(tokenizer(rendered, add_special_tokens=False)["input_ids"])

        src_metadata = json.loads((src_dir / "metadata.json").read_text(encoding="utf-8"))
        metadata = dict(src_metadata)
        metadata["tokenizer"] = args.tokenizer
        metadata.pop("harmony_encoding", None)
        metadata["chat_format"] = "qwen3"
        metadata["enable_thinking"] = args.enable_thinking
        metadata["input_tokens"] = token_count
        metadata["ported_from"] = str(args.source / case)

        dest_dir = args.dest / case
        dest_dir.mkdir(parents=True)
        (dest_dir / "rendered_prompt.txt").write_text(rendered, encoding="utf-8")
        (dest_dir / "token_count.txt").write_text(f"{token_count}\n", encoding="utf-8")
        (dest_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # source.json / reference_output.txt carry no Harmony-specific content -- copy verbatim.
        shutil.copyfile(src_dir / "source.json", dest_dir / "source.json")
        if (src_dir / "reference_output.txt").is_file():
            shutil.copyfile(src_dir / "reference_output.txt", dest_dir / "reference_output.txt")

        index_rows.append({"case": case, **metadata})
        print(f"{case}: {token_count:>6} input tokens (was {src_metadata.get('input_tokens')} harmony tokens)")

    if not index_rows:
        raise SystemExit("no cases converted -- check --source/--count")

    with (args.dest / "candidate_index.jsonl").open("w", encoding="utf-8") as handle:
        for row in index_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    counts = [row["input_tokens"] for row in index_rows]
    (args.dest / "selection_summary.json").write_text(
        json.dumps(
            {
                "source": str(args.source),
                "selected": len(index_rows),
                "tokenizer": args.tokenizer,
                "chat_format": "qwen3",
                "enable_thinking": args.enable_thinking,
                "min_input_tokens": min(counts),
                "max_input_tokens": max(counts),
            },
            ensure_ascii=False, indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"\nwrote {len(index_rows)} cases to {args.dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
