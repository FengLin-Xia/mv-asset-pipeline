"""
Step 3: 关键帧抽取
- 对每个 shot 抽 3 帧（10% / 50% / 90%）
- 输出 frames/*.jpg
- 输出 keyframes_raw.json（追加到 shots 结构）
"""
from pathlib import Path
from tqdm import tqdm

from src.utils.ffmpeg_utils import extract_frame_at, get_duration
from src.utils.json_utils import save_json, load_json, seconds_to_timecode
from src.utils.path_utils import get_frames_dir, get_analysis_dir, get_clips_dir

FRAME_ROLES = [
    ("F001", 0.10, "开始帧", "shot_10_percent"),
    ("F002", 0.50, "代表帧", "shot_50_percent"),
    ("F003", 0.90, "结束帧", "shot_90_percent"),
]


def extract_keyframes(
    mv_id: str,
    output_root: str = "data/processed",
) -> list[dict]:
    analysis_dir = get_analysis_dir(output_root, mv_id)
    frames_dir = get_frames_dir(output_root, mv_id)
    clips_dir = get_clips_dir(output_root, mv_id)
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
