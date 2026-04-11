#!/usr/bin/env python3
"""Phase-1 MIDI dataset pipeline.

Scans artist directories under midi-library/, validates MIDI files, extracts
basic metadata, marks duplicates, and writes per-artist manifest outputs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.core.manifest_models import ArtistManifest
from pipeline.core.midi_scan import (
    build_manifest_entries,
    iter_artist_dirs,
    iter_midi_files,
    read_midi_metadata,
    write_artist_manifest,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build phase-1 MIDI manifests")
    parser.add_argument(
        "--midi-library",
        type=Path,
        default=Path("midi-library"),
        help="Root containing artist subdirectories.",
    )
    parser.add_argument(
        "--manifest-subdir",
        default=".dataset",
        help="Subdirectory name under each artist dir for outputs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root: Path = args.midi_library

    if not root.exists() or not root.is_dir():
        raise SystemExit(f"MIDI library root not found: {root}")

    artists = list(iter_artist_dirs(root))
    if not artists:
        print(f"No artist directories found under {root}")
        return 0

    for artist_dir in artists:
        artist = artist_dir.name
        midi_files = list(iter_midi_files(artist_dir))
        metadata_rows = [read_midi_metadata(path, root) for path in midi_files]
        entries = build_manifest_entries(artist, metadata_rows)

        manifest = ArtistManifest.create(artist=artist, root_dir=root, entries=entries)
        out_dir = artist_dir / args.manifest_subdir
        json_path, csv_path = write_artist_manifest(manifest, out_dir)

        valid_count = sum(1 for row in metadata_rows if row.is_valid_midi)
        dup_count = sum(1 for entry in entries if entry.is_duplicate)
        print(
            f"[{artist}] files={len(metadata_rows)} valid={valid_count} "
            f"duplicates={dup_count} -> {json_path}, {csv_path}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
