# Anonymized snapshot for double-blind review

This directory is not part of the snapshot. It builds a scrubbed, history-free
copy of the repo that can go to a throwaway GitHub repository and then to
[anonymous.4open.science](https://anonymous.4open.science). This repository
itself is never modified.

## Why a snapshot and not this repo directly

- **History.** This repo's git history is about 1.5 GB and still contains the
  removed `proposals.jsonl` traces plus every commit author and message.
  anonymous.4open.science only scrubs the files at one commit, but a history
  that big pushes it out of full-download mode.
- **Size limits.** In its default config, full-download mode needs a packed
  repo of 60 MB or less; anything larger is proxied file by file from GitHub
  instead. Folders with more than 1000 entries are not fully listed, and files
  over 100 MB are not served.
- **Identifiers.** Run configs and logs embed absolute paths
  (`/home/<user>/<repo>`, `/scratch/<user>`, `/project/<alloc>`). Docs name
  people, the Slurm allocation (which names the PI) and the clusters.
  `terms.tsv` covers all of them. The web tool's own term box only replaces
  text in file contents; the snapshot also renames paths such as
  `setup_nibi.sh`.

## Steps

```bash
# 1. build (outside this repo); --slim keeps only readme/summary files under
#    runs/, old_runs/, runs_phase1/, logs/  (~60 MB packed vs ~1.2 GB of files)
python3 tools/anonymize/make_snapshot.py ../anon-snapshot --slim

# 2. it must end with "leak scan: clean"; otherwise add the term to terms.tsv and rebuild

# 3. push to a NEW repository under an account/org with no link to the authors
cd ../anon-snapshot
git remote add origin git@github.com:<throwaway>/<neutral-name>.git
git push -u origin main

# 4. on anonymous.4open.science: point it at that repo, paste the left column of
#    terms.tsv (non-comment lines) into "terms to anonymize" as a second net,
#    set an expiry date, and put the resulting link in the paper
```

What the snapshot changes:

- File contents and paths are rewritten with `terms.tsv`. Rules scoped
  `docs` (people, HPC organisations) are not applied under `runs*/`,
  `old_runs/`, `logs/` or `prompts/`, because those hold model output and
  dataset text where the same words have unrelated meanings.
- `cascade/results/final_results.pdf` is dropped, because the author name
  and cluster are rendered into the image. Regenerate it in the snapshot with
  `cascade/analysis/results_pdf.py` if needed.
- `--slim` also drops `analysis/semantic_guard/results/recurrence_vs_unproductive.jsonl`
  (52 MB, derived from hidden-state dumps that are not in the repo; its
  summaries sit next to it).
- The result is one commit by `Anonymous <anonymous@example.com>` dated
  2026-01-01.

Things to check by hand before submitting:

- The Co-Authored-By lines and `noreply@anthropic.com` in
  `scripts/addendum_campaign.py` identify the tooling, not the authors; they
  are left in.
- Free-text docs (`campaign/JOURNAL.md`, `campaign/addendum/PROGRESS.md`,
  `cascade/JOURNAL.md`) are working logs. They are scrubbed, but they still
  read as one team's diary (time zones, "this Mac", and so on). Consider
  excluding them for review.
