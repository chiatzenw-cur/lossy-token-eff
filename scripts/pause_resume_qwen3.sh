#!/usr/bin/env bash
# One-shot pause/resume wrapper for the Qwen3-8B campaign (2026-08-18, user
# request: "stop and free the gpu at 7pm china time today and resume after
# 12pm"). Interpreted as 19:00 CST 2026-08-18 -> 12:00 CST 2026-08-19 (an
# overnight pause; confirmed in the chat reply, correctable if wrong).
#
# Runs detached (nohup) rather than as a Claude-session cron job on purpose:
# this session's own cron jobs are session-only and vanish if the session
# ends before they fire (CronCreate's own documented behavior), and this
# spans ~26 hours -- the same reason the original campaign_all.sh survives
# an SSH disconnect via nohup, this wrapper needs the same property.
#
# campaign_run.py is resumable by design (skip-if-done via run.json,
# clean_partial_runs() clears any half-written directory from an
# interrupted run) -- killing mid-run and relaunching the same
# campaign_all_qwen3.sh command later is safe, not a hack.
set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
LOG="logs/campaign_all_qwen3_stdout.log"
STOP_EPOCH="$1"
RESUME_EPOCH="$2"
DRIVER_PGREP='campaign_all_qwen3\.sh'

now="$(date -u +%s)"
echo "=== pause_resume_qwen3.sh started $(date -u +%Y-%m-%dT%H:%M:%SZ), stop=$(date -u -d @"$STOP_EPOCH" +%Y-%m-%dT%H:%M:%SZ) resume=$(date -u -d @"$RESUME_EPOCH" +%Y-%m-%dT%H:%M:%SZ) ===" >> "$LOG"

sleep_until() {
  local target="$1"
  while true; do
    now="$(date -u +%s)"
    remaining=$(( target - now ))
    [[ "$remaining" -le 0 ]] && break
    # Cap each sleep so a killed/suspended host doesn't leave this stuck
    # asleep indefinitely past the target -- re-checks the clock at least
    # every 10 minutes.
    sleep "$(( remaining < 600 ? remaining : 600 ))"
  done
}

sleep_until "$STOP_EPOCH"

echo "" >> "$LOG"
echo "########## PAUSE requested $(date -u +%Y-%m-%dT%H:%M:%SZ): stopping campaign_all_qwen3.sh and freeing the GPU ##########" >> "$LOG"
pkill -f "$DRIVER_PGREP" 2>/dev/null || true
pkill -f "scripts/campaign_run.py" 2>/dev/null || true
pkill -f "scripts/fresh_server_replay.py" 2>/dev/null || true
bash remote/stop_server.sh >> "$LOG" 2>&1 || true
echo "campaign stopped, GPU released, free space: $(df -h . | tail -1)" >> "$LOG"

sleep_until "$RESUME_EPOCH"

echo "" >> "$LOG"
echo "########## RESUME $(date -u +%Y-%m-%dT%H:%M:%SZ): relaunching campaign_all_qwen3.sh ##########" >> "$LOG"
nohup bash scripts/campaign_all_qwen3.sh >> "$LOG" 2>&1 < /dev/null &
disown
echo "relaunched campaign_all_qwen3.sh, pid $!" >> "$LOG"
