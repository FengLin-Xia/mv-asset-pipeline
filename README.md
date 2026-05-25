# MV 案例资产拆解 Pipeline

将 MV 视频自动拆解为结构化资产，供后续 AI 辅助创作使用。

**输出内容**：镜头切分、关键帧、音乐段落结构、视觉 Caption、四层 JSON 资产表。

---

## 目录

- [前提条件](#前提条件)
- [环境安装](#环境安装)
  - [主环境（mvcase）](#1-主环境mvcase)
  - [Step 4 音乐分析环境（songformer）](#2-step-4-音乐分析环境songformer)
- [配置](#配置)
- [WSL 侧运行机制与排查](#wsl-侧运行机制与排查)
- [运行](#运行)
- [输出结构](#输出结构)
- [常见问题](#常见问题)

---

## 前提条件

| 要求 | 说明 |
|------|------|
| OS | Windows 10/11，已安装 WSL2（Ubuntu 22.04） |
| GPU | NVIDIA 独显，驱动已安装，`nvidia-smi` 可用 |
| Miniconda | Windows 侧安装，用于主环境；WSL 侧安装，用于 SongFormer |

> FFmpeg 由 `environment.yml` 通过 conda-forge 自动安装，无需手动配置。

---

## 环境安装

### 1. 主环境（mvcase）

在 Windows 终端中运行：

```bash
# 在 mv_case_pipeline/ 目录下
conda env create -f environment.yml
conda activate mvcase
```

安装 PyTorch（根据显卡选择）：

```bash
# 查看 CUDA 版本
nvidia-smi

# CUDA 12.x
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# 仅 CPU（不支持 Step 4）
pip install torch torchvision torchaudio
```

### 2. Step 4 音乐分析环境（SongFormer）

Step 4 运行在 WSL 侧独立 conda 环境中，与主环境完全隔离。

**在 WSL Ubuntu 终端中**运行初始化脚本：

```bash
cd /mnt/c/Users/<你的用户名>/Desktop/BIG_PROGRAM/mv_case_pipeline/step4_songformer
chmod +x setup_wsl_env.sh
./setup_wsl_env.sh
```

脚本会自动完成：创建 conda 环境 `songformer`、安装 PyTorch + 依赖、克隆 SongFormer 仓库、应用必要的 patch。

**脚本完成后，手动下载 ckpts**（模型文件较大，无法自动下载）：

从以下任一地址下载：
- HuggingFace：https://huggingface.co/ASLP-lab/SongFormer
- ModelScope：https://modelscope.cn/models/ASLP-lab/SongFormer

将文件放入 WSL 中的以下目录（路径为 SongFormer 仓库内）：

```
~/projects/SongFormer/src/SongFormer/ckpts/
├── SongFormer.safetensors
├── muq_config2.json
├── MusicFM/
│   ├── msd_stats.json
│   └── pretrained_msd.pt
└── wav2vec2-conformer-rope-large-960h-ft/
    └── config.json
```

验证 SongFormer 可以独立运行：

```bash
cd ~/projects/SongFormer
bash run_local_test.sh
```

---

## 配置

### API Key（Step 5 视觉 Caption 需要）

```bash
cp .env.example .env
# 编辑 .env，填入 VLM_API_KEY（必填）
# VLM_API_BASE 和 VLM_MODEL 有默认值，可按需修改
```

不需要 Caption 时可跳过此步，运行时加 `--skip-caption` 参数即可。

### pipeline.yaml

主要配置项在 `configs/pipeline.yaml`，一般不需要修改。

如果你的 WSL miniconda 或 SongFormer 路径与默认不同，修改：

```yaml
music_structure:
  songformer:
    wsl_python: "/home/<你的用户名>/miniconda3/envs/songformer/bin/python"
    project_dir: "/home/<你的用户名>/projects/SongFormer"
```

---

## WSL 侧运行机制与排查

### 调用架构

Step 4 不在 Windows 主环境中运行，而是通过 `wsl` 命令跨边界调用：

```
Windows 主环境（mvcase）
  └── subprocess: wsl python run_step4.py
        └── WSL Ubuntu（songformer conda 环境）
              └── SongFormer infer.py
                    └── 输出 music_structure_raw.json（写回 Windows 文件系统）
```

### 路径映射关系

Windows 路径与 WSL 路径是同一文件的两种写法：

| Windows | WSL |
|---------|-----|
| `C:\Users\vip\Desktop\BIG_PROGRAM\` | `/mnt/c/Users/vip/Desktop/BIG_PROGRAM/` |
| `data/processed/MV_001/source/audio.wav` | `/mnt/c/.../data/processed/MV_001/source/audio.wav` |

`music_structure_analyzer.py` 会自动完成路径转换，无需手动处理。

### 已验证的 WSL 配置

```yaml
# configs/pipeline.yaml
music_structure:
  songformer:
    wsl_python: "/home/vip/miniconda3/envs/songformer/bin/python"
    project_dir: "/home/vip/projects/SongFormer"
```

### ckpts 实际检查路径

ckpts 必须放在仓库内的 `src/SongFormer/ckpts/`，**不是**仓库根目录的 `ckpts/`：

```
# 正确路径
~/projects/SongFormer/src/SongFormer/ckpts/

# 错误位置（run_step4.py 不会在这里查找）
~/projects/SongFormer/ckpts/
```

### WSL 侧验证命令

Step 4 出问题时，在 WSL 中依次检查：

```bash
# 1. 确认 conda 环境和 Python 路径
conda activate songformer
which python
# 预期：/home/<user>/miniconda3/envs/songformer/bin/python

# 2. 确认 GPU 可用
nvidia-smi

# 3. 确认 ckpts 完整
ls -lah ~/projects/SongFormer/src/SongFormer/ckpts/
# 预期：看到 SongFormer.safetensors、muq_config2.json、MusicFM/、wav2vec2-conformer-rope-large-960h-ft/

# 4. 独立跑一次验证
cd ~/projects/SongFormer
bash run_local_test.sh
# 预期：在 test_run/output/ 生成 audio.json
```

---

## 运行

将视频放入 `data/raw/`，然后在 `mv_case_pipeline/` 目录下运行：

### 一键全流程

```bash
python src/main.py --input data/raw/MV_001.mp4 --mv-id MV_001
```

### 分步运行

```bash
python scripts/run_stage1_standardize.py --input data/raw/MV_001.mp4 --mv-id MV_001
python scripts/run_stage2_detect_shots.py --mv-id MV_001
python scripts/run_stage3_extract_keyframes.py --mv-id MV_001
python scripts/run_stage4_music_structure.py --mv-id MV_001
python scripts/run_stage5_caption.py --mv-id MV_001
python scripts/run_stage6_build_json.py --mv-id MV_001
```

### 常用参数

| 参数 | 说明 |
|------|------|
| `--debug --max-shots 10` | 只处理前 N 个镜头，用于快速验证 |
| `--skip-music` | 跳过 Step 4（SongFormer 未配置时使用） |
| `--skip-caption` | 跳过 Step 5（无 API Key 时使用） |
| `--start-from 5` | 从第 N 步继续，跳过已完成的步骤 |

### 示例

```bash
# 快速验证前 3 步（不需要 GPU 也不需要 API Key）
python src/main.py --input data/raw/MV_001.mp4 --mv-id MV_001 --skip-music --skip-caption --debug

# 跳过 Caption，只跑到 Step 4
python src/main.py --input data/raw/MV_001.mp4 --mv-id MV_001 --skip-caption

# 已有 Step 1-4 结果，只重跑 Caption 和 JSON 结构化
python src/main.py --input data/raw/MV_001.mp4 --mv-id MV_001 --start-from 5
```

---

## 输出结构

```
data/processed/MV_001/
├── source/
│   ├── video.mp4             标准化视频（720p 25fps）
│   ├── audio.wav             提取的音频
│   └── metadata.json         视频元信息（时长、分辨率等）
├── clips/
│   └── MV_001_S001.mp4       各镜头视频片段
├── frames/
│   └── MV_001_S001_F001.jpg  关键帧（每镜头开始/中间/结尾各 1 张）
└── analysis/
    ├── scenes_raw.json           镜头切分结果（Step 2）
    ├── keyframes_raw.json        关键帧索引（Step 3）
    ├── music_structure_raw.json  音乐段落结构（Step 4）
    ├── captions_raw.json         视觉 Caption（Step 5）
    ├── mv_case_asset.json        四层资产 JSON（Step 6）
    └── shot_review.csv           人工复核表（Step 6）
```

### music_structure_raw.json 格式

```json
{
  "mv_id": "MV_001",
  "method": "songformer_wsl",
  "bpm": null,
  "segments": [
    {
      "start_time": "00:00:00.000",
      "end_time": "00:00:02.520",
      "start_seconds": 0.0,
      "end_seconds": 2.52,
      "label": "intro",
      "mapped_music_section": "开场"
    }
  ]
}
```

---

## 常见问题

### Step 4 失败：ckpts 文件缺失

```
[Step 4] ERROR: 缺少必要的 ckpts 文件
```

按照 [Step 4 音乐分析环境](#2-step-4-音乐分析环境songformer) 中的说明下载并放置 ckpts 文件。

### Step 4 失败：GPU 不可用

在 WSL 中验证 GPU 是否可访问：

```bash
wsl nvidia-smi
```

如果无输出，检查 NVIDIA 驱动版本是否支持 WSL2 GPU（驱动版本需 ≥ 470.76）。

### Step 4 失败：WSL Python 路径不对

报错中含 `No such file or directory` 且指向 Python 路径，修改 `configs/pipeline.yaml` 中的 `wsl_python` 为实际路径：

```bash
# 在 WSL 中查看实际路径
which python  # 在 songformer 环境激活后
```

### Step 5 失败：API Key 未配置

```
VLM_API_KEY not set
```

编辑 `.env` 文件填入 API Key，或使用 `--skip-caption` 跳过。

---

## 致谢

Step 4 音乐结构分析基于 [SongFormer](https://github.com/ASLP-lab/SongFormer) 实现，感谢 ASLP-lab 的开源工作。

---

### 从某步继续时提示文件不存在

前置步骤的输出文件缺失，需要先跑前面的步骤，或从 Step 1 重新开始。

### Step 4 输出了 warning，但不确定是否成功

Step 4 运行时终端会出现若干 warning，**只要最终生成了 `music_structure_raw.json` 且内容不为空，这些 warning 均可忽略**：

| Warning | 原因 | 是否影响结果 |
|---------|------|------------|
| `UserWarning: WSL localhost proxy` | WSL 网络代理提示，与推理无关 | 否 |
| `FutureWarning: ...` | PyTorch / transformers 版本兼容提示 | 否 |
| `RuntimeWarning: invalid value encountered in divide` | 音频特征计算中的边界情况 | 通常否，检查 JSON 内容确认 |

验证方式：

```bash
# 检查文件是否生成且 segments 不为空
python -c "import json; d=json.load(open('data/processed/MV_001/analysis/music_structure_raw.json')); print(len(d['segments']), 'segments')"
```
