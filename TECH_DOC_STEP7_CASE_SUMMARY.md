# Step 7 案例级总结技术方案

## 1. 背景

当前 `mv_case_pipeline` 已经完成 MV 视频的基础结构化拆解能力，包括视频标准化、镜头切分、关键帧抽取、颜色调性分析、音乐结构分析、人声标注、视觉 Caption，以及最终四层 JSON 资产表输出。

现有系统主要解决的是：

> 一支 MV 中有哪些镜头、关键帧、音乐段落、视觉描述和局部资产。

但对于后续 AI 辅助创作、案例检索、风格复用、Prompt 生成等场景，仅有镜头级资产还不够。系统还需要进一步回答：

> 这支 MV 整体是什么风格？  
> 它的音乐与画面如何配合？  
> 它的剪辑节奏有什么规律？  
> 它属于什么类型的 MV？  
> 它有哪些可复用的创作模式？

因此，本阶段新增 **Step 7：案例级总结 Case-level Summary**，用于将 `mv_case_asset.json` 中的局部事实聚合为案例级分析结果。

---

## 2. 目标

### 2.1 核心目标

新增一个案例级总结模块，将单个 MV 的结构化资产进一步聚合为：

```text
analysis/case_summary.json
analysis/case_summary.md
```

其中：

| 文件 | 用途 |
|---|---|
| `case_summary.json` | 给系统、检索、RAG、Prompt 生成模块使用 |
| `case_summary.md` | 给人类阅读、交接、复核、展示使用 |

---

### 2.2 能力目标

Step 7 需要实现以下能力：

1. 从 `mv_case_asset.json` 中读取镜头、音乐、视觉、颜色、人声等结构化信息。
2. 自动计算案例级基础统计指标。
3. 按音乐段落聚合镜头数量、平均镜头时长、视觉节奏变化。
4. 基于 caption 和颜色信息总结整体视觉风格。
5. 基于音乐段落与镜头节奏关系，总结音乐—视觉同步策略。
6. 基于分析结果生成结构化 `case_summary.json`。
7. 生成可读性更强的 `case_summary.md`。
8. 支持单个 MV 运行，也支持批量运行。

---

## 3. 非目标

本阶段暂不解决以下问题：

1. 不做复杂前端展示。
2. 不做跨 MV 检索。
3. 不做向量数据库接入。
4. 不做模型训练或微调。
5. 不做人工标注平台。
6. 不强依赖 LLM。如果没有 API Key，应至少能输出基础统计版 summary。
7. 不追求完全准确的艺术批评，只追求可解释、可复核、可复用的结构化总结。

---

## 4. Pipeline 位置

当前 Pipeline 为：

```text
Step 1   视频标准化 + BPM 计算
Step 1.5 音源分离
Step 2   镜头切分
Step 2.5 人声标注
Step 3   关键帧抽取
Step 3.5 颜色调性分析
Step 4   音乐结构分析
Step 5   视觉 Caption
Step 6   四层 JSON 结构化
```

新增：

```text
Step 7   案例级总结 Case-level Summary
```

更新后：

```text
Step 1   视频标准化 + BPM 计算
Step 1.5 音源分离
Step 2   镜头切分
Step 2.5 人声标注
Step 3   关键帧抽取
Step 3.5 颜色调性分析
Step 4   音乐结构分析
Step 5   视觉 Caption
Step 6   四层 JSON 结构化
Step 7   案例级总结
```

---

## 5. 输入与输出

### 5.1 输入文件

Step 7 的主要输入为：

```text
data/processed/{mv_id}/analysis/mv_case_asset.json
```

可选辅助输入：

```text
data/processed/{mv_id}/analysis/music_structure_raw.json
data/processed/{mv_id}/analysis/captions_raw.json
data/processed/{mv_id}/analysis/keyframes_raw.json
data/processed/{mv_id}/analysis/vocal_annotation_raw.json
data/processed/{mv_id}/source/bpm.json
data/processed/{mv_id}/source/metadata.json
```

原则上，Step 7 应优先读取 `mv_case_asset.json`。如果其中缺少字段，再回退读取上游 raw 文件。

---

### 5.2 输出文件

```text
data/processed/{mv_id}/analysis/case_summary.json
data/processed/{mv_id}/analysis/case_summary.md
```

---

## 6. `case_summary.json` 设计

### 6.1 顶层结构

```json
{
  "mv_id": "MV_001",
  "generated_at": "2026-05-27T12:00:00Z",
  "method": "rule_stats_with_optional_llm",
  "basic_stats": {},
  "visual_language": {},
  "editing_rhythm": {},
  "music_visual_relation": {},
  "narrative_performance_structure": {},
  "reusable_patterns": [],
  "search_tags": {},
  "summary_text": {}
}
```

---

### 6.2 `basic_stats`

用于记录稳定、可程序计算的基础指标。

```json
{
  "duration_seconds": 215.4,
  "shot_count": 167,
  "avg_shot_duration": 1.29,
  "median_shot_duration": 0.94,
  "min_shot_duration": 0.32,
  "max_shot_duration": 5.8,
  "bpm": 128,
  "music_section_count": 12,
  "captioned_shot_count": 160,
  "caption_coverage_ratio": 0.96,
  "vocal_shot_count": 102,
  "vocal_shot_ratio": 0.61
}
```

---

### 6.3 `visual_language`

用于总结整支 MV 的视觉语言。

```json
{
  "overall_style": "cold urban performance MV",
  "dominant_scene_types": [
    "urban night",
    "indoor performance",
    "close-up portrait"
  ],
  "dominant_visual_elements": [
    "singer close-up",
    "neon lighting",
    "dark background",
    "moving camera"
  ],
  "color_palette": [
    "blue",
    "purple",
    "black"
  ],
  "lighting_style": "low-key lighting with neon highlights",
  "camera_language": "frequent close-ups and handheld movement",
  "visual_mood": [
    "cold",
    "intense",
    "lonely",
    "high-energy"
  ]
}
```

---

### 6.4 `editing_rhythm`

用于总结剪辑节奏。

```json
{
  "overall_cutting_intensity": "high",
  "avg_shot_duration": 1.29,
  "fast_cut_ratio": 0.42,
  "slow_cut_ratio": 0.18,
  "fastest_sections": [
    "chorus_1",
    "chorus_2"
  ],
  "slowest_sections": [
    "intro",
    "bridge"
  ],
  "rhythm_strategy": "The chorus sections use shorter shots and higher visual density, while verse sections maintain longer performance shots."
}
```

---

### 6.5 `music_visual_relation`

用于总结音乐结构与视觉结构的关系。

```json
{
  "sync_strategy": "beat-synced editing",
  "section_level_relation": [
    {
      "section_id": "section_001",
      "label": "intro",
      "start_seconds": 0.0,
      "end_seconds": 12.4,
      "shot_count": 6,
      "avg_shot_duration": 2.06,
      "visual_strategy": "establishing mood and environment"
    },
    {
      "section_id": "section_004",
      "label": "chorus",
      "start_seconds": 62.5,
      "end_seconds": 91.2,
      "shot_count": 38,
      "avg_shot_duration": 0.75,
      "visual_strategy": "fast cutting and increased close-up density"
    }
  ],
  "chorus_visual_change": "Chorus sections show faster cutting and stronger performance emphasis.",
  "vocal_visual_relation": "Vocal-heavy parts tend to contain more singer performance shots."
}
```

---

### 6.6 `narrative_performance_structure`

用于判断 MV 是偏叙事、偏表演、偏舞蹈，还是偏概念氛围。

```json
{
  "structure_type": "performance-led",
  "performance_density": "high",
  "narrative_density": "low",
  "artist_presence": "high",
  "dance_presence": "low",
  "story_progression": "weak",
  "description": "The MV is mainly driven by singer performance, visual atmosphere, and editing rhythm rather than a clear linear narrative."
}
```

---

### 6.7 `reusable_patterns`

用于沉淀可复用创作模式。

```json
[
  {
    "pattern_name": "chorus_fast_cut_burst",
    "display_name": "副歌快剪爆发",
    "description": "The chorus section significantly reduces shot duration and increases close-up and motion shots.",
    "suitable_for": [
      "high-energy pop music",
      "electronic music",
      "rap MV chorus"
    ],
    "prompt_hint": "Use rapid beat-synced cuts during the chorus, alternating singer close-ups with high-motion urban shots."
  },
  {
    "pattern_name": "cold_urban_neon_mood",
    "display_name": "冷色都市霓虹氛围",
    "description": "The MV builds a cold urban mood through dark backgrounds, blue-purple lighting, and night street imagery.",
    "suitable_for": [
      "urban loneliness",
      "night city mood",
      "cool electronic style"
    ],
    "prompt_hint": "Use cold blue and purple neon lighting, dark urban night backgrounds, and isolated singer close-ups."
  }
]
```

---

### 6.8 `search_tags`

用于后续案例库检索。

```json
{
  "mv_type": [
    "performance_led"
  ],
  "visual_style": [
    "urban",
    "night",
    "cold_tone",
    "neon",
    "high_contrast"
  ],
  "editing": [
    "fast_cut",
    "beat_sync",
    "montage"
  ],
  "music_energy": [
    "high_energy",
    "fast_bpm"
  ],
  "content": [
    "singer_performance",
    "close_up",
    "city_environment"
  ],
  "generation_use": [
    "chorus_reference",
    "style_reference",
    "editing_reference"
  ]
}
```

---

### 6.9 `summary_text`

用于保存可直接展示的自然语言总结。

```json
{
  "one_sentence_summary": "This is a high-energy performance-led MV built around cold urban visuals, fast cutting, and singer close-ups.",
  "visual_summary": "The MV mainly uses dark urban scenes, cold blue-purple lighting, and frequent close-up shots to create an intense and isolated mood.",
  "rhythm_summary": "The editing rhythm becomes significantly faster in chorus sections, suggesting a strong relationship between music structure and visual intensity.",
  "reuse_summary": "This case is suitable as a reference for fast-cut chorus editing, cold urban neon style, and performance-centered MV generation."
}
```

---

## 7. `case_summary.md` 设计

`case_summary.md` 面向人类阅读，结构建议如下：

```markdown
# MV_001 案例级总结

## 1. 一句话概括

这是一支以冷色都市夜景、快速剪辑和高频人物特写为核心的表演型 MV。

## 2. 基础统计

| 指标 | 数值 |
|---|---|
| 视频时长 | 215.4s |
| 镜头数量 | 167 |
| 平均镜头时长 | 1.29s |
| BPM | 128 |
| 人声镜头比例 | 61% |

## 3. 视觉语言

整体画面以冷色、高对比、低照度为主，频繁出现人物近景、夜景空间、霓虹灯和运动镜头。

## 4. 剪辑节奏

整体剪辑强度较高。副歌段落镜头平均时长明显降低，说明画面节奏与音乐高潮存在较强同步关系。

## 5. 音乐—视觉关系

主歌段落更偏稳定表演镜头，副歌段落则通过快剪、特写和运动镜头制造爆发感。

## 6. 叙事 / 表演结构

该 MV 以表演驱动为主，没有强线性叙事，主要通过人物表演、场景切换和剪辑节奏推动情绪。

## 7. 可复用创作模式

### 7.1 副歌快剪爆发

适合用于高能量流行、电子、说唱类音乐的高潮段落。

### 7.2 冷色都市霓虹氛围

适合用于都市孤独感、夜景、冷色电子风格的 MV 生成参考。

## 8. 推荐检索标签

- performance_led
- cold_tone
- urban_night
- neon
- fast_cut
- beat_sync
- chorus_reference
```

---

## 8. 模块设计

### 8.1 新增目录建议

```text
src/
├── analysis/
│   ├── case_summary/
│   │   ├── __init__.py
│   │   ├── case_summary_builder.py
│   │   ├── stats_extractor.py
│   │   ├── section_analyzer.py
│   │   ├── visual_summarizer.py
│   │   ├── llm_case_summarizer.py
│   │   └── markdown_renderer.py
```

---

### 8.2 新增脚本

```text
scripts/run_stage7_case_summary.py
```

运行方式：

```bash
python scripts/run_stage7_case_summary.py --mv-id MV_001
```

支持参数：

| 参数 | 说明 |
|---|---|
| `--mv-id` | 指定 MV ID |
| `--no-llm` | 不调用 LLM，只输出规则统计版 summary |
| `--overwrite` | 覆盖已有 case_summary |
| `--debug` | 输出中间统计信息 |
| `--language zh` | 输出中文总结 |
| `--language en` | 输出英文总结 |

示例：

```bash
# 默认运行，使用 LLM 增强总结
python scripts/run_stage7_case_summary.py --mv-id MV_001

# 不调用 LLM，只生成基础统计版
python scripts/run_stage7_case_summary.py --mv-id MV_001 --no-llm

# 覆盖已有结果
python scripts/run_stage7_case_summary.py --mv-id MV_001 --overwrite
```

---

## 9. 核心实现逻辑

### 9.1 主流程

```python
def build_case_summary(mv_id: str, use_llm: bool = True):
    paths = resolve_paths(mv_id)

    asset = load_json(paths.mv_case_asset)

    basic_stats = extract_basic_stats(asset)
    section_stats = analyze_music_sections(asset)
    visual_stats = summarize_visual_signals(asset)
    rhythm_stats = analyze_editing_rhythm(asset, section_stats)

    draft_summary = build_rule_based_summary(
        mv_id=mv_id,
        basic_stats=basic_stats,
        section_stats=section_stats,
        visual_stats=visual_stats,
        rhythm_stats=rhythm_stats,
    )

    if use_llm:
        case_summary = enhance_summary_with_llm(draft_summary, asset)
    else:
        case_summary = draft_summary

    save_json(case_summary, paths.case_summary_json)

    markdown = render_case_summary_md(case_summary)
    save_text(markdown, paths.case_summary_md)

    return case_summary
```

---

### 9.2 基础统计计算

```python
def extract_basic_stats(asset: dict) -> dict:
    shots = asset.get("shots", [])

    durations = [
        shot["end_seconds"] - shot["start_seconds"]
        for shot in shots
        if "start_seconds" in shot and "end_seconds" in shot
    ]

    return {
        "shot_count": len(shots),
        "avg_shot_duration": mean(durations),
        "median_shot_duration": median(durations),
        "min_shot_duration": min(durations),
        "max_shot_duration": max(durations),
        "captioned_shot_count": count_captioned_shots(shots),
        "caption_coverage_ratio": count_captioned_shots(shots) / max(len(shots), 1),
        "vocal_shot_count": count_vocal_shots(shots),
        "vocal_shot_ratio": count_vocal_shots(shots) / max(len(shots), 1),
    }
```

---

### 9.3 音乐段落聚合

```python
def analyze_music_sections(asset: dict) -> list[dict]:
    sections = asset.get("music_structure", {}).get("segments", [])
    shots = asset.get("shots", [])

    results = []

    for idx, section in enumerate(sections):
        section_start = section["start_seconds"]
        section_end = section["end_seconds"]

        overlapping_shots = [
            shot for shot in shots
            if overlaps(
                shot["start_seconds"],
                shot["end_seconds"],
                section_start,
                section_end,
            )
        ]

        durations = [
            shot["end_seconds"] - shot["start_seconds"]
            for shot in overlapping_shots
        ]

        results.append({
            "section_id": f"section_{idx + 1:03d}",
            "label": section.get("label"),
            "mapped_music_section": section.get("mapped_music_section"),
            "start_seconds": section_start,
            "end_seconds": section_end,
            "shot_count": len(overlapping_shots),
            "avg_shot_duration": mean(durations) if durations else None,
            "visual_intensity": classify_visual_intensity(durations),
        })

    return results
```

---

### 9.4 剪辑强度判断

建议先用简单规则：

```python
def classify_cutting_intensity(avg_shot_duration: float) -> str:
    if avg_shot_duration <= 1.0:
        return "high"
    elif avg_shot_duration <= 2.5:
        return "medium"
    else:
        return "low"
```

镜头级判断：

```python
def classify_shot_duration(duration: float) -> str:
    if duration <= 1.0:
        return "fast_cut"
    elif duration <= 2.5:
        return "medium_cut"
    else:
        return "slow_cut"
```

---

### 9.5 视觉信息聚合

从 caption、关键帧颜色、已有标签中抽取高频信息。

```python
def summarize_visual_signals(asset: dict) -> dict:
    shots = asset.get("shots", [])

    captions = [
        shot.get("caption", "")
        for shot in shots
        if shot.get("caption")
    ]

    colors = collect_dominant_colors(shots)

    keywords = extract_keywords_from_captions(captions)

    return {
        "caption_count": len(captions),
        "top_caption_keywords": keywords[:20],
        "dominant_colors": colors[:5],
        "representative_captions": select_representative_captions(captions),
    }
```

第一版 `extract_keywords_from_captions` 可以非常简单：

1. 英文 caption：用词频 + stopwords。
2. 中文 caption：先不做复杂分词，可直接交给 LLM。
3. 如果已有 scene/object 标签，则优先用结构化标签。

---

## 10. LLM 增强总结

### 10.1 是否必须使用 LLM

不是必须。

Step 7 应支持两种模式：

| 模式 | 说明 |
|---|---|
| `rule_only` | 只基于程序统计生成 summary |
| `rule_stats_with_llm` | 先程序统计，再让 LLM 生成自然语言判断和标签 |

推荐默认：

```text
如果 VLM_API_KEY / LLM_API_KEY 存在，则启用 LLM。
否则自动退化为 rule_only。
```

---

### 10.2 LLM 输入

不要把所有镜头完整塞给 LLM。应只输入压缩后的信息：

```json
{
  "mv_id": "MV_001",
  "basic_stats": {},
  "section_stats": [],
  "visual_stats": {},
  "representative_captions": [],
  "top_colors": [],
  "vocal_stats": {}
}
```

---

### 10.3 LLM Prompt

```text
你是一个专业的 MV 视听语言分析助手。

下面是一支 MV 的结构化统计信息，包括：
- 基础镜头统计
- 音乐段落统计
- 代表性视觉 caption
- 颜色信息
- 人声标注统计

请生成一个 case_summary.json。

要求：
1. 输出必须是合法 JSON，不要输出 Markdown。
2. 不要编造数据中没有出现的具体人物、剧情、地点或物体。
3. 可以基于统计趋势进行风格归纳，但需要保持谨慎。
4. 如果信息不足，请使用 "unknown" 或 "insufficient_data"。
5. 重点总结整体风格、视觉语言、剪辑节奏、音乐视觉关系、叙事/表演结构、可复用创作模式、检索标签。
6. search_tags 必须使用 snake_case 英文标签。
7. summary_text 可以使用中文。
```

---

### 10.4 LLM 输出校验

LLM 输出必须经过 JSON 校验。

校验内容：

```text
1. 是否是合法 JSON
2. 是否包含必要字段
3. reusable_patterns 是否为数组
4. search_tags 是否为对象
5. basic_stats 不允许被 LLM 改写
6. 所有数值统计以程序统计结果为准
```

重要原则：

> LLM 只能补充解释和标签，不能覆盖程序计算出的事实数值。

---

## 11. 配置项

在 `configs/pipeline.yaml` 中新增：

```yaml
case_summary:
  enabled: true
  use_llm: true
  language: "zh"
  output_markdown: true

  thresholds:
    fast_cut_seconds: 1.0
    medium_cut_seconds: 2.5
    high_fast_cut_ratio: 0.35

  llm:
    api_key_env: "VLM_API_KEY"
    api_base_env: "VLM_API_BASE"
    model_env: "VLM_MODEL"
    max_representative_captions: 30
    max_section_items: 20
```

说明：

| 配置 | 说明 |
|---|---|
| `enabled` | 是否启用 Step 7 |
| `use_llm` | 是否使用 LLM 增强总结 |
| `language` | 输出语言 |
| `output_markdown` | 是否生成 MD 报告 |
| `fast_cut_seconds` | 小于等于该值视为快剪 |
| `medium_cut_seconds` | 中等镜头时长阈值 |
| `high_fast_cut_ratio` | 快剪比例超过该值视为高剪辑强度 |
| `max_representative_captions` | 传给 LLM 的最大 caption 数量 |
| `max_section_items` | 传给 LLM 的最大音乐段落数量 |

---

## 12. 与 `main.py` 集成

### 12.1 新增参数

在 `src/main.py` 中新增：

```bash
--skip-summary
```

含义：

```text
跳过 Step 7 案例级总结。
```

---

### 12.2 `start-from` 支持

现有 pipeline 已支持 `--start-from` 参数。新增 Step 7 后，应支持：

```bash
python src/main.py --input data/raw/MV_001.mp4 --mv-id MV_001 --start-from 7
```

即只重新生成案例级总结。

---

### 12.3 `main.py` 调用逻辑

```python
if not args.skip_summary and start_from <= 7:
    run_step7_case_summary(mv_id=args.mv_id)
```

---

## 13. 与 `batch_run.py` 集成

批量处理时，默认在 Step 6 后运行 Step 7。

新增支持：

```bash
python src/batch_run.py --skip-summary
```

批量案例总结：

```bash
python src/batch_run.py --start-from 7
```

---

## 14. 错误处理

### 14.1 缺少 `mv_case_asset.json`

报错：

```text
[Step 7] ERROR: Missing mv_case_asset.json. Please run Step 6 first.
```

处理方式：

```bash
python src/main.py --input data/raw/MV_001.mp4 --mv-id MV_001 --start-from 6
```

---

### 14.2 LLM 调用失败

不应中断整个流程。

处理方式：

```text
[Step 7] WARNING: LLM summary failed. Falling back to rule-only summary.
```

然后仍然输出：

```text
case_summary.json
case_summary.md
```

其中 method 标记为：

```json
"method": "rule_only_fallback"
```

---

### 14.3 caption 缺失

如果 Step 5 被跳过，仍然可以生成基础统计版 summary。

处理方式：

```json
{
  "visual_language": {
    "overall_style": "insufficient_data",
    "reason": "caption data is missing"
  }
}
```

---

### 14.4 music_structure 缺失

如果 Step 4 被跳过，则音乐—视觉关系不可分析。

处理方式：

```json
{
  "music_visual_relation": {
    "sync_strategy": "insufficient_data",
    "reason": "music structure data is missing"
  }
}
```

---

## 15. 验收标准

### 15.1 基础验收

运行：

```bash
python scripts/run_stage7_case_summary.py --mv-id MV_001
```

应生成：

```text
data/processed/MV_001/analysis/case_summary.json
data/processed/MV_001/analysis/case_summary.md
```

---

### 15.2 JSON 验收

`case_summary.json` 必须满足：

1. 是合法 JSON。
2. 包含 `mv_id`。
3. 包含 `basic_stats`。
4. 包含 `visual_language`。
5. 包含 `editing_rhythm`。
6. 包含 `music_visual_relation`。
7. 包含 `reusable_patterns`。
8. 包含 `search_tags`。
9. 程序统计字段不能为明显错误值，例如镜头数量为 0。
10. 如果上游信息缺失，应写入 `insufficient_data`，而不是编造。

---

### 15.3 Markdown 验收

`case_summary.md` 必须包含：

```text
# {mv_id} 案例级总结
## 1. 一句话概括
## 2. 基础统计
## 3. 视觉语言
## 4. 剪辑节奏
## 5. 音乐—视觉关系
## 6. 叙事 / 表演结构
## 7. 可复用创作模式
## 8. 推荐检索标签
```

---

### 15.4 降级验收

当没有 API Key 或 LLM 调用失败时，运行：

```bash
python scripts/run_stage7_case_summary.py --mv-id MV_001 --no-llm
```

仍应生成基础版：

```text
case_summary.json
case_summary.md
```

---

## 16. 推荐开发顺序

### Phase 1：规则统计版

目标：不依赖 LLM，先跑通 Step 7。

任务：

```text
1. 新建 scripts/run_stage7_case_summary.py
2. 新建 case_summary_builder.py
3. 读取 mv_case_asset.json
4. 计算 basic_stats
5. 计算 section_stats
6. 计算 editing_rhythm
7. 输出 case_summary.json
8. 输出 case_summary.md
```

---

### Phase 2：LLM 增强版

目标：让 summary 更像真正的案例分析。

任务：

```text
1. 增加 llm_case_summarizer.py
2. 设计压缩输入 schema
3. 调用已有 VLM/LLM API 配置
4. 校验 LLM JSON 输出
5. 合并程序统计结果和 LLM 分析结果
6. 失败时 fallback 到 rule_only
```

---

### Phase 3：Pipeline 集成

目标：纳入主链路。

任务：

```text
1. main.py 增加 Step 7
2. batch_run.py 增加 Step 7
3. 增加 --skip-summary
4. 支持 --start-from 7
5. 更新 README
```

---

### Phase 4：为后续检索做准备

目标：让 case_summary 可被案例库使用。

任务：

```text
1. 保证 search_tags 稳定
2. 保证 reusable_patterns 可转 prompt
3. 新增 case_index.json 构建脚本
4. 为后续 embedding 检索保留字段
```

---

## 17. 后续扩展方向

Step 7 完成后，可以继续发展：

```text
Step 8   Case Index Builder
Step 9   Case Retrieval Demo
Step 10  Prompt Pack Generator
Step 11  Human Review / Label Correction
```

其中最自然的下一步是：

```text
Step 8: 把多个 case_summary.json 聚合成 case_index.json
```

例如：

```json
[
  {
    "mv_id": "MV_001",
    "one_sentence_summary": "...",
    "search_tags": ["fast_cut", "cold_tone", "urban_night"],
    "reusable_patterns": ["chorus_fast_cut_burst"]
  },
  {
    "mv_id": "MV_002",
    "one_sentence_summary": "...",
    "search_tags": ["warm_tone", "narrative_led", "slow_cut"],
    "reusable_patterns": ["story_driven_progression"]
  }
]
```

这会为后续案例检索和 RAG 铺路。

---

## 18. 总结

Step 7 的核心价值不是多生成一个报告，而是把当前 pipeline 从：

```text
MV 拆解工具
```

升级为：

```text
MV 案例资产分析系统
```

当前 Step 1–6 解决的是：

```text
这支 MV 里有什么？
```

Step 7 解决的是：

```text
这支 MV 是怎么工作的？
它适合如何被后续 AI 创作系统复用？
```

因此，Step 7 是后续案例库、检索系统、Prompt Pack、AI 辅助 MV 生成平台之间的关键中间层。
