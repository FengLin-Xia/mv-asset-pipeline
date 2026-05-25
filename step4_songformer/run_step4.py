"""
Step 4 WSL 入口脚本 - SongFormer 音乐结构分析

由主项目 music_structure_analyzer.py 通过 WSL 调用：
  wsl /home/vip/miniconda3/envs/songformer/bin/python \
      /mnt/c/.../step4_songformer/run_step4.py \
      --audio /mnt/c/.../audio.wav \
      --output /mnt/c/.../music_structure_raw.json \
      --mv-id MV_001
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ── 可配置路径（新开发者如有不同路径在此处修改）──────────────────────────
SONGFORMER_ROOT = Path("/home/vip/projects/SongFormer")
PYTHON_BIN = Path("/home/vip/miniconda3/envs/songformer/bin/python")
# ────────────────────────────────────────────────────────────────────────────

SONGFORMER_SRC = SONGFORMER_ROOT / "src" / "SongFormer"

LABEL_MAP = {
    "intro":         "开场",
    "verse":         "主歌",
    "pre-chorus":    "预副歌",
    "chorus":        "副歌",
    "bridge":        "Bridge",
    "outro":         "结尾",
    "break":         "Bridge",
    "inst":          "器乐段落",
    "instrumental":  "器乐段落",
}


def seconds_to_timecode(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def check_ckpts() -> None:
    ckpts = SONGFORMER_SRC / "ckpts"
    required = [
        ckpts / "SongFormer.safetensors",
        ckpts / "muq_config2.json",
        ckpts / "MusicFM" / "msd_stats.json",
        ckpts / "MusicFM" / "pretrained_msd.pt",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("[Step 4] ERROR: 缺少必要的 ckpts 文件：", file=sys.stderr)
        for m in missing:
            print(f"  {m}", file=sys.stderr)
        print("[Step 4] 请参考 step4_songformer/README.md 下载 ckpts。", file=sys.stderr)
        sys.exit(1)


def run_songformer(audio_path: Path, job_dir: Path) -> Path:
    """调用 SongFormer infer.py，返回输出 JSON 路径。"""
    input_scp = job_dir / "input.scp"
    output_dir = job_dir / "output"
    output_dir.mkdir(exist_ok=True)

    input_scp.write_text(str(audio_path) + "\n", encoding="utf-8")

    env = os.environ.copy()
    src = SONGFORMER_ROOT / "src"
    env["PYTHONPATH"] = ":".join([
        str(src),
        str(src / "SongFormer"),
        str(src / "third_party"),
        str(src / "third_party" / "musicfm"),
        env.get("PYTHONPATH", ""),
    ])

    cmd = [
        str(PYTHON_BIN),
        "infer/infer.py",
        "-i", str(input_scp),
        "-o", str(output_dir),
        "--model", "SongFormer",
        "--checkpoint", "SongFormer.safetensors",
        "--config_path", "SongFormer.yaml",
        "-gn", "1",
        "-tn", "1",
    ]

    print(f"[Step 4] 调用 SongFormer infer.py ...")
    result = subprocess.run(cmd, cwd=str(SONGFORMER_SRC), env=env)
    if result.returncode != 0:
        raise RuntimeError(f"SongFormer infer.py 返回错误码 {result.returncode}")

    output_json = output_dir / f"{audio_path.stem}.json"
    if not output_json.exists():
        raise FileNotFoundError(
            f"SongFormer 未生成预期输出文件: {output_json}\n"
            f"输出目录内容: {list(output_dir.iterdir())}"
        )
    return output_json


def convert_output(raw_segments: list, mv_id: str) -> dict:
    """将 SongFormer 原始输出转换为主 pipeline 格式。"""
    segments = []
    for seg in raw_segments:
        label = seg.get("label", "").lower()
        start = seg["start"]
        end = seg["end"]
        segments.append({
            "start_time":           seconds_to_timecode(start),
            "end_time":             seconds_to_timecode(end),
            "start_seconds":        round(start, 3),
            "end_seconds":          round(end, 3),
            "label":                label,
            "mapped_music_section": LABEL_MAP.get(label, "不确定"),
        })
    return {
        "mv_id":    mv_id,
        "method":   "songformer_wsl",
        "bpm":      None,
        "segments": segments,
    }


def main():
    parser = argparse.ArgumentParser(description="SongFormer Step 4 WSL 入口")
    parser.add_argument("--audio",  required=True, help="输入 audio.wav 的 WSL 路径")
    parser.add_argument("--output", required=True, help="输出 JSON 的 WSL 路径")
    parser.add_argument("--mv-id",  default="unknown", help="MV ID，如 MV_001")
    args = parser.parse_args()

    audio_path  = Path(args.audio)
    output_path = Path(args.output)

    if not audio_path.exists():
        print(f"[Step 4] ERROR: 音频文件不存在: {audio_path}", file=sys.stderr)
        sys.exit(1)

    check_ckpts()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="songformer_") as tmp:
        raw_json_path = run_songformer(audio_path, Path(tmp))
        raw_segments = json.loads(raw_json_path.read_text(encoding="utf-8"))

    structured = convert_output(raw_segments, args.mv_id)
    output_path.write_text(
        json.dumps(structured, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[Step 4] 完成 -> {output_path}")


if __name__ == "__main__":
    main()
