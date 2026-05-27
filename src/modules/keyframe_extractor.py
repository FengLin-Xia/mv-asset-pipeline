"""
Step 3: 关键帧抽取
- 对每个 shot 抽 3 帧（10% / 50% / 90%）
- 可选：跳过黑帧（亮度过低）和模糊帧（拉普拉斯方差过低）
- 输出 frames/*.jpg
- 输出 keyframes_raw.json（追加到 shots 结构）
"""
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm

from src.utils.ffmpeg_utils import extract_frame_at, get_duration
from src.utils.json_utils import save_json, load_json, seconds_to_timecode
from src.utils.path_utils import get_frames_dir, get_analysis_dir, get_clips_dir

FRAME_ROLES = [
    ("F001", 0.10, "开始帧", "shot_10_percent"),
    ("F002", 0.50, "代表帧", "shot_50_percent"),
    ("F003", 0.90, "结束帧", "shot_90_percent"),
]

_BLACK_BRIGHTNESS_THRESHOLD = 15   # 平均亮度低于此值视为黑帧（0-255）
_BLUR_LAPLACIAN_THRESHOLD = 50.0   # 拉普拉斯方差低于此值视为模糊帧
_MAX_RETRY_STEPS = 5               # 遇到烂帧最多向后偏移几次
_RETRY_STEP_RATIO = 0.03           # 每次偏移 shot 时长的 3%
_TARGET_FPS = 25                   # pipeline 标准帧率，用于计算最后一帧时间戳上限


def _is_bad_frame(img_path: Path, avoid_black: bool, avoid_blur: bool) -> bool:
    """返回 True 表示该帧需要丢弃重抽。"""
    if not avoid_black and not avoid_blur:
        return False
    img = cv2.imread(str(img_path))
    if img is None:
        return False
    if avoid_black:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if gray.mean() < _BLACK_BRIGHTNESS_THRESHOLD:
            return True
    if avoid_blur:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if avoid_black else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if cv2.Laplacian(gray, cv2.CV_64F).var() < _BLUR_LAPLACIAN_THRESHOLD:
            return True
    return False


def extract_keyframes(
    mv_id: str,
    output_root: str = "data/processed",
    avoid_black_frames: bool = True,
    avoid_blur_frames: bool = False,
) -> list[dict]:
    analysis_dir = get_analysis_dir(output_root, mv_id)
    frames_dir = get_frames_dir(output_root, mv_id)
    frames_dir.mkdir(parents=True, exist_ok=True)

    scenes_path = analysis_dir / "scenes_raw.json"
    scenes_data = load_json(scenes_path)
    shots = scenes_data["shots"]

    keyframes_by_shot = []

    for shot in tqdm(shots, desc="[Step 3] 抽关键帧"):
        shot_id = shot["shot_id"]
        clip_path = Path(output_root) / mv_id / shot["video_clip_path"]

        if not clip_path.exists():
            print(f"  警告: 找不到 clip {clip_path}，跳过")
            continue

        duration = shot["duration"]
        frames = []

        for fid, ratio, role, method in FRAME_ROLES:
            ts = duration * ratio
            frame_name = f"{shot_id}_{fid}.jpg"
            frame_path = frames_dir / frame_name

            extract_frame_at(clip_path, ts, frame_path)

            # 黑帧/模糊帧过滤：向后偏移重试，上限为最后一帧时间戳
            ts_max = max(0.0, duration - 1.0 / _TARGET_FPS)
            for _ in range(_MAX_RETRY_STEPS):
                if not _is_bad_frame(frame_path, avoid_black_frames, avoid_blur_frames):
                    break
                ts = min(ts + duration * _RETRY_STEP_RATIO, ts_max)
                extract_frame_at(clip_path, ts, frame_path)

            frames.append({
                "frame_id": f"{shot_id}_{fid}",
                "timestamp_in_shot": round(ts, 3),
                "timestamp_global": seconds_to_timecode(shot["start_seconds"] + ts),
                "frame_role": role,
                "image_path": f"frames/{frame_name}",
                "selection_method": method,
            })

        keyframes_by_shot.append({
            "shot_id": shot_id,
            "keyframes": frames,
        })

    out_path = analysis_dir / "keyframes_raw.json"
    save_json(keyframes_by_shot, out_path)
    print(f"[Step 3] 完成，输出 -> {out_path}")
    return keyframes_by_shot
