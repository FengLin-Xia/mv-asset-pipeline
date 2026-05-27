"""
Step 7 独立运行脚本

用法：
  python scripts/run_stage7_case_summary.py --mv-id MV_001
  python scripts/run_stage7_case_summary.py --mv-id MV_001 --no-llm
  python scripts/run_stage7_case_summary.py --mv-id MV_001 --overwrite
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_config
from src.modules.case_summary.case_summary_builder import build_case_summary


def main():
    parser = argparse.ArgumentParser(description="Step 7: 案例级总结")
    parser.add_argument("--mv-id", required=True)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    parser.add_argument("--no-llm", action="store_true", help="只生成规则统计版，不调用 LLM")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有 case_summary")
    parser.add_argument("--language", default="zh", choices=["zh", "en"])
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    cfg = load_config(args.config)
    output_root = cfg["project"]["output_root"]
    cs_cfg = cfg.get("case_summary", {})
    thresholds = cs_cfg.get("thresholds", {})

    use_llm = (not args.no_llm) and cs_cfg.get("use_llm", True)

    summary = build_case_summary(
        mv_id=args.mv_id,
        output_root=output_root,
        use_llm=use_llm,
        language=args.language,
        overwrite=args.overwrite,
        fast_threshold=thresholds.get("fast_cut_seconds", 1.0),
        medium_threshold=thresholds.get("medium_cut_seconds", 2.5),
        max_captions=cs_cfg.get("llm", {}).get("max_representative_captions", 30),
    )

    if args.debug:
        import json
        print("\n── basic_stats ──")
        print(json.dumps(summary.get("basic_stats", {}), ensure_ascii=False, indent=2))
        print("\n── editing_rhythm ──")
        print(json.dumps(summary.get("editing_rhythm", {}), ensure_ascii=False, indent=2))

    print(f"\n[Step 7] 完成  method={summary.get('method')}")


if __name__ == "__main__":
    main()
