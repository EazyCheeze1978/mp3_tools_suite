# MP3 Reduce Tool — Python Port  

## Release History (Pre‑Release Branch)

This document tracks the evolution of the Python rewrite of the MP3 Reduce Tool.  
All versions listed here are **pre‑release**, experimental, and Windows‑only unless otherwise noted.

---

## 📘 Version Index

- [MP3 Reduce Tool — Python Port](#mp3-reduce-tool--python-port)
  - [Release History (Pre‑Release Branch)](#release-history-prerelease-branch)
  - [📘 Version Index](#-version-index)
  - [0.0.x — Foundations](#00x--foundations)
    - [**v0.0.1**](#v001)
    - [**v0.0.2**](#v002)
    - [**v0.0.3**](#v003)
    - [**v0.0.4**](#v004)
  - [0.1.x — Parallelization \& Logging](#01x--parallelization--logging)
    - [**v0.1.0**](#v010)
    - [**v0.1.1**](#v011)
    - [**v0.1.2**](#v012)
    - [**v0.1.3**](#v013)
  - [0.2.x — Windows Compatibility \& CLI Flags](#02x--windows-compatibility--cli-flags)
    - [**v0.2.0**](#v020)
    - [**v0.2.1**](#v021)
    - [**v0.2.2**](#v022)
    - [**v0.2.3**](#v023)
    - [**v0.2.4**](#v024)
    - [**v0.2.5**](#v025)
    - [**v0.2.6**](#v026)
    - [**v0.2.7**](#v027)
  - [v0.3.0 — Windows‑Only Simplification \& Codebase Cleanup](#v030--windowsonly-simplification--codebase-cleanup)
    - [🔥 Major Changes](#-major-changes)
    - [🧹 Internal Cleanup](#-internal-cleanup)
    - [🎯 Why This Matters](#-why-this-matters)
    - [🧪 Behavior Changes](#-behavior-changes)
    - [📌 Notes](#-notes)
  - [1.0.0 — Planned: First Stable Python Release](#100--planned-first-stable-python-release)
    - [Goals](#goals)
  - [🕰 Historical Note](#-historical-note)

---

## 0.0.x — Foundations  

Early prototypes establishing the core architecture.

### **v0.0.1**

- First Python prototype  
- Sequential reduction  
- Basic ffprobe metadata extraction  
- Minimal logging  

### **v0.0.2**

- Added savings calculations  
- Added skip‑reason logic  
- Improved metadata handling  

### **v0.0.3**

- Added PASS/SKIP audit rows  
- Added timestamped log file  
- Improved error handling  

### **v0.0.4**

- Introduced directory scanning  
- Added `_reduced.mp3` detection  
- Added estimated size calculations  

---

## 0.1.x — Parallelization & Logging  

Core functionality becomes stable and performant.

### **v0.1.0**

- Introduced parallel ffmpeg workers  
- Added worker task structure  
- Added silent worker mode  

### **v0.1.1**

- Added spinner‑based progress indicator  
- Improved output formatting  
- Added lexicographically sortable logs  

### **v0.1.2**

- Added confirmation prompt before reduction  
- Added non‑destructive output (`*_reduced.mp3`)  
- Added safe‑delete verification logic (initial draft)  

### **v0.1.3**

- Added CSV scaffolding (internal row collection)  
- Added PASS/REDUCE row structure  
- Prepared for full CSV export  

---

## 0.2.x — Windows Compatibility & CLI Flags  

The tool becomes Windows‑native, user‑friendly, and automation‑ready.

### **v0.2.0**

- Added Windows path normalization  
- Added environment detection (Windows / WSL / Linux)  
- Added ffmpeg/ffprobe auto‑detection  
- Added improved error messages  

### **v0.2.1**

- Added `--dir` / `--folder` directory selection  
- Added `--minutes` time‑window filtering  
- Added improved skip‑reason reporting  

### **v0.2.2**

- Added full CSV export (timestamped filenames)  
- Added PASS/SKIP/REDUCE rows to CSV  
- Added spreadsheet‑safe formatting  

### **v0.2.3**

- Added improved logging structure  
- Added summary reporting  
- Added total estimated savings calculation  

### **v0.2.4**

- Added Windows‑native behavior refinements  
- Improved path handling  
- Improved error handling for missing metadata  

### **v0.2.5**

- Added `--auto` mode  
  - Skips all prompts  
  - Performs reduction  
  - Performs safe deletion  
  - Writes CSV automatically  
- Major quality‑of‑life improvement for batch workflows  

### **v0.2.6**

- Added `--nocsv` flag to suppress CSV export  
- Added interactive CSV prompt when not in auto mode  
- Polished user experience  
- Cleaned up prompt flow and messaging  

### **v0.2.7**

- Documentation overhaul  
- Updated README files  
- Internal `--help` output  
- Comment cleanup  
- Preparation for Linux removal in 0.3.0  

---

## v0.3.0 — Windows‑Only Simplification & Codebase Cleanup  

**Release Date:** 2026‑02‑23  
**Milestone:** 0.3.x — Cleanup & Preparation for CSV Input

This release marks a major turning point for the Python port.  
After extensive testing and real‑world usage, the project is now officially **Windows‑only**, fully aligned with Playnite and UniPlaySong’s ecosystem. All Linux/WSL support has been removed, resulting in a cleaner, faster, and more maintainable codebase.

### 🔥 Major Changes

- **Removed all Linux and WSL support**
  - No more environment detection  
  - No more WSL path normalization  
  - No more Linux branches or fallback logic  
  - No more `mode` variable throughout the script  

- **Simplified path handling**
  - `normalize_path()` is now Windows‑only  
  - Directory normalization is straightforward and predictable  

- **Simplified ffmpeg/ffprobe detection**
  - Clean Windows‑only check  
  - Clear error message if tools are missing  

- **Spinner always enabled**
  - No more WSL‑based disabling  
  - Cleaner, more consistent user experience  

### 🧹 Internal Cleanup

- Removed ~60 lines of legacy cross‑platform code  
- Removed all comments referencing Linux/WSL  
- Removed environment‑specific branches in worker, deletion, and preview logic  
- Reduced cognitive load for future contributors  
- Script is now easier to read, maintain, and extend  

### 🎯 Why This Matters

This cleanup:

- eliminates entire classes of bugs  
- removes the need to test multiple environments  
- aligns the tool with its real user base  
- prepares the codebase for upcoming CSV Input support  
- makes the project emotionally and technically sustainable  

### 🧪 Behavior Changes

- No functional changes to reduction logic  
- No changes to CSV export  
- No changes to auto mode  
- No changes to logging  
- Only platform‑related behavior was removed  

### 📌 Notes

- The message “Detected environment: Windows (native Python)” remains for now as a harmless reminder of the project’s evolution.  
- May be removed in a future patch (0.3.1).  

---

This release completes the transition from a cross‑platform prototype to a focused, Windows‑native tool ready for deeper integration with Playnite and UniPlaySong.

---

## 1.0.0 — Planned: First Stable Python Release  

The first fully stable, documented, packaged release.

### Goals

- Windows‑only, fully supported  
- Packaged via PyInstaller  
- Complete documentation  
- Stable CLI  
- Optional GUI wrapper (stretch goal)  
- Ready for general use by Playnite & UniPlaySong users  

---

## 🕰 Historical Note

The Python port began as a simple sequential rewrite of the Bash tool.  
Through iterative development, it evolved into a parallel, logged, auditable utility with a clear roadmap toward a Windows‑only stable release.

This file documents that evolution in real time.
