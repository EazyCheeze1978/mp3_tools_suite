# MP3 Reduce Tool — Release Notes (Python Port, Pre‑Release Branch)

This document tracks the evolution of the Python port of the MP3 Reduce Tool.  
These versions represent the active development line and may differ from the stable versions on the `main` branch. [Ya think, Copilot?! :)]

---

## Further evolutions!

### **v0.1.2 — Logging Enhancements & CSV Scaffolding**  

**Date:** 2026‑02‑20  
**Type:** Patch Release  

#### Added

- Timestamped log entries for all actions (SKIP, PASS, REDUCE, SUMMARY).
- PASS entries now logged for full auditability.
- Improved SKIP formatting for lexicographic sorting:
  - `SKIP (reason): filename.mp3`
- CSV scaffolding added:
  - Internal `csv_rows` list collects PASS and REDUCE data.
  - CSV writing will be implemented in a future version.

#### Notes

- All v0.1.1 features preserved.
- No changes to reduction logic or parallel behavior.

---

### **v0.1.1 — Logging, Summary, Confirmation**  

**Date:** 2026‑02‑20  
**Type:** Patch Release  

#### Added

- Full logging system:
  - Skip reasons
  - Reduction results
  - Final summary
- Summary of reducible files before reduction.
- Total estimated savings displayed.
- Confirmation prompt before starting reduction.
- Clean separation between preview and reduction phases.

#### Notes

- First version with a real audit trail.
- Parallel workers remain unchanged from v0.1.0.

---

### **v0.1.0 — Parallel FFmpeg Workers**  

**Date:** 2026‑02‑20  
**Type:** Minor Release  

#### Added

- True parallel reduction using `ProcessPoolExecutor`.
- Dedicated worker function for ffmpeg.
- Spinner‑based progress indicator.
- Silent workers (no interleaved output).
- Clean progress reporting: `Processing N/M`.

#### Notes

- First “production‑grade” Python version.
- Preview mode preserved exactly as in 0.0.x.
- Significant performance improvement over sequential versions.

---

## Preliminaries!

### **0.0.x Series — Sequential Development & Core Logic**

These versions represent the foundational work of the Python port.  
All were sequential, single‑process versions focused on correctness and parity with the Bash tool.

---

#### **v0.0.6 — Reducible File List**  

**Added**

- Full reducible file list construction.
- Savings calculations stored for later use.
- Summary of reducible files printed.

---

#### **v0.0.5 — Time‑Filter Logic**  

**Added**

- “Modified in last X minutes” filter.
- Cutoff timestamp calculation.
- Skip reasons for time‑filtered files.

---

#### **v0.0.4 — Savings Threshold Logic**  

**Added**

- 20% minimum savings threshold.
- Skip reasons for below‑threshold files.

---

#### **v0.0.3 — Estimated Size Calculation**  

**Added**

- Estimated reduced size at 128 kbps.
- Skip reasons for files that would not shrink.

---

#### **v0.0.2 — Metadata Extraction**  

**Added**

- ffprobe integration for bitrate, duration, and size.
- Skip reasons for missing metadata.

---

#### **v0.0.1 — Initial Python Port**  

**Added**

- Basic directory scanning.
- Sequential preview of MP3 files.
- Initial structure for future parity with Bash version.

---

### End of Release Notes
