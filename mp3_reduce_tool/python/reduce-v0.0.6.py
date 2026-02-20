import subprocess
import json
from pathlib import Path
import time


# ------------------------------------------------------------
# ffprobe: read bitrate, duration, and file size
# ------------------------------------------------------------
def ffprobe_audio_info(path: Path):
    """
    Returns a dict with bitrate (int), duration (float), and size (int bytes).
    Returns None if ffprobe fails or metadata is missing.
    """
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
# Main program
# ------------------------------------------------------------
def main():
    music_dir = Path(input("Enter directory to scan: ").strip('"'))
    if not music_dir.exists():
        print(f"Directory not found: {music_dir}")
        return

    # Ask for time filter
    try:
        minutes = int(input("Process only files modified in the last X minutes (0 = all): "))
    except ValueError:
        print("Invalid number. Using 0 (all files).")
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

    reducible_files = []  # <-- NEW LIST

    for mp3 in find_mp3_files(music_dir):

        # Time filter
        if cutoff is not None:
            if mp3.stat().st_mtime < cutoff:
                continue

        # Skip files already reduced
        if "_reduced" in mp3.name.lower():
            print(f"{mp3.name}:")
            print("  Skipping (already reduced)")
            print("")
            continue

        info = ffprobe_audio_info(mp3)
        if info is None:
            print(f"{mp3.name}:")
            print("  Skipping (no metadata)")
            print("")
            continue

        bitrate = info["bitrate"]
        duration = info["duration"]
        size = info["size"]

        # Skip files already at or below 128 kbps
        if bitrate <= TARGET_BITRATE:
            print(f"{mp3.name}:")
            print(f"  Bitrate: {bitrate} bps")
            print("  Skipping (already 128 kbps or lower)")
            print("")
            continue

        # Estimated reduced size
        estimated_size = int((TARGET_BITRATE * duration) / 8)
        savings_bytes = size - estimated_size

        # Skip if no savings
        if savings_bytes <= 0:
            print(f"{mp3.name}:")
            print(f"  Bitrate: {bitrate} bps")
            print("  Skipping (would not shrink or would grow)")
            print("")
            continue

        # Savings percent
        savings_percent = (savings_bytes / size) * 100

        # Skip if below threshold
        if savings_percent < MIN_SAVINGS_PERCENT:
            print(f"{mp3.name}:")
            print(f"  Bitrate: {bitrate} bps")
            print(f"  Savings: {savings_percent:.2f}% (below {MIN_SAVINGS_PERCENT}%)")
            print("  Skipping (below threshold)")
            print("")
            continue

        # If we reach here, file is reducible
        print(f"{mp3.name}:")
        print(f"  Bitrate:        {bitrate} bps")
        print(f"  Duration:       {duration:.2f} s")
        print(f"  Size:           {size} bytes")
        print(f"  Est. reduced:   {estimated_size} bytes")
        print(f"  Savings:        {savings_bytes} bytes ({savings_percent:.2f}%)")
        print("")

        # Add to reducible list
        reducible_files.append({
            "path": mp3,
            "bitrate": bitrate,
            "duration": duration,
            "size": size,
            "estimated_size": estimated_size,
            "savings_bytes": savings_bytes,
            "savings_percent": savings_percent
        })

    # Summary
    print(f"Files meeting {MIN_SAVINGS_PERCENT}%+ savings: {len(reducible_files)}\n")

    # Optional: show list
    if reducible_files:
        print("Reducible files:")
        for item in reducible_files:
            print(f"  {item['path'].name}")
        print("")


# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
