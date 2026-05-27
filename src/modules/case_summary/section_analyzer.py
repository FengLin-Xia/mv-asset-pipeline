"""
音乐段落级分析：聚合剪辑节奏、找最快/最慢段落、生成 music_visual_relation。
"""
import statistics
from .stats_extractor import classify_cutting_intensity, DEFAULT_FAST_CUT_SECONDS, DEFAULT_MEDIUM_CUT_SECONDS


def analyze_music_sections(asset: dict) -> list[dict]:
    """基于 sequence_table 计算每段落视觉强度。"""
    sections = asset.get("sequence_table", [])
    results = []
    for seg in sections:
        avg = seg.get("avg_shot_duration")
        results.append({
            "segment_id": seg.get("segment_id"),
            "label": seg.get("label", "不确定"),
            "start_seconds": seg.get("start_seconds"),
            "end_seconds": seg.get("end_seconds"),
            "duration": seg.get("duration"),
            "shot_count": seg.get("shot_count", 0),
            "avg_shot_duration": avg,
            "cut_frequency": seg.get("cut_frequency"),
            "visual_intensity": classify_cutting_intensity(avg) if avg else "unknown",
        })
    return results


def analyze_editing_rhythm(asset: dict,
                            section_stats: list[dict],
                            fast_threshold: float = DEFAULT_FAST_CUT_SECONDS,
                            medium_threshold: float = DEFAULT_MEDIUM_CUT_SECONDS) -> dict:
    shots = asset.get("shot_table", [])
    durations = [s["duration"] for s in shots if s.get("duration") is not None]

    if not durations:
        return {"overall_cutting_intensity": "unknown"}

    avg = statistics.mean(durations)
    overall_intensity = classify_cutting_intensity(avg, fast_threshold, medium_threshold)

    fast_ratio = sum(1 for d in durations if d <= fast_threshold) / len(durations)
    slow_ratio = sum(1 for d in durations if d > medium_threshold) / len(durations)

    # 按 avg_shot_duration 找最快和最慢段落（过滤无 shot 的段落）
    valid_sections = [s for s in section_stats if s.get("shot_count", 0) > 0 and s.get("avg_shot_duration") is not None]
    sorted_by_speed = sorted(valid_sections, key=lambda x: x["avg_shot_duration"])

    fastest = [s["label"] for s in sorted_by_speed[:3]]
    slowest = [s["label"] for s in sorted_by_speed[-3:]][::-1]

    return {
        "overall_cutting_intensity": overall_intensity,
        "avg_shot_duration": round(avg, 3),
        "fast_cut_ratio": round(fast_ratio, 3),
        "slow_cut_ratio": round(slow_ratio, 3),
        "fastest_sections": fastest,
        "slowest_sections": slowest,
    }


def build_music_visual_relation(asset: dict, section_stats: list[dict]) -> dict:
    if not section_stats:
        return {
            "sync_strategy": "insufficient_data",
            "reason": "music structure data is missing",
        }

    # 副歌 vs 其他段落的剪辑速度对比
    chorus_sections = [s for s in section_stats if "chorus" in s["label"].lower() or "副歌" in s["label"]]
    other_sections = [s for s in section_stats
                      if s not in chorus_sections and s.get("avg_shot_duration") is not None]

    chorus_avg = (
        round(statistics.mean([s["avg_shot_duration"] for s in chorus_sections
                                if s.get("avg_shot_duration") is not None]), 3)
        if chorus_sections else None
    )
    other_avg = (
        round(statistics.mean([s["avg_shot_duration"] for s in other_sections
                                if s.get("avg_shot_duration") is not None]), 3)
        if other_sections else None
    )

    # 人声与镜头的关系统计
    shots = asset.get("shot_table", [])
    vocal_shots = [s for s in shots if s.get("has_vocals") is True]
    n = len(shots)
    vocal_ratio = round(len(vocal_shots) / n, 3) if n else 0.0

    return {
        "sync_strategy": "rule_based",
        "chorus_avg_shot_duration": chorus_avg,
        "non_chorus_avg_shot_duration": other_avg,
        "section_level_relation": section_stats,
        "vocal_shot_ratio": vocal_ratio,
        "vocal_visual_relation": (
            "Vocal-heavy parts cover {:.0%} of shots.".format(vocal_ratio)
            if vocal_ratio else "insufficient_data"
        ),
    }
