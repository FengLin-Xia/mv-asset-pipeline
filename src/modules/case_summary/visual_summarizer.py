"""
视觉信号聚合：颜色调性统计、caption 采样、结构化标签频率统计。
"""
from collections import Counter
from typing import Optional


# hex → 人类可读颜色名的粗粒度映射
_HEX_TO_NAME = {}  # 由 _classify_hex 动态判断


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return (128, 128, 128)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _classify_hex_to_name(hex_color: str) -> str:
    """将 hex 粗分类为人类可读颜色名。"""
    r, g, b = _hex_to_rgb(hex_color)
    # 亮度
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    if brightness < 40:
        return "black/dark"
    if brightness > 200:
        return "white/bright"
    # 色调
    max_c = max(r, g, b)
    if max_c == 0:
        return "black/dark"
    if r == max_c and r - min(g, b) > 40:
        return "red/warm"
    if g == max_c and g - min(r, b) > 40:
        return "green"
    if b == max_c and b - min(r, g) > 40:
        return "blue/cool"
    if r > 150 and g > 100 and b < 80:
        return "yellow/orange"
    if r > 120 and b > 100 and g < 80:
        return "purple/violet"
    return "neutral/gray"


def aggregate_dominant_colors(keyframe_table: list[dict], top_n: int = 5) -> list[str]:
    """统计出现最频繁的颜色类别名。"""
    name_counter: Counter = Counter()
    for kf in keyframe_table:
        for hex_color in kf.get("dominant_colors", []):
            name_counter[_classify_hex_to_name(hex_color)] += 1
    return [name for name, _ in name_counter.most_common(top_n)]


def aggregate_color_temperature(keyframe_table: list[dict]) -> str:
    """统计主导色温。"""
    temps = [kf.get("color_temperature") for kf in keyframe_table if kf.get("color_temperature")]
    if not temps:
        return "unknown"
    counter = Counter(temps)
    return counter.most_common(1)[0][0]


def collect_field_distribution(shot_table: list[dict], field: str, top_n: int = 5) -> list[str]:
    """统计 shot_table 中某结构化字段的高频值。"""
    values = []
    for shot in shot_table:
        val = shot.get(field, {})
        if isinstance(val, dict):
            v = val.get("value", "")
        else:
            v = val
        # 列表型字段（如 lighting_color、costume_style）展开
        if isinstance(v, list):
            for item in v:
                if item and item not in ("不确定", "unknown", ""):
                    values.append(item)
        elif v and v not in ("不确定", "unknown", ""):
            values.append(v)
    counter = Counter(values)
    return [v for v, _ in counter.most_common(top_n)]


def select_representative_captions(shot_table: list[dict], max_n: int = 30) -> list[str]:
    """均匀采样 caption，避免只取开头。"""
    captions = [
        s.get("caption", {}).get("value", "")
        for s in shot_table
        if s.get("caption", {}).get("value", "").strip()
    ]
    if not captions:
        return []
    if len(captions) <= max_n:
        return captions
    step = len(captions) / max_n
    return [captions[int(i * step)] for i in range(max_n)]


def summarize_visual_signals(asset: dict, max_captions: int = 30) -> dict:
    shots = asset.get("shot_table", [])
    keyframes = asset.get("keyframe_table", [])

    dominant_colors = aggregate_dominant_colors(keyframes)
    color_temperature = aggregate_color_temperature(keyframes)
    scene_types = collect_field_distribution(shots, "scene_type")
    performance_types = collect_field_distribution(shots, "performance_type")
    shot_sizes = collect_field_distribution(shots, "shot_size")
    camera_movements = collect_field_distribution(shots, "camera_movement_guess")
    representative_captions = select_representative_captions(shots, max_captions)

    return {
        "color_palette": dominant_colors,
        "color_temperature": color_temperature,
        "dominant_scene_types": scene_types,
        "dominant_performance_types": performance_types,
        "dominant_shot_sizes": shot_sizes,
        "dominant_camera_movements": camera_movements,
        "caption_count": len([s for s in shots if s.get("caption", {}).get("value", "").strip()]),
        "representative_captions": representative_captions,
    }
