#!/bin/bash
#SBATCH --account=def-hongyanz_cpu
#SBATCH --job-name=add-grade
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#
# Grade every run in the addendum's grading mirror on Nibi scratch with the
# campaign's own graders (scripts/addendum_grade.py). CPU only. The Mac
# uploads run.json + config.json + output.txt per run into $MIRROR/runs
# (scripts/addendum_campaign.py grade) and pulls $MIRROR/grades.csv back.
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$HOME/projects/def-hongyanz/$USER}"
REPO_DIR="${REPO_DIR:-$PROJECT_DIR/lossy-token-eff}"
MIRROR="${MIRROR:-$SCRATCH/lossy-addendum/mirror}"
# shellcheck disable=SC2086
module load StdEnv/2023 python/3.12
unset PYTHONPATH
cd "$REPO_DIR"
echo "=== grade job $SLURM_JOB_ID on $(hostname) mirror=$MIRROR $(date -u +%FT%TZ) ==="
python3 scripts/addendum_grade.py --runs-root "$MIRROR/runs" --out "$MIRROR/grades.csv.new" \
  --cache "$MIRROR/grades.csv" --workers "${SLURM_CPUS_PER_TASK:-16}"
mv "$MIRROR/grades.csv.new" "$MIRROR/grades.csv"
echo "=== done $(date -u +%FT%TZ) ==="
