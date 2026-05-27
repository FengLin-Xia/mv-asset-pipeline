"""
Step 2.5: 人声段落标注
- 读取 source/vocals.wav（htdemucs 分离结果）
- 对每个 shot 的时间窗口计算 RMS 能量，判断是否有人声
- 输出 analysis/vocal_annotation_raw.json
"""
from pathlib import Path

import librosa
import numpy as np

from src.utils.json_utils import save_json, load_json
from src.utils.path_utils import get_source_dir, get_analysis_dir

# RMS 能量阈值：低于此值视为无人声（相对 full mix 的比例）
_VOCAL_ENERGY_THRESHOLD = 0.02


def detect_vocals(
    mv_id: str,
    output_root: str = "data/processed",
) -> list[dict]:
    src_dir = get_source_dir(output_root, mv_id)
    analysis_dir = get_analysis_dir(output_root, mv_id)

    vocals_path = src_dir / "vocals.wav"
    scenes_path = analysis_dir / "scenes_raw.json"

    if not vocals_path.exists():
        raise FileNotFoundError(
            f"[Step 2.5] vocals.wav 不存在: {vocals_path}\n"
            "请先运行 Step 1.5（音源分离）。"
        )

    scenes_data = load_json(scenes_path)
    shots = scenes_data["shots"]

    print(f"[Step 2.5] 加载 vocals.wav: {vocals_path}")
    y, sr = librosa.load(str(vocals_path), sr=None, mono=True)
    total_samples = len(y)

    annotations = []
    for shot in shots:
        start_sec = shot["start_seconds"]
        end_sec = shot["end_seconds"]

        start_sample = int(start_sec * sr)
        end_sample = min(int(end_sec * sr), total_samples)

        if start_sample >= end_sample:
            rms = 0.0
        else:
            segment = y[start_sample:end_sample]
            rms = float(np.sqrt(np.mean(segment ** 2)))

        has_vocals = rms >= _VOCAL_ENERGY_THRESHOLD

        annotations.append({
            "shot_id": shot["shot_id"],
            "has_vocals": has_vocals,
            "vocal_energy": round(rms, 4),
        })

    out_path = analysis_dir / "vocal_annotation_raw.json"
    save_json(annotations, out_path)
    print(f"[Step 2.5] 完成，共标注 {len(annotations)} 个 shot -> {out_path}")
    return annotations
