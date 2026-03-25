# 6/8 CS42448 Laser DAC (KiCad Starter Package)

This is a complete starter handoff package for a layout service.

## Project files
- `6_8_cs42448_laser_dac.kicad_pro`
- `6_8_cs42448_laser_dac.kicad_sch`
- `6_8_cs42448_laser_dac.kicad_pcb`

## Handoff folders
- `fabrication/` Gerber + drill + fab notes placeholders
- `assembly/` BOM + pick/place + assembly drawing placeholders
- `test/` functional test and calibration templates
- `docs/` pinout and stackup templates
- `scripts/` optional helper scripts

## Immediate next steps
1. Open `.kicad_pro` in KiCad 8+.
2. Replace placeholder symbols/footprints with final parts (Teensy 4.1 headers, CS42448, power, connectors).
3. Finalize board outline and connector placement in `.kicad_pcb`.
4. Run ERC/DRC and fix all errors.
5. Export manufacturing outputs into `fabrication/` and `assembly/`.

## Notes
- This package is intentionally a starter and is not production-ready until schematic and PCB are completed.
- `scripts/publish_to_new_repo.sh` can push this package into a new GitHub repo once `gh` CLI auth is available.
