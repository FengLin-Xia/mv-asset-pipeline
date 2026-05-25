"""python scripts/run_stage2_detect_shots.py --mv-id MV_001"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import load_config
from src.modules.shot_detector_pyscenedetect import detect_shots

parser = argparse.ArgumentParser()
parser.add_argument("--mv-id", required=True)
parser.add_argument("--config", default="configs/pipeline.yaml")
args = parser.parse_args()

cfg = load_config(args.config)
sd_cfg = cfg["shot_detection"]["pyscenedetect"]
result = detect_shots(
    mv_id=args.mv_id,
    output_root=cfg["project"]["output_root"],
    threshold=sd_cfg["threshold"],
    min_scene_len=sd_cfg["min_scene_len"],
)
print(f"检测到 {result['shot_count']} 个镜头")
