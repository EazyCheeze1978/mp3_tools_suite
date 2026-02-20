# MP3 Reduce Tool — Python Port (Pre‑Release Branch)

This branch contains the **active development** of the cross‑platform Python rewrite of the MP3 Reduce Tool.  
It is experimental, fast‑moving, and may include features not yet available in the stable Bash version on `main`.

If you're here, you're either:

- testing new features  
- contributing to development  
- curious about the future direction of the suite  

Either way — welcome.

---

## 🚀 Project Status

The Python port is now fully functional through **v0.1.2**, including:

- ffprobe‑based metadata extraction  
- savings calculations  
- time‑filter logic  
- skip‑reason reporting  
- reducible file list construction  
- confirmation prompts  
- parallel ffmpeg workers  
- spinner‑based progress indicator  
- timestamped logging  
- PASS/SKIP/REDUCE audit entries  
- CSV scaffolding  

This branch evolves rapidly and may contain breaking changes between versions.

For a full version history, see:  
👉 `mp3_reduce_tool/python/RELEASES.md`

---

## 🧩 Why a Python Port?

The original Bash tools require **Windows Subsystem for Linux (WSL)** due to:

- subshell behavior  
- xargs parallelization  
- ffmpeg process orchestration  

Python removes these barriers and enables:

- true cross‑platform support  
- cleaner logic  
- easier installation  
- better logging  
- richer metadata handling  
- future integration with UniPlaySong or Playnite  

The long‑term goal is for the Python version to become the **primary** reduce tool.

---

## 🧪 Current Features (v0.1.x Series)

### ✔ Full Preview Mode  

- Bitrate, duration, size  
- Estimated reduced size  
- Savings percentage  
- Detailed skip reasons  
- PASS entries for reducible files  

### ✔ Parallel Reduction  

- Multi‑core ffmpeg workers  
- Silent worker processes  
- Spinner‑based progress indicator  
- Clean, non‑interleaved output  

#### ✔ Logging  

- Timestamped entries  
- SKIP, PASS, REDUCE, SUMMARY  
- Lexicographically sortable formatting  

#### ✔ Safety  

- Confirmation prompt before reduction  
- Non‑destructive output (`*_reduced.mp3`)  
- No automatic deletion  

#### ✔ CSV Scaffolding  

- Internal row collection for PASS/REDUCE  
- CSV export coming in v0.1.3+  

---

## 🛣 Roadmap (Short‑Term)

### **v0.1.3 — CSV Export**

- Write `reduce_report.csv`  
- Spreadsheet‑friendly formatting  
- Optional command‑line flag  

### **v0.1.4 — Command‑Line Arguments**

- `--dir`  
- `--minutes`  
- `--auto` (skip confirmation)  
- `--csv`  

### **v0.1.5 — Windows Compatibility Layer**

- Auto‑detect platform  
- Normalize paths  
- Use Windows ffmpeg if available  

---

## 🗺 Milestone Roadmap

The Python port follows a clear semantic versioning roadmap.  
Each Milestone represents a development phase with its own goals and issues.

### **v0.1.x — Parallelization & Logging (Current)**

Core functionality: parallel workers, logging, skip‑reason reporting, confirmation prompts, CSV scaffolding.

### **v0.2.x — Windows Compatibility & CLI Flags**

Cross‑platform support, command‑line arguments, CSV export, path normalization.

### **v0.3.x — Packaging & Distribution**

pip packaging, PyInstaller builds, version metadata, optional GUI wrapper.

### **v1.0.0 — First Stable Python Release**

Feature‑complete, cross‑platform, documented, and ready for general use.

### **Future Ideas & Explorations**

Long‑term possibilities: GUI, Playnite integration, multi‑format support, unified media toolkit.

---

## 🛣 Roadmap (Long‑Term)

- Full cross‑platform packaging (pip or PyInstaller)  
- Optional GUI wrapper  
- Integration hooks for UniPlaySong  
- Unified media‑management toolkit  
- Support for additional audio formats  
- Optional Playnite metadata enrichment  

These are possibilities, not promises — development follows energy and community interest.

---

## 🧭 Directory Structure

mp3_reduce_tool/
python/
reduce-v0.0.1.py
reduce-v0.0.2.py
...
reduce-v0.1.2.py
RELEASES.md
README.md   ← this file

Older Bash versions are preserved in:

mp3_reduce_tool/bash (deprecated!)/

---

## 🧪 Testing Notes

- ffmpeg must be installed and available in PATH  
- WSL is recommended for development  
- Windows support is planned but not yet complete  
- Parallel reduction will increase CPU usage (expected)  
- Logs are written to the working directory  

If you encounter issues, please include:

- the log file  
- your Python version  
- your OS  
- the command used to run the script  

---

## 🤝 Contributing

Contributions are welcome — especially around:

- Windows compatibility  
- CSV export  
- command‑line argument parsing  
- performance improvements  
- documentation  
- testing across platforms  

---

## 📄 License

This branch follows the project’s MIT License (see `LICENSE.md` on main).

---

## 🕰 Historical Note

The Python port began as a simple sequential rewrite of the Bash tool.  
Through iterative vibe‑coding, it evolved into a parallel, logged, auditable utility with a clear roadmap toward full cross‑platform support.

This branch represents that evolution in real time.

---
