# **README for MP3 Tools Suite**

## **Readme current as of v1.4.6**

### **MP3 Tools Suite**  

#### *Transparent, reversible, metadata‑rich audio library utilities*

This suite contains two Bash‑based tools designed for safely analyzing and managing MP3 libraries. They are especially useful for [**Playnite**](https://playnite.link/) users and for those using the [**UniPlaySong** extension](https://github.com/aHuddini/UniPlaySong), which stores soundtrack files in game‑ID‑named folders.

Both tools emphasize:

- Transparency  
- Reversibility  
- Safety  
- Metadata visibility  
- User choice (interactive or autonomous modes)  
- Predictable, deterministic behavior  

---

### **Tools Included**

---

#### **`mp3_full_audit.sh` — v1.4.6 (Current Flagship Tool)**  

A comprehensive, Playnite‑aware audit tool for *all* MP3 files in a directory tree.

This is the most advanced tool in the suite and the one under active development. It is designed to work seamlessly with **Playnite’s Library Exporter Advanced** extension, enabling rich metadata cross‑referencing and game‑aware CSV output.

##### **Features (v1.4.6)**

- Scans all MP3s recursively  
- Extracts:
  - Bitrate  
  - File size  
  - Duration  
  - ID3 metadata (title, artist, album)  
  - ID3 tag presence  
- **Playnite metadata integration (expected workflow)**  
  - Uses exported CSV (`Name, Sources, Id`)  
  - Maps MP3 folders to Playnite game IDs  
  - Adds `game_title`, `game_source`, and `game_id` to the audit  
- **AWK‑based CSV loader**  
  - Handles UTF‑8, BOM, CRLF, quoted fields, embedded commas  
  - Scales to 5,000+ Playnite entries  
  - Fully Git‑Bash‑compatible  
- **Clean CSV output**  
  - Human‑friendly column order  
  - Fully escaped fields  
  - Spreadsheet‑safe  
- **Progress bar and pre‑scan**  
- **Batch totals and grand totals**  
- **Color‑coded output**  
- Optional directory argument  
- Non‑destructive and fully transparent  

##### **Intended Use**

This tool is ideal for:

- UniPlaySong users wanting to audit soundtrack coverage  
- Playnite users maintaining large game‑ID‑based music libraries  
- Anyone needing a metadata‑rich CSV of their MP3 collection  
- Future integration into Playnite or UniPlaySong (pending interest)  

---

#### **`mp3_reduce_tool.sh` — v1.1.0 (Legacy Tool, Pending Update)**  

A full‑featured utility for reducing MP3 files to 128 kbps with complete safety.

This was the first tool in the suite and will be modernized to match the audit tool’s robustness and CSV style. Until then, it remains fully functional but less advanced.

##### **Features**

- Preview reducible files (above 128 kbps)  
- Reduce files to 128 kbps (creates `_reduced.mp3` copies)  
- CSV export with batch totals or final totals  
- Safe‑delete mode (verifies reduced files before deleting originals)  
- Color‑coded output  
- Interactive or autonomous display modes  
- Optional directory argument  

##### **Future Plans**

- Bring CSV output in line with `mp3_full_audit`  
- Add Playnite‑aware reduction reporting  
- Add AWK‑based metadata loading  
- Improve safety checks and logging  

### Tools for the Future

#### `mp3_tag_enrich.sh` - tag MP3s with missing ID3 information

UniPlaySong includes a capability to download music from YouTube videos via [yt-dlp](https://github.com/yt-dlp/yt-dlp). The resulting downloads lack ID3 tags.

This prospective tool will scan, as with the other tools, all MP3s in a target directory, pair them with their game titles (again via the Playnite Library Exporter Advanced extension export) and set those as the album name tags, and set the filenames as the title tags.

(I don't know of anywhere in Playnite or any extension that exposes discrete composer information for the artist tags, and there also may be/usually are multiple composers for a game - if you know how to handle this, please reach out)

---

### **Playnite Metadata Integration**

The audit tool is designed to work with **Playnite’s Library Exporter Advanced** extension.

#### **Workflow**

1. Export a CSV from Playnite containing:  
   `Name, Sources, Id`
2. Place the CSV in the same directory as the audit script.  
3. The script automatically detects and loads it.  
4. MP3 folder names (game IDs) are matched to the `Id` column.  
5. The audit CSV gains:
   - `game_title`  
   - `game_source`  
   - `game_id`  

This workflow is now the *expected* mode of operation for the audit tool.

---

### **Requirements**

- Git Bash (Windows) or any POSIX‑compatible shell (Linux/macOS/WSL)  
- `ffmpeg` and `ffprobe` in your PATH  
- `stat`  
- `bc`  

#### **Windows PATH setup**

If you installed ffmpeg manually:

1. Add the `bin/` folder to your PATH  
2. Sign out and back in (or restart)  

---

### **Usage**

#### **Option A — Run inside the target directory**

``` Code
cd "/path/to/music"
./mp3_full_audit.sh
```

##### **Option B — Provide a directory argument**

``` Code
./mp3_full_audit.sh "/path/to/music"
```

Same for the reduce tool.

---

### What's next for the tools - and going forward

I'd like to be able to introduce parallelization to the extent that Bash allows - and maybe at some point upgrade the entire codebase to Python for more robust parallel execution.

Of course, the big big goal is going to be integration, in whole or in part, with UniPlaySong, that most sonic of Playnite extensions! I will of course give a massive gratitude burst and shout-out to Huddini, who inspired me to make these tools - if you haven't checked his work out, I highly recommend it!

### **Versioning**

This project uses semantic versioning:

``` Code
MAJOR.MINOR.PATCH
```

---

### **License**

This project is released under the MIT License (see LICENSE.md).

---

### **Contributing**

Pull requests, suggestions, and improvements are welcome — especially around:

- Playnite integration  
- UniPlaySong compatibility  
- Metadata extraction  
- Workflow enhancements  
- Future GUI or Playnite extension development  

---

### **Historical Note (v1.0.0)**

The MP3 Tools Suite began as a pair of simple Bash utilities for analyzing and reducing MP3 files with complete transparency and safety. Over time, the audit tool evolved into a Playnite‑aware metadata engine, and the reduce tool will follow.

---
