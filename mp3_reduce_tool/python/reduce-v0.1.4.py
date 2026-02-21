#!/usr/bin/env python3
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


# ------------------------------------------------------------
# Utility: timestamped logging
# ------------------------------------------------------------
def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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
# ffprobe: read bitrate, duration, and file size
# ------------------------------------------------------------
def ffprobe_audio_info(path: Path):
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=bit_rate",
            "-show_entries", "format=duration",
            "-of", "json",
            str(path)
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )

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
# Find MP3 files recursively
# ------------------------------------------------------------
def find_mp3_files(root: Path):
    for path in root.rglob("*.mp3"):
        yield path


# ------------------------------------------------------------
# Worker function for ffmpeg reduction
# ------------------------------------------------------------
def reduce_worker(item):
    src = item["path"]
    dst = src.with_name(src.stem + "_reduced.mp3")

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(src),
        "-vn",
        "-acodec", "libmp3lame",
        "-b:a", "128k",
        str(dst)
    ]

    subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return {
        "src": str(src),
        "dst": str(dst),
        "savings_bytes": item["savings_bytes"],
        "savings_percent": item["savings_percent"]
    }


# ------------------------------------------------------------
# Simple spinner for progress display
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
    # -----------------------------
    # argparse setup
    # -----------------------------
    parser = argparse.ArgumentParser(
        description="MP3 Reduce Tool — v0.1.4 (Python Port)"
    )

    parser.add_argument(
        "--dir",
        type=str,
        help="Directory to scan for MP3 files"
    )

    parser.add_argument(
        "--minutes",
        type=int,
        default=None,
        help="Only process files modified in the last X minutes"
    )

    args = parser.parse_args()

    # -----------------------------
    # Logging setup
    # -----------------------------
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = Path(f"reduce_log_{timestamp_str}.txt")

    def log(msg):
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp()}] {msg}\n")

    # CSV collection
    csv_rows = []

    # -----------------------------
    # Directory selection
    # -----------------------------
    if args.dir:
        music_dir = Path(args.dir.strip('"'))
    else:
        music_dir = Path(input("Enter directory to scan: ").strip('"'))

    if not music_dir.exists():
        print(f"Directory not found: {music_dir}")
        return

    # -----------------------------
    # Minutes selection
    # -----------------------------
    if args.minutes is not None:
        minutes = args.minutes
    else:
        try:
            minutes = int(input("Process only files modified in the last X minutes (0 = all): "))
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

    # -----------------------------
    # Preview mode
    # -----------------------------
    for mp3 in find_mp3_files(music_dir):

        # Time filter
        if cutoff is not None and mp3.stat().st_m_mtime < cutoff:
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

        # Already reduced
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

        # Metadata
        info = ffprobe_audio_info(mp3)
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

        # Already low bitrate
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

        # Estimated reduced size
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

        # PASS entry
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
            "savings_percent": savings_percent
        })

        total_estimated_savings += savings_bytes

    # -----------------------------
    # Summary + confirmation
    # -----------------------------
    print(f"Files meeting {MIN_SAVINGS_PERCENT}%+ savings: {len(reducible_files)}")

    if not reducible_files:
        print("Nothing to reduce.")
        log("SUMMARY: No reducible files.")
        write_csv(csv_rows, Path("reduce_report.csv"))
        return

    print("\nReducible files:")
    for item in reducible_files:
        print(f"  {item['path'].name} ({item['savings_percent']:.2f}%)")

    print(f"\nTotal estimated savings: {total_estimated_savings / (1024*1024):.2f} MB")

    choice = input("\nProceed with reduction? (y/n): ").strip().lower()
    if choice != "y":
        print("Aborted.")
        log("SUMMARY: Reduction aborted by user.")
        write_csv(csv_rows, Path("reduce_report.csv"))
        return

    log(f"SUMMARY: Starting reduction of {len(reducible_files)} files.")

    file_info = {str(item["path"]): item for item in reducible_files}

    # -----------------------------
    # Parallel reduction
    # -----------------------------
    print("\nStarting parallel reduction...\n")

    counter = {"count": 0}
    stop_event = threading.Event()

    spinner_thread = threading.Thread(
        target=spinner,
        args=(stop_event, len(reducible_files), counter),
        daemon=True
    )
    spinner_thread.start()

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(reduce_worker, item) for item in reducible_files]

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            counter["count"] += 1

            log(f"REDUCE ({result['savings_percent']:.2f}%): "
                f"{result['src']} → {result['dst']}")

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

    write_csv(csv_rows, Path("reduce_report.csv"))


# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
