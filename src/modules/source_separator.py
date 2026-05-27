"""
Step 1.5: 音源分离（htdemucs）
- 对 source/audio.wav 运行 demucs，提取 vocals.wav
- 输出到 source/vocals.wav（供后续 vocal_detector 使用）
- 若 source/vocals.wav 已存在则跳过，不重复运行
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

from src.utils.path_utils import get_source_dir


def separate_vocals(
    mv_id: str,
    output_root: str = "data/processed",
) -> Path:
    src_dir = get_source_dir(output_root, mv_id)
    audio_path = src_dir / "audio.wav"
    vocals_out = src_dir / "vocals.wav"

    if vocals_out.exists():
        print(f"[Step 1.5] vocals.wav 已存在，跳过音源分离 -> {vocals_out}")
        return vocals_out

    if not audio_path.exists():
        raise FileNotFoundError(
            f"[Step 1.5] audio.wav 不存在: {audio_path}\n"
            "请先运行 Step 1 完成视频标准化和音频提取。"
        )

    print(f"[Step 1.5] 运行 htdemucs 分离人声: {audio_path}")

    with tempfile.TemporaryDirectory() as tmp:
        cmd = [
            "demucs",
            "-n", "htdemucs",
            "--two-stems=vocals",
            str(audio_path),
            "-o", tmp,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"[Step 1.5] demucs 运行失败（返回码 {result.returncode}）\n"
                f"stderr: {result.stderr}\n"
                "请确认 demucs 已安装：pip install demucs"
            )

        # demucs 输出路径：<tmp>/htdemucs/<audio_stem>/vocals.wav
        audio_stem = audio_path.stem
        generated = Path(tmp) / "htdemucs" / audio_stem / "vocals.wav"
        if not generated.exists():
            raise FileNotFoundError(
                f"[Step 1.5] 未找到 demucs 输出: {generated}\n"
                f"stdout: {result.stdout}"
            )
        shutil.copy2(generated, vocals_out)

    print(f"[Step 1.5] 完成，输出 -> {vocals_out}")
    return vocals_out
