#!/usr/bin/env python3
"""Grade archived LiveCodeBench runs by execution, not text matching.

Two harnesses, chosen per test case by its own `testtype` field -- **not**
a single stdin/stdout harness for every problem, which was this script's
own bug until 2026-08-22 (see below):

- `testtype == "stdin"` (Codeforces/AtCoder-style problems): run the
  candidate as a whole program, `input` piped to stdin, compare stdout
  against `output` (line-by-line, trailing-whitespace-insensitive -- a
  correct solution that differs only in trailing spaces/newlines is not a
  meaningful failure for this campaign's purposes).
- `testtype == "functional"` (LeetCode-style problems): the prompt asks
  the model to "Complete the following function" against a `class
  Solution:` stub (see `prompts/livecodebench/<case>/rendered_prompt.txt`),
  not write an I/O program. `input` is one JSON-literal argument per line
  (in the starter code's own parameter order), `output` is one
  JSON-literal return value. Grading imports the candidate's `Solution`
  class, calls `getattr(Solution(), func_name)(*args)`, and compares the
  JSON-decoded return value against the JSON-decoded expected output.
  `func_name` comes from `test_cases.json`'s own `metadata.func_name`
  field (`{"func_name": "doesValidArrayExist"}` for that problem).

**Bug found and fixed 2026-08-22**: this script used to run every problem
through the stdin harness regardless of `testtype`. 10 of this campaign's
12 livecodebench cases are `leetcode`-platform ("functional") problems --
a candidate that correctly implements the requested function has no
stdin/stdout I/O of its own, so it produced empty stdout and was marked
"failed" no matter how correct the logic was. Confirmed by hand: extracted
one "failed" candidate (case with question_id 2792, "neighboring-bitwise-
xor"), ran it directly against the LeetCode calling convention rather than
piping stdin to it -- correct, textbook solution (XOR of the whole array
must be 0). Every prior accuracy number this grader ever produced for
livecodebench (both GPT-OSS-20B and Qwen3-8B) undercounts real accuracy by
an unknown amount up to this fix; re-run grading and update
`campaign/results/livecodebench*.csv` + `campaign/FINDINGS.md` after this
fix lands, don't trust the old numbers.

**Public test cases only, by design, not an oversight**: LiveCodeBench's
`private_test_cases` field is a base64+zlib+**pickle** blob. Unpickling
data fetched from a URL is a real deserialization risk (arbitrary code
execution) independent of how much the host is trusted, so this grader
never touches it. `public_test_cases` is plain JSON (a string-encoded list
of {input, output, testtype} dicts) -- no such risk, and typically a few
test cases per problem, enough to catch a badly-wrong solution even though
it's not the full private suite a real LiveCodeBench leaderboard run would
use. See campaign/JOURNAL.md for how the 12 needed rows were fetched
(streamed, matched by question_id, discarded from disk after -- the full
test.jsonl is ~1.25GB, this campaign only ever needed 12 specific rows'
worth of it).

Candidate code runs in its own subprocess (not exec() in this process)
with a wall-clock timeout and a memory cap, for the same reason
grade_humaneval.py does: this repo studies decoding pathologies
(repetition loops) that can produce code that hangs.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from answer_extraction import final_segment  # noqa: E402 -- covers both Harmony (GPT-OSS) and Qwen3's </think> convention

CODE_BLOCK = re.compile(r"```(?:\w+)?\s*\n(.*?)```", re.DOTALL)

DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MEMORY_LIMIT_MB = 1024

WORKER_PREAMBLE = """
import resource
resource.setrlimit(resource.RLIMIT_AS, ({mem_bytes}, {mem_bytes}))
"""

# Pre-imported into the functional worker's globals before the candidate is
# exec'd: LeetCode starter-code signatures reference List/Optional/etc. and
# many candidates don't repeat the import themselves (the starter snippet
# they're completing doesn't show one) -- harmless to import twice for the
# candidates that do.
FUNCTIONAL_WORKER_TEMPLATE = """
import json, sys
from typing import *

{candidate_code}

_args = [json.loads(_line) for _line in sys.stdin.read().splitlines()]
_result = Solution().{func_name}(*_args)
sys.stdout.write(json.dumps(_result))
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-root", type=pathlib.Path, required=True)
    parser.add_argument("--prompt-root", type=pathlib.Path, default=pathlib.Path("prompts/livecodebench"))
    parser.add_argument(
        "--test-cases", type=pathlib.Path, default=None,
        help="Defaults to <prompt-root>/test_cases.json (question_id -> row with public_test_cases + metadata.func_name).",
    )
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
    final, how = final_segment(text)
    if final is None:
        return None, how
    blocks = CODE_BLOCK.findall(final)
    if not blocks:
        return None, "final_channel_without_code_block"
    return blocks[-1], "last_fenced_block"


def normalize(output: str) -> list[str]:
    return [line.rstrip() for line in output.strip("\n").splitlines()]


def run_one_case(candidate_path: str, stdin_text: str, timeout: float, mem_bytes: int) -> tuple[str, str]:
    """Return (verdict, detail) for a single stdin/stdout test case: ok, timeout, or error."""
    worker = WORKER_PREAMBLE.format(mem_bytes=mem_bytes)
    try:
        proc = subprocess.run(
            [sys.executable, "-c", worker + f"\nexec(compile(open({candidate_path!r}).read(), {candidate_path!r}, 'exec'))"],
            input=stdin_text, capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "timeout", f"exceeded {timeout}s"
    if proc.returncode != 0:
        tail = proc.stderr.strip().splitlines()
        return "error", (tail[-1] if tail else f"exit={proc.returncode}")[:200]
    return "ok", proc.stdout


def run_one_functional_case(
    candidate_code: str, func_name: str, input_text: str, timeout: float, mem_bytes: int,
) -> tuple[str, str]:
    """Return (verdict, detail) for a single functional (LeetCode-style) test case."""
    worker = WORKER_PREAMBLE.format(mem_bytes=mem_bytes) + FUNCTIONAL_WORKER_TEMPLATE.format(
        candidate_code=candidate_code, func_name=func_name,
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-c", worker],
            input=input_text, capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "timeout", f"exceeded {timeout}s"
    if proc.returncode != 0:
        tail = proc.stderr.strip().splitlines()
        return "error", (tail[-1] if tail else f"exit={proc.returncode}")[:200]
    return "ok", proc.stdout


def execute(
    candidate_code: str, func_name: str | None, test_cases: list[dict], timeout: float, mem_bytes: int,
) -> tuple[str, str]:
    """Return (verdict, detail). verdict in: passed, failed, timeout, error, grader_error."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as handle:
        handle.write(candidate_code)
        candidate_path = handle.name
    try:
        for i, case in enumerate(test_cases):
            testtype = case.get("testtype", "stdin")
            if testtype == "functional":
                if not func_name:
                    return "grader_error", f"case {i}: functional test case but no func_name in metadata"
                verdict, detail = run_one_functional_case(candidate_code, func_name, case["input"], timeout, mem_bytes)
            elif testtype == "stdin":
                verdict, detail = run_one_case(candidate_path, case["input"], timeout, mem_bytes)
            else:
                return "grader_error", f"case {i}: unknown testtype {testtype!r}"

            if verdict == "timeout":
                return "timeout", f"case {i}: {detail}"
            if verdict == "error":
                return "error", f"case {i}: {detail}"

            if testtype == "functional":
                try:
                    matches = json.loads(detail) == json.loads(case["output"])
                except json.JSONDecodeError:
                    matches = False
            else:
                matches = normalize(detail) == normalize(case["output"])
            if not matches:
                return "failed", f"case {i}: output mismatch"
        return "passed", f"{len(test_cases)}/{len(test_cases)} public cases"
    finally:
        pathlib.Path(candidate_path).unlink(missing_ok=True)


def grade(
    run_dir: pathlib.Path, prompt_root: pathlib.Path, test_cases_by_qid: dict[str, dict[str, Any]],
    timeout: float = DEFAULT_TIMEOUT_SECONDS, memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
) -> dict[str, Any] | None:
    run = read_json(run_dir / "run.json")
    config = read_json(run_dir / "config.json")
    if not run and not config:
        return None
    case = run_dir.parent.name
    params = run_dir.parent.parent.name
    method = run_dir.parent.parent.parent.name
    meta = read_json(prompt_root / case / "metadata.json")
    question_id = meta.get("question_id")
    entry = test_cases_by_qid.get(question_id) or {}
    test_cases = entry.get("cases")
    func_name = entry.get("func_name")
    try:
        text = (run_dir / "output.txt").read_text(encoding="utf-8")
    except OSError:
        text = ""

    candidate_code, how = extract_candidate(text)
    if candidate_code is None:
        verdict, detail = "no_answer", how
    elif not test_cases:
        verdict, detail = "grader_error", f"no public test cases for question_id={question_id!r}"
    else:
        verdict, detail = execute(candidate_code, func_name, test_cases, timeout, memory_limit_mb * 1024 * 1024)

    return {
        "case": case,
        "seed": config.get("seed", run_dir.name.removeprefix("seed_")),
        "tag": f"{method}/{params}",
        "method": method,
        "params": params,
        "mode": config.get("mode"),
        "lossy_method": config.get("lossy_method"),
        "question_id": question_id,
        "extracted_by": how,
        "verdict": verdict,
        "detail": detail,
        "output_tokens": run.get("output_tokens"),
        "finish_reason": run.get("finish_reason"),
        "hit_cap": run.get("finish_reason") == "length",
        "l_bar": run.get("l_bar"),
    }


def load_test_cases(path: pathlib.Path) -> dict[str, dict[str, Any]]:
    raw = read_json(path)
    out = {}
    for qid, row in raw.items():
        cases = row.get("public_test_cases")
        if isinstance(cases, str):
            cases = json.loads(cases)
        meta = row.get("metadata")
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except json.JSONDecodeError:
                meta = {}
        out[qid] = {"cases": cases or [], "func_name": (meta or {}).get("func_name")}
    return out


def render(rows: list[dict[str, Any]]) -> str:
    columns = ("case", "seed", "tag", "question_id", "verdict", "detail", "output_tokens", "finish_reason", "l_bar")
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
    test_cases_path = args.test_cases or (args.prompt_root / "test_cases.json")
    if not test_cases_path.is_file():
        print(f"no test cases at {test_cases_path} -- fetch them first (see campaign/JOURNAL.md)", file=sys.stderr)
        return 1
    test_cases_by_qid = load_test_cases(test_cases_path)

    rows = []
    for run_json in sorted(args.runs_root.glob("*/*/*/seed_*/run.json")):
        tag = f"{run_json.parent.parent.parent.name}/{run_json.parent.parent.name}"
        if args.tags and tag not in args.tags:
            continue
        row = grade(run_json.parent, args.prompt_root, test_cases_by_qid, args.timeout, args.memory_limit_mb)
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

    verdicts = ("passed", "failed", "timeout", "error", "no_answer", "grader_error")
    print("\n| tag | runs | " + " | ".join(verdicts) + " |")
    print("|---|---:|" + "|".join("---:" for _ in verdicts) + "|")
    for tag, group in sorted(by_tag.items()):
        counts = {v: sum(1 for r in group if r["verdict"] == v) for v in verdicts}
        print(f"| {tag} | {len(group)} | " + " | ".join(str(counts[v]) for v in verdicts) + " |")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"runs": rows}, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
