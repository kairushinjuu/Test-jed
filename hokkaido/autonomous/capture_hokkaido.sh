#!/usr/bin/env bash
set -Eeuo pipefail
PKG=${PKG:-dev.lichii.android.lowramv025}
INTERVAL=${INTERVAL:-5}
[[ "$INTERVAL" =~ ^[0-9]+$ ]] && (( INTERVAL >= 2 && INTERVAL <= 60 )) || { echo "INTERVAL must be 2..60 seconds" >&2; exit 2; }
if [[ -n "${ADB_SERIAL:-}" ]]; then ADB=(adb -s "$ADB_SERIAL"); else
  mapfile -t devices < <(adb devices | awk 'NR>1 && $2=="device" {print $1}')
  (( ${#devices[@]} == 1 )) || { echo "Select ADB_SERIAL; multiple or no devices connected" >&2; adb devices >&2; exit 2; }
  ADB=(adb -s "${devices[0]}")
fi
"${ADB[@]}" shell pm path "$PKG" >/dev/null || { echo "Install $PKG first" >&2; exit 3; }
OUT=${OUT:-"$HOME/storage/downloads/hokkaido-v025-$(date +%Y%m%d-%H%M%S)"}
mkdir -p "$OUT"
{ echo "package=$PKG"; echo "start_host=$(date -Is)"; echo "interval_sec=$INTERVAL"; } > "$OUT/manifest.txt"
"${ADB[@]}" shell dumpsys activity exit-info "$PKG" > "$OUT/exit-info-before.txt" 2>&1 || true
echo "Local diagnostic output: $OUT. Launch game manually. Ctrl+C ends capture."
stop=0; trap 'stop=1' INT TERM
started=0; last_pid=''
for ((sample=0; sample<3600; sample++)); do
  (( stop )) && break
  now=$(date -Is)
  pid=$("${ADB[@]}" shell pidof "$PKG" 2>/dev/null | tr -d '\r' || true); pid=${pid%% *}
  if [[ -n "$pid" ]]; then started=1; last_pid=$pid; fi
  { printf '=== timestamp=%s sample=%d pid=%s ===\n' "$now" "$sample" "${pid:-none}"
    "${ADB[@]}" shell cat /proc/meminfo 2>&1 | grep -E "^(MemTotal|MemAvailable|MemFree|SwapTotal|SwapFree|Cached|SReclaimable|Dirty):" || true
    "${ADB[@]}" shell cat /proc/pressure/memory 2>&1 || true; } >> "$OUT/system-memory.txt"
  if [[ -n "$pid" ]]; then
    { printf '=== timestamp=%s sample=%d pid=%s ===\n' "$now" "$sample" "$pid"; "${ADB[@]}" shell dumpsys meminfo "$PKG" 2>&1 || true; } >> "$OUT/app-meminfo.txt"
  elif (( started )); then echo "Process exited; collecting exit diagnostics." >&2; break; fi
  sleep "$INTERVAL" || true
done
"${ADB[@]}" shell dumpsys activity exit-info "$PKG" > "$OUT/exit-info-after.txt" 2>&1 || true
if [[ -n "$last_pid" ]]; then "${ADB[@]}" logcat -d --pid="$last_pid" -v threadtime > "$OUT/logcat-app-pid.txt" 2>&1 || true; fi
printf 'end_host=%s\nlast_pid=%s\n' "$(date -Is)" "$last_pid" >> "$OUT/manifest.txt"
( cd "$OUT/.." && zip -q -r "$(basename "$OUT").zip" "$(basename "$OUT")" ) || true
echo "Saved locally to $OUT; review private logs before uploading."
