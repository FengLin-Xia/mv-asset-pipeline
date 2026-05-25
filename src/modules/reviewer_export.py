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
        "music_section", "caption",
        "performer_count_type", "performance_type", "scene_type",
        "shot_size", "camera_movement_guess",
        "shot_function", "reuse_value", "prompt_hint",
        "needs_review", "review_notes",
    ]

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
                "caption": v("caption"),
                "performer_count_type": v("performer_count_type"),
                "performance_type": v("performance_type"),
                "scene_type": v("scene_type"),
                "shot_size": v("shot_size"),
                "camera_movement_guess": v("camera_movement_guess"),
                "shot_function": v("shot_function"),
                "reuse_value": v("reuse_value"),
                "prompt_hint": v("prompt_hint"),
                "needs_review": True,
                "review_notes": "",
            })

    print(f"[Step 7] 复核 CSV 输出 -> {csv_path}")
    return csv_path
