"""
Step 3.5: 关键帧颜色调性分析
- 对每个关键帧做 K-Means 聚色，提取主色调
- 判断色温（cool / warm / neutral）
- 在 keyframes_raw.json 的每条记录中补充 dominant_colors / color_temperature
"""
from pathlib import Path

import numpy as np
from PIL import Image

from src.utils.json_utils import save_json, load_json
from src.utils.path_utils import get_frames_dir, get_analysis_dir

_K = 3          # 聚类数
_RESIZE = 100   # 缩小分辨率加速，px（长边）


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def _color_temperature(dominant_rgb: list[tuple]) -> str:
    """根据主色判断色温。warm: R 通道占优；cool: B 通道占优；neutral: 介于之间。"""
    if not dominant_rgb:
        return "neutral"
    r, g, b = dominant_rgb[0]  # 第一主色
    if r - b > 20:
        return "warm"
    if b - r > 20:
        return "cool"
    return "neutral"


def _kmeans_colors(img_path: Path, k: int = _K) -> tuple[list[str], str]:
    """返回 (hex_colors, temperature)，若图片不存在返回空列表。"""
    if not img_path.exists():
        return [], "neutral"

    img = Image.open(img_path).convert("RGB")

    # 缩小以加速
    w, h = img.size
    scale = _RESIZE / max(w, h)
    if scale < 1.0:
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)

    pixels = np.array(img, dtype=np.float32).reshape(-1, 3)

    # 简单 K-Means（不引入 sklearn，纯 numpy 实现）
    rng = np.random.default_rng(seed=42)
    centers = pixels[rng.choice(len(pixels), k, replace=False)]

    for _ in range(20):
        dists = np.linalg.norm(pixels[:, None, :] - centers[None, :, :], axis=2)
        labels = dists.argmin(axis=1)
        new_centers = np.array([
            pixels[labels == i].mean(axis=0) if (labels == i).any() else centers[i]
            for i in range(k)
        ])
        if np.allclose(centers, new_centers, atol=1.0):
            break
        centers = new_centers

    # 按聚类大小降序排列
    counts = np.array([(labels == i).sum() for i in range(k)])
    order = counts.argsort()[::-1]
    sorted_rgb = [(int(centers[i][0]), int(centers[i][1]), int(centers[i][2])) for i in order]

    hex_colors = [_rgb_to_hex(r, g, b) for r, g, b in sorted_rgb]
    temperature = _color_temperature(sorted_rgb)
    return hex_colors, temperature


def analyze_colors(
    mv_id: str,
    output_root: str = "data/processed",
) -> list[dict]:
    analysis_dir = get_analysis_dir(output_root, mv_id)
    frames_dir = get_frames_dir(output_root, mv_id)
    kf_path = analysis_dir / "keyframes_raw.json"

    keyframes_data = load_json(kf_path)

    for shot_entry in keyframes_data:
        for kf in shot_entry["keyframes"]:
            img_path = frames_dir / Path(kf["image_path"]).name
            hex_colors, temperature = _kmeans_colors(img_path)
            kf["dominant_colors"] = hex_colors
            kf["color_temperature"] = temperature

    save_json(keyframes_data, kf_path)
    print(f"[Step 3.5] 颜色分析完成，已更新 -> {kf_path}")
    return keyframes_data
