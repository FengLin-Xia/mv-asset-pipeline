"""python scripts/run_stage6_build_json.py --mv-id MV_001"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import load_config
from src.modules.schema_builder import build_schema
from src.modules.reviewer_export import export_review_csv

parser = argparse.ArgumentParser()
parser.add_argument("--mv-id", required=True)
parser.add_argument("--config", default="configs/pipeline.yaml")
args = parser.parse_args()

cfg = load_config(args.config)
output_root = cfg["project"]["output_root"]
build_schema(mv_id=args.mv_id, output_root=output_root)
export_review_csv(mv_id=args.mv_id, output_root=output_root)
