"""Interfaces reserved for phase-2 audio->MIDI ingestion.

Phase 1 does not implement transcription. This module defines stable contracts so
future adapters can emit MIDI files that reuse the same manifest pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(slots=True)
class AudioIngestionRecord:
    """Metadata for an audio asset to be transcribed in phase 2."""

    artist: str
    audio_path: Path
    source_uri: str | None = None
    source_license: str | None = None


@dataclass(slots=True)
class TranscriptionResult:
    """Common output contract for audio->MIDI engines."""

    midi_output_path: Path
    backend_name: str
    backend_version: str | None = None
    confidence: float | None = None


class AudioToMidiAdapter(Protocol):
    """Protocol to support swappable backends (e.g., Basic Pitch)."""

    def transcribe(self, record: AudioIngestionRecord, output_dir: Path) -> TranscriptionResult:
        """Transcribe one audio record to MIDI."""
        ...
