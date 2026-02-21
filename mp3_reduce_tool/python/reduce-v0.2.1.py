#!/usr/bin/env python3
# ------------------------------------------------------------
# MP3 Reduce Tool — v0.2.1
# WSL Directory Input Fix + Path Normalization Improvements
#
# Major features:
# - Fixes WSL directory input bug (0.2.0 regression)
# - Robust normalization of user-provided directory paths
# - Windows → WSL path conversion
# - Leading-backslash correction
# - Mixed-separator correction
# - Correct .exists() checks using normalized paths
# - All 0.2.0 features preserved
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
import platform
import shutil
import os


# ------------------------------------------------------------
# Utility: timestamped logging
# ------------------------------------------------------------
def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ------------------------------------------------------------
# Environment detection
# ------------------------------------------------------------
def detect_environment():
    """
    Detects whether we are running on:
    - Windows native Python
    - WSL Python
    - Linux

    Returns:
        ffmpeg_cmd (str)
        ffprobe_cmd (str)
        mode (str): "windows", "wsl", "linux"
        description (str): human-readable environment summary
    """
    system = platform.system().lower()

    if system == "windows":
        base_desc = "Windows"
    elif system == "linux":
        base_desc = "Linux"
    else:
        base_desc = system.capitalize()

    # Detect WSL
    is_wsl = False
    try:
        with open("/proc/version", "r", encoding="utf-8") as f:
            if "microsoft" in f.read().lower():
                is_wsl = True
    except Exception:
        pass

    # WSL Python
    if system == "linux" and is_wsl:
        ffmpeg = shutil.which("ffmpeg")
        ffprobe = shutil.which("ffprobe")
        if not ffmpeg or not ffprobe:
            raise RuntimeError("ffmpeg/ffprobe not found in WSL environment")
        desc = "WSL (Linux kernel under Windows)"
        return ffmpeg, ffprobe, "wsl", desc

    # Windows native Python
    if system == "windows":
        ffmpeg = shutil.which("ffmpeg")
        ffprobe = shutil.which("ffprobe")
        if ffmpeg and ffprobe:
            desc = f"{base_desc} (native Python)"
            return ffmpeg, ffprobe, "windows", desc
        raise RuntimeError("ffmpeg/ffprobe not found on Windows PATH")

    # Plain Linux
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg and ffprobe:
        desc = f"{base_desc} (native)"
        return ffmpeg, ffprobe, "linux", desc

    raise RuntimeError("ffmpeg/ffprobe not found on this system")


# ------------------------------------------------------------
# Normalize directory input BEFORE checking .exists()
# ------------------------------------------------------------
def normalize_directory_input(raw: str, mode: str) -> str:
    """
    Normalizes user-provided directory paths so .exists() works correctly.

    Handles:
    - Leading backslashes (\mnt\e\...) → /mnt/e/...
    - Windows paths (E:\folder) → /mnt/e/folder (WSL)
    - Mixed separators (E:/folder\sub) → /mnt/e/folder/sub
    - Leaves POSIX paths untouched
    """
    raw = raw.strip()

    # Fix accidental leading backslashes
    if raw.startswith("\\"):
        raw = raw.replace("\\", "/")

    # Fix mixed separators
    raw = raw.replace("\\", "/")

    # WSL: Convert Windows paths → /mnt/<drive>/
    if mode == "wsl":
        if ":" in raw:
            drive, rest = raw.split(":", 1)
            drive = drive.lower()
            rest = rest.replace("\\", "/")
            return f"/mnt/{drive}{rest}"
        return raw

    # Windows: convert slashes to forward slashes
    if mode == "windows":
        return raw.replace("\\", "/")

    # Linux: return as-is
    return raw


# ------------------------------------------------------------
# Path normalization for ffmpeg
# ------------------------------------------------------------
def normalize_path(path: Path, mode: str) -> str:
    """
    Converts a Path object into a string suitable for ffmpeg/ffprobe.
    """
    expanded = os.path.expandvars(str(path))
    resolved = str(Path(expanded).resolve())

    # UNC paths
    if resolved.startswith("\\\\"):
        return resolved.replace("\\", "/")

    if mode == "windows":
        return resolved.replace("\\", "/")

    if mode == "wsl":
        # Convert Windows-style paths to /mnt/<drive>/
        if ":" in resolved and "\\" in resolved:
            drive, rest = resolved.split(":", 1)
            drive = drive.lower()
            rest = rest.replace("\\", "/")
            return f"/mnt/{drive}{rest}"
        return resolved

    return resolved
# ------------------------------------------------------------
# Reduced file detection
# ------------------------------------------------------------
def reduced_exists(path: Path) -> bool:
    if path.suffix.lower() != ".mp3":
        return False
    reduced = path.with_name(path.stem + "_reduced.mp3")
    return reduced.exists()


# ------------------------------------------------------------
# CSV writer
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
# ffprobe wrapper
# ------------------------------------------------------------
def ffprobe_audio_info(path: Path, ffprobe_cmd: str, mode: str):
    try:
        cmd = [
            ffprobe_cmd,
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=bit_rate",
            "-show_entries", "format=duration",
            "-of", "json",
            normalize_path(path, mode),
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

        return {
            "bitrate": bitrate,
            "duration": duration,
            "size": size
        }

    except Exception:
        return None


# ------------------------------------------------------------
# Worker function
# ------------------------------------------------------------
def reduce_worker(item):
    src = item["path"]
    dst = src.with_name(src.stem + "_reduced.mp3")

    ffmpeg_cmd = item["ffmpeg_cmd"]
    mode = item["mode"]

    cmd = [
        ffmpeg_cmd,
        "-y",
        "-i", normalize_path(src, mode),
        "-vn",
        "-acodec", "libmp3lame",
        "-b:a", "128k",
        normalize_path(dst, mode),
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
# Safe deletion workflow
# ------------------------------------------------------------
def verify_and_delete(original: Path, reduced: Path, ffprobe_cmd: str, mode: str, log):
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

        info = ffprobe_audio_info(reduced, ffprobe_cmd, mode)
        if info is None:
            log(f"DELETE SKIP (reduced failed ffprobe): {original}")
            return

        original.unlink()
        log(f"DELETE: {original} → removed after verifying {reduced.name}")

    except Exception as e:
        log(f"DELETE ERROR ({original}): {e}")


# ------------------------------------------------------------
# Spinner
# ------------------------------------------------------------
def spinner(stop_event, total, counter):
    spin = itertools.cycle(["-", "\\", "|", "/"])
    while not stop_event.is_set():
        done = counter["count"]
        print(f"\rProcessing {done}/{total} {next(spin)}", end="", flush=True)
        time.sleep(0.1)
# ------------------------------------------------------------
# Main program
# ------------------------------------------------------------
def main():
    # Detect environment
    try:
        ffmpeg_cmd, ffprobe_cmd, mode, env_desc = detect_environment()
    except RuntimeError as e:
        print(f"Environment error: {e}")
        return

    print(f"Detected environment: {env_desc}")
    print(f"ffmpeg mode: {mode}\n")

    # argparse
    parser = argparse.ArgumentParser(
        description="MP3 Reduce Tool — v0.2.1 (Python Port)"
    )

    parser.add_argument("--dir", type=str, help="Directory to scan for MP3 files")
    parser.add_argument("--minutes", type=int, default=None,
                        help="Only process files modified in the last X minutes")

    args = parser.parse_args()

    # Logging
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = Path(f"reduce_log_{timestamp_str}.txt")

    def log(msg):
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp()}] {msg}\n")

    csv_rows = []

    # Directory selection
    if args.dir:
        raw_dir = args.dir.strip('"')
    else:
        raw_dir = input("Enter directory to scan: ").strip('"')

    # Normalize directory input BEFORE checking .exists()
    normalized_dir = normalize_directory_input(raw_dir, mode)
    music_dir = Path(normalized_dir)

    if not music_dir.exists():
        print(f"Directory not found: {normalized_dir}")
        return

    # Minutes selection
    if args.minutes is not None:
        minutes = args.minutes
    else:
        try:
            minutes = int(input("Process only files modified in the last X minutes (0=all): "))
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

        info = ffprobe_audio_info(mp3, ffprobe_cmd, mode)
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
            "mode": mode,
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
        csv_name = f"reduce_report_{timestamp_str}.csv"
        write_csv(csv_rows, Path(csv_name))
        return

    print("\nReducible files:")
    for item in reducible_files:
        print(f"  {item['path'].name} ({item['savings_percent']:.2f}%)")

    print(f"\nTotal estimated savings: {total_estimated_savings / (1024*1024):.2f} MB")

    # -------------------------------
    # Reduction confirmation prompt
    # -------------------------------
    choice = input("\nProceed with reduction? (y/n): ").strip().lower()
    if choice != "y":
        print("Aborted.")
        log("SUMMARY: Reduction aborted by user.")
        csv_name = f"reduce_report_{timestamp_str}.csv"
        write_csv(csv_rows, Path(csv_name))
        return
    # -------------------------------
    # Parallel reduction
    # -------------------------------
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

    print(f"\nDone! Reduced {counter['count']} files.\n")
    log(f"SUMMARY: Reduced {counter['count']} files successfully.")

    # -------------------------------
    # Deletion prompt
    # -------------------------------
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

            verify_and_delete(original, reduced, ffprobe_cmd, mode, log)
    else:
        log("SUMMARY: User chose not to delete originals.")

    # -------------------------------
    # Final CSV write
    # -------------------------------
    csv_name = f"reduce_report_{timestamp_str}.csv"
    write_csv(csv_rows, Path(csv_name))

    print(f"CSV report written to: {csv_name}")
    print(f"Log file written to: {log_path.name}")


# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
