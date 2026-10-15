#!/usr/bin/env python3
import argparse
import csv
import re
from collections import Counter
from pathlib import Path

PATTERN = re.compile(
    r"subscription|subscribe|premium|billing|purchases?|entitlement|"
    r"takoboto\.feature|takoboto\.cloud|extra_purchase_ok|subscribe_purchase_ok|"
    r"extra_kanjidraw|extra_audio|extra_game",
    re.IGNORECASE
)

def scan(root):
    rows = []
    for path in sorted(root.rglob("*.cs")):
        relative = path.relative_to(root)
        if any(part.lower() in ("obj", "bin") for part in relative.parts):
            continue
        with path.open("r", encoding="utf-8", errors="replace") as stream:
            for number, value in enumerate(stream, 1):
                if PATTERN.search(value):
                    rows.append((str(relative), number, value.strip()[:500]))
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("--output", default="output/audit")
    args = parser.parse_args()
    root = Path(args.source)
    if not root.is_dir():
        parser.error("source directory not found")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    hits = scan(root)
    with (output / "code_matches.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["file", "line", "matched_text"])
        writer.writerows(hits)
    counts = Counter(path for path, _, _ in hits)
    lines = ["# Source reference inventory", "", f"Matches: {len(hits)}", "", "## Files"]
    lines.extend(f"- {path} — {total}" for path, total in counts.most_common())
    (output / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(hits)} matching lines in {len(counts)} files")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
