#!/usr/bin/env bash
# Push the working tree to the cluster without committing (for quick
# iteration); pull results back with the rsync in cluster/README.md.
# Excludes everything large or machine-specific. Uses the `nibi` host from
# ~/.ssh/config (Duo push once per multiplexed connection).
#
#   bash cascade/cluster/sync_to_nibi.sh            # dry run first
#   bash cascade/cluster/sync_to_nibi.sh --go
set -euo pipefail
HOST="${HOST:-nibi}"
# cluster username from the ssh config entry for $HOST, so nothing is hard-coded here
NIBI_USER="${NIBI_USER:-$(ssh -G "$HOST" 2>/dev/null | awk '/^user /{print $2}')}"
DEST="${DEST:-projects/def-hongyanz/$NIBI_USER/lossy-token-eff}"
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

flags=(-avz --delete-excluded
  --exclude /runs/ --exclude /runs_old_backup/ --exclude /old_runs/ --exclude /logs/
  --exclude '.venv*' --exclude .git/ --exclude '__pycache__/' --exclude '*.pyc'
  --exclude .claude/)
if [[ "${1:-}" != "--go" ]]; then
  flags+=(--dry-run)
  echo "(dry run; pass --go to sync)"
fi
rsync "${flags[@]}" ./ "$HOST:$DEST/"
