# **mp3_full_audit - Full Documentation - Newest First**

## **As of 1.4.x**

### **1. Introduction**

`mp3_full_audit.sh` is a comprehensive audit tool designed to analyze a UniPlaySong‑style game soundtrack library. It inspects MP3 files stored in game‑ID‑named folders, extracts metadata, cross‑references Playnite’s exported game list, and produces a clean CSV report suitable for spreadsheet analysis, debugging, and metadata verification.

The tool was built collaboratively (full transparency: vibe coded with Microsoft Copilot)with a focus on:

- **Transparency** — every step is visible and logged  
- **Reversibility** — no destructive actions  
- **Portability** — works on Git Bash for Windows and POSIX shells  
- **Resilience** — handles malformed files, missing metadata, and large datasets  
- **Community integration** — designed with UniPlaySong and Playnite users in mind  

This document explains the motivations, architecture, workflow, and design decisions behind the tool.

---

### **2. Background & Motivation**

#### **2.1 The Problem Space**

UniPlaySong downloads soundtrack files into folders named after Playnite game IDs. This is elegant and deterministic — but it leaves users with questions:

- Which games have soundtrack files?  
- Which games are missing music entirely?  
- Are any tracks misfiled under the wrong game ID?  
- Do the MP3s contain proper ID3 tags?  
- Are there duplicates, anomalies, or mismatches?  
- How complete is my soundtrack library?  

Playnite itself does not provide a built‑in way to audit soundtrack coverage.  
UniPlaySong focuses on downloading, not validating [so far!].

#### **2.2 The Goal**

The goal was to create a tool that:

- Scans the entire soundtrack library  
- Cross‑references it with Playnite’s exported metadata  
- Produces a clean, sortable CSV  
- Surfaces errors and mismatches  
- Helps users (and developers like Huddini) understand coverage and gaps  

#### **2.3 Why Bash?**

Bash was chosen because:

- It’s universally available  
- It integrates well with FFmpeg/ffprobe  
- It’s easy to distribute  
- It’s transparent and readable  
- It allows rapid iteration  

Special care was taken to support **Git Bash on Windows**, which has unique quirks.

---

### **3. High‑Level Architecture**

The tool consists of four major components:

1. **Playnite Metadata Loader**  
2. **Library Prescan**  
3. **MP3 Audit Loop**  
4. **CSV Output Engine**

Each component is modular and can be improved independently.

---

### **4. Playnite Metadata Loader**

#### **4.1 Input**

Playnite’s exported CSV [provided by the separate extension Library Exporter Advanced]:

``` Code
titles_sources_ids.csv
```

This file contains:

- Game Title  
- Game Source (Steam, Epic, GOG, etc.)  
- Game ID (GUID)  

#### **4.2 Why AWK?**

Early versions used a Bash `while read` loop, but Git Bash struggled with:

- Long lines  
- UTF‑8 characters  
- Quoted fields  
- Large files (5,000+ entries)  
- Process substitution  

The AWK‑based loader solves all of these issues.

#### **4.3 What the Loader Produces**

Two associative arrays:

``` Code
GAME_TITLE_BY_ID[id]  → "Psychonauts"
GAME_SOURCE_BY_ID[id] → "Steam"
```

These arrays allow instant lookup during the audit.

#### **4.4 Error Handling**

The loader:

- Skips malformed lines  
- Strips BOM  
- Strips CRLF  
- Handles quoted fields  
- Ignores blank lines  
- Warns if the CSV is missing  

---

### **5. Library Prescan**

Before auditing MP3s, the script performs a fast prescan:

- Detects all folders matching Playnite game IDs  
- Counts MP3 files in each folder  
- Logs empty or missing folders  
- Builds the list of files to audit  

This step is extremely fast and provides early feedback.

---

### **6. MP3 Audit Loop**

For each MP3 file, the script extracts:

- **Duration** (via ffprobe)  
- **Bitrate**  
- **File size**  
- **ID3 tag presence**  
- **Title**  
- **Artist**  
- **Album**  

Then it determines:

- **Game ID** (from folder name)  
- **Game Title** (from Playnite CSV)  
- **Game Source**  

#### **6.1 Error Handling**

The audit loop:

- Skips unreadable files  
- Handles missing ID3 tags  
- Handles malformed metadata  
- Logs anomalies  
- Continues gracefully  

---

### **7. CSV Output Engine**

#### **7.1 Output Format**

The CSV is written to:

``` Code
full_audit_YYYYMMDD_HHMMSS.csv
```

#### **7.2 Column Order**

Optimized for readability:

``` Code
game_title,
game_source,
game_id,
duration,
bitrate,
size,
has_id3_tags,
title,
artist,
album,
file
```

#### **7.3 Escaping**

All fields that may contain:

- commas  
- quotes  
- Unicode  
- special characters  

…are escaped using `esc_` variables to ensure CSV integrity.

---

### **8. Design Philosophy**

#### **8.1 Transparency**

Every major step prints status messages:

- Metadata loaded  
- MP3s found  
- Files processed  
- Errors detected  

#### **8.2 Reversibility**

The script:

- Never deletes files  
- Never modifies MP3s  
- Never overwrites existing CSVs  

#### **8.3 Portability**

The AWK loader and careful avoidance of Bash pitfalls ensure:

- Works on Git Bash  
- Works on Linux  
- Works on macOS  

#### **8.4 Community Integration**

The tool is designed to complement UniPlaySong:

- Helps validate downloads  
- Helps detect misfiled tracks  
- Helps identify missing soundtracks  
- Helps maintain clean metadata  

---

### **9. Future Enhancements**

#### **9.1 Missing‑Music Report**

A companion CSV listing:

- All Playnite games with **no** associated MP3 files  
- Reasons (no folder, empty folder, unreadable files, etc.)  

#### **9.2 Integration Hooks**

Optional features for UniPlaySong:

- Auto‑verification  
- Metadata enrichment  
- Folder renaming suggestions  

#### **9.3 Reduction Tool Integration**

The `mp3_reduction` script will eventually share:

- CSV output format  
- Metadata extraction logic  
- Error handling  

---

### **10. Requirements**

- Git Bash (Windows) or POSIX shell  
- `ffprobe` from FFmpeg  
- Playnite’s exported `titles_sources_ids.csv`  
- MP3 files stored in game‑ID‑named folders  

---

### **11. Usage Summary**

1. Place the script in your soundtrack root folder  
2. Ensure `titles_sources_ids.csv` is present  
3. Run:

``` Code
bash mp3_full_audit-v1.4.x.sh
```

4. Review the generated CSV  

---

---
---

## OLD documentation

## 📄 **Earlier, before decided to divide documentation per tool**

### MP3 Tools Suite  

#### *Transparent, reversible, safe audio library management*

---

### Overview

This suite contains two Bash-based utilities designed to help users analyze, reduce, and manage MP3 files in a music library. The tools are built with transparency, safety, and reversibility in mind, making them ideal for workflows where data integrity matters — such as Playnite’s UniPlaySong extension.

The suite includes:

- **mp3_reduce_tool.sh**  
  A full-featured tool for previewing, reducing, exporting CSV reports, and safely deleting originals after verified reduction.

- **mp3_full_audit.sh**  
  A non-destructive audit tool that scans *all* MP3 files and produces detailed reports and CSV exports.

Both tools support:

- Optional directory argument  
- Color-coded output  
- Interactive or autonomous display modes  
- Batch summaries every 50 files  
- Cumulative totals  
- CSV export with selectable totals mode  

---

### Requirements

These tools require:

- **Git Bash** (Windows) or any POSIX-compatible shell (Linux/macOS/WSL)
- **ffmpeg** and **ffprobe** in your PATH  
- `stat`  
- `bc`  

#### Verifying PATH on Windows

If you installed ffmpeg manually:

1. Copy the `bin/` folder path (e.g., `C:\ffmpeg\bin`)
2. Add it to **System Properties → Environment Variables → PATH**
3. Sign out and back in (or restart) to apply changes

---

### Installation

1. Place both `.sh` files in a folder of your choice  
2. Make them executable (Linux/macOS/WSL):

``` Code
chmod +x mp3_reduce_tool.sh
chmod +x mp3_full_audit.sh
```

On Windows Git Bash, this step is optional but recommended.

---

### Usage

#### Option A — Run inside the target directory

``` Code
cd "/path/to/music"
./mp3_reduce_tool.sh
```

#### Option B — Provide a directory argument

``` Code
./mp3_reduce_tool.sh "/path/to/music"
```

Both scripts support this pattern.

---

### mp3_reduce_tool.sh — Features

#### 1. Preview reducible files  

Shows only MP3s above 128 kbps.  
Displays:

- Bitrate  
- Size  
- Duration  
- Estimated reduced size  
- Batch totals  
- Cumulative totals  

User chooses:

- Interactive mode (pause every 50 files)  
- Autonomous mode (continuous scrolling)  

---

#### 2. Reduce files to 128 kbps  

Creates new files with `_reduced.mp3` suffix.  
Originals are untouched.

---

#### 3. Export CSV (reducible files only)  

User chooses:

- Interactive or autonomous display  
- CSV with batch totals  
- CSV with final totals only  

CSV includes:

- File path  
- Bitrate  
- Size  
- Duration  
- Estimated reduced size  
- Savings  

---

#### 4. Safe-delete originals  

Deletes originals **only if**:

- A `_reduced.mp3` exists  
- Reduced file is non-zero  
- Reduced file is newer  
- Reduced file passes ffprobe validation  

All deletions are logged.

---

### mp3_full_audit.sh — Features

#### 1. Full audit (all MP3s)  

Displays:

- Bitrate  
- Size  
- Duration  
- Batch totals  
- Cumulative totals  

Supports interactive/autonomous modes.

---

#### 2. Export full CSV  

User chooses:

- Batch totals  
- Final totals only  

CSV includes:

- File path  
- Bitrate  
- Size  
- Duration  

---

### Safety Philosophy

These tools were designed with:

- **Reversibility**  
- **Transparency**  
- **Predictability**  
- **Zero destructive surprises**  

No destructive action occurs without:

- Verification  
- Confirmation  
- Logging
