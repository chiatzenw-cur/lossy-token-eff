#!/usr/bin/env python3
"""Phase B of the single-event counterfactual experiment: splice the ONE
token that a fresh strict-mode probe actually produced (see
prepare_counterfactual_probe.py for phase A) onto the reconstructed prefix,
and write it as a new prompt case to be run under r_fuzzy to a realistic
continuation length.

Important correction found while building this: proposals.jsonl's
output_position 0 for these short completions-endpoint probe requests does
NOT capture the true first generated token -- it is consistently missing
exactly one leading token (confirmed by tokenizing response.json's `text`
field, which IS authoritative, and finding one more token than
proposals.jsonl logs, with the extra token accounting for the prefix/suffix
mismatch every time). So the single token spliced here is always taken from
response.json's decoded text, re-tokenized, NEVER from proposals.jsonl's
row 0. This is a real, reproducible under-logging bug in the trace hook for
tiny fresh-prompt completions requests; noted here rather than fixed, since
fixing it is out of scope for this experiment and response.json is a fully
adequate ground truth for what was actually generated.

Also: case_020's original nearest-preceding lossy-only-accept (t=3669) probed
as a NULL counterfactual -- strict's independent resample reproduced the
exact same 5 tokens (" + y ζ - ") as the factual run, token-for-token. That
intervention point was therefore replaced with the next-nearest
lossy-only-accept before it (t=3659) that a probe confirmed actually
diverges ("7" -> "2"). See the run log / conversation for the full
before/after comparison.

Usage:
    python3 analysis/semantic_guard/build_counterfactual_continuation.py
"""

from __future__ import annotations

import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "analysis" / "semantic_guard"))
from count_relaxed_only_hesitation import get_encoding  # noqa: E402
from prepare_counterfactual_probe import reconstruct_prefix_text, write_probe_case  # noqa: E402

CONTINUATION_PROMPT_ROOT = REPO_ROOT / "prompts" / "counterfactual_continuation"
PROBE_RUNS_ROOT = REPO_ROOT / "runs" / "counterfactual_probe" / "strict_probe"

# (continuation_label, source_case, run_dir, intervention_output_position, probe_label)
CASES = [
    (
        "case_028_onset31322",
        "case_028",
        REPO_ROOT / "runs/semantic_guard_pilot/aime24/case_028/seed_0/rFuzzy0p3",
        31318,
        "case_028_onset31322",
    ),
    (
        "case_020_onset3673",
        "case_020",
        REPO_ROOT / "runs/hidden_state_pilot/aime24/case_020/seed_0/rFuzzy0p3",
        3659,  # revised intervention point -- see module docstring
        "case_020_onset3673_alt3659",
    ),
    (
        "case_020_onset28786",
        "case_020",
        REPO_ROOT / "runs/hidden_state_pilot/aime24/case_020/seed_0/rFuzzy0p3",
        28770,
        "case_020_onset28786",
    ),
]


def get_probe_first_token(probe_label: str) -> tuple[int, str]:
    """True first generated token id+text for a probe, from response.json
    (authoritative), not proposals.jsonl (drops the first token -- see
    module docstring)."""
    response = json.loads((PROBE_RUNS_ROOT / probe_label / "seed_0" / "strict" / "response.json").read_text(encoding="utf-8"))
    text = response["choices"][0]["text"]
    enc = get_encoding()
    ids = enc.encode(text, allowed_special="all")
    first_id = ids[0]
    return first_id, enc.decode([first_id])


def main() -> int:
    manifest = []
    for label, source_case, run_dir, t, probe_label in CASES:
        prefix_text = reconstruct_prefix_text(run_dir, up_to_output_position=t)
        token_id, token_text = get_probe_first_token(probe_label)

        # original token at this exact position, for the report
        rows = [json.loads(line) for line in (run_dir / "proposals.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        orig_row = next(r for r in rows if r["output_position"] == t)
        enc = get_encoding()
        orig_text = enc.decode([orig_row["emitted_token_id"]])

        continuation_text = prefix_text + token_text
        case_dir = write_probe_case(label, source_case, continuation_text)
        # write_probe_case() writes to PROBE_PROMPT_ROOT; move/copy into the
        # dedicated continuation root instead so phase A and phase B prompts
        # don't collide under the same label.
        dest_dir = CONTINUATION_PROMPT_ROOT / label
        dest_dir.mkdir(parents=True, exist_ok=True)
        (dest_dir / "rendered_prompt.txt").write_text((case_dir / "rendered_prompt.txt").read_text(encoding="utf-8"), encoding="utf-8")
        (dest_dir / "metadata.json").write_text((case_dir / "metadata.json").read_text(encoding="utf-8"), encoding="utf-8")

        print(f"{label}: t={t} original={orig_text!r} (id={orig_row['emitted_token_id']}) -> counterfactual={token_text!r} (id={token_id})")
        print(f"  wrote {dest_dir}")
        manifest.append(
            {
                "label": label,
                "source_case": source_case,
                "run_dir": str(run_dir),
                "intervention_output_position": t,
                "original_token_id": orig_row["emitted_token_id"],
                "original_token_text": orig_text,
                "counterfactual_token_id": token_id,
                "counterfactual_token_text": token_text,
                "continuation_prompt_dir": str(dest_dir),
            }
        )

    manifest_path = REPO_ROOT / "analysis" / "semantic_guard" / "results" / "counterfactual_continuation_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nwrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
