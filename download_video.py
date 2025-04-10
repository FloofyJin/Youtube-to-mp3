import sys
import os
import yt_dlp
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3

def ensure_ffmpeg():
    """Check if ffmpeg is available in PATH or in the local directory."""
    # On Windows, expect ffmpeg in ./ffmpeg/ffmpeg.exe, otherwise look for ffmpeg in PATH
    ffmpeg_name = "ffmpeg/ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    local_ffmpeg = Path(__file__).parent / ffmpeg_name
    if local_ffmpeg.exists():
        return str(local_ffmpeg)
    try:
        import shutil
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return ffmpeg_path
    except Exception:
        pass

    print("FFmpeg not found. Please install FFmpeg and add it to PATH.")
    print("You can download it from: https://ffmpeg.org/download.html")
    sys.exit(1)

def download_audio(url, output_path="./musics"):
    try:
        os.makedirs(output_path, exist_ok=True)

        ydl_opts = {
            'format': 'bestaudio/best',
            'paths': {'home': output_path},
            'outtmpl': '%(title)s.%(ext)s',
            # Uncomment the next line to force the .mp3 extension (optional):
            # 'outtmpl': '%(title)s.mp3',
            'writethumbnail': True,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                },
                {
                    'key': 'EmbedThumbnail',
                },
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                }
            ],
            'ffmpeg_location': ensure_ffmpeg(),
            # Temporarily disable cookies and extra extractor arguments for debugging.
            'ignoreerrors': False,
            'no_warnings': False,
            'quiet': False,
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True,
            'extract_flat': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("\nGetting video information...")
            info = ydl.extract_info(url, download=False)
            if not info:
                print(f"Could not retrieve info for: {url}")
                return False

            print(f"Title: {info.get('title', 'N/A')}")
            print(f"Duration: {info.get('duration', 'N/A')} seconds")
            print("\nStarting download...")
            ydl.download([url])
            print("\nDownload completed successfully!")
            print(f"Saved to: {output_path}")
    except Exception as e:
        print(f"An error occurred while processing {url}: {e}")
        return False
    return True

def set_album_metadata(mp3_file, album_name="Album", artist_name="Unknown Artist"):
    try:
        # Attempt to load with EasyID3; create tags if they don't exist
        audio = MP3(mp3_file, ID3=EasyID3)
    except Exception:
        audio = MP3(mp3_file)
        audio.add_tags()
    audio["album"] = album_name
    audio["artist"] = artist_name
    audio.save()
    print(f"Album metadata set for {mp3_file.name}: Album='{album_name}', Artist='{artist_name}'")

if __name__ == "__main__":
    print("YouTube Audio Downloader (yt-dlp)")
    print("--------------------------------")
    print("Checking FFmpeg installation...")
    _ = ensure_ffmpeg()

    foldername = "./musics"
    artist = ""
    if len(sys.argv) > 1:
        artist = sys.argv[1]
        foldername = os.path.join(foldername, artist)
        print(f"Received artist argument: {artist}")

    os.makedirs(foldername, exist_ok=True)

    if os.path.exists("links.txt"):
        print("\nFound links.txt, processing URLs...")
        with open("links.txt", "r") as f:
            urls = [line.strip() for line in f if line.strip()]
            total = len(urls)
            for idx, url in enumerate(urls, 1):
                print(f"\nProcessing URL {idx} of {total}: {url}")
                if not download_audio(url, foldername):
                    print(f"Failed to download: {url}")

            # Apply album metadata for all downloaded MP3 files
            for mp3_file in Path(foldername).glob("*.mp3"):
                set_album_metadata(mp3_file, album_name=artist, artist_name=artist)
    else:
        print("links.txt not found. Please create links.txt with one YouTube URL per line.")
