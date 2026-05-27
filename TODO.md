# Pipeline 待办

## 已完成

- [x] 音视频节奏关联分析 — `sequence_table` 填充（镜头数 / 平均时长 / 剪辑频率）
- [x] 关键帧颜色调性分析 — K-Means 聚色，输出主色 hex + 冷暖色温
- [x] 人声段落标注 — htdemucs 接入 + librosa RMS，输出 `has_vocals` / `vocal_energy`
- [x] BPM 自动计算 — librosa，Step 1 输出 `source/bpm.json`
- [x] 关键帧黑帧/模糊帧过滤 — 拉普拉斯方差 + 亮度检测，自动偏移重试
- [x] shot_review.csv 补充颜色和人声列
- [x] 批量处理 — `src/batch_run.py`，自动扫描 `data/raw/`
- [x] Step 7 案例级总结（规则版 + LLM 增强）— `case_summary.json` + `case_summary.md`

---

## 待做

### 一、Step 7 Phase 4：为检索做准备

**目标**：让 `case_summary` 可被案例库使用。

**实现方式**：
1. 新增 `scripts/build_case_index.py`，将多个 `case_summary.json` 聚合为 `case_index.json`
2. 保证 `search_tags` 枚举稳定（对齐 `label_taxonomy.yaml`）
3. 为后续 embedding 检索保留字段（`one_sentence_summary` + `search_tags`）

---

### 二、TransNetV2 镜头检测接入

**目标**：替代 PySceneDetect，提升镜头切分精度。

**实现方式**：`configs/pipeline.yaml` 中 `transnetv2.enabled` 已预留，补充 `shot_detector_transnetv2.py` 并接入 `main.py`。

---

### 三、shot_review 复核回写机制

**目标**：人工复核 CSV 修改后，能回写到 `mv_case_asset.json`，形成闭环。

**实现方式**：新增 `scripts/import_review.py`，读取修改后的 `shot_review.csv`，更新对应 shot 的字段和 `needs_review` 状态。

---

## 优先级建议

| 项目 | 依赖新环境 | 新依赖包 | 工作量 |
|------|-----------|---------|--------|
| 一、Case Index Builder | 否 | 否 | 小 |
| 三、复核回写 | 否 | 否 | 小 |
| 二、TransNetV2 | 否 | 需安装 | 中 |

建议顺序：一 → 三 → 二
