"""python scripts/run_stage3_extract_keyframes.py --mv-id MV_001"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import load_config
from src.modules.keyframe_extractor import extract_keyframes

parser = argparse.ArgumentParser()
parser.add_argument("--mv-id", required=True)
parser.add_argument("--config", default="configs/pipeline.yaml")
args = parser.parse_args()

cfg = load_config(args.config)
extract_keyframes(
    mv_id=args.mv_id,
    output_root=cfg["project"]["output_root"],
)
