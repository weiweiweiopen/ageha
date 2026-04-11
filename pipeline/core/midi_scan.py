"""Core scan and dedup utilities for phase-1 MIDI dataset pipeline."""

from __future__ import annotations

import csv
import hashlib
import json
import struct
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from pipeline.core.manifest_models import ArtistManifest, ManifestEntry, MidiMetadata

SUPPORTED_EXTENSIONS = {".mid", ".midi"}


def iter_artist_dirs(midi_library_root: Path) -> Iterable[Path]:
    """Yield artist directories (one level below midi-library root)."""
    for path in sorted(midi_library_root.iterdir()):
        if path.is_dir():
            yield path


def iter_midi_files(artist_dir: Path) -> Iterable[Path]:
    """Yield MIDI files recursively for an artist."""
    for path in sorted(artist_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_midi_header(raw: bytes) -> tuple[int, int, int]:
    """Parse SMF header: format, track count, division (ticks per quarter).

    Raises:
        ValueError: if header is invalid.
    """
    if len(raw) < 14:
        raise ValueError("File too small for MIDI header")
    if raw[:4] != b"MThd":
        raise ValueError("Missing MThd header")

    header_len = struct.unpack(">I", raw[4:8])[0]
    if header_len < 6:
        raise ValueError(f"Invalid MIDI header length: {header_len}")

    fmt, ntrks, division = struct.unpack(">HHH", raw[8:14])
    return fmt, ntrks, division


def _sum_track_bytes(raw: bytes) -> int | None:
    """Best-effort sum of MTrk chunk sizes for dedup signatures."""
    idx = 14
    total = 0
    safety = 0

    while idx + 8 <= len(raw) and safety < 10000:
        safety += 1
        chunk_type = raw[idx : idx + 4]
        chunk_len = struct.unpack(">I", raw[idx + 4 : idx + 8])[0]
        idx += 8

        if idx + chunk_len > len(raw):
            return None

        if chunk_type == b"MTrk":
            total += chunk_len
        idx += chunk_len

    return total


def read_midi_metadata(path: Path, root_dir: Path) -> MidiMetadata:
    """Read robust, low-level metadata for a MIDI candidate."""
    raw = path.read_bytes()
    file_size = len(raw)
    extension = path.suffix.lower()

    midi_format: int | None = None
    track_count: int | None = None
    ticks_per_quarter: int | None = None
    track_byte_total: int | None = None
    is_valid = True
    error: str | None = None

    try:
        midi_format, track_count, ticks_per_quarter = _parse_midi_header(raw)
        track_byte_total = _sum_track_bytes(raw)
    except ValueError as exc:
        is_valid = False
        error = str(exc)

    return MidiMetadata(
        file_name=path.name,
        relative_path=str(path.relative_to(root_dir)),
        extension=extension,
        file_size=file_size,
        sha256=_sha256(path),
        midi_format=midi_format,
        track_count=track_count,
        ticks_per_quarter=ticks_per_quarter,
        track_byte_total=track_byte_total,
        is_valid_midi=is_valid,
        validation_error=error,
    )


def _fuzzy_signature(meta: MidiMetadata) -> str:
    """Signature for likely duplicates across renamed files.

    This is intentionally conservative. Exact hash match remains highest priority.
    """
    parts = (
        meta.file_size,
        meta.midi_format,
        meta.track_count,
        meta.ticks_per_quarter,
        meta.track_byte_total,
    )
    return "|".join(str(p) for p in parts)


def build_manifest_entries(artist: str, metadata_rows: list[MidiMetadata]) -> list[ManifestEntry]:
    """Mark duplicates and pick canonical files per duplicate group."""
    by_exact: dict[str, list[MidiMetadata]] = defaultdict(list)
    for row in metadata_rows:
        by_exact[row.sha256].append(row)

    exact_group_for_path: dict[str, str] = {}
    canonical_for_path: dict[str, str] = {}

    for sha, rows in by_exact.items():
        canonical = sorted(rows, key=lambda r: r.relative_path)[0]
        for row in rows:
            exact_group_for_path[row.relative_path] = f"sha256:{sha}"
            canonical_for_path[row.relative_path] = canonical.relative_path

    # Fuzzy grouping only for non-exact singleton files.
    singleton_rows = [rows[0] for rows in by_exact.values() if len(rows) == 1]
    by_fuzzy: dict[str, list[MidiMetadata]] = defaultdict(list)
    for row in singleton_rows:
        by_fuzzy[_fuzzy_signature(row)].append(row)

    entries: list[ManifestEntry] = []
    for row in sorted(metadata_rows, key=lambda r: r.relative_path):
        group = exact_group_for_path[row.relative_path]
        strategy = "sha256"

        fuzzy_rows = by_fuzzy[_fuzzy_signature(row)]
        if len(fuzzy_rows) > 1 and len(by_exact[row.sha256]) == 1:
            strategy = "fuzzy"
            canonical = sorted(fuzzy_rows, key=lambda r: r.relative_path)[0]
            group = f"fuzzy:{_fuzzy_signature(row)}"
            canonical_path = canonical.relative_path
        else:
            canonical_path = canonical_for_path[row.relative_path]

        entries.append(
            ManifestEntry(
                artist=artist,
                metadata=row,
                duplicate_group=group,
                duplicate_strategy=strategy,
                is_duplicate=row.relative_path != canonical_path,
                canonical_relative_path=canonical_path,
            )
        )

    return entries


def write_artist_manifest(manifest: ArtistManifest, out_dir: Path) -> tuple[Path, Path]:
    """Write JSON + CSV outputs for one artist."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "manifest.json"
    csv_path = out_dir / "manifest.csv"

    json_payload = {
        "artist": manifest.artist,
        "generated_at_utc": manifest.generated_at_utc,
        "root_dir": manifest.root_dir,
        "entries": [asdict(entry) for entry in manifest.entries],
    }
    json_path.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")

    flat_rows = [entry.to_flat_dict() for entry in manifest.entries]
    fieldnames = sorted({key for row in flat_rows for key in row.keys()})
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_rows)

    return json_path, csv_path
