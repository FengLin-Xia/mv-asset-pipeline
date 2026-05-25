"""python scripts/run_stage5_caption.py --mv-id MV_001 [--max-shots 10]"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import load_config
from src.modules.captioner import caption_shots

parser = argparse.ArgumentParser()
parser.add_argument("--mv-id", required=True)
parser.add_argument("--max-shots", type=int, default=None, help="调试用，只处理前 N 个 shot")
parser.add_argument("--config", default="configs/pipeline.yaml")
args = parser.parse_args()

cfg = load_config(args.config)
caption_shots(
    mv_id=args.mv_id,
    output_root=cfg["project"]["output_root"],
    max_shots=args.max_shots,
)
