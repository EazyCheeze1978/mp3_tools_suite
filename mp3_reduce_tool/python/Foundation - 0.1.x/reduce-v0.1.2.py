#!/usr/bin/env python3
import subprocess
import json
from pathlib import Path
import time
import concurrent.futures
import itertools
import threading
from datetime import datetime


# ------------------------------------------------------------
# Utility: timestamped logging
# ------------------------------------------------------------
def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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
    # Create log file
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = Path(f"reduce_log_{timestamp_str}.txt")

    def log(msg):
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp()}] {msg}\n")

    # CSV scaffolding
    csv_rows = []  # Will hold dicts for future CSV export

    music_dir = Path(input("Enter directory to scan: ").strip('"'))
    if not music_dir.exists():
        print(f"Directory not found: {music_dir}")
        return

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
        if cutoff is not None and mp3.stat().st_mtime < cutoff:
            reason = "outside time window"
            log(f"SKIP ({reason}): {mp3.name}")
            continue

        # Already reduced
        if "_reduced" in mp3.name.lower():
            print(f"{mp3.name}:")
            print("  Skipping (already reduced)\n")
            reason = "already reduced"
            log(f"SKIP ({reason}): {mp3.name}")
            continue

        # Metadata
        info = ffprobe_audio_info(mp3)
        if info is None:
            print(f"{mp3.name}:")
            print("  Skipping (no metadata)\n")
            reason = "no metadata"
            log(f"SKIP ({reason}): {mp3.name}")
            continue

        bitrate = info["bitrate"]
        duration = info["duration"]
        size = info["size"]

        # Already low bitrate
        if bitrate <= TARGET_BITRATE:
            print(f"{mp3.name}:")
            print(f"  Bitrate: {bitrate} bps")
            print("  Skipping (already 128 kbps or lower)\n")
            reason = "already 128 kbps or lower"
            log(f"SKIP ({reason}): {mp3.name}")
            continue

        # Estimated reduced size
        estimated_size = int((TARGET_BITRATE * duration) / 8)
        savings_bytes = size - estimated_size

        if savings_bytes <= 0:
            print(f"{mp3.name}:")
            print(f"  Bitrate: {bitrate} bps")
            print("  Skipping (would not shrink or would grow)\n")
            reason = "would not shrink"
            log(f"SKIP ({reason}): {mp3.name}")
            continue

        savings_percent = (savings_bytes / size) * 100

        if savings_percent < MIN_SAVINGS_PERCENT:
            print(f"{mp3.name}:")
            print(f"  Bitrate: {bitrate} bps")
            print(f"  Savings: {savings_percent:.2f}% (below {MIN_SAVINGS_PERCENT}%)")
            print("  Skipping (below threshold)\n")
            reason = f"below threshold ({savings_percent:.2f}%)"
            log(f"SKIP ({reason}): {mp3.name}")
            continue

        # PASS entry
        log(f"PASS (reducible {savings_percent:.2f}%): {mp3.name}")

        # CSV scaffolding
        csv_rows.append({
            "filename": mp3.name,
            "bitrate": bitrate,
            "duration": duration,
            "size": size,
            "estimated_size": estimated_size,
            "savings_bytes": savings_bytes,
            "savings_percent": savings_percent,
            "action": "PASS"
        })

        # Print preview
        print(f"{mp3.name}:")
        print(f"  Bitrate:        {bitrate} bps")
        print(f"  Duration:       {duration:.2f} s")
        print(f"  Size:           {size} bytes")
        print(f"  Est. reduced:   {estimated_size} bytes")
        print(f"  Savings:        {savings_bytes} bytes ({savings_percent:.2f}%)\n")

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
        return

    print("\nReducible files:")
    for item in reducible_files:
        print(f"  {item['path'].name} ({item['savings_percent']:.2f}%)")

    print(f"\nTotal estimated savings: {total_estimated_savings / (1024*1024):.2f} MB")

    choice = input("\nProceed with reduction? (y/n): ").strip().lower()
    if choice != "y":
        print("Aborted.")
        log("SUMMARY: Reduction aborted by user.")
        return

    log(f"SUMMARY: Starting reduction of {len(reducible_files)} files.")

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

            # CSV scaffolding
            csv_rows.append({
                "filename": Path(result["src"]).name,
                "bitrate": None,
                "duration": None,
                "size": None,
                "estimated_size": None,
                "savings_bytes": result["savings_bytes"],
                "savings_percent": result["savings_percent"],
                "action": "REDUCE"
            })

    stop_event.set()
    spinner_thread.join()

    print(f"\nDone! Reduced {counter['count']} files.\n")
    log(f"SUMMARY: Reduced {counter['count']} files successfully.")

    # CSV export scaffolding (not yet writing a file)
    # Future version will add:
    # write_csv(csv_rows, "reduce_report.csv")


# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
