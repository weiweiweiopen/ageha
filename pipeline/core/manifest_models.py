"""Typed models for phase-1 dataset manifests.

These models are intentionally small and dependency-free so they can be used by
CLI scripts and future adapters (audio->MIDI, cloud crawlers, etc.).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class MidiMetadata:
    """Basic metadata extracted from a MIDI file.

    Fields focus on robust, low-cost extraction that does not require heavy MIDI
    dependencies. This keeps the pipeline portable across environments.
    """

    file_name: str
    relative_path: str
    extension: str
    file_size: int
    sha256: str
    midi_format: int | None
    track_count: int | None
    ticks_per_quarter: int | None
    track_byte_total: int | None
    is_valid_midi: bool
    validation_error: str | None


@dataclass(slots=True)
class ManifestEntry:
    """A manifest row for one source MIDI candidate."""

    artist: str
    metadata: MidiMetadata
    duplicate_group: str
    duplicate_strategy: str
    is_duplicate: bool
    canonical_relative_path: str
    ingestion_source: str = "midi_local"

    def to_flat_dict(self) -> dict[str, Any]:
        """Flatten nested metadata for CSV serialization."""
        payload = asdict(self)
        metadata = payload.pop("metadata")
        flat = {f"metadata_{key}": value for key, value in metadata.items()}
        payload.update(flat)
        return payload


@dataclass(slots=True)
class ArtistManifest:
    """A full manifest for one artist folder."""

    artist: str
    generated_at_utc: str
    root_dir: str
    entries: list[ManifestEntry]

    @classmethod
    def create(cls, artist: str, root_dir: Path, entries: list[ManifestEntry]) -> "ArtistManifest":
        now = datetime.now(tz=timezone.utc).isoformat()
        return cls(
            artist=artist,
            generated_at_utc=now,
            root_dir=str(root_dir),
            entries=entries,
        )
