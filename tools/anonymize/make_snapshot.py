#!/usr/bin/env python3
"""Export an anonymized, history-free copy of this repository for double-blind review.

Reads the committed tree at a ref (default HEAD; uncommitted changes are ignored),
applies tools/anonymize/terms.tsv to file contents and paths, drops files that
cannot be scrubbed as text, and writes a fresh one-commit git repo with an
anonymous author. The source repository is never modified.

    python3 tools/anonymize/make_snapshot.py OUT_DIR [--ref HEAD] [--slim]

--slim keeps only readme/summary files under the per-run data directories
(runs/, old_runs/, runs_phase1/, logs/), which is what makes the snapshot small
enough for anonymous.4open.science's full-download mode; see README.md here.

After writing, it re-scans the snapshot for every identifier in terms.tsv (plus
a few raw tokens) and exits non-zero if any remain.
"""
import argparse
import collections
import io
import os
import re
import subprocess
import sys
import tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

DATA_DIRS = ("runs/", "old_runs/", "runs_phase1/", "logs/")
DOC_EXCLUDE = DATA_DIRS + ("prompts/",)  # "docs"-scoped terms are not applied here (model/dataset text)

# Always dropped: this kit itself, and binaries with identifying text rendered in
# (regenerate cascade/results/final_results.pdf with cascade/analysis/results_pdf.py
# from the snapshot if it is needed).
DROP = ("tools/anonymize/", "cascade/results/final_results.pdf")
# Also dropped with --slim: large intermediates whose summaries sit next to them and
# whose inputs (hidden-state dumps) are not in the repository anyway.
SLIM_DROP = ("analysis/semantic_guard/results/recurrence_vs_unproductive.jsonl",)

# Raw tokens checked after replacement, independent of terms.tsv's patterns.
# Person names are only checked outside run data / prompts, which hold unrelated dataset text.
LEAK_CHECK = ["chiatzen", "billxby", "hongyanz", "6101837", "6071935", "sharcnet", "nibi",
              "killarney", "lossy-token-eff", "xubill", "billxu"]
LEAK_CHECK_DOCS = ["bill xu", "haochen"]

MAX_FOLDER = 1000          # anonymous.4open.science lists at most this many entries per folder
FULL_MODE_LIMIT = 60_000   # KB; above this it proxies files from GitHub on the fly instead


def load_terms():
    terms = []
    for line in open(os.path.join(HERE, "terms.tsv")):
        if not line.strip() or line.startswith("#"):
            continue
        pat, repl, scope = line.rstrip("\n").split("\t")
        terms.append((re.compile(pat, re.I), repl, scope))
    return terms


def scrub(text, path, terms):
    in_data = path.startswith(DOC_EXCLUDE)
    for rx, repl, scope in terms:
        if scope == "docs" and in_data:
            continue
        text = rx.sub(repl, text)
    return text


def keep(path, slim):
    if path.startswith(DROP):
        return False
    if slim and path.startswith(SLIM_DROP):
        return False
    if slim and path.startswith(DATA_DIRS):
        name = path.rsplit("/", 1)[-1].lower()
        return name in ("readme.md",) or name.startswith("summary")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--ref", default="HEAD")
    ap.add_argument("--slim", action="store_true")
    args = ap.parse_args()

    out = os.path.abspath(args.out)
    if os.path.exists(out) and os.listdir(out):
        sys.exit(f"{out} exists and is not empty")
    if out.startswith(REPO + os.sep):
        sys.exit("write the snapshot outside this repository")
    os.makedirs(out, exist_ok=True)

    terms = load_terms()
    tar = subprocess.run(["git", "-C", REPO, "archive", "--format=tar", args.ref],
                         check=True, capture_output=True).stdout
    n_files = n_changed = 0
    with tarfile.open(fileobj=io.BytesIO(tar)) as tf:
        for m in tf:
            if not m.isfile() or not keep(m.name, args.slim):
                continue
            data = tf.extractfile(m).read()
            dest = scrub(m.name, m.name, terms)
            if b"\0" not in data[:8192]:
                try:
                    text = data.decode("utf-8")
                except UnicodeDecodeError:
                    text = None
                if text is not None:
                    new = scrub(text, m.name, terms)
                    if new != text:
                        n_changed += 1
                    data = new.encode("utf-8")
            p = os.path.join(out, dest)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as f:
                f.write(data)
            os.chmod(p, m.mode & 0o777)
            n_files += 1
    print(f"wrote {n_files} files ({n_changed} rewritten) to {out}")

    # Leak scan over the written snapshot: contents and paths.
    leaks = collections.Counter()
    examples = {}
    folder = collections.Counter()
    total = 0
    for root, dirs, files in os.walk(out):
        dirs[:] = [d for d in dirs if d != ".git"]
        rel_root = os.path.relpath(root, out)
        folder[rel_root] = len(files) + len(dirs)
        for fn in files:
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, out)
            total += os.path.getsize(p)
            low = (rel + "\n").lower() + open(p, "rb").read().decode("utf-8", "replace").lower()
            for tok in LEAK_CHECK + ([] if rel.startswith(DOC_EXCLUDE) else LEAK_CHECK_DOCS):
                # left boundary only: catches compounds (nibiref) but not base64 noise (...HNibIf...)
                # or JSON-escaped newlines in model output ("\\nibility")
                if re.search(r"(?<![a-z0-9+/\\])" + re.escape(tok), low):
                    leaks[tok] += 1
                    examples.setdefault(tok, rel)

    subprocess.run(["git", "init", "-q", "-b", "main", out], check=True)
    subprocess.run(["git", "-C", out, "add", "-A"], check=True)
    env = {**os.environ, "GIT_AUTHOR_NAME": "Anonymous", "GIT_AUTHOR_EMAIL": "anonymous@example.com",
           "GIT_COMMITTER_NAME": "Anonymous", "GIT_COMMITTER_EMAIL": "anonymous@example.com",
           "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z"}
    subprocess.run(["git", "-C", out, "-c", "commit.gpgsign=false", "-c", "gc.auto=0", "commit", "-q", "-m", "Initial commit"],
                   check=True, env=env)
    subprocess.run(["git", "-C", out, "gc", "-q", "--prune=now"], check=True)
    packed = subprocess.run(["git", "-C", out, "count-objects", "-v"], capture_output=True, text=True).stdout
    pack_kb = int(re.search(r"^size-pack: (\d+)", packed, re.M).group(1))

    print(f"working tree: {total / 2**20:.1f} MB; packed git repo: {pack_kb / 1024:.1f} MB")
    print(f"anonymous.4open.science full-download mode needs <= {FULL_MODE_LIMIT // 1000} MB packed"
          f" ({'OK' if pack_kb <= FULL_MODE_LIMIT else 'over: it will stream files from GitHub instead'})")
    big = [(n, d) for d, n in folder.items() if n > MAX_FOLDER]
    for n, d in sorted(big, reverse=True):
        print(f"  folder over {MAX_FOLDER} entries (not fully listable there): {d} ({n})")
    if leaks:
        print("LEAKS remaining (fix terms.tsv or the source, then re-run):")
        for tok, n in leaks.most_common():
            print(f"  {tok!r}: {n} files, e.g. {examples[tok]}")
        sys.exit(1)
    print("leak scan: clean")


if __name__ == "__main__":
    main()
