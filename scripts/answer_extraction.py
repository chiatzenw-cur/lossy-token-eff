#!/usr/bin/env python3
"""Shared "find the model's real answer text" step for every grade_*.py
script, covering both chat formats this campaign has run: Harmony
(GPT-OSS-20B) and Qwen3's own template (Qwen3-8B, 2026-08-17 addition).

Each grade_*.py script used to inline its own copy of
`text.split(FINAL_MARKER)[-1]` (Harmony-only). Qwen3 never emits that
marker -- it (optionally) reasons inside `<think>...</think>` and then just
writes the answer as plain text -- so this factors the "locate the answer
segment" step out from the dataset-specific "parse the answer out of that
segment" regexes, which are unaffected and stay in each grade_*.py file.
"""

from __future__ import annotations

FINAL_MARKER = "<|channel|>final<|message|>"
THINK_CLOSE = "</think>"


def final_segment(text: str) -> tuple[str | None, str]:
    """Return (segment, how). segment is None only when there's truly no
    output text to grade at all.

    - Harmony (GPT-OSS): the real answer is whatever follows the LAST
      final-channel marker (a run can pass through analysis/commentary
      channels first).
    - Qwen3: closing `</think>` marks the end of reasoning, if the model
      reasoned at all -- whatever follows is the answer. A non-thinking
      response never opens `<think>` in the first place, so the whole text
      already IS the answer segment.
    """
    if FINAL_MARKER in text:
        return text.split(FINAL_MARKER)[-1], "harmony_final_channel"
    if THINK_CLOSE in text:
        return text.split(THINK_CLOSE, 1)[-1], "qwen3_after_think"
    if text.strip():
        return text, "qwen3_no_think"
    return None, "no_final_channel"
