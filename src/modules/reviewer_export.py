"""
Step 7: 导出人工复核 CSV
"""
import csv
from pathlib import Path

from src.utils.json_utils import load_json, save_json
from src.utils.path_utils import get_analysis_dir


def export_review_csv(
    mv_id: str,
    output_root: str = "data/processed",
) -> Path:
    analysis_dir = get_analysis_dir(output_root, mv_id)
    asset = load_json(analysis_dir / "mv_case_asset.json")

    csv_path = analysis_dir / "shot_review.csv"
    fields = [
        "shot_id", "start_time", "end_time", "duration",
        "music_section", "has_vocals", "vocal_energy",
        "caption",
        "performer_count_type", "performance_type", "scene_type",
        "shot_size", "camera_movement_guess",
        "dominant_colors", "color_temperature",
        "shot_function", "reuse_value", "prompt_hint",
        "needs_review", "review_notes",
    ]

    # 每个 shot 取第一张关键帧（代表帧 F002）的颜色，没有则用任意第一张
    kf_color_map = {}
    for kf in asset.get("keyframe_table", []):
        sid = kf["shot_id"]
        if sid not in kf_color_map or kf.get("frame_role") == "代表帧":
            kf_color_map[sid] = {
                "dominant_colors": ", ".join(kf.get("dominant_colors", [])),
                "color_temperature": kf.get("color_temperature", ""),
            }

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for shot in asset["shot_table"]:
            def v(field):
                val = shot.get(field, {})
                if isinstance(val, dict):
                    return val.get("value", "")
                return val

            writer.writerow({
                "shot_id": shot["shot_id"],
                "start_time": shot["start_time"],
                "end_time": shot["end_time"],
                "duration": shot["duration"],
                "music_section": v("music_section"),
                "has_vocals": shot.get("has_vocals", ""),
                "vocal_energy": shot.get("vocal_energy", ""),
                "caption": v("caption"),
                "performer_count_type": v("performer_count_type"),
                "performance_type": v("performance_type"),
                "scene_type": v("scene_type"),
                "shot_size": v("shot_size"),
                "camera_movement_guess": v("camera_movement_guess"),
                "dominant_colors": kf_color_map.get(shot["shot_id"], {}).get("dominant_colors", ""),
                "color_temperature": kf_color_map.get(shot["shot_id"], {}).get("color_temperature", ""),
                "shot_function": v("shot_function"),
                "reuse_value": v("reuse_value"),
                "prompt_hint": v("prompt_hint"),
                "needs_review": True,
                "review_notes": "",
            })

    print(f"[Step 7] 复核 CSV 输出 -> {csv_path}")
    return csv_path
