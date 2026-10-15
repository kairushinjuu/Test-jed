#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 4 ]; then
  echo "Usage: sign_apk.sh unsigned.apk signed.apk keystore.jks alias" >&2
  exit 2
fi
input="$1"
output="$2"
keystore="$3"
alias="$4"
command -v zipalign >/dev/null
command -v apksigner >/dev/null
mkdir -p "$(dirname "$output")"
tmp="$(mktemp --suffix=.apk)"
trap 'rm -f "$tmp"' EXIT
zipalign -p -f 4 "$input" "$tmp"
apksigner sign --ks "$keystore" --ks-key-alias "$alias" --out "$output" "$tmp"
apksigner verify --verbose "$output"
