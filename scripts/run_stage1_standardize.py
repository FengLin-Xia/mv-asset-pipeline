"""python scripts/run_stage1_standardize.py --input data/raw/MV_001.mp4 --mv-id MV_001"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import load_config
from src.modules.video_standardizer import standardize

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True, help="输入视频路径")
parser.add_argument("--mv-id", required=True, help="MV ID，如 MV_001")
parser.add_argument("--config", default="configs/pipeline.yaml")
args = parser.parse_args()

cfg = load_config(args.config)
result = standardize(
    input_path=args.input,
    mv_id=args.mv_id,
    output_root=cfg["project"]["output_root"],
    target_height=cfg["video"]["target_height"],
    target_fps=cfg["video"]["target_fps"],
    audio_sample_rate=cfg["video"]["audio_sample_rate"],
)
print(result)
