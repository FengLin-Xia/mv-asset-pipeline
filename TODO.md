# Pipeline 待办

## 已完成

- [x] 一、音视频节奏关联分析 — `sequence_table` 填充（镜头数 / 平均时长 / 剪辑频率）
- [x] 二、关键帧颜色调性分析 — K-Means 聚色，输出主色 hex + 冷暖色温
- [x] 三、人声段落标注 — htdemucs 接入 + librosa RMS，输出 `has_vocals` / `vocal_energy`

---

## 待做

### ~~一、批量处理多个 MV~~ ✓

**目标**：支持一次性处理 `data/raw/` 下所有视频，自动分配 MV ID。

**实现方式**：在 `main.py` 或新增 `batch_run.py`，遍历 raw 目录，循环调用现有 pipeline。

---

### ~~二、关键帧模糊/黑帧过滤~~ ✓

**目标**：抽帧时跳过纯黑帧和模糊帧，提高关键帧质量。

**实现方式**：在 `keyframe_extractor.py` 中用 OpenCV 计算拉普拉斯方差（模糊检测）和亮度均值（黑帧检测），低于阈值则向后偏移重试。配置项 `avoid_blur_frames` 已在 `pipeline.yaml` 中预留，目前未生效。

---

### ~~三、shot_review.csv 补充颜色和人声列~~ ✓

**目标**：人工复核表目前只有 caption 相关字段，缺少颜色调性和人声标注列，不方便复核。

**实现方式**：在 `reviewer_export.py` 中补充 `dominant_colors` / `color_temperature` / `has_vocals` / `vocal_energy` 列。

---

### ~~四、BPM 接入~~ ✓

**目标**：`mv_table` 的 `bpm` 字段目前恒为 `null`，SongFormer 不输出 BPM，需单独计算。

**实现方式**：用 `librosa.beat.beat_track` 计算整首歌 BPM，在 Step 1.5 或 Step 4 后写入 `music_structure_raw.json`，schema_builder 直接读取。

---

## 优先级建议

| 项目 | 依赖新环境 | 新依赖包 | 工作量 |
|------|-----------|---------|--------|
| 三、复核表补列 | 否 | 否 | 小 |
| 四、BPM 接入 | 否 | 否（librosa 已有） | 小 |
| 二、黑帧/模糊过滤 | 否 | 否（OpenCV 已有） | 小 |
| 一、批量处理 | 否 | 否 | 中 |

建议顺序：三 → 四 → 二 → 一
