#!/usr/bin/env bash
# ============================================================
# Step 4 SongFormer WSL 环境一键初始化脚本
#
# 适用对象：GPU Windows + WSL2 (Ubuntu) 新开发者
# 前提条件：
#   1. WSL2 已安装 Ubuntu 22.04
#   2. NVIDIA 驱动已安装，nvidia-smi 在 WSL 内可用
#   3. Miniconda 已安装（默认路径 ~/miniconda3）
#
# 用法：
#   chmod +x setup_wsl_env.sh
#   ./setup_wsl_env.sh
#
# 完成后还需手动下载 ckpts，见脚本末尾说明。
# ============================================================

set -e

CONDA_BASE="${HOME}/miniconda3"
ENV_NAME="songformer"
PROJECT_DIR="${HOME}/projects/SongFormer"
REPO_URL="https://github.com/ASLP-lab/SongFormer.git"

echo "=================================================="
echo "  Step 4 SongFormer 环境初始化"
echo "=================================================="

# ── 1. 检查 conda ─────────────────────────────────────
if [ ! -f "${CONDA_BASE}/bin/conda" ]; then
    echo "[ERROR] 未找到 conda：${CONDA_BASE}/bin/conda"
    echo "请先安装 Miniconda：https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

CONDA="${CONDA_BASE}/bin/conda"
PIP="${CONDA_BASE}/envs/${ENV_NAME}/bin/pip"
PYTHON="${CONDA_BASE}/envs/${ENV_NAME}/bin/python"

# ── 2. 创建 conda 环境 ────────────────────────────────
if "${CONDA}" env list | grep -q "^${ENV_NAME} "; then
    echo "[跳过] conda 环境 '${ENV_NAME}' 已存在"
else
    echo "[1/6] 创建 conda 环境 ${ENV_NAME} (Python 3.10) ..."
    "${CONDA}" create -n "${ENV_NAME}" python=3.10 -y
fi

# ── 3. 安装 PyTorch 2.4.0 + CUDA 12.1 ────────────────
echo "[2/6] 安装 PyTorch 2.4.0 (CUDA 12.1) ..."
"${PIP}" install torch==2.4.0 torchaudio==2.4.0 \
    --index-url https://download.pytorch.org/whl/cu121 \
    --quiet

# ── 4. 克隆 SongFormer 仓库 ───────────────────────────
if [ -d "${PROJECT_DIR}/.git" ]; then
    echo "[跳过] SongFormer 仓库已存在：${PROJECT_DIR}"
else
    echo "[3/6] 克隆 SongFormer ..."
    mkdir -p "${HOME}/projects"
    git clone "${REPO_URL}" "${PROJECT_DIR}"
    cd "${PROJECT_DIR}"
    git submodule update --init --recursive
fi

cd "${PROJECT_DIR}"

# ── 5. 安装 Python 依赖（排除 torch/torchaudio/triton）──
echo "[4/6] 安装 SongFormer 依赖 ..."
grep -vE "^(torch==|torchaudio==|triton==|#|$)" requirements.txt > /tmp/sf_requirements_filtered.txt
"${PIP}" install -r /tmp/sf_requirements_filtered.txt \
    --quiet \
    --timeout 120 \
    --retries 5

# setuptools<81 避免 pkg_resources 兼容问题
"${PIP}" install "setuptools<81" --quiet

# ── 6. 应用必要的 patch ───────────────────────────────
echo "[5/6] 应用 patch ..."

INFER_PY="${PROJECT_DIR}/src/SongFormer/infer/infer.py"

# Patch A: MuQ 加载方式
# 原始：muq = MuQ.from_pretrained("OpenMuQ/MuQ-large-msd-iter")
# 原因：MuQ.__init__() 接口变更，from_pretrained 不再兼容
if grep -q 'from_pretrained("OpenMuQ/MuQ-large-msd-iter")' "${INFER_PY}" 2>/dev/null; then
    python3 - "${INFER_PY}" <<'PATCH_SCRIPT'
import sys
path = sys.argv[1]
with open(path, "r") as f:
    content = f.read()
content = content.replace(
    'muq = MuQ.from_pretrained("OpenMuQ/MuQ-large-msd-iter")',
    'muq_config_file = OmegaConf.load(os.path.join("ckpts", "muq_config2.json"))\n    muq = MuQ(muq_config_file)'
)
with open(path, "w") as f:
    f.write(content)
print("  Patch A (MuQ loading) 已应用")
PATCH_SCRIPT
else
    echo "  Patch A (MuQ loading) 已存在，跳过"
fi

# Patch B: MusicFM wav2vec2 config 本地化
# 原始：Wav2Vec2ConformerConfig.from_pretrained("facebook/wav2vec2-conformer-rope-large-960h-ft")
# 原因：联网访问 HuggingFace 不稳定，改为读 ckpts 本地文件
MUSICFM_PY="${PROJECT_DIR}/src/third_party/musicfm/model/musicfm_25hz.py"
if grep -q '"facebook/wav2vec2-conformer-rope-large-960h-ft"' "${MUSICFM_PY}" 2>/dev/null; then
    sed -i 's|"facebook/wav2vec2-conformer-rope-large-960h-ft"|"ckpts/wav2vec2-conformer-rope-large-960h-ft"|g' "${MUSICFM_PY}"
    echo "  Patch B (MusicFM local config) 已应用"
else
    echo "  Patch B (MusicFM local config) 已存在，跳过"
fi

echo "[6/6] 环境初始化完成！"

# ── ckpts 说明 ────────────────────────────────────────
echo ""
echo "=================================================="
echo "  !! 需要手动下载 ckpts !!"
echo "=================================================="
echo ""
echo "将以下文件放入 ${PROJECT_DIR}/src/SongFormer/ckpts/ ："
echo ""
echo "  ckpts/"
echo "  ├── SongFormer.safetensors      <- 主模型"
echo "  ├── muq_config2.json            <- MuQ 配置"
echo "  ├── MusicFM/"
echo "  │   ├── msd_stats.json"
echo "  │   └── pretrained_msd.pt"
echo "  └── wav2vec2-conformer-rope-large-960h-ft/"
echo "      └── config.json"
echo ""
echo "下载来源（选其一）："
echo "  HuggingFace: https://huggingface.co/ASLP-lab/SongFormer"
echo "  ModelScope:  https://modelscope.cn/models/ASLP-lab/SongFormer"
echo ""
echo "下载完成后运行验证："
echo "  cd ${PROJECT_DIR}"
echo "  bash run_local_test.sh"
echo ""
