# Pipeline 深度扩展待办

## 一、音视频节奏关联分析

**目标**：计算每个音乐段落内的剪辑密度，量化音乐结构与视觉节奏的对应关系。

**输入**：已有的 `scenes_raw.json`（镜头时间码）+ `music_structure_raw.json`（音乐段落）

**输出**：在 Step 6 的 `sequence_table` 中填入每个音乐段落的视觉节奏统计：

```json
{
  "segment_id": "SEQ_001",
  "label": "chorus",
  "start_seconds": 33.36,
  "end_seconds": 51.84,
  "shot_count": 8,
  "avg_shot_duration": 2.31,
  "cut_frequency": 0.43
}
```

**实现方式**：纯数据计算，不需要新模型，在 `schema_builder.py` 中补充逻辑即可。

---

## 二、关键帧颜色调性分析

**目标**：提取每个关键帧的主色调，补充视觉风格维度。

**输入**：已有的关键帧图片（`frames/`）

**输出**：在 `keyframes_raw.json` 或 `mv_case_asset.json` 的关键帧条目中补充：

```json
{
  "frame_id": "MV_001_S003_F002",
  "dominant_colors": ["#1a2b4c", "#e8d5a3", "#ffffff"],
  "color_temperature": "cool"
}
```

**实现方式**：用 OpenCV 或 Pillow 做 K-Means 聚色，主环境已有这两个库，无需新依赖。新增 `src/modules/color_analyzer.py`，在 Step 3 后或 Step 6 前运行。

---

## 三、人声段落标注

**目标**：检测每个时间段是否有人声，为 shot 增加 `has_vocals` 字段。

**输入**：htdemucs 已分离的 `vocals.wav`（现在在 `demix/` 目录，需接入 pipeline）

**输出**：在 shot 条目中补充：

```json
{
  "shot_id": "MV_001_S005",
  "has_vocals": true,
  "vocal_energy": 0.72
}
```

**实现方式**：
1. 将 htdemucs 音源分离接入 Step 1（或新增 Step 1.5），输出 `source/vocals.wav`
2. 新增 `src/modules/vocal_detector.py`，用 librosa 计算 RMS 能量判断有无人声
3. 主环境已有 librosa，无需新依赖

**前置工作**：需要先把 demix 流程从手动改为 pipeline 内自动调用。

---

## 优先级建议

| 项目 | 依赖新环境 | 新依赖包 | 工作量 |
|------|-----------|---------|--------|
| 一、节奏关联 | 否 | 否 | 小 |
| 二、颜色分析 | 否 | 否 | 小 |
| 三、人声标注 | 否 | 否（librosa 已有） | 中（需先接入 demix） |

建议顺序：一 → 二 → 三
