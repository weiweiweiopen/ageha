# ageha workspace

## MIDI Dataset Pipeline (Phase 1)

This repository now includes a **modular Python phase-1 dataset pipeline** for
projects that use artist-organized MIDI folders (for example,
`midi-library/<artist>/...`).

### What phase 1 does

- Scans artist folders under `midi-library/`
- Validates `.mid` / `.midi` files via SMF header checks
- Extracts basic metadata (hash, size, MIDI format, tracks, PPQ, etc.)
- Flags duplicate candidates using:
  - exact duplicate strategy (`sha256`)
  - conservative fuzzy signature strategy (size + structural metadata)
- Writes per-artist:
  - `manifest.json`
  - `manifest.csv`

Output files are written to `midi-library/<artist>/.dataset/` by default.

### Run

```bash
python scripts/dataset/phase1_build_manifest.py --midi-library midi-library
```

Optional flags:

- `--manifest-subdir .dataset` (default)

### Design goals

- **No workflow breakage**: phase-1 outputs are additive metadata only.
- **Portability**: standard-library-first implementation, typed models, and small modules.
- **Future extension**: a stable audio-to-MIDI adapter interface lives at:
  `pipeline/adapters/audio2midi/interface.py`.

### Phase 2 integration point

Future audio-to-MIDI tools should implement the `AudioToMidiAdapter` protocol and
emit MIDI files to artist folders (or an interim folder), then re-run phase 1 to
materialize manifests consistently across native and transcribed MIDI sources.
