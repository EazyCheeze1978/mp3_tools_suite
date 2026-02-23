#!/usr/bin/env python3
# ------------------------------------------------------------
# MP3 Reduce Tool — v0.3.0
# ------------------------------------------------------------
# Changes in 0.3.0:
# - Removed all Linux/WSL support
# - Removed environment detection
# - Removed mode variable entirely
# - Simplified path normalization for Windows-only
# - Simplified directory normalization
# - Spinner always enabled (no WSL disabling)
# ------------------------------------------------------------

import subprocess
import json
from pathlib import Path
import time
import concurrent.futures
import itertools
import threading
from datetime import datetime
import csv
import argparse
import shutil
import os
import sys


# ------------------------------------------------------------
# SECTION: Utility
# ------------------------------------------------------------
def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ------------------------------------------------------------
# SECTION: ffmpeg/ffprobe Detection (Windows-only)
# ------------------------------------------------------------
def detect_ffmpeg_windows_only():
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")

    if not ffmpeg or not ffprobe:
        raise RuntimeError(
            "ffmpeg/ffprobe not found on PATH.\n"
            "Please install ffmpeg and ensure both ffmpeg.exe and ffprobe.exe "
            "are available in your system PATH."
        )

    return ffmpeg, ffprobe


# ------------------------------------------------------------
# SECTION: ffmpeg Version Detection
# ------------------------------------------------------------
def get_ffmpeg_version(ffmpeg_cmd):
    try:
        result = subprocess.run(
            [ffmpeg_cmd, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        first_line = result.stdout.splitlines()[0]
        return first_line
    except Exception:
        return "Unknown ffmpeg version"


# ------------------------------------------------------------
# SECTION: Directory Input Normalization (Windows-only)
# ------------------------------------------------------------
def normalize_directory_input(raw: str) -> str:
    raw = raw.strip()
    raw = raw.replace("\\", "/")
    return raw


# ------------------------------------------------------------
# SECTION: Path Normalization for ffmpeg (Windows-only)
# ------------------------------------------------------------
def normalize_path(path: Path) -> str:
    expanded = os.path.expandvars(str(path))
    resolved = str(Path(expanded).resolve())
    return resolved.replace("\\", "/")


# ------------------------------------------------------------
# SECTION: Reduced File Detection
# ------------------------------------------------------------
def reduced_exists(path: Path) -> bool:
    if path.suffix.lower() != ".mp3":
        return False
    return path.with_name(path.stem + "_reduced.mp3").exists()


# ------------------------------------------------------------
# SECTION: CSV Writer
# ------------------------------------------------------------
def write_csv(rows, path: Path):
    if not rows:
        return

    columns = [
        "filename",
        "bitrate",
        "size_bytes",
        "estimated_size_bytes",
        "savings_bytes",
        "savings_percent",
        "action",
        "skip_reason",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([
                row.get("filename", ""),
                row.get("bitrate", ""),
                row.get("size_bytes", ""),
                row.get("estimated_size_bytes", ""),
                row.get("savings_bytes", ""),
                row.get("savings_percent", ""),
                row.get("action", ""),
                row.get("skip_reason", ""),
            ])


# ------------------------------------------------------------
# SECTION: ffprobe Wrapper
# ------------------------------------------------------------
def ffprobe_audio_info(path: Path, ffprobe_cmd: str):
    try:
        cmd = [
            ffprobe_cmd,
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=bit_rate",
            "-show_entries", "format=duration",
            "-of", "json",
            normalize_path(path),
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )

        if not result.stdout.strip():
            return None

        data = json.loads(result.stdout)

        bitrate = None
        if "streams" in data and data["streams"]:
            bitrate = data["streams"][0].get("bit_rate")

        duration = None
        if "format" in data:
            duration = data["format"].get("duration")

        if bitrate is not None:
            bitrate = int(bitrate)
        if duration is not None:
            duration = float(duration)

        size = path.stat().st_size

        if bitrate is None or duration is None:
            return None

        return {"bitrate": bitrate, "duration": duration, "size": size}

    except Exception:
        return None


# ------------------------------------------------------------
# SECTION: Worker Function
# ------------------------------------------------------------
def reduce_worker(item):
    src = item["path"]
    dst = src.with_name(src.stem + "_reduced.mp3")

    cmd = [
        item["ffmpeg_cmd"],
        "-y",
        "-i", normalize_path(src),
        "-vn",
        "-acodec", "libmp3lame",
        "-b:a", "128k",
        normalize_path(dst),
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    success = (result.returncode == 0) and dst.exists() and dst.stat().st_size > 0

    return {
        "src": str(src),
        "dst": str(dst),
        "savings_bytes": item["savings_bytes"],
        "savings_percent": item["savings_percent"],
        "success": success,
    }


# ------------------------------------------------------------
# SECTION: Safe Deletion
# ------------------------------------------------------------
def verify_and_delete(original: Path, reduced: Path, ffprobe_cmd: str, log):
    try:
        if not reduced.exists():
            log(f"DELETE SKIP (no reduced file): {original}")
            return

        if reduced.stat().st_size <= 0:
            log(f"DELETE SKIP (reduced size 0): {original}")
            return

        if reduced.stat().st_size >= original.stat().st_size:
            log(f"DELETE SKIP (reduced not smaller): {original}")
            return

        if reduced.stat().st_mtime <= original.stat().st_mtime:
            log(f"DELETE SKIP (reduced not newer): {original}")
            return

        info = ffprobe_audio_info(reduced, ffprobe_cmd)
        if info is None:
            log(f"DELETE SKIP (reduced failed ffprobe): {original}")
            return

        original.unlink()
        log(f"DELETE: {original} → removed")

    except Exception as e:
        log(f"DELETE ERROR ({original}): {e}")


# ------------------------------------------------------------
# SECTION: Spinner (always enabled now)
# ------------------------------------------------------------
def spinner(stop_event, total, counter):
    spin = itertools.cycle(["-", "\\", "|", "/"])
    while not stop_event.is_set():
        done = counter["count"]
        print(f"\rProcessing {done}/{total} {next(spin)}", end="", flush=True)
        time.sleep(0.1)


# ------------------------------------------------------------
# SECTION: Main Program
# ------------------------------------------------------------
def main():
    # ffmpeg/ffprobe detection (Windows-only)
    try:
        ffmpeg_cmd, ffprobe_cmd = detect_ffmpeg_windows_only()
    except RuntimeError as e:
        print(f"Environment error: {e}")
        return

    print("Detected environment: Windows (native Python)")
    print(f"ffmpeg version: {get_ffmpeg_version(ffmpeg_cmd)}\n")

    # argparse with descriptive help text
    parser = argparse.ArgumentParser(
        description=(
            "MP3 Reduce Tool — v0.3.0 (Python Port, Windows Only)\n\n"
            "Safely reduces MP3 files to 128 kbps using ffmpeg, with full metadata "
            "inspection, skip‑reason reporting, parallel processing, and optional "
            "automatic mode. Designed for Playnite and UniPlaySong users who maintain "
            "large game‑ID‑based soundtrack libraries.\n\n"
            "Notes:\n"
            "  • Output files are written as *_reduced.mp3 alongside originals.\n"
            "  • Safe‑delete verification ensures reduced files are valid before originals are removed.\n"
            "  • Logs are written to reduce_log_<timestamp>.txt.\n"
            "  • CSV reports are written to reduce_report_<timestamp>.csv unless suppressed with --nocsv.\n"
            "  • Windows is the only supported platform as of v0.3.x.\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "--dir", "--folder",
        type=str,
        help=(
            "Folder to scan for MP3 files. If omitted, the current working\n"
            "directory is used (or auto‑selected in --auto mode)."
        )
    )

    parser.add_argument(
        "--minutes",
        type=int,
        default=None,
        help=(
            "Only process files modified in the last N minutes.\n"
            "Use 0 to process all files. Default: 0."
        )
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help=(
            "Run fully automatically with no prompts. Performs reduction,\n"
            "safe‑delete verification, and CSV export without user input."
        )
    )

    parser.add_argument(
        "--nocsv",
        action="store_true",
        help=(
            "Suppress CSV export at the end of the run. By default, a\n"
            "timestamped CSV report is written containing PASS, SKIP, and\n"
            "REDUCE entries."
        )
    )

    args = parser.parse_args()

    # Logging setup
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = Path(f"reduce_log_{timestamp_str}.txt")

    def log(msg):
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp()}] {msg}\n")

    csv_rows = []

    # Auto-mode message
    if args.auto:
        print("Auto mode enabled: proceeding without prompts.\n")

    # nocsv message
    if args.nocsv:
        print("--nocsv specified: CSV export will be skipped.\n")

    # Directory selection
    if args.dir:
        raw_dir = args.dir.strip('"')
    else:
        if args.auto:
            raw_dir = os.getcwd()
            print(f"No folder specified. Auto mode using current folder: {raw_dir}")
        else:
            raw_dir = input("Enter directory to scan: ").strip('"')

    normalized_dir = normalize_directory_input(raw_dir)
    music_dir = Path(normalized_dir)

    if not music_dir.exists():
        print(f"Directory not found: {normalized_dir}")
        return

    # Minutes selection
    if args.minutes is not None:
        minutes = args.minutes
    else:
        if args.auto:
            minutes = 0
        else:
            try:
                minutes = int(input(
                    "Process only files modified in the last X minutes (0=all): "
                ))
            except ValueError:
                minutes = 0

    cutoff = None
    if minutes > 0:
        cutoff = time.time() - (minutes * 60)
        print(f"\nOnly processing files modified in the last {minutes} minutes.\n")
    else:
        print("\nProcessing all files.\n")

    print(f"Scanning {music_dir} for MP3 files...\n")

    TARGET_BITRATE = 128000
    MIN_SAVINGS_PERCENT = 20

    reducible_files = []
    total_estimated_savings = 0
    file_info = {}

    # Preview mode
    for mp3 in music_dir.rglob("*.mp3"):

        if reduced_exists(mp3):
            reason = "_reduced version exists"
            log(f"SKIP ({reason}): {mp3.name}")
            csv_rows.append({
                "filename": mp3.name,
                "bitrate": "",
                "size_bytes": "",
                "estimated_size_bytes": "skip",
                "savings_bytes": "skip",
                "savings_percent": "skip",
                "action": "SKIP",
                "skip_reason": reason,
            })
            continue

        if cutoff is not None and mp3.stat().st_mtime < cutoff:
            reason = "outside time window"
            log(f"SKIP ({reason}): {mp3.name}")
            csv_rows.append({
                "filename": mp3.name,
                "bitrate": "",
                "size_bytes": "",
                "estimated_size_bytes": "skip",
                "savings_bytes": "skip",
                "savings_percent": "skip",
                "action": "SKIP",
                "skip_reason": reason,
            })
            continue

        if "_reduced" in mp3.name.lower():
            reason = "already reduced"
            log(f"SKIP ({reason}): {mp3.name}")
            csv_rows.append({
                "filename": mp3.name,
                "bitrate": "",
                "size_bytes": "",
                "estimated_size_bytes": "skip",
                "savings_bytes": "skip",
                "savings_percent": "skip",
                "action": "SKIP",
                "skip_reason": reason,
            })
            continue

        info = ffprobe_audio_info(mp3, ffprobe_cmd)
        if info is None:
            reason = "no metadata"
            log(f"SKIP ({reason}): {mp3.name}")
            csv_rows.append({
                "filename": mp3.name,
                "bitrate": "",
                "size_bytes": "",
                "estimated_size_bytes": "skip",
                "savings_bytes": "skip",
                "savings_percent": "skip",
                "action": "SKIP",
                "skip_reason": reason,
            })
            continue

        bitrate = info["bitrate"]
        duration = info["duration"]
        size = info["size"]

        if bitrate <= TARGET_BITRATE:
            reason = "already 128 kbps or lower"
            log(f"SKIP ({reason}): {mp3.name}")
            csv_rows.append({
                "filename": mp3.name,
                "bitrate": bitrate,
                "size_bytes": size,
                "estimated_size_bytes": "skip",
                "savings_bytes": "skip",
                "savings_percent": "skip",
                "action": "SKIP",
                "skip_reason": reason,
            })
            continue

        estimated_size = int((TARGET_BITRATE * duration) / 8)
        savings_bytes = size - estimated_size

        if savings_bytes <= 0:
            reason = "would not shrink"
            log(f"SKIP ({reason}): {mp3.name}")
            csv_rows.append({
                "filename": mp3.name,
                "bitrate": bitrate,
                "size_bytes": size,
                "estimated_size_bytes": "skip",
                "savings_bytes": "skip",
                "savings_percent": "skip",
                "action": "SKIP",
                "skip_reason": reason,
            })
            continue

        savings_percent = (savings_bytes / size) * 100

        if savings_percent < MIN_SAVINGS_PERCENT:
            reason = f"below threshold ({savings_percent:.2f}%)"
            log(f"SKIP ({reason}): {mp3.name}")
            csv_rows.append({
                "filename": mp3.name,
                "bitrate": bitrate,
                "size_bytes": size,
                "estimated_size_bytes": "skip",
                "savings_bytes": "skip",
                "savings_percent": "skip",
                "action": "SKIP",
                "skip_reason": reason,
            })
            continue

        log(f"PASS (reducible {savings_percent:.2f}%): {mp3.name}")
        csv_rows.append({
            "filename": mp3.name,
            "bitrate": bitrate,
            "size_bytes": size,
            "estimated_size_bytes": estimated_size,
            "savings_bytes": savings_bytes,
            "savings_percent": f"{savings_percent:.2f}",
            "action": "PASS",
            "skip_reason": "",
        })

        reducible_files.append({
            "path": mp3,
            "bitrate": bitrate,
            "duration": duration,
            "size": size,
            "estimated_size": estimated_size,
            "savings_bytes": savings_bytes,
            "savings_percent": savings_percent,
            "ffmpeg_cmd": ffmpeg_cmd,
        })

        file_info[str(mp3)] = {
            "bitrate": bitrate,
            "size": size,
            "estimated_size": estimated_size,
            "savings_bytes": savings_bytes,
            "savings_percent": savings_percent,
        }

        total_estimated_savings += savings_bytes

    # Summary
    print(f"Files meeting {MIN_SAVINGS_PERCENT}%+ savings: {len(reducible_files)}")

    if not reducible_files:
        print("Nothing to reduce.")
        log("SUMMARY: No reducible files.")

        # CSV export decision
        if not args.nocsv:
            if not args.auto:
                choice = input("Export CSV report? (Y/n): ").strip().lower()
                export_csv = (choice != "n")
            else:
                export_csv = True
        else:
            export_csv = False

        if export_csv:
            csv_name = f"reduce_report_{timestamp_str}.csv"
            write_csv(csv_rows, Path(csv_name))
            print(f"CSV report written to: {csv_name}")
        else:
            print("CSV export skipped.")

        return

    print("\nReducible files:")
    for item in reducible_files:
        print(f"  {item['path'].name} ({item['savings_percent']:.2f}%)")

    print(f"\nTotal estimated savings: {total_estimated_savings / (1024*1024):.2f} MB")

    # Reduction confirmation
    if args.auto:
        choice = "y"
    else:
        choice = input("\nProceed with reduction? (y/n): ").strip().lower()

    if choice != "y":
        print("Aborted.")
        log("SUMMARY: Reduction aborted by user.")

        # CSV export decision
        if not args.nocsv:
            if not args.auto:
                choice = input("Export CSV report? (Y/n): ").strip().lower()
                export_csv = (choice != "n")
            else:
                export_csv = True
        else:
            export_csv = False

        if export_csv:
            csv_name = f"reduce_report_{timestamp_str}.csv"
            write_csv(csv_rows, Path(csv_name))
            print(f"CSV report written to: {csv_name}")
        else:
            print("CSV export skipped.")

        return

    # ------------------------------------------------------------
    # Parallel reduction (spinner always enabled)
    # ------------------------------------------------------------
    print("\nStarting parallel reduction...\n")

    counter = {"count": 0}
    stop_event = threading.Event()

    spinner_thread = threading.Thread(
        target=spinner,
        args=(stop_event, len(reducible_files), counter),
        daemon=True
    )
    spinner_thread.start()

    reduction_results = []

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(reduce_worker, item) for item in reducible_files]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            reduction_results.append(result)
            counter["count"] += 1

            log(f"REDUCE ({result['savings_percent']:.2f}%): "
                f"{result['src']} → {result['dst']} (success={result['success']})")

            info = file_info.get(result["src"], None)

            if info is not None:
                bitrate = info["bitrate"]
                size = info["size"]
                estimated_size = info["estimated_size"]
                savings_bytes = info["savings_bytes"]
                savings_percent = info["savings_percent"]
            else:
                bitrate = ""
                size = ""
                estimated_size = ""
                savings_bytes = result["savings_bytes"]
                savings_percent = result["savings_percent"]

            csv_rows.append({
                "filename": Path(result["src"]).name,
                "bitrate": bitrate,
                "size_bytes": size,
                "estimated_size_bytes": estimated_size,
                "savings_bytes": savings_bytes,
                "savings_percent": f"{savings_percent:.2f}",
                "action": "REDUCE",
                "skip_reason": "",
            })

    stop_event.set()
    spinner_thread.join()
    print()

    print(f"\nDone! Reduced {counter['count']} files.\n")
    log(f"SUMMARY: Reduced {counter['count']} files successfully.")

    # ------------------------------------------------------------
    # Deletion prompt (auto-mode aware)
    # ------------------------------------------------------------
    if args.auto:
        delete_choice = "y"
    else:
        delete_choice = input(
            "Delete original files after verifying reduced versions? (y/n): "
        ).strip().lower()

    if delete_choice == "y":
        print("\nVerifying reduced files and deleting originals where safe...\n")
        for result in reduction_results:
            if not result["success"]:
                log(f"DELETE SKIP (reduction failed): {result['src']}")
                continue

            original = Path(result["src"])
            reduced = Path(result["dst"])

            if not original.exists():
                log(f"DELETE SKIP (original missing): {original}")
                continue

            verify_and_delete(original, reduced, ffprobe_cmd, log)
    else:
        log("SUMMARY: User chose not to delete originals.")

    # ------------------------------------------------------------
    # CSV export decision (final)
    # ------------------------------------------------------------
    if not args.nocsv:
        if not args.auto:
            choice = input("Export CSV report? (Y/n): ").strip().lower()
            export_csv = (choice != "n")
        else:
            export_csv = True
    else:
        export_csv = False

    if export_csv:
        csv_name = f"reduce_report_{timestamp_str}.csv"
        write_csv(csv_rows, Path(csv_name))
        print(f"CSV report written to: {csv_name}")
    else:
        print("CSV export skipped.")

    print(f"Log file written to: {log_path.name}")


# ------------------------------------------------------------
# SECTION: Entry Point
# ------------------------------------------------------------
if __name__ == "__main__":
    main()