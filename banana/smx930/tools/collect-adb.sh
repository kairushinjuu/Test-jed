#!/usr/bin/env bash
# Read-only Android SM-X930 collection. Uses adb shell, no root, no app data mutation.
set -euo pipefail
PKG='dev.nxnative.android.malig925'
DURATION="${DURATION:-600}"; INTERVAL="${INTERVAL:-5}"
if ! [[ "$DURATION" =~ ^[0-9]+$ && "$INTERVAL" =~ ^[0-9]+$ ]] || (( INTERVAL < 2 || DURATION < INTERVAL || DURATION > 3600 )); then
  echo 'DURATION must be 2-3600 s, INTERVAL at least 2 s' >&2;exit 2
fi
ADB="${ADB:-adb}"
"$ADB" get-state >/dev/null
MODEL="$("$ADB" shell getprop ro.product.model | tr -d '\r')"
if [[ "$MODEL" != SM-X930 ]];then echo "Refusing collection on non-target $MODEL" >&2;exit 3;fi
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${OUT:-smx930-${STAMP}}";mkdir -p "$OUT"
printf 'device=%s\npackage=%s\nstart_utc=%s\nduration_seconds=%s\ninterval_seconds=%s\n' "$MODEL" "$PKG" "$STAMP" "$DURATION" "$INTERVAL" > "$OUT/manifest.txt"
"$ADB" shell getprop >"$OUT/getprop.txt" 2>&1 || :
"$ADB" shell dumpsys battery >"$OUT/battery-start.txt" 2>&1 || :
"$ADB" shell dumpsys thermalservice >"$OUT/thermal-start.txt" 2>&1 || :
START="$(date +%s)"; COUNT=0
while (( $(date +%s) - START < DURATION )); do
  COUNT=$((COUNT+1)); 
  { echo "--- $(date -u +%FT%TZ) sample=$COUNT";
    "$ADB" shell pidof "$PKG" || :;
    "$ADB" shell pidof "$PKG:game" || :;
    "$ADB" shell dumpsys meminfo "$PKG" || :;
    "$ADB" shell cat /proc/pressure/memory || :;
    "$ADB" shell dumpsys thermalservice | grep -E 'mStatus|Status|Temperature|temperature|current' | head -35 || :;
  } >>"$OUT/samples.txt" 2>&1
  sleep "$INTERVAL"
done
"$ADB" logcat -d -v threadtime > "$OUT/logcat.txt" 2>&1 || :
"$ADB" shell dumpsys battery > "$OUT/battery-end.txt" 2>&1 || :
"$ADB" shell dumpsys thermalservice > "$OUT/thermal-end.txt" 2>&1 || :
printf 'Collection finished: %s\nShare the app\047s exported game log separately (Settings > Help > Share log).\n' "$OUT"
