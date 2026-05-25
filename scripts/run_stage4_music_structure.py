"""python scripts/run_stage4_music_structure.py --mv-id MV_001"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import load_config
from src.modules.music_structure_analyzer import analyze_music

parser = argparse.ArgumentParser()
parser.add_argument("--mv-id", required=True)
parser.add_argument("--config", default="configs/pipeline.yaml")
parser.add_argument("--no-wsl", action="store_true", help="直接本地调用 allin1，不走 WSL 子进程")
args = parser.parse_args()

cfg = load_config(args.config)
analyze_music(
    mv_id=args.mv_id,
    output_root=cfg["project"]["output_root"],
    use_wsl=not args.no_wsl,
)
