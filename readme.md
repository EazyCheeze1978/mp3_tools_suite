# MP3 Tools Suite  

## Transparent, reversible, metadata‑rich audio utilities for Playnite & UniPlaySong

This suite provides tools for safely analyzing, reducing, and enriching MP3 libraries — especially those managed by **Playnite** and the **UniPlaySong** extension, which stores soundtrack files in game‑ID‑named folders.

The project emphasizes:

- Transparency  
- Reversibility  
- Metadata visibility  
- Predictable, deterministic behavior  
- User choice (interactive or autonomous modes)  
- Safety above all else  

---

## 🚧 Active Development (Python Port)

A new **cross‑platform Python version** of the reduce tool is under active development on the  
👉 **`pre-release` branch**  
with versions **0.0.1 → 0.1.2** already implemented.

This new version includes:

- Full ffprobe‑based metadata extraction  
- Time‑filter logic  
- Savings threshold logic  
- Reducible file list construction  
- Parallel ffmpeg workers  
- Logging with timestamps  
- PASS/SKIP audit entries  
- Confirmation prompts  
- CSV scaffolding  

See `mp3_reduce_tool/python/RELEASES.md` on the `pre-release` branch for full details.

The Bash tools below remain stable and fully functional, but the Python port will eventually become the recommended version for most users.

---

## 🛠 Tools Included (Stable Bash Versions)

### `mp3_reduce_tool.sh` — v1.1.0  

**(Requires Windows Subsystem for Linux — see Requirements below)**

A safe, transparent utility for reducing MP3 files to 128 kbps.  
This was the first tool in the suite and remains fully functional, though less advanced than the audit tool.

### Features

- Preview reducible files (above 128 kbps)  
- Reduce files to 128 kbps (`*_reduced.mp3`)  
- CSV export (batch totals or final totals)  
- Safe‑delete mode (verifies reduced files before deleting originals)  
- Color‑coded output  
- Interactive or autonomous modes  
- Optional directory argument  

#### Future Plans for Reduce

- Align CSV output with `mp3_full_audit`  
- Improve safety checks and logging  
- Optional Playnite‑aware reporting (now largely handled by UniPlaySong)  
- Parallelization (completed in Python port)  
- Eventual migration to Python for cross‑platform support  

---

### `mp3_full_audit.sh` — v1.4.6  

*A comprehensive Playnite‑aware audit tool for MP3 libraries.*

This tool scans all MP3s recursively and produces a metadata‑rich CSV, optionally enriched with Playnite game metadata via **Library Exporter Advanced**.

#### Features

- Recursive MP3 scanning  
- Extracts bitrate, duration, size, ID3 tags  
- Detects missing metadata  
- Playnite metadata integration (expected workflow)  
- Robust AWK‑based CSV loader  
- Clean, spreadsheet‑safe CSV output  
- Batch totals and grand totals  
- Color‑coded output  
- Optional directory argument  
- Non‑destructive and fully transparent  

#### Intended Use

Ideal for:

- UniPlaySong users auditing soundtrack coverage  
- Playnite users maintaining large game‑ID‑based libraries  
- Anyone needing a metadata‑rich CSV of their MP3 collection  

---

## 🧪 Future Tools

## `mp3_tag_enrich.sh` (Planned)

A tool to fill in missing ID3 tags for MP3s downloaded via UniPlaySong’s YouTube integration (yt‑dlp).  
Will set:

- Album = Playnite game title  
- Title = filename  

Artist tagging remains an open question due to inconsistent composer metadata.

---

## 🎮 Playnite Metadata Integration (Audit Tool)

The audit tool integrates with **Library Exporter Advanced**:

1. Export a CSV containing `Name, Sources, Id`  
2. Place it next to the audit script  
3. The script auto‑detects and loads it  
4. MP3 folder names (game IDs) are matched to the CSV  
5. Output CSV gains:
   - `game_title`  
   - `game_source`  
   - `game_id`  

This is now the *expected* workflow.

---

## 🧩 Requirements (Bash Tools)

### Windows Subsystem for Linux (WSL)

A hard requirement for the Bash versions.

Git Bash cannot reliably handle:

- subshells  
- xargs parallelization  
- ffmpeg process management  

WSL provides the full Linux environment needed for stable operation.

### Installing ffmpeg in WSL (Ubuntu)

```bash
sudo apt update
sudo apt install ffmpeg
