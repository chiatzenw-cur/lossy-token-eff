#!/usr/bin/env python3
"""sha256 digest of prompt roots, exactly scripts/addendum_campaign.prompt_digest (sorted case_*/* relpaths + bytes);
stdlib only, so it runs on a cluster login node:  python3 scripts/prompt_digest.py <repo> prompts/<set> ... -> JSON."""
import hashlib
import json
import pathlib
import sys


def digest(root: pathlib.Path) -> str | None:
    files = sorted(p for p in root.glob("case_*/*") if p.is_file()) if root.is_dir() else []
    if not files:
        return None
    h = hashlib.sha256()
    for path in files:
        h.update(str(path.relative_to(root)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


if __name__ == "__main__":
    base = pathlib.Path(sys.argv[1])
    print(json.dumps({rel: digest(base / rel) for rel in sys.argv[2:]}))
