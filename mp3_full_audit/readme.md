# NEWEST readme!

## **mp3_full_audit — README (v1.4.x)**

### **Overview**

`mp3_full_audit.sh` is a Bash-based audit tool designed to analyze a UniPlaySong‑style game soundtrack library. It scans all MP3 files stored in game‑ID‑named folders, extracts metadata, cross‑references Playnite’s exported game list, and produces a clean CSV report suitable for spreadsheet analysis.

The tool is built for transparency, reversibility, and portability — with special care taken to support Git Bash on Windows.

---

### **Key Features**

- **Automatic Playnite CSV integration**  
  Loads `titles_sources_ids.csv` (or a user‑specified file) and maps each game ID to its title and source.

- **Robust MP3 metadata extraction**  
  Reads duration, bitrate, size, ID3 tags, title, artist, and album.

- **AWK‑based CSV loader (Git Bash safe)**  
  Handles large Playnite exports (5,000+ entries) without freezing.

- **Clean, human‑readable CSV output**  
  Columns include:  
  `game_title, game_source, game_id, duration, bitrate, size, has_id3_tags, title, artist, album, file`

- **Automatic detection of misfiled or mismatched tracks**  
  Immediately surfaces incorrect folder assignments or missing metadata.

- **Versioned, modular design**  
  Each release is saved as `mp3_full_audit-vX.Y.Z.sh` for clarity and reproducibility.

---

### **How It Works (Backend Summary)**

#### **1. Playnite Metadata Loading**

The script loads Playnite’s exported CSV using a custom AWK parser that:

- Handles UTF‑8 safely  
- Handles quoted fields and commas  
- Strips BOM and CRLF  
- Populates associative arrays:  
  - `GAME_TITLE_BY_ID[id]`  
  - `GAME_SOURCE_BY_ID[id]`

This ensures fast, reliable lookups even with thousands of entries.

---

#### **2. Library Prescan**

The script scans the working directory for folders named like Playnite game IDs.  
For each folder, it:

- Counts MP3 files  
- Notes missing or empty folders  
- Prepares the audit list

This step is fast and gives early warnings about misnamed or misplaced content.

---

#### **3. MP3 Audit Loop**

For each MP3 file, the script extracts:

- Duration  
- Bitrate  
- File size  
- ID3 tag presence  
- Title / Artist / Album  

It then cross‑references the file’s parent folder with Playnite metadata to determine:

- Game title  
- Game source  
- Game ID  

All results are appended to the CSV.

---

#### **4. CSV Output**

The final CSV is written to:

``` Code
full_audit_YYYYMMDD_HHMMSS.csv
```

The column order is optimized for readability in spreadsheet tools like LibreOffice Calc.

---

### **Usage**

1. Place the script in the root folder containing your game‑ID‑named soundtrack folders.  
2. Ensure Playnite’s `titles_sources_ids.csv` is present (or be ready to specify another file).  
3. Run:

``` bash
bash mp3_full_audit-v1.4.x.sh
```

4. The script will:
   - Load Playnite metadata  
   - Scan your library  
   - Audit all MP3s  
   - Produce a CSV report  

---

### **Requirements**

- Git Bash (Windows) or any POSIX‑compatible shell  
- `ffprobe` (from FFmpeg) in PATH  
- Playnite’s exported `titles_sources_ids.csv` - this is optional, but if you choose to use it, use Library Exporter Advanced, select only Sources and IDs - the titles are already included - and strip off the date at the end of the filename.

---

### **Future Enhancements**

- **Missing‑Music Report**  
  A companion CSV listing all Playnite games with *no* associated MP3 files.

- **Integration with UniPlaySong**  
  Optional hooks for automated verification or metadata enrichment.

---

### **License**

MIT License (recommended for community tools)

---
---

## OLDER versions

### NEWEST Readme v1.1.0

#### MP3 Tools Suite  

##### Transparent, reversible, metadata-rich audio library utilities

This suite contains two Bash-based tools designed for safely analyzing and managing MP3 libraries. They are especially useful for large collections, game music libraries, and Playnite’s UniPlaySong extension — but they work perfectly well for *any* folder of MP3 files.

Both tools emphasize:

- Transparency  
- Reversibility  
- Safety  
- Metadata visibility  
- User choice (interactive or autonomous modes)

---

#### Tools Included

##### `mp3_reduce_tool.sh`

A full-featured utility for reducing MP3 files to 128 kbps with complete safety.

###### Features

- Preview reducible files (above 128 kbps)
- Reduce files to 128 kbps (creates `_reduced.mp3` copies)
- CSV export with batch totals or final totals
- Safe-delete mode (verifies reduced files before deleting originals)
- Color-coded output
- Interactive or autonomous display modes
- Optional directory argument

---

##### `mp3_full_audit.sh`

A comprehensive audit tool for *all* MP3 files in a directory.

###### Features

- Scans all MP3s recursively
- Extracts:
  - Bitrate  
  - File size  
  - Duration  
  - ID3 metadata (title, artist, album)  
  - ID3 tag presence  
- Optional Playnite metadata cross-referencing  
- Batch totals every 50 files (configurable)
- Cumulative totals
- CSV export with selectable totals mode
- Progress bar and pre-scan
- Color-coded output
- Optional directory argument

---

#### Playnite Metadata (Optional)

If you use Playnite and store music in folders named after game IDs (this method is used by the UniPlaySong extension!), the audit tool can enrich your CSV with game information.

##### How it works

1. Export a CSV from Playnite using the Library Exporter Advanced extension.  
2. Place the CSV in the same directory as the audit script.  
3. The script will automatically detect:

> Name,Sources,Id

4. MP3 folder names are matched to the `Id` column.
5. The audit CSV gains:

- `game_id`
- `game_title`
- `game_source`

##### If you don’t use Playnite

No problem — the script works perfectly without it.  
Playnite metadata is optional and only used if a CSV is present.

---

#### Requirements

- Git Bash (Windows) or any POSIX-compatible shell (Linux/macOS/WSL)
- `ffmpeg` and `ffprobe` in your PATH
- `stat`
- `bc`

##### Windows PATH setup

If you installed ffmpeg manually:

1. Add the `bin/` folder to your PATH  
2. Sign out and back in (or restart) to apply changes

---

#### Usage

##### Option A — Run inside the target directory

> cd "/path/to/music"
> ./mp3_reduce_tool.sh

##### Option B — Provide a directory argument

> ./mp3_reduce_tool.sh "/path/to/music"

Same for the audit tool.

---

#### Versioning

This project uses semantic versioning:

> MAJOR.MINOR.PATCH

---

### License

This project is released under the MIT License (see LICENSE file).

---

### Contributing

Pull requests, suggestions, and improvements are welcome — especially around metadata extraction, Playnite integration, and workflow enhancements.

### 1.0.0

#### MP3 Tools Suite

A pair of Bash utilities for analyzing and reducing MP3 files with complete transparency and safety. Designed for workflows like Playnite’s UniPlaySong extension, where predictable behavior and reversible operations matter.

##### Tools Included

###### **mp3_reduce_tool.sh**

- Preview reducible files  
- Reduce to 128 kbps  
- Export CSV  
- Safe-delete originals (with verification)  
- Color-coded output  
- Interactive or autonomous modes  

###### **mp3_full_audit.sh**

- Full audit of *all* MP3 files  
- CSV export  
- Batch and cumulative totals  
- Non-destructive  

##### Requirements

- Git Bash (Windows) or any POSIX shell  
- ffmpeg + ffprobe in PATH  
- stat, bc  

##### Usage

Run inside the music folder:

``` bash
./mp3_reduce_tool.sh
```

Or provide a directory:

``` bash
./mp3_reduce_tool.sh "/path/to/music"
```

Same for the audit tool.
