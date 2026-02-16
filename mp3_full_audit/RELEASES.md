# **mp3_full_audit — Releases**

This document summarizes each public release of the **MP3 Full Audit Tool**, including major features, improvements, and download links (once GitHub releases are created). For detailed technical history, see **CHANGELOG.md**.

---

## **v1.4.6 — Current Release**

**Released:** 2026‑02‑15  
**Status:** Stable

### **Highlights**

- Reordered CSV columns into a clean, human‑friendly layout:

  ``` Code
  game_title, game_source, game_id, duration, bitrate, size,
  has_id3_tags, title, artist, album, file
  ```

- Updated CSV header to match new order.
- Ensured all text fields are properly escaped for CSV safety.
- Polished console output and progress display.

### **Why this release matters**

This version produces the cleanest, most readable CSV yet — ideal for LibreOffice Calc, Excel, or Playnite‑adjacent workflows.

---

## **v1.4.5**

**Released:** 2026‑02‑15

### **Highlights**

- Added robust CSV escaping for all text fields.
- Improved compatibility with spreadsheet tools.
- Refined progress bar and batch total formatting.

### **Why this release matters**

This version made the CSV output professional‑grade and safe for large libraries.

---

## **v1.4.0**

**Released:** 2026‑02‑15  
**Major Upgrade**

### **Highlights**

- Introduced **AWK‑based Playnite CSV loader**:
  - Handles UTF‑8, BOM, CRLF, quoted fields, embedded commas.
  - Loads large Playnite exports (5,000+ entries) instantly.
  - Eliminates Git Bash freezing and subshell issues.

### **Why this release matters**

This was the breakthrough that made the tool fast [relatively - without parallelization it's still slow as molasses with thousands of songs!], stable, and scalable.

---

## **v1.3.0**

**Released:** 2026‑02‑15

### **Highlights**

- Replaced process substitution with a Git‑Bash‑safe loader.
- Added temporary cleaned CSV file handling.
- Improved BOM stripping and whitespace trimming.

### **Why this release matters**

This version fixed the infinite bash.exe respawn loop on Windows.

---

## **v1.2.0**

**Released:** 2026‑02‑15

### **Highlights**

- Added first “forgiving” CSV loader.
- Improved error handling for malformed Playnite exports.
- Added CRLF → LF conversion and BOM stripping.

### **Why this release matters**

This was the first step toward robust Playnite integration.

---

## **v1.1.0**

**Released:** 2026‑02‑15

### **Highlights**

- Added ID3 metadata extraction (title, artist, album).
- Added detection of missing ID3 tags.
- Added Playnite CSV integration (basic parser).
- Added game ID → title/source mapping.
- Expanded CSV output with metadata fields.
- Added progress bar and prescan.

### **Why this release matters**

This version transformed the tool from a simple scanner into a metadata‑aware audit system.

---

# **mp3_reduce_tool - Releases**

## **v1.0.0 — Initial Release**

**Released:** 2026‑02‑15

### **Highlights**

- Scans all MP3 files.
- Extracts bitrate, size, duration.
- Supports interactive/autonomous modes.
- Exports simple CSV.
- Color‑coded console output.

### **Why this release matters**

The foundation of everything that followed.

---

## **Future Releases**

### **v2.0.0 (Planned)**

- Missing‑music report (games with zero soundtrack files).
- Coverage analysis.
- Optional UniPlaySong integration hooks.
- Potential Playnite extension groundwork.

---

## **Download Links**

Once GitHub releases are created, download links will appear here.

---
