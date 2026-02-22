import subprocess
import json
from pathlib import Path


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
            "-v", "error",              # suppress warnings
            "-select_streams", "a:0",   # first audio stream
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

        # Extract bitrate
        bitrate = None
        if "streams" in data and data["streams"]:
            bitrate = data["streams"][0].get("bit_rate")

        # Extract duration
        duration = None
        if "format" in data:
            duration = data["format"].get("duration")

        # Convert types
        if bitrate is not None:
            bitrate = int(bitrate)
        if duration is not None:
            duration = float(duration)

        # File size
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

    print(f"\nScanning {music_dir} for MP3 files...\n")

    TARGET_BITRATE = 128000  # 128 kbps in bps
    MIN_SAVINGS_PERCENT = 20  # default threshold
    count = 0

    for mp3 in find_mp3_files(music_dir):
        info = ffprobe_audio_info(mp3)
        if info is None:
            print(f"Skipping (no metadata): {mp3}")
            continue

        bitrate = info["bitrate"]
        duration = info["duration"]
        size = info["size"]

        # Estimated reduced size at 128 kbps
        estimated_size = int((TARGET_BITRATE * duration) / 8)
        savings_bytes = size - estimated_size

        # Avoid negative or zero savings
        if savings_bytes <= 0:
            print(f"{mp3.name}:")
            print(f"  Bitrate: {bitrate} bps")
            print(f"  Skipping (would not shrink or would grow)")
            print("")
            continue

        # Calculate savings percent
        savings_percent = (savings_bytes / size) * 100

        # Apply threshold
        if savings_percent < MIN_SAVINGS_PERCENT:
            print(f"{mp3.name}:")
            print(f"  Bitrate: {bitrate} bps")
            print(f"  Savings: {savings_percent:.2f}% (below {MIN_SAVINGS_PERCENT}%)")
            print(f"  Skipping (below threshold)")
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

        count += 1

    print(f"Files meeting {MIN_SAVINGS_PERCENT}%+ savings: {count}\n")


# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
