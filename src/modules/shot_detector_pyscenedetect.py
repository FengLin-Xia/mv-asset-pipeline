"""
Step 2: 镜头切分（PySceneDetect）
- 检测 shot 边界
- 切出 clips/*.mp4
- 输出 scenes_raw.json
"""
from pathlib import Path
from scenedetect import open_video, SceneManager, split_video_ffmpeg
from scenedetect.detectors import ContentDetector

from src.utils.json_utils import save_json, seconds_to_timecode
from src.utils.path_utils import get_clips_dir, get_analysis_dir, get_source_dir


def detect_shots(
    mv_id: str,
    output_root: str = "data/processed",
    threshold: float = 27.0,
    min_scene_len: int = 12,
) -> dict:
    src_dir = get_source_dir(output_root, mv_id)
    clips_dir = get_clips_dir(output_root, mv_id)
    analysis_dir = get_analysis_dir(output_root, mv_id)
    clips_dir.mkdir(parents=True, exist_ok=True)

    video_path = src_dir / "video.mp4"
    print(f"[Step 2] 镜头检测: {video_path}")

    video = open_video(str(video_path))
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold, min_scene_len=min_scene_len))
    scene_manager.detect_scenes(video, show_progress=True)
    scenes = scene_manager.get_scene_list()

    print(f"[Step 2] 检测到 {len(scenes)} 个镜头，开始切片...")
    split_video_ffmpeg(
        str(video_path),
        scenes,
        output_dir=str(clips_dir),
        output_file_template=f"{mv_id}_S$SCENE_NUMBER.mp4",
        show_progress=True,
    )

    shots = []
    for i, (start, end) in enumerate(scenes, start=1):
        shot_id = f"{mv_id}_S{i:03d}"
        clip_name = f"{mv_id}_S{i:03d}.mp4"
        shots.append({
            "shot_id": shot_id,
            "shot_index": i,
            "start_time": seconds_to_timecode(start.get_seconds()),
            "end_time": seconds_to_timecode(end.get_seconds()),
            "start_seconds": round(start.get_seconds(), 3),
            "end_seconds": round(end.get_seconds(), 3),
            "duration": round(end.get_seconds() - start.get_seconds(), 3),
            "video_clip_path": f"clips/{clip_name}",
        })

    result = {
        "mv_id": mv_id,
        "method": "pyscenedetect_content",
        "params": {"threshold": threshold, "min_scene_len": min_scene_len},
        "shot_count": len(shots),
        "shots": shots,
    }

    out_path = analysis_dir / "scenes_raw.json"
    save_json(result, out_path)
    print(f"[Step 2] 完成，输出 -> {out_path}")
    return result
