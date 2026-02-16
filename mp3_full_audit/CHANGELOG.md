# **CHANGELOG.md**  

## **[1.4.6] – 2026‑02‑15**

### Changed

- Reordered CSV columns to a more intuitive, human‑friendly layout:
  `game_title, game_source, game_id, duration, bitrate, size, has_id3_tags, title, artist, album, file`
- Updated CSV header to match new column order.
- Ensured all text fields use escaped versions (`esc_*`) for CSV safety.
- Polished console output and messaging.

---

## **[1.4.5] – 2026‑02‑15**

### Added

- Full CSV escaping for all text fields (quotes doubled for safety).
- Improved compatibility with LibreOffice Calc and Excel.

### Improved

- Progress bar behavior and batch total formatting.
- Consistency of color‑coded output.

---

## **[1.4.0] – 2026‑02‑15**

### Added

- **AWK‑based Playnite CSV loader** (major architectural upgrade).
  - Handles UTF‑8, BOM, CRLF, quoted fields, embedded commas, and large CSVs.
  - Eliminates Git Bash process‑substitution issues.
  - Outputs Bash‑friendly associative array assignments via `/tmp/playnite_map.sh`.

### Improved

- Metadata loading speed and reliability for large Playnite exports (5,000+ entries).

---

## **[1.3.0] – 2026‑02‑15**

### Fixed

- Git Bash compatibility issues caused by process substitution (`< <(...)`).
- CSV loader now uses a temporary cleaned file (`mktemp`) instead of subshells.

### Improved

- BOM stripping, whitespace trimming, and CRLF handling.
- Cleanup of temporary files after metadata load.

---

## **[1.2.0] – 2026‑02‑15**

### Added

- “Forgiving” CSV loader (first iteration).
  - BOM stripping.
  - CRLF → LF conversion.
  - Whitespace trimming.
  - Malformed‑line skipping.

### Improved

- Error messages when Playnite CSV is missing or malformed.

---

## **[1.1.0] – 2026‑02‑15**

### Added

- ID3 metadata extraction (title, artist, album).
- Detection of whether ID3 tags are present.
- Playnite CSV integration (basic parser).
- Associative arrays for:
  - `GAME_TITLE_BY_ID`
  - `GAME_SOURCE_BY_ID`
- Folder‑based game ID → metadata mapping.
- Expanded CSV export with game metadata fields.
- Progress bar and prescan for total MP3 count.

---

## **[1.0.0] – 2026‑02‑15**

### Initial Release

- Scans all MP3 files in the working directory.
- Extracts bitrate, file size, and duration.
- Supports interactive and autonomous modes.
- Batch totals and grand totals.
- Simple CSV export:
  `file, bitrate, size, duration`
- Color‑coded console output.

---

## **Versioning Notes**

This project follows **Semantic Versioning (SemVer)**:

- **MAJOR** — breaking changes or major new subsystems  
- **MINOR** — new features, enhancements  
- **PATCH** — fixes, refinements, internal improvements  

The next planned milestone is **v2.0.0**, which will introduce:

- Missing‑music report  
- Game‑coverage analysis  
- Optional UniPlaySong integration hooks  
