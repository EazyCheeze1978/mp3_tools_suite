# MP3 Reduce Tool — Python Port (Pre‑Release Branch)

This branch contains the **active development** of the Windows‑only Python rewrite of the MP3 Reduce Tool.  
It is experimental, fast‑moving, and represents the future direction of the MP3 Tools Suite.

If you're here, you're likely:

- testing new features  
- contributing to development  
- curious about the upcoming Windows‑only release  

Either way — welcome.

---

## 🚀 Project Status (v0.2.x Series)

The Python port is now fully functional through **v0.2.6**, including:

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
- CSV export (with optional suppression via `--nocsv`)  
- Windows‑native path handling  
- Auto mode (`--auto`)  

This branch evolves rapidly and may contain breaking changes between versions.

For a full version history, see:  
👉 `mp3_reduce_tool/python/RELEASES.md`

---

## 🧩 Why a Python Port?

The original Bash tools required **Windows Subsystem for Linux (WSL)** due to:

- subshell behavior  
- xargs parallelization  
- ffmpeg process orchestration  

Python removes these barriers and enables:

- cleaner logic  
- easier installation  
- richer metadata handling  
- parallel processing  
- safer file operations  
- better logging  
- future integration with UniPlaySong or Playnite  

### ❗ Important Change (Post‑0.2.x)

Although Python *could* be cross‑platform, the project is now **Windows‑only** going forward.  
This aligns with:

- Playnite being Windows‑only  
- UniPlaySong being Windows‑only  
- the complexity and instability of WSL testing  
- the needs of actual users  

Linux/WSL support will be fully removed in **v0.3.0**.

---

## 🧪 Current Features (v0.2.x)

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

### ✔ Logging  

- Timestamped entries  
- SKIP, PASS, REDUCE, SUMMARY  
- Lexicographically sortable formatting  

### ✔ Safety  

- Confirmation prompt before reduction  
- Non‑destructive output (`*_reduced.mp3`)  
- Safe‑delete verification  
- Optional auto mode (`--auto`)  

### ✔ CSV Export  

- PASS/SKIP/REDUCE rows  
- Timestamped filenames  
- Optional suppression via `--nocsv`  

---

## 🧭 Roadmap (Short‑Term)

### **v0.2.7 — Documentation & Help Text**

- Updated README files  
- Internal `--help` output  
- Cleanup of comments and structure  

### **v0.3.0 — Linux/WSL Removal**

- Remove environment detection  
- Remove WSL path normalization  
- Remove Linux branches  
- Simplify codebase  
- Windows‑only assumptions everywhere  

### **v0.3.x — Packaging & Distribution**

- PyInstaller builds  
- Version metadata  
- Optional GUI wrapper  

---

## 🗺 Milestone Roadmap (High‑Level)

### **v0.2.x — Windows Compatibility & CLI Flags (Current)**

- Windows‑native behavior  
- CLI arguments  
- CSV export  
- Auto mode  
- Logging improvements  

### **v0.3.x — Cleanup & Packaging**

- Remove Linux code  
- Simplify architecture  
- Prepare for distribution  

### **v1.0.0 — First Stable Python Release**

- Fully documented  
- Packaged  
- Windows‑only  
- Feature‑complete  

### **Future Ideas**

- GUI  
- Playnite integration  
- Multi‑format support  
- Unified media toolkit  

These are possibilities, not promises — development follows energy and community interest.

---

## 📁 Directory Structure

```
mp3_reduce_tool/
  python/
    reduce-v0.0.1.py
    reduce-v0.0.2.py
    ...
    reduce-v0.2.6.py
    RELEASES.md
    README.md   ← this file

  bash/ (deprecated)
    mp3_reduce_tool.sh
    mp3_full_audit.sh
```

---

## 🧪 Testing Notes

- ffmpeg must be installed and available in PATH  
- Windows is the only supported platform  
- Parallel reduction will increase CPU usage (expected)  
- Logs are written to the working directory  

If you encounter issues, please include:

- the log file  
- your Python version  
- your OS (Windows only)  
- the command used to run the script  

---

## 🤝 Contributing

Contributions are welcome — especially around:

- Windows compatibility  
- CSV export  
- command‑line argument parsing  
- performance improvements  
- documentation  
- testing  

---

## 📄 License

This branch follows the project’s MIT License (see `LICENSE.md` on main).

---

## 🕰 Historical Note

The Python port began as a simple sequential rewrite of the Bash tool.  
Through iterative development, it evolved into a parallel, logged, auditable utility with a clear roadmap toward a Windows‑only stable release.

This branch represents that evolution in real time.
