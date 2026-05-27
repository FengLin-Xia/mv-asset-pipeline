"""
基础统计指标提取：从 mv_case_asset.json 计算 basic_stats 和剪辑强度分类。
"""
import statistics
from typing import Optional


# 剪辑强度阈值（秒），可由 pipeline.yaml 覆盖
DEFAULT_FAST_CUT_SECONDS = 1.0
DEFAULT_MEDIUM_CUT_SECONDS = 2.5


def classify_cutting_intensity(avg_shot_duration: float,
                                fast_threshold: float = DEFAULT_FAST_CUT_SECONDS,
                                medium_threshold: float = DEFAULT_MEDIUM_CUT_SECONDS) -> str:
    if avg_shot_duration <= fast_threshold:
        return "high"
    elif avg_shot_duration <= medium_threshold:
        return "medium"
    return "low"


def classify_shot_duration(duration: float,
                            fast_threshold: float = DEFAULT_FAST_CUT_SECONDS,
                            medium_threshold: float = DEFAULT_MEDIUM_CUT_SECONDS) -> str:
    if duration <= fast_threshold:
        return "fast_cut"
    elif duration <= medium_threshold:
        return "medium_cut"
    return "slow_cut"


def extract_basic_stats(asset: dict,
                         fast_threshold: float = DEFAULT_FAST_CUT_SECONDS,
                         medium_threshold: float = DEFAULT_MEDIUM_CUT_SECONDS) -> dict:
    mv_info = asset.get("mv_table", [{}])[0]
    shots = asset.get("shot_table", [])

    durations = [s["duration"] for s in shots if s.get("duration") is not None]

    captioned = sum(
        1 for s in shots
        if s.get("caption", {}).get("value", "").strip()
    )
    vocal_shots = sum(
        1 for s in shots
        if s.get("has_vocals") is True
    )

    fast_cuts = sum(1 for d in durations if d <= fast_threshold)
    slow_cuts = sum(1 for d in durations if d > medium_threshold)
    n = len(durations)

    return {
        "duration_seconds": mv_info.get("duration"),
        "shot_count": len(shots),
        "avg_shot_duration": round(statistics.mean(durations), 3) if durations else None,
        "median_shot_duration": round(statistics.median(durations), 3) if durations else None,
        "min_shot_duration": round(min(durations), 3) if durations else None,
        "max_shot_duration": round(max(durations), 3) if durations else None,
        "bpm": mv_info.get("bpm"),
        "music_section_count": len(asset.get("sequence_table", [])),
        "captioned_shot_count": captioned,
        "caption_coverage_ratio": round(captioned / n, 3) if n else 0.0,
        "vocal_shot_count": vocal_shots,
        "vocal_shot_ratio": round(vocal_shots / n, 3) if n else 0.0,
        "fast_cut_count": fast_cuts,
        "fast_cut_ratio": round(fast_cuts / n, 3) if n else 0.0,
        "slow_cut_count": slow_cuts,
        "slow_cut_ratio": round(slow_cuts / n, 3) if n else 0.0,
    }
