#!/usr/bin/env bash
set -euo pipefail

NEW_REPO="weiweiweiopen/6-8-CS42448-laser-DAC"
TARGET_DIR="kicad/6_8_cs42448_laser_dac"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found. Install and authenticate first." >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "gh auth missing. Run: gh auth login" >&2
  exit 1
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

cp -R "$TARGET_DIR" "$tmpdir/project"
cd "$tmpdir/project"

git init

git add .
git commit -m "Initial KiCad starter package for 6/8 CS42448 Laser DAC"

gh repo create "$NEW_REPO" --public --source=. --push

echo "Published to https://github.com/$NEW_REPO"
