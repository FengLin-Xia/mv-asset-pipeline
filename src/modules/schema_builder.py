"""
Step 6: 四层 JSON 结构化
- 合并 metadata / scenes / music / captions
- 输出 mv_case_asset.json
"""
from pathlib import Path

from src.utils.json_utils import save_json, load_json, seconds_to_timecode
from src.utils.path_utils import get_source_dir, get_analysis_dir


def _build_sequence_table(mv_id: str, segments: list[dict], shots: list[dict]) -> list[dict]:
    """为每个音乐段落计算视觉节奏统计。"""
    sequence_table = []
    for idx, seg in enumerate(segments):
        seg_start = seg["start_seconds"]
        seg_end = seg["end_seconds"]
        seg_duration = seg_end - seg_start

        # 找出与本段落有重叠的 shots
        overlapping = [
            s for s in shots
            if s["start_seconds"] < seg_end and s["end_seconds"] > seg_start
        ]
        shot_count = len(overlapping)

        if shot_count > 0:
            avg_shot_duration = round(
                sum(min(s["end_seconds"], seg_end) - max(s["start_seconds"], seg_start)
                    for s in overlapping) / shot_count,
                3,
            )
        else:
            avg_shot_duration = 0.0

        cut_frequency = round(shot_count / seg_duration, 3) if seg_duration > 0 else 0.0

        sequence_table.append({
            "segment_id": f"SEQ_{idx + 1:03d}",
            "mv_id": mv_id,
            "label": seg.get("mapped_music_section", "不确定"),
            "start_seconds": seg_start,
            "end_seconds": seg_end,
            "duration": round(seg_duration, 3),
            "shot_count": shot_count,
            "avg_shot_duration": avg_shot_duration,
            "cut_frequency": cut_frequency,
        })
    return sequence_table


def _find_music_section(start_sec: float, end_sec: float, segments: list[dict]) -> str:
    best = "不确定"
    best_overlap = 0.0
    for seg in segments:
        overlap_start = max(start_sec, seg["start_seconds"])
        overlap_end = min(end_sec, seg["end_seconds"])
        overlap = max(0.0, overlap_end - overlap_start)
        if overlap > best_overlap:
            best_overlap = overlap
            best = seg["mapped_music_section"]
    return best


def build_schema(
    mv_id: str,
    output_root: str = "data/processed",
) -> dict:
    analysis_dir = get_analysis_dir(output_root, mv_id)
    src_dir = get_source_dir(output_root, mv_id)

    metadata = load_json(src_dir / "metadata.json")
    scenes = load_json(analysis_dir / "scenes_raw.json")
    keyframes_data = load_json(analysis_dir / "keyframes_raw.json")

    music_path = analysis_dir / "music_structure_raw.json"
    music = load_json(music_path) if music_path.exists() else {"segments": [], "bpm": None}

    bpm_path = src_dir / "bpm.json"
    bpm = load_json(bpm_path).get("bpm") if bpm_path.exists() else music.get("bpm")

    captions_path = analysis_dir / "captions_raw.json"
    captions_map = {}
    if captions_path.exists():
        for item in load_json(captions_path):
            captions_map[item["shot_id"]] = item["caption_result"]

    vocal_path = analysis_dir / "vocal_annotation_raw.json"
    vocal_map = {}
    if vocal_path.exists():
        for item in load_json(vocal_path):
            vocal_map[item["shot_id"]] = item

    kf_map = {item["shot_id"]: item["keyframes"] for item in keyframes_data}

    # 找视频总时长
    fmt = metadata.get("format", {})
    total_duration = float(fmt.get("duration", 0))

    # ── MV 级 ──
    mv_table = [{
        "mv_id": mv_id,
        "video_path": f"source/video.mp4",
        "audio_path": f"source/audio.wav",
        "duration": round(total_duration, 3),
        "bpm": bpm,
        "shot_count": scenes["shot_count"],
        "source": "system_generated",
    }]

    # ── Shot 级 ──
    shot_table = []
    keyframe_table = []

    for shot in scenes["shots"]:
        shot_id = shot["shot_id"]
        start_sec = shot["start_seconds"]
        end_sec = shot["end_seconds"]

        music_section = _find_music_section(start_sec, end_sec, music.get("segments", []))

        cap = captions_map.get(shot_id, {})
        vocal = vocal_map.get(shot_id, {})

        shot_entry = {
            "shot_id": shot_id,
            "mv_id": mv_id,
            "shot_index": shot["shot_index"],
            "start_time": shot["start_time"],
            "end_time": shot["end_time"],
            "start_seconds": start_sec,
            "end_seconds": end_sec,
            "duration": shot["duration"],
            "video_clip_path": shot["video_clip_path"],
            "music_section": {
                "value": music_section,
                "source": "music_analyzer",
                "confidence": None,
                "needs_review": True,
            },
            "caption": {
                "value": cap.get("caption", ""),
                "source": cap.get("source", ""),
                "needs_review": True,
            },
            "performer_count_type": {"value": cap.get("performer_count_type", "不确定"), "source": cap.get("source", ""), "needs_review": True},
            "performance_type": {"value": cap.get("performance_type", "不确定"), "source": cap.get("source", ""), "needs_review": True},
            "scene_type": {"value": cap.get("scene_type", "不确定"), "source": cap.get("source", ""), "needs_review": True},
            "shot_size": {"value": cap.get("shot_size", "不确定"), "source": cap.get("source", ""), "needs_review": True},
            "lighting_color": {"value": cap.get("lighting_color", []), "source": cap.get("source", ""), "needs_review": True},
            "costume_style": {"value": cap.get("costume_style", []), "source": cap.get("source", ""), "needs_review": True},
            "camera_movement_guess": {"value": cap.get("camera_movement_guess", "不确定"), "source": cap.get("source", ""), "needs_review": True},
            "has_vocals": vocal.get("has_vocals", None),
            "vocal_energy": vocal.get("vocal_energy", None),
            # C 类字段，留空待人工填写
            "shot_function": {"value": "", "source": "", "needs_review": True},
            "reuse_value": {"value": None, "source": "", "needs_review": True},
            "prompt_hint": {"value": "", "source": "", "needs_review": True},
        }
        shot_table.append(shot_entry)

        # ── 关键帧级 ──
        for kf in kf_map.get(shot_id, []):
            keyframe_table.append({
                "frame_id": kf["frame_id"],
                "shot_id": shot_id,
                "mv_id": mv_id,
                "timestamp_in_shot": kf["timestamp_in_shot"],
                "timestamp_global": kf["timestamp_global"],
                "frame_role": kf["frame_role"],
                "image_path": kf["image_path"],
                "selection_method": kf["selection_method"],
                "dominant_colors": kf.get("dominant_colors", []),
                "color_temperature": kf.get("color_temperature", None),
                "frame_caption": {"value": "", "source": "", "needs_review": True},
            })

    asset = {
        "schema_name": "MV案例资产库字段表",
        "schema_version": "v0.1",
        "mv_table": mv_table,
        "sequence_table": _build_sequence_table(mv_id, music.get("segments", []), scenes["shots"]),
        "shot_table": shot_table,
        "keyframe_table": keyframe_table,
    }

    out_path = analysis_dir / "mv_case_asset.json"
    save_json(asset, out_path)
    print(f"[Step 6] 完成，输出 -> {out_path}")
    return asset
