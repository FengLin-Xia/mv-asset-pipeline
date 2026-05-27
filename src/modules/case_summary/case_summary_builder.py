"""
Step 7: 案例级总结 Case-level Summary
- 读取 mv_case_asset.json
- 规则统计 + 可选 LLM 增强
- 输出 case_summary.json + case_summary.md
"""
from datetime import datetime, timezone
from pathlib import Path

from src.utils.json_utils import save_json, load_json
from src.utils.path_utils import get_analysis_dir

from .stats_extractor import extract_basic_stats, DEFAULT_FAST_CUT_SECONDS, DEFAULT_MEDIUM_CUT_SECONDS
from .section_analyzer import analyze_music_sections, analyze_editing_rhythm, build_music_visual_relation
from .visual_summarizer import summarize_visual_signals
from .markdown_renderer import render_case_summary_md


def build_case_summary(
    mv_id: str,
    output_root: str = "data/processed",
    use_llm: bool = True,
    language: str = "zh",
    overwrite: bool = False,
    fast_threshold: float = DEFAULT_FAST_CUT_SECONDS,
    medium_threshold: float = DEFAULT_MEDIUM_CUT_SECONDS,
    max_captions: int = 30,
) -> dict:
    analysis_dir = get_analysis_dir(output_root, mv_id)
    asset_path = analysis_dir / "mv_case_asset.json"
    out_json = analysis_dir / "case_summary.json"
    out_md = analysis_dir / "case_summary.md"

    if not asset_path.exists():
        raise FileNotFoundError(
            f"[Step 7] ERROR: Missing mv_case_asset.json at {asset_path}\n"
            "Please run Step 6 first."
        )

    if out_json.exists() and not overwrite:
        print(f"[Step 7] case_summary.json 已存在，跳过（使用 --overwrite 强制重新生成）")
        return load_json(out_json)

    print(f"[Step 7] 读取资产文件: {asset_path}")
    asset = load_json(asset_path)

    # ── 规则统计 ──
    basic_stats = extract_basic_stats(asset, fast_threshold, medium_threshold)
    section_stats = analyze_music_sections(asset)
    editing_rhythm = analyze_editing_rhythm(asset, section_stats, fast_threshold, medium_threshold)
    music_visual_relation = build_music_visual_relation(asset, section_stats)
    visual_stats = summarize_visual_signals(asset, max_captions)

    # 规则版 visual_language（颜色 + 结构化字段，不含 overall_style 等主观判断）
    visual_language_rule = {
        "overall_style": "insufficient_data",
        "color_palette": visual_stats.get("color_palette", []),
        "color_temperature": visual_stats.get("color_temperature"),
        "dominant_scene_types": visual_stats.get("dominant_scene_types", []),
        "dominant_shot_sizes": visual_stats.get("dominant_shot_sizes", []),
        "dominant_camera_movements": visual_stats.get("dominant_camera_movements", []),
        "dominant_performance_types": visual_stats.get("dominant_performance_types", []),
    }

    draft = {
        "mv_id": mv_id,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "method": "rule_only",
        "basic_stats": basic_stats,
        "visual_language": visual_language_rule,
        "editing_rhythm": editing_rhythm,
        "music_visual_relation": music_visual_relation,
        "narrative_performance_structure": {"structure_type": "insufficient_data"},
        "reusable_patterns": [],
        "search_tags": {},
        "summary_text": {},
    }

    # ── LLM 增强 ──
    if use_llm:
        from .llm_case_summarizer import enhance_summary_with_llm
        summary = enhance_summary_with_llm(draft, visual_stats, max_captions)
    else:
        summary = draft

    # ── 输出 ──
    save_json(summary, out_json)
    print(f"[Step 7] JSON 输出 -> {out_json}")

    md_text = render_case_summary_md(summary)
    out_md.write_text(md_text, encoding="utf-8")
    print(f"[Step 7] Markdown 输出 -> {out_md}")

    return summary
