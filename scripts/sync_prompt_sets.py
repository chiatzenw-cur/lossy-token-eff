#!/usr/bin/env python3
"""Make <repo>/prompts/<set> byte-identical to the Mac's committed prompt sets, from a staged copy on the cluster
(step 9: pushing ~85 MB of prompt sets per lane over the Mac's link took >10 min per lane). Stdlib only, runs on a
login node. Expected digests (scripts/addendum_campaign.prompt_digest) come as JSON on stdin {rel: digest}.

  python3 sync_prompt_sets.py <stage-root> <repo> [<repo> ...] < expected.json

A set whose digest already matches is left alone. Otherwise the staged copy (digest checked first) is copied next
to it and swapped in; the replaced copy is removed. Prints {repo: {rel: "ok" | "replaced" | "stage-mismatch"}}.
"""
import hashlib
import json
import pathlib
import shutil
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


def main() -> int:
    stage, repos = pathlib.Path(sys.argv[1]), [pathlib.Path(r) for r in sys.argv[2:]]
    expected = json.load(sys.stdin)
    staged = {rel: digest(stage / rel) == want for rel, want in expected.items()}
    report = {}
    for repo in repos:
        out = {}
        for rel, want in expected.items():
            dest = repo / rel
            if digest(dest) == want:
                out[rel] = "ok"
                continue
            if not staged[rel]:
                out[rel] = "stage-mismatch"
                continue
            tmp, old = dest.with_name(dest.name + ".s9tmp"), dest.with_name(dest.name + ".s9old")
            for p in (tmp, old):
                if p.exists():
                    shutil.rmtree(p)
            shutil.copytree(stage / rel, tmp, symlinks=True)
            if dest.exists():
                dest.rename(old)
            tmp.rename(dest)
            if old.exists():
                shutil.rmtree(old)
            out[rel] = "replaced" if digest(dest) == want else "replaced-but-mismatch"
        report[str(repo)] = out
    print(json.dumps(report))
    return 0 if all(v in ("ok", "replaced") for r in report.values() for v in r.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
