#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 1 ]; then
  echo "Usage: run_audit.sh original.apk" >&2
  exit 2
fi
apk="$1"
mkdir -p output/recovered output/decompiled output/audit
python scripts/inspect_apk.py "$apk"
python scripts/recover_assembly.py "$apk" --output output/recovered
if [ ! -x .tools/ilspycmd ]; then
  dotnet tool install --tool-path .tools ilspycmd --version 11.1.0.9782
fi
.tools/ilspycmd -p -o output/decompiled output/recovered/Takoboto.dll
python scripts/audit_source.py output/decompiled --output output/audit
