"""
将 case_summary dict 渲染为人类可读的 Markdown 报告。
"""


def _val(v, fallback: str = "—") -> str:
    if v is None or v == "insufficient_data":
        return fallback
    if isinstance(v, float):
        return str(round(v, 3))
    return str(v)


def _pct(v) -> str:
    if v is None:
        return "—"
    return f"{v:.1%}"


def render_case_summary_md(summary: dict) -> str:
    mv_id = summary.get("mv_id", "未知")
    bs = summary.get("basic_stats", {})
    vl = summary.get("visual_language", {})
    er = summary.get("editing_rhythm", {})
    mvr = summary.get("music_visual_relation", {})
    nps = summary.get("narrative_performance_structure", {})
    patterns = summary.get("reusable_patterns", [])
    tags = summary.get("search_tags", {})
    st = summary.get("summary_text", {})
    method = summary.get("method", "rule_only")

    lines = []

    lines.append(f"# {mv_id} 案例级总结\n")
    lines.append(f"> 生成方式：`{method}`  |  生成时间：{summary.get('generated_at', '—')}\n")

    # 1. 一句话概括
    lines.append("## 1. 一句话概括\n")
    one_liner = st.get("one_sentence_summary") or vl.get("overall_style") or "（待 LLM 生成）"
    lines.append(f"{one_liner}\n")

    # 2. 基础统计
    lines.append("## 2. 基础统计\n")
    lines.append("| 指标 | 数值 |")
    lines.append("|---|---|")
    lines.append(f"| 视频时长 | {_val(bs.get('duration_seconds'))}s |")
    lines.append(f"| 镜头数量 | {_val(bs.get('shot_count'))} |")
    lines.append(f"| 平均镜头时长 | {_val(bs.get('avg_shot_duration'))}s |")
    lines.append(f"| 中位镜头时长 | {_val(bs.get('median_shot_duration'))}s |")
    lines.append(f"| 最短镜头 | {_val(bs.get('min_shot_duration'))}s |")
    lines.append(f"| 最长镜头 | {_val(bs.get('max_shot_duration'))}s |")
    lines.append(f"| BPM | {_val(bs.get('bpm'))} |")
    lines.append(f"| 音乐段落数 | {_val(bs.get('music_section_count'))} |")
    lines.append(f"| 快剪镜头比例 | {_pct(bs.get('fast_cut_ratio'))} |")
    lines.append(f"| 人声镜头比例 | {_pct(bs.get('vocal_shot_ratio'))} |")
    lines.append(f"| Caption 覆盖率 | {_pct(bs.get('caption_coverage_ratio'))} |")
    lines.append("")

    # 3. 视觉语言
    lines.append("## 3. 视觉语言\n")
    if vl.get("overall_style") and vl["overall_style"] not in ("insufficient_data", "unknown"):
        lines.append(f"**整体风格**：{vl['overall_style']}\n")
    palette = vl.get("color_palette") or []
    if palette:
        lines.append(f"**主色调**：{', '.join(palette)}")
    temp = vl.get("color_temperature") or vl.get("lighting_style")
    if temp:
        lines.append(f"\n**色温**：{temp}")
    scene_types = vl.get("dominant_scene_types") or []
    if scene_types:
        lines.append(f"\n**主要场景类型**：{', '.join(scene_types)}")
    shot_sizes = vl.get("dominant_shot_sizes") or []
    if shot_sizes:
        lines.append(f"\n**主要景别**：{', '.join(shot_sizes)}")
    camera = vl.get("dominant_camera_movements") or vl.get("camera_language")
    if camera:
        lines.append(f"\n**运镜风格**：{camera if isinstance(camera, str) else ', '.join(camera)}")
    mood = vl.get("visual_mood") or []
    if mood:
        lines.append(f"\n**视觉情绪**：{', '.join(mood)}")
    if vl.get("visual_summary"):
        lines.append(f"\n{vl['visual_summary']}")
    lines.append("")

    # 4. 剪辑节奏
    lines.append("## 4. 剪辑节奏\n")
    intensity = er.get("overall_cutting_intensity", "—")
    lines.append(f"**整体剪辑强度**：{intensity}")
    lines.append(f"\n**平均镜头时长**：{_val(er.get('avg_shot_duration'))}s")
    lines.append(f"\n**快剪比例**：{_pct(er.get('fast_cut_ratio'))}  |  **慢剪比例**：{_pct(er.get('slow_cut_ratio'))}")
    fastest = er.get("fastest_sections") or []
    if fastest:
        lines.append(f"\n**最快段落**：{', '.join(fastest)}")
    slowest = er.get("slowest_sections") or []
    if slowest:
        lines.append(f"\n**最慢段落**：{', '.join(slowest)}")
    if er.get("rhythm_strategy"):
        lines.append(f"\n\n{er['rhythm_strategy']}")
    if st.get("rhythm_summary"):
        lines.append(f"\n{st['rhythm_summary']}")
    lines.append("")

    # 5. 音乐—视觉关系
    lines.append("## 5. 音乐—视觉关系\n")
    if mvr.get("sync_strategy") == "insufficient_data":
        lines.append("_音乐段落数据缺失，无法分析。_\n")
    else:
        chorus_avg = mvr.get("chorus_avg_shot_duration")
        other_avg = mvr.get("non_chorus_avg_shot_duration")
        if chorus_avg is not None:
            lines.append(f"**副歌平均镜头时长**：{chorus_avg}s")
        if other_avg is not None:
            lines.append(f"\n**非副歌平均镜头时长**：{other_avg}s")
        if mvr.get("vocal_visual_relation"):
            lines.append(f"\n**人声关系**：{mvr['vocal_visual_relation']}")
        if mvr.get("chorus_visual_change"):
            lines.append(f"\n\n{mvr['chorus_visual_change']}")
        if st.get("rhythm_summary") and not er.get("rhythm_strategy"):
            lines.append(f"\n{st['rhythm_summary']}")
    lines.append("")

    # 6. 叙事 / 表演结构
    lines.append("## 6. 叙事 / 表演结构\n")
    if nps.get("structure_type") and nps["structure_type"] != "insufficient_data":
        lines.append(f"**结构类型**：{nps['structure_type']}")
        for k, label in [
            ("performance_density", "表演密度"),
            ("narrative_density", "叙事密度"),
            ("artist_presence", "艺人出镜"),
            ("dance_presence", "舞蹈元素"),
        ]:
            if nps.get(k):
                lines.append(f"\n**{label}**：{nps[k]}")
        if nps.get("description"):
            lines.append(f"\n\n{nps['description']}")
    else:
        lines.append("_（需 LLM 生成，或 caption 覆盖率不足）_")
    lines.append("")

    # 7. 可复用创作模式
    lines.append("## 7. 可复用创作模式\n")
    if patterns:
        for i, p in enumerate(patterns, 1):
            name = p.get("display_name") or p.get("pattern_name", f"模式{i}")
            lines.append(f"### 7.{i} {name}\n")
            if p.get("description"):
                lines.append(f"{p['description']}\n")
            if p.get("suitable_for"):
                lines.append(f"**适用场景**：{', '.join(p['suitable_for'])}\n")
            if p.get("prompt_hint"):
                lines.append(f"**Prompt 提示**：{p['prompt_hint']}\n")
    else:
        lines.append("_（需 LLM 生成）_\n")

    # 8. 推荐检索标签
    lines.append("## 8. 推荐检索标签\n")
    if tags:
        all_tags = []
        for v in tags.values():
            if isinstance(v, list):
                all_tags.extend(v)
            else:
                all_tags.append(str(v))
        for tag in all_tags:
            lines.append(f"- {tag}")
    else:
        lines.append("_（需 LLM 生成）_")
    lines.append("")

    return "\n".join(lines)
