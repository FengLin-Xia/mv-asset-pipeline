"""
Step 4: 音乐结构分析（SongFormer via WSL）
- 分析 audio.wav，输出段落结构（intro / verse / chorus / bridge / outro 等）
- 输出 music_structure_raw.json

调用链：
  main.py
  → analyze_music()
  → wsl python step4_songformer/run_step4.py
  → SongFormer infer.py（在 WSL conda 环境 'songformer' 中运行）
  → music_structure_raw.json

WSL 侧环境初始化（新开发者）：
  cd step4_songformer && bash setup_wsl_env.sh
"""
import json
import subprocess
from pathlib import Path

from src.utils.json_utils import save_json
from src.utils.path_utils import get_source_dir, get_analysis_dir

# WSL 侧 Python 解释器（songformer conda 环境）
_WSL_PYTHON = "/home/vip/miniconda3/envs/songformer/bin/python"

# run_step4.py 相对于本文件的位置：
# src/modules/music_structure_analyzer.py → ../../step4_songformer/run_step4.py
_STEP4_SCRIPT = Path(__file__).parent.parent.parent / "step4_songformer" / "run_step4.py"


def _to_wsl_path(windows_path: Path) -> str:
    """将 Windows 绝对路径转为 WSL /mnt/ 路径。"""
    p = windows_path.resolve()
    drive = p.drive.rstrip(":").lower()
    rest = p.as_posix().split(":", 1)[-1]
    return f"/mnt/{drive}{rest}"


def analyze_music(
    mv_id: str,
    output_root: str = "data/processed",
    use_wsl: bool = True,
) -> dict:
    src_dir = get_source_dir(output_root, mv_id)
    analysis_dir = get_analysis_dir(output_root, mv_id)

    audio_path = src_dir / "audio.wav"
    out_path = analysis_dir / "music_structure_raw.json"

    if not audio_path.exists():
        raise FileNotFoundError(
            f"[Step 4] audio.wav 不存在: {audio_path}\n"
            "请先运行 Step 1 完成视频标准化和音频提取。"
        )

    print(f"[Step 4] 运行 SongFormer (WSL): {audio_path}")

    wsl_audio  = _to_wsl_path(audio_path)
    wsl_out    = _to_wsl_path(out_path)
    wsl_script = _to_wsl_path(_STEP4_SCRIPT)

    cmd = [
        "wsl",
        _WSL_PYTHON,
        wsl_script,
        "--audio",  wsl_audio,
        "--output", wsl_out,
        "--mv-id",  mv_id,
    ]

    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"[Step 4] SongFormer 运行失败（返回码 {result.returncode}）\n"
            "请检查：\n"
            "  1. WSL 中 conda 环境 'songformer' 是否正确安装\n"
            "  2. ckpts 文件是否完整（参考 step4_songformer/README.md）\n"
            "  3. NVIDIA GPU 是否可用（wsl nvidia-smi）"
        )

    structured = json.loads(out_path.read_text(encoding="utf-8"))
    print(f"[Step 4] 完成，输出 -> {out_path}")
    return structured
