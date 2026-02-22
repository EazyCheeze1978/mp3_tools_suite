import os
from pathlib import Path

def find_mp3_files(root: Path):
    for path in root.rglob("*.mp3"):
        yield path

def main():
    music_dir = Path(input("Enter directory to scan: ").strip('"'))
    if not music_dir.exists():
        print(f"Directory not found: {music_dir}")
        return

    print(f"Scanning {music_dir} for MP3 files...\n")

    count = 0
    for mp3 in find_mp3_files(music_dir):
        print(mp3)
        count += 1

    print(f"\nFound {count} MP3 files.")

if __name__ == "__main__":
    main()
