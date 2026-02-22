# MP3 Tools Suite  

## Transparent, reversible, metadata‑rich audio utilities for Playnite & UniPlaySong

The MP3 Tools Suite provides safe, predictable utilities for analyzing, reducing, and enriching MP3 libraries — especially those managed by **Playnite** and the **UniPlaySong** extension, which stores soundtrack files in game‑ID‑named folders.

This project emphasizes:

- Transparency  
- Reversibility  
- Metadata visibility  
- Predictable, deterministic behavior  
- User choice (interactive or autonomous modes)  
- Safety above all else  

---

## 🚀 Current Status

### **Recommended Tool (Windows‑only):**  

**`reduce.py` — Python port (active development)**  
Located on the **`pre-release` branch`**.  
Versions **0.0.1 → 0.2.6** are already implemented.

### **Legacy Tools (WSL‑required):**  

- `mp3_reduce_tool.sh`  
- `mp3_full_audit.sh`  

These Bash tools remain stable and functional, but are no longer the primary focus of development.

### **Platform Support**

- **Windows 10/11:** Fully supported (Python port)  
- **Linux/WSL:** Deprecated — full removal planned for **v0.3.0**  
- **Git Bash:** Not supported (cannot handle subshells, xargs, or ffmpeg process management)

---

## ⚡ Quick Start (Python Reduce Tool)

```bash
python reduce.py --auto
python reduce.py --dir "E:\Music"
python reduce.py --minutes 30
python reduce.py --nocsv
```

---

## 🧰 Features (Python Port)

- Automatic MP3 reduction to 128 kbps  
- Safe deletion with ffprobe verification  
- PASS/SKIP/REDUCE audit entries  
- CSV reporting (optional suppression via `--nocsv`)  
- Auto mode (`--auto`)  
- Time‑window filtering (`--minutes`)  
- Directory selection (`--dir` / `--folder`)  
- Parallel ffmpeg workers  
- Windows‑native path handling  
- Logging with timestamps  
- Deterministic, transparent behavior  

The Python port is the future of this project and will eventually replace the Bash tools entirely.

---

## 📝 Command Line Flags (Python)

| Flag                | Description                                   |
|---------------------|-----------------------------------------------|
| `--auto`            | Run fully automatically (no prompts)          |
| `--dir`, `--folder` | Select folder to scan                         |
| `--minutes`         | Only process files modified in last X minutes |
| `--nocsv`           | Suppress CSV export                           |
| `--help`            | Show help text                                |

---

## 🧪 Python Port Details

The Python version of the reduce tool is under active development on the  
👉 **`pre-release` branch**

It includes:

- Full ffprobe‑based metadata extraction  
- Savings threshold logic  
- Reducible file list construction  
- Parallel processing  
- Logging  
- CSV export  
- Interactive and autonomous modes  
- Safe‑delete verification  
- Windows‑only design for Playnite users  

See `mp3_reduce_tool/python/RELEASES.md` on the `pre-release` branch for full details.

---

## 🛠 Legacy Bash Tools (Stable)

### `mp3_reduce_tool.sh` — v1.1.0  

**Requires WSL**

A safe, transparent utility for reducing MP3 files to 128 kbps.

#### Features

- Preview reducible files  
- Reduce to 128 kbps (`*_reduced.mp3`)  
- CSV export  
- Safe‑delete mode  
- Color‑coded output  
- Interactive or autonomous modes  
- Optional directory argument  

#### Notes

This tool is stable but no longer actively developed.  
The Python port supersedes it for Windows users.

---

### `mp3_full_audit.sh` — v1.4.6  

*A comprehensive Playnite‑aware audit tool for MP3 libraries.*

#### Features

- Recursive MP3 scanning  
- Extracts bitrate, duration, size, ID3 tags  
- Detects missing metadata  
- Playnite metadata integration  
- Spreadsheet‑safe CSV output  
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

## 🧩 Future Tools

### `enrich.py` (Planned)

A tool to fill in missing ID3 tags for MP3s downloaded via UniPlaySong’s YouTube integration.

Will set:

- Album = Playnite game title  
- Title = filename  

Artist tagging remains an open question.

---

### 🎮 Playnite Metadata Integration (Audit Tool)

The audit tool integrates with CSV exports from **Library Exporter Advanced**:

1. Export a CSV containing `Name, Sources, Id`  
2. Place it next to the audit script  
3. The script auto‑detects and loads it  
4. MP3 folder names (game IDs) are matched  
5. Output CSV gains:
   - `game_title`  
   - `game_source`  
   - `game_id`  

This is the expected workflow for Playnite users.

---

## 🧭 Roadmap

Long‑term possibilities include:

- Unified media‑management toolkit  
- UPS‑aware workflows  
- Generalized Playnite media auditing  
- Full Python migration (in progress)  
- Optional GUI or Playnite extension integration  

Development follows energy, interest, and community needs.

---

## 🧾 Versioning

This project uses semantic versioning:

```
MAJOR.MINOR.PATCH
```

---

## 📄 License

Released under the MIT License (see LICENSE.md).

---

## 🤝 Contributing

Pull requests and suggestions are welcome — especially around:

- Playnite integration  
- UniPlaySong compatibility  
- Metadata extraction  
- Workflow improvements  
- Python port testing  
- Future GUI or extension development  

---

## 🕰 Historical Note

The MP3 Tools Suite began as two simple Bash utilities for analyzing and reducing MP3 files with complete transparency. Over time, the audit tool evolved into a Playnite‑aware metadata engine, and the reduce tool is now undergoing a full Python rewrite to bring the same clarity and safety to a Windows‑only environment.
