"""
LLM 增强总结：将规则统计结果送给 LLM，生成自然语言判断、标签和可复用模式。
LLM 只能补充解释性字段，不能覆盖程序统计的数值。
"""
import json
import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

_SYSTEM_PROMPT = """你是一个专业的 MV 视听语言分析助手。

下面是一支 MV 的结构化统计信息，包括：
- 基础镜头统计（basic_stats）
- 音乐段落统计（section_stats）
- 视觉信号统计（visual_stats）
- 剪辑节奏统计（editing_rhythm）

请生成一个 case_summary 的增强字段，严格遵守以下规则：

1. 输出必须是合法 JSON，只输出 JSON，不要有任何多余文字或 Markdown。
2. 不要编造数据中没有出现的具体人物、剧情、地点或物体。
3. 可以基于统计趋势进行风格归纳，但需要保持谨慎。
4. 如果信息不足，请使用 "insufficient_data"。
5. 所有数值统计字段（basic_stats 中的内容）不得修改。
6. search_tags 必须使用 snake_case 英文标签。
7. summary_text 使用中文。

请输出以下 JSON 结构（只输出这个 JSON）：
{
  "visual_language": {
    "overall_style": "...",
    "dominant_visual_elements": [],
    "lighting_style": "...",
    "camera_language": "...",
    "visual_mood": []
  },
  "narrative_performance_structure": {
    "structure_type": "performance-led / narrative-led / dance-led / concept-led / mixed",
    "performance_density": "high / medium / low",
    "narrative_density": "high / medium / low",
    "artist_presence": "high / medium / low",
    "dance_presence": "high / medium / low",
    "story_progression": "strong / moderate / weak",
    "description": "..."
  },
  "reusable_patterns": [
    {
      "pattern_name": "snake_case_name",
      "display_name": "中文名称",
      "description": "...",
      "suitable_for": [],
      "prompt_hint": "..."
    }
  ],
  "search_tags": {
    "mv_type": [],
    "visual_style": [],
    "editing": [],
    "music_energy": [],
    "content": [],
    "generation_use": []
  },
  "summary_text": {
    "one_sentence_summary": "...",
    "visual_summary": "...",
    "rhythm_summary": "...",
    "reuse_summary": "..."
  }
}"""


def _call_llm(prompt: str, api_key: str, api_base: str, model: str) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 2000,
        "temperature": 0.3,
    }
    resp = requests.post(
        f"{api_base.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=90,
        proxies={"http": None, "https": None},
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _validate_llm_output(data: dict, basic_stats: dict) -> dict:
    """校验 LLM 输出，确保必要字段存在，且 basic_stats 未被覆盖。"""
    required = ["visual_language", "narrative_performance_structure",
                 "reusable_patterns", "search_tags", "summary_text"]
    for field in required:
        if field not in data:
            data[field] = {}

    if not isinstance(data.get("reusable_patterns"), list):
        data["reusable_patterns"] = []
    if not isinstance(data.get("search_tags"), dict):
        data["search_tags"] = {}

    return data


def _build_llm_input(draft_summary: dict, visual_stats: dict, max_captions: int) -> str:
    """压缩输入，不把全量 shot 塞给 LLM。"""
    payload = {
        "mv_id": draft_summary.get("mv_id"),
        "basic_stats": draft_summary.get("basic_stats", {}),
        "editing_rhythm": draft_summary.get("editing_rhythm", {}),
        "section_stats": draft_summary.get("music_visual_relation", {}).get("section_level_relation", [])[:20],
        "visual_stats": {
            k: v for k, v in visual_stats.items()
            if k != "representative_captions"
        },
        "representative_captions": visual_stats.get("representative_captions", [])[:max_captions],
        "vocal_stats": {
            "vocal_shot_ratio": draft_summary.get("basic_stats", {}).get("vocal_shot_ratio"),
            "vocal_shot_count": draft_summary.get("basic_stats", {}).get("vocal_shot_count"),
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def enhance_summary_with_llm(
    draft_summary: dict,
    visual_stats: dict,
    max_captions: int = 30,
) -> dict:
    """
    调用 LLM 增强 draft_summary，返回合并后的完整 summary。
    失败时返回原始 draft_summary，method 标记为 rule_only_fallback。
    """
    api_key = os.getenv("VLM_API_KEY") or os.getenv("LLM_API_KEY", "")
    api_base = os.getenv("VLM_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("VLM_MODEL", "gpt-4o")

    if not api_key:
        print("[Step 7] WARNING: 未找到 API Key，跳过 LLM 增强")
        draft_summary["method"] = "rule_only_fallback"
        return draft_summary

    llm_input = _build_llm_input(draft_summary, visual_stats, max_captions)

    try:
        raw = _call_llm(llm_input, api_key, api_base, model)

        # 提取 JSON（防止 LLM 包了 markdown 代码块）
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        llm_data = json.loads(raw)
        llm_data = _validate_llm_output(llm_data, draft_summary.get("basic_stats", {}))

        # 合并：LLM 字段覆盖 draft，但 basic_stats 保持程序计算结果
        merged = {**draft_summary}
        for field in ["visual_language", "narrative_performance_structure",
                       "reusable_patterns", "search_tags", "summary_text"]:
            if field in llm_data:
                merged[field] = llm_data[field]

        # 把颜色等规则统计结果补回 visual_language（LLM 可能没填）
        vl = merged.get("visual_language", {})
        if not vl.get("color_palette"):
            vl["color_palette"] = visual_stats.get("color_palette", [])
        if not vl.get("color_temperature"):
            vl["color_temperature"] = visual_stats.get("color_temperature")
        if not vl.get("dominant_scene_types"):
            vl["dominant_scene_types"] = visual_stats.get("dominant_scene_types", [])
        merged["visual_language"] = vl
        merged["method"] = "rule_stats_with_llm"

        print("[Step 7] LLM 增强完成")
        return merged

    except Exception as e:
        print(f"[Step 7] WARNING: LLM 调用失败，退回规则版本\n  原因: {e}")
        draft_summary["method"] = "rule_only_fallback"
        return draft_summary
