#!/usr/bin/env python3
"""Grade archived HumanEval runs by execution (pass@1), not text matching.

Unlike AIME, HumanEval has no single scalar answer to string-match: a
"correct" completion is one whose code satisfies the problem's hidden unit
tests. That means actually running model-generated code, which needs the
same care as every other execution harness for this benchmark family (see
OpenAI's own human-eval repo) plus one extra reason to take it seriously
here specifically: this repo studies repetition loops under relaxed
speculative decoding, and a candidate that inherited a degenerate loop from
its own generation is exactly the kind of thing that can hang. Every
candidate therefore runs in its own subprocess with a wall-clock timeout and
a memory cap, never via in-process exec().

Prompt convention (see prompts/humaneval/build_humaneval_prompts.py): the
model is asked to reproduce the WHOLE function -- signature, docstring, and
body -- not just complete a body left open in the prompt. So the graded
candidate is the fenced ```python block extracted from the model's own
output, standalone, not the prompt's signature + a completion glued on.

Extraction mirrors grade_aime.py's convention: split on the Harmony final-
channel marker (a run that never reaches it is scored `no_final_channel`,
never `failed` -- the distinction matters for the same reason it does for
AIME), then take the LAST fenced code block in that channel, robust to any
prose the model adds before or after the block.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import resource
import subprocess
import sys
import textwrap
from collections import defaultdict
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from answer_extraction import final_segment  # noqa: E402 -- covers both Harmony (GPT-OSS) and Qwen3's </think> convention

# Trailing markers that can leak into the final segment (a generation that
# ran past its own turn-end token before the server truncated it). Harmony's
# is "<|end|>"; Qwen3's chat template closes an assistant turn with
# "<|im_end|>" instead -- trim whichever is present.
END_MARKERS = ("<|end|>", "<|im_end|>")
CODE_BLOCK = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)

DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MEMORY_LIMIT_MB = 1024

# Executed in a fresh subprocess as `python -c WORKER`, never in-process:
# candidate code is untrusted (LLM-generated, and this repo specifically
# studies decoding pathologies that can produce infinite loops), so it must
# be killable by the OS on timeout rather than hoping a signal handler or
# thread-based timeout inside this process catches it.
WORKER = """
import resource, sys
resource.setrlimit(resource.RLIMIT_AS, ({mem_bytes}, {mem_bytes}))
candidate_ns = {{}}
exec(compile(CANDIDATE_CODE, "<candidate>", "exec"), candidate_ns)
exec(compile(TEST_CODE, "<test>", "exec"), candidate_ns)
candidate_ns["check"](candidate_ns[{entry_point!r}])
print("PASS")
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-root", type=pathlib.Path, required=True)
    parser.add_argument("--prompt-root", type=pathlib.Path, default=pathlib.Path("prompts/humaneval"))
    parser.add_argument("--tags", nargs="+", default=None, help="Restrict to these run tags.")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--memory-limit-mb", type=int, default=DEFAULT_MEMORY_LIMIT_MB)
    parser.add_argument("--out", type=pathlib.Path, default=None, help="Write the rows as JSON here.")
    return parser.parse_args()


def read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def extract_candidate(text: str) -> tuple[str | None, str]:
    """Return (candidate_code, how). None means no gradeable candidate."""
    final, how = final_segment(text)
    if final is None:
        return None, how
    for marker in END_MARKERS:
        if marker in final:
            final = final.split(marker, 1)[0]
    blocks = CODE_BLOCK.findall(final)
    if not blocks:
        return None, "final_channel_without_code_block"
    return textwrap.dedent(blocks[-1]).strip("\n"), "fenced_block"


def execute(
    candidate_code: str, test_code: str, entry_point: str, timeout: float, memory_limit_mb: int
) -> tuple[str, str]:
    """Return (verdict, detail). verdict in: passed, failed, timeout, worker_error."""
    worker = WORKER.format(mem_bytes=memory_limit_mb * 1024 * 1024, entry_point=entry_point)
    script = (
        f"CANDIDATE_CODE = {candidate_code!r}\n"
        f"TEST_CODE = {test_code!r}\n"
        f"{worker}"
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "timeout", f">{timeout}s"
    if proc.returncode == 0 and "PASS" in proc.stdout:
        return "passed", ""
    # Last line of stderr is normally the exception: AssertionError means the
    # tests ran and disagreed with the candidate; anything else (NameError,
    # SyntaxError, IndentationError, ...) means the candidate never got that
    # far -- both are "failed", but the detail says which.
    tail = proc.stderr.strip().splitlines()
    detail = tail[-1] if tail else f"exit={proc.returncode}"
    return "failed", detail[:200]


def grade(
    run_dir: pathlib.Path, prompt_root: pathlib.Path, timeout: float, memory_limit_mb: int
) -> dict[str, Any] | None:
    # run_dir layout: <runs-root>/<method>/<params>/<case>/<seed_N>/ -- run_dir
    # IS the seed_N directory (case is its parent, params its grandparent).
    run = read_json(run_dir / "run.json")
    config = read_json(run_dir / "config.json")
    if not run and not config:
        return None
    case = run_dir.parent.name
    params = run_dir.parent.parent.name
    method = run_dir.parent.parent.parent.name
    source = read_json(prompt_root / case / "source.json")
    entry_point = source.get("entry_point")
    test_code = source.get("test")
    try:
        text = (run_dir / "output.txt").read_text(encoding="utf-8")
    except OSError:
        text = ""

    candidate_code, how = extract_candidate(text)
    if candidate_code is None:
        verdict, detail = "no_answer", how
    elif not entry_point or not test_code:
        verdict, detail = "grader_error", f"missing entry_point/test in {prompt_root / case / 'source.json'}"
    else:
        verdict, detail = execute(candidate_code, test_code, entry_point, timeout, memory_limit_mb)

    return {
        "case": case,
        "seed": config.get("seed", run_dir.name.removeprefix("seed_")),
        "tag": f"{method}/{params}",
        "method": method,
        "params": params,
        "mode": config.get("mode"),
        "lossy_method": config.get("lossy_method"),
        "entry_point": entry_point,
        "extracted_by": how,
        "verdict": verdict,
        "detail": detail,
        "output_tokens": run.get("output_tokens"),
        "finish_reason": run.get("finish_reason"),
        "hit_cap": run.get("finish_reason") == "length",
        "l_bar": run.get("l_bar"),
    }


def render(rows: list[dict[str, Any]]) -> str:
    columns = ("case", "seed", "tag", "verdict", "detail", "output_tokens", "finish_reason")
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
    for row in rows:
        cells = []
        for column in columns:
            value = row.get(column)
            if isinstance(value, float):
                value = round(value, 3)
            cells.append("" if value is None else str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    rows = []
    # runs_root layout: <runs-root>/<method>/<params>/<case>/<seed_N>/run.json
    # (runs-root is expected to be a per-benchmark path, e.g. runs/humaneval).
    for run_json in sorted(args.runs_root.glob("*/*/*/seed_*/run.json")):
        tag = f"{run_json.parent.parent.parent.name}/{run_json.parent.parent.name}"
        if args.tags and tag not in args.tags:
            continue
        row = grade(run_json.parent, args.prompt_root, args.timeout, args.memory_limit_mb)
        if row is not None:
            rows.append(row)
    if not rows:
        print(f"no runs under {args.runs_root}", file=sys.stderr)
        return 1

    rows.sort(key=lambda r: (str(r["case"]), str(r["tag"]), str(r["seed"])))
    print(render(rows))

    by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_tag[row["tag"]].append(row)

    print("\n| tag | runs | pass@1 | passed | failed | timeout | no answer | grader error |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for tag, group in sorted(by_tag.items()):
        counts = {
            verdict: sum(1 for r in group if r["verdict"] == verdict)
            for verdict in ("passed", "failed", "timeout", "no_answer", "grader_error")
        }
        pass_at_1 = counts["passed"] / len(group) if group else 0.0
        print(
            f"| {tag} | {len(group)} | {pass_at_1:.3f} | {counts['passed']} | "
            f"{counts['failed']} | {counts['timeout']} | {counts['no_answer']} | {counts['grader_error']} |"
        )

    seeds = {row["seed"] for row in rows}
    if len(seeds) > 1:
        print(f"\nPer-case pass rate over {len(seeds)} seeds:\n")
        tags = sorted(by_tag)
        print("| case | " + " | ".join(tags) + " |")
        print("|---|" + "|".join("---:" for _ in tags) + "|")
        for case in sorted({row["case"] for row in rows}):
            cells = []
            for tag in tags:
                group = [r for r in rows if r["case"] == case and r["tag"] == tag]
                if not group:
                    cells.append("")
                    continue
                passed = sum(1 for r in group if r["verdict"] == "passed")
                cells.append(f"{passed}/{len(group)}")
            print(f"| {case} | " + " | ".join(cells) + " |")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"runs": rows}, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
