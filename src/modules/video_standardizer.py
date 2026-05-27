"""
Step 1: 视频标准化
- 转码到目标分辨率 / FPS
- 提取 WAV 音频
- 提取 metadata.json
"""
import subprocess
import json
from pathlib import Path

import librosa
import numpy as np

from src.utils.ffmpeg_utils import run_ffmpeg, get_video_metadata
from src.utils.json_utils import save_json
from src.utils.path_utils import get_source_dir, ensure_dirs


def standardize(
    input_path: str,
    mv_id: str,
    output_root: str = "data/processed",
    target_height: int = 720,
    target_fps: int = 25,
    audio_sample_rate: int = 44100,
) -> dict:
    ensure_dirs(output_root, mv_id)
    src_dir = get_source_dir(output_root, mv_id)

    video_out = src_dir / "video.mp4"
    audio_out = src_dir / "audio.wav"
    meta_out = src_dir / "metadata.json"

    print(f"[Step 1] 转码视频 -> {video_out}")
    run_ffmpeg([
        "-i", str(input_path),
        "-vf", f"scale=-2:{target_height},fps={target_fps}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-y", str(video_out)
    ])

    print(f"[Step 1] 提取音频 -> {audio_out}")
    run_ffmpeg([
        "-i", str(video_out),
        "-vn", "-acodec", "pcm_s16le",
        "-ar", str(audio_sample_rate), "-ac", "2",
        "-y", str(audio_out)
    ])

    print(f"[Step 1] 提取 metadata -> {meta_out}")
    meta = get_video_metadata(video_out)
    save_json(meta, meta_out)

    print(f"[Step 1] 计算 BPM -> {src_dir / 'bpm.json'}")
    try:
        y, sr = librosa.load(str(audio_out), sr=None, mono=True)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = round(float(np.atleast_1d(tempo)[0]), 2)
    except Exception:
        bpm = None
    save_json({"bpm": bpm}, src_dir / "bpm.json")

    print(f"[Step 1] 完成")
    return {"video_path": str(video_out), "audio_path": str(audio_out), "metadata_path": str(meta_out)}
