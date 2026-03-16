#!/usr/bin/env python3
# ------------------------------------------------------------
# MP3 Reduce Tool — v0.3.2
# ------------------------------------------------------------
# Changes in 0.3.2:
# - Added optional bitrate and savings limiters (disabled by default)
# - Homogenization-first behavior: all files are processed unless
#   user explicitly enables limiters via CLI flags
# - Bitrate limiter (--force-bitrate) restores "skip <=128 kbps"
# - Savings limiter (--force-savings) restores "skip <20% savings"
# - _reduced skip logic remains mandatory
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
# SECTION: Spinner (always enabled)
# ------------------------------------------------------------
def spinner(stop_event, total, counter):
    spin = itertools.cycle(["-", "\\", "|", "/"])
    while not stop_event.is_set():
        done = counter["count"]
        print(f"\rProcessing {done}/{total} {next(spin)}", end="", flush=True)
        time.sleep(0.1)

# ------------
# Begin Part 2
# ------------
# ------------------------------------------------------------
# SECTION: CSV Input Loader (unchanged from 0.3.1)
# ------------------------------------------------------------
def load_csv_paths(csv_path: Path, ups_root: Path | None):
    """
    Load file paths from a CSV file.

    Priority:
    1. If FilePath is present in the CSV, use it directly.
    2. If FilePath is missing, derive the path from GameId using ups_root.

    Returns:
        paths: list[Path]
        missing_filepaths: bool
    """
    paths = []
    missing_filepaths = False

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            file_path = row.get("FilePath", "").strip()
            game_id = row.get("GameId", "").strip()

            if file_path:
                paths.append(Path(file_path))
                continue

            if not game_id:
                continue

            missing_filepaths = True

            if ups_root is not None:
                derived_folder = ups_root / "Games" / game_id
                for mp3 in derived_folder.glob("*.mp3"):
                    paths.append(mp3)

    return paths, missing_filepaths


# ------------------------------------------------------------
# SECTION: Main Program
# ------------------------------------------------------------
def main():
    # ffmpeg/ffprobe detection
    try:
        ffmpeg_cmd, ffprobe_cmd = detect_ffmpeg_windows_only()
    except RuntimeError as e:
        print(f"Environment error: {e}")
        return

    print("Detected environment: Windows (native Python)")
    print(f"ffmpeg version: {get_ffmpeg_version(ffmpeg_cmd)}\n")

    # argparse
    parser = argparse.ArgumentParser(
        description=(
            "MP3 Reduce Tool — v0.3.2 (Python Port, Windows Only)\n\n"
            "Adds optional CSV Input support for UniPlaySong users.\n"
            "Adds optional bitrate and savings limiters (disabled by default).\n"
            "Homogenization-first behavior: all files are processed unless\n"
            "limiters are explicitly enabled.\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "--dir", "--folder",
        type=str,
        help="Folder to scan for MP3 files (ignored if --csv is used)."
    )

    parser.add_argument(
        "--minutes",
        type=int,
        default=None,
        help="Only process files modified in the last N minutes (ignored if --csv)."
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="Run fully automatically with no prompts."
    )

    parser.add_argument(
        "--nocsv",
        action="store_true",
        help="Suppress CSV export at the end of the run."
    )

    parser.add_argument(
        "--csv",
        type=str,
        help="Optional CSV file listing tracks to process."
    )

    # NEW IN 0.3.2 — optional limiters (disabled by default)
    parser.add_argument(
        "--force-bitrate",
        action="store_true",
        help="Enable bitrate limiter (skip files already 128 kbps or lower)."
    )

    parser.add_argument(
        "--force-savings",
        action="store_true",
        help="Enable savings limiter (skip files with <20% estimated savings)."
    )

    args = parser.parse_args()

    # Logging setup
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = Path(f"reduce_log_{timestamp_str}.txt")

    def log(msg):
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp()}] {msg}\n")

    csv_rows = []

    if args.auto:
        print("Auto mode enabled: proceeding without prompts.\n")

    if args.nocsv:
        print("--nocsv specified: CSV export will be skipped.\n")

    # NEW IN 0.3.2 — determine limiter behavior
    apply_bitrate_limit = args.force_bitrate
    apply_savings_limit = args.force_savings

    if apply_bitrate_limit:
        print("Bitrate limiter ENABLED (skip <=128 kbps).")
    else:
        print("Bitrate limiter DISABLED (homogenization mode).")

    if apply_savings_limit:
        print("Savings limiter ENABLED (skip <20% savings).")
    else:
        print("Savings limiter DISABLED (homogenization mode).")

    print()

    # ------------------------------------------------------------
    # CSV Input Override
    # ------------------------------------------------------------
    csv_paths = None
    ups_root = None

    if args.csv:
        csv_file = Path(args.csv)

        if not csv_file.exists():
            print(f"CSV file not found: {csv_file}")
            return

        print(f"CSV Input enabled: {csv_file}")

        temp_paths, missing_filepaths = load_csv_paths(csv_file, ups_root=None)

        if missing_filepaths:
            print(
                "\nSome CSV rows did not include FilePath.\n"
                "To locate these tracks, I need the path to your UniPlaySong folder.\n"
                "This is the folder that contains the 'Games' subfolder.\n"
                "\nExample:\n"
                "  C:/Playnite/ExtraMetadata/UniPlaySong\n"
            )

            if args.auto:
                print("Auto mode cannot prompt for UPS root. Aborting.")
                return

            ups_root_input = input("Enter UniPlaySong folder path: ").strip('"')
            ups_root = Path(ups_root_input)

            if not ups_root.exists():
                print(f"UPS root folder not found: {ups_root}")
                return

            csv_paths, _ = load_csv_paths(csv_file, ups_root)
        else:
            csv_paths = temp_paths

        if csv_paths:
            print(f"\nCSV provided {len(csv_paths)} file(s).")
        else:
            print("\nCSV provided no usable file paths.")
            return

    # ------------------------------------------------------------
    # Directory selection (ignored if CSV Input is used)
    # ------------------------------------------------------------
    if csv_paths is None:
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

        discovered_files = list(music_dir.rglob("*.mp3"))
    else:
        cutoff = None
        discovered_files = csv_paths
        print("\nUsing file list from CSV Input.\n")

# --------
# Begin Part 3
# --------
    # ------------------------------------------------------------
    # PREVIEW LOOP (updated for optional limiters in 0.3.2)
    # ------------------------------------------------------------
    TARGET_BITRATE = 128000
    MIN_SAVINGS_PERCENT = 20

    reducible_files = []
    total_estimated_savings = 0
    file_info = {}

    for mp3 in discovered_files:

        # Skip if a reduced version already exists (mandatory)
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

        # Skip if outside time window (directory mode only)
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

        # Skip if filename already contains "_reduced"
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

        # ffprobe metadata
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

        # OPTIONAL LIMITER (0.3.2): bitrate threshold
        if apply_bitrate_limit and bitrate <= TARGET_BITRATE:
            reason = "already 128 kbps or lower (bitrate limiter enabled)"
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

        # Estimate output size at 128 kbps
        estimated_size = int((TARGET_BITRATE / 8) * duration)
        savings_bytes = size - estimated_size
        savings_percent = (savings_bytes / size) * 100 if size > 0 else 0

        # OPTIONAL LIMITER (0.3.2): savings threshold
        if apply_savings_limit and savings_percent < MIN_SAVINGS_PERCENT:
            reason = "insufficient savings (savings limiter enabled)"
            log(f"SKIP ({reason}): {mp3.name}")
            csv_rows.append({
                "filename": mp3.name,
                "bitrate": bitrate,
                "size_bytes": size,
                "estimated_size_bytes": estimated_size,
                "savings_bytes": savings_bytes,
                "savings_percent": round(savings_percent, 2),
                "action": "SKIP",
                "skip_reason": reason,
            })
            continue

        # Otherwise: file is eligible for processing
        reducible_files.append(mp3)
        total_estimated_savings += max(savings_bytes, 0)

        file_info[mp3] = {
            "bitrate": bitrate,
            "size": size,
            "estimated_size": estimated_size,
            "savings_bytes": savings_bytes,
            "savings_percent": savings_percent,
        }

        log(f"READY: {mp3.name} ({round(savings_percent, 2)}% savings est.)")

    # ------------------------------------------------------------
    # SUMMARY BEFORE PROCESSING
    # ------------------------------------------------------------
    print(f"\nFound {len(reducible_files)} file(s) eligible for processing.")
    print(f"Estimated total savings: {total_estimated_savings / (1024*1024):.2f} MB\n")

    if not args.auto:
        proceed = input("Proceed with reduction? (y/n): ").strip().lower()
        if proceed != "y":
            print("Aborted by user.")
            return

    # ------------------------------------------------------------
    # PROCESSING LOOP
    # ------------------------------------------------------------
    print("\nStarting reduction...\n")

    stop_event = threading.Event()
    counter = {"count": 0}

    spinner_thread = threading.Thread(
        target=spinner,
        args=(stop_event, len(reducible_files), counter),
        daemon=True
    )
    spinner_thread.start()

    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for mp3 in reducible_files:
            info = file_info[mp3]
            futures.append(executor.submit(reduce_worker, {
                "path": mp3,
                "ffmpeg_cmd": ffmpeg_cmd,
                "savings_bytes": info["savings_bytes"],
                "savings_percent": info["savings_percent"],
            }))

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            counter["count"] += 1

    stop_event.set()
    spinner_thread.join()
    print("\n")

    # ------------------------------------------------------------
    # POST-PROCESSING: SAFE DELETION
    # ------------------------------------------------------------
    print("Verifying and deleting originals...\n")

    for r in results:
        if not r["success"]:
            log(f"REDUCE FAILED: {r['src']}")
            continue

        original = Path(r["src"])
        reduced = Path(r["dst"])

        verify_and_delete(original, reduced, ffprobe_cmd, log)

        csv_rows.append({
            "filename": original.name,
            "bitrate": "",
            "size_bytes": "",
            "estimated_size_bytes": r["savings_bytes"],
            "savings_bytes": r["savings_bytes"],
            "savings_percent": round(r["savings_percent"], 2),
            "action": "REDUCED",
            "skip_reason": "",
        })

    # ------------------------------------------------------------
    # CSV EXPORT
    # ------------------------------------------------------------
    if not args.nocsv:
        csv_path = Path(f"reduce_results_{timestamp_str}.csv")
        write_csv(csv_rows, csv_path)
        print(f"CSV written: {csv_path}")

    print("\nDone.\n")


if __name__ == "__main__":
    main()
