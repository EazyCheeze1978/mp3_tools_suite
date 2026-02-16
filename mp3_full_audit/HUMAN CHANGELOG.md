# **📜 CHANGELOG — mp3_full_audit (v1.0.0 → v1.4.6)**  

---

## **v1.0.0 — Initial Release**

**Core functionality introduced**

- Scans all MP3 files in the working directory  
- Extracts bitrate, file size, and duration  
- Supports interactive vs. autonomous display modes  
- Provides batch totals and grand totals  
- Exports a simple CSV with:  
  `file, bitrate, size, duration`  
- Includes color‑coded console output  
- No Playnite integration  
- No ID3 metadata extraction  
- No game mapping  
- No progress bar  

This version established the foundation: a clean, reliable MP3 scanner.

---

## **v1.1.0 — ID3 Metadata + Playnite Integration**

**Major feature expansion**

- Added ID3 extraction (title, artist, album)  
- Added detection of whether ID3 tags exist  
- Introduced Playnite CSV loading (basic, non‑forgiving parser)  
- Added associative arrays for:  
  - `GAME_TITLE_BY_ID`  
  - `GAME_SOURCE_BY_ID`  
- Added game ID → title/source mapping based on folder names  
- CSV export expanded to include:  
  `title, artist, album, has_id3_tags, game_id, game_title, game_source`  
- Added progress bar  
- Added prescan to count total MP3 files  

This version transformed the tool from a simple scanner into a metadata‑aware audit system.

---

## **v1.2.0 — Forgiving CSV Loader (First Attempt)**

**Improved Playnite CSV handling**

- Replaced strict CSV parsing with a “forgiving” loader  
- Added BOM stripping  
- Added CRLF → LF conversion  
- Added whitespace trimming  
- Added malformed‑line skipping  
- Added fallback prompting if CSV missing  
- Improved error messages  

However, this version still used **process substitution** (`< <(...)`), which later proved problematic on Git Bash.

---

## **v1.3.0 — Git Bash Compatibility Fixes**

**Stability improvements**

- Removed process substitution from CSV loader  
- Switched to temporary cleaned CSV file (`mktemp`)  
- Ensured compatibility with Windows line endings  
- Improved robustness of Playnite metadata loading  
- Added explicit cleanup of temp files  
- Improved whitespace trimming logic  

This version made the tool stable on Windows Git Bash for small CSVs.

---

## **v1.4.0 — AWK‑Based CSV Loader (Breakthrough Version)**

**Massive reliability upgrade**

- Replaced Bash‑based CSV parsing with a full AWK parser  
- AWK loader now handles:  
  - UTF‑8  
  - BOM  
  - CRLF  
  - quoted fields  
  - embedded commas  
  - large CSVs (5,000+ entries)  
- Eliminated Git Bash infinite‑loop issues  
- Ensured instant loading of large Playnite exports  
- Added Bash‑friendly output via `/tmp/playnite_map.sh`  

This was the turning point — the loader became fast, safe, and scalable.

---

## **v1.4.5 — CSV Output Refinements**

**Quality‑of‑life improvements**

- Added escaping for all CSV text fields  
- Ensured quotes inside metadata are doubled (`""`)  
- Improved CSV safety for LibreOffice Calc and Excel  
- Cleaned up progress bar behavior  
- Improved batch total formatting  
- Added more consistent color output  

This version made the CSV output professional‑grade.

---

## **v1.4.6 — Column Reordering + Final Polish**

**User‑driven refinement**

- Reordered CSV columns to the preferred, human‑friendly layout:  
  `game_title, game_source, game_id, duration, bitrate, size, has_id3_tags, title, artist, album, file`  
- Updated CSV header to match new order  
- Ensured all fields use escaped versions (`esc_*`)  
- Verified alignment between header and data  
- Cleaned up minor formatting inconsistencies  
- Finalized AWK loader integration  
- Improved console messaging  

This version represents the most polished, stable, and user‑friendly release to date.

---
