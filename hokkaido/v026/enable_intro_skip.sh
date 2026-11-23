#!/usr/bin/env bash
# Configure isolated Hokkaido v0.26 without overwriting existing env.txt settings.
set -Eeuo pipefail
PKG=dev.lichii.android.lowramv026
VALUE=${1:-1}
[[ "$VALUE" == 0 || "$VALUE" == 1 ]] || { echo 'Usage: enable_intro_skip.sh [1|0]' >&2; exit 2; }
ADB=(adb)
if [[ -n "${ADB_SERIAL:-}" ]]; then ADB+=( -s "$ADB_SERIAL" ); fi
if ! "${ADB[@]}" shell pm path "$PKG" 2>/dev/null | grep -q '^package:'; then
 echo "The isolated $PKG app must be installed before configuring the intro skip." >&2; exit 3
fi
# This operates on the app's external files directory only. On some Android versions shell
# cannot write Android/data; if so, use the device's file manager or another authorized file API.
DIR="/sdcard/Android/data/$PKG/files"
"${ADB[@]}" shell "mkdir -p '$DIR' && ( [ ! -f '$DIR/env.txt' ] || sed -i '/^HOKKAIDO_OOT_SKIP_INTRO=/d' '$DIR/env.txt' ) && printf '%s\\n' 'HOKKAIDO_OOT_SKIP_INTRO=$VALUE' >> '$DIR/env.txt' && tail -n 8 '$DIR/env.txt'"
echo "Changed skip to $VALUE. Force-stop the app before launching Ocarina."
