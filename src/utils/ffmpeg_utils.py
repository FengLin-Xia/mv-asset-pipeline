import subprocess
import json
from pathlib import Path


def run_ffmpeg(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error"] + args
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def run_ffprobe(args: list[str]) -> dict:
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json"] + args
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def get_video_metadata(video_path: Path) -> dict:
    return run_ffprobe([
        "-show_format", "-show_streams",
        str(video_path)
    ])


def extract_frame_at(video_path: Path, timestamp: float, output_path: Path) -> None:
    run_ffmpeg([
        "-ss", str(timestamp),
        "-i", str(video_path),
        "-frames:v", "1",
        "-q:v", "2",
        "-y",
        str(output_path)
    ])


def get_duration(video_path: Path) -> float:
    meta = run_ffprobe(["-show_format", str(video_path)])
    return float(meta["format"]["duration"])
