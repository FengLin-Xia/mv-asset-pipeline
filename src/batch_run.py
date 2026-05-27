"""
批量处理 data/raw/ 下所有视频，自动分配 MV ID。

用法：
  python src/batch_run.py
  python src/batch_run.py --skip-demix --skip-music --skip-caption
  python src/batch_run.py --prefix PROJ --start-index 1
  python src/batch_run.py --start-from 3

MV ID 规则：按文件名排序后依次编号，如 MV_001、MV_002...
若需自定义 ID，直接用 main.py 单独处理。
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_config
from src.modules.video_standardizer import standardize
from src.modules.shot_detector_pyscenedetect import detect_shots
from src.modules.keyframe_extractor import extract_keyframes
from src.modules.music_structure_analyzer import analyze_music
from src.modules.captioner import caption_shots
from src.modules.color_analyzer import analyze_colors
from src.modules.source_separator import separate_vocals
from src.modules.vocal_detector import detect_vocals
from src.modules.schema_builder import build_schema
from src.modules.reviewer_export import export_review_csv
from src.modules.case_summary.case_summary_builder import build_case_summary


def run_one(mv_id: str, input_path: Path, cfg: dict, args: argparse.Namespace) -> None:
    output_root = cfg["project"]["output_root"]
    max_shots = args.max_shots if args.debug else None

    print(f"\n{'='*50}")
    print(f"  处理: {input_path.name}  →  {mv_id}")
    print(f"{'='*50}\n")

    if args.start_from <= 1:
        print("── Step 1: 视频标准化 ──")
        standardize(
            input_path=str(input_path),
            mv_id=mv_id,
            output_root=output_root,
            target_height=cfg["video"]["target_height"],
            target_fps=cfg["video"]["target_fps"],
            audio_sample_rate=cfg["video"]["audio_sample_rate"],
        )

    if args.start_from <= 1:
        if not args.skip_demix:
            print("\n── Step 1.5: 音源分离 (htdemucs) ──")
            try:
                separate_vocals(mv_id=mv_id, output_root=output_root)
            except Exception as e:
                print(f"\n  [Step 1.5] 失败，跳过（has_vocals 将为 null）\n  原因: {e}")
        else:
            print("\n── Step 1.5: 跳过音源分离 ──")

    if args.start_from <= 2:
        print("\n── Step 2: 镜头切分 ──")
        sd_cfg = cfg["shot_detection"]["pyscenedetect"]
        detect_shots(
            mv_id=mv_id,
            output_root=output_root,
            threshold=sd_cfg["threshold"],
            min_scene_len=sd_cfg["min_scene_len"],
        )

    if args.start_from <= 2:
        print("\n── Step 2.5: 人声标注 ──")
        try:
            detect_vocals(mv_id=mv_id, output_root=output_root)
        except Exception as e:
            print(f"\n  [Step 2.5] 失败，跳过（has_vocals 将为 null）\n  原因: {e}")

    if args.start_from <= 3:
        print("\n── Step 3: 关键帧抽取 ──")
        kf_cfg = cfg.get("keyframe", {})
        extract_keyframes(
            mv_id=mv_id,
            output_root=output_root,
            avoid_black_frames=kf_cfg.get("avoid_black_frames", True),
            avoid_blur_frames=kf_cfg.get("avoid_blur_frames", False),
        )

    if args.start_from <= 3:
        print("\n── Step 3.5: 关键帧颜色分析 ──")
        analyze_colors(mv_id=mv_id, output_root=output_root)

    if args.start_from <= 4:
        if not args.skip_music:
            print("\n── Step 4: 音乐结构分析 (SongFormer) ──")
            try:
                analyze_music(mv_id=mv_id, output_root=output_root)
            except Exception as e:
                print(f'\n  [Step 4] 失败，跳过（music_section 将为"不确定"）\n  原因: {e}')
        else:
            print("\n── Step 4: 跳过音乐结构分析 ──")

    if args.start_from <= 5:
        if not args.skip_caption:
            print("\n── Step 5: 视觉 Caption ──")
            caption_shots(mv_id=mv_id, output_root=output_root, max_shots=max_shots)
        else:
            print("\n── Step 5: 跳过 Caption ──")

    if args.start_from <= 6:
        print("\n── Step 6: 四层 JSON 结构化 ──")
        build_schema(mv_id=mv_id, output_root=output_root)
        export_review_csv(mv_id=mv_id, output_root=output_root)

    if args.start_from <= 7:
        if not args.skip_summary:
            print("\n── Step 7: 案例级总结 ──")
            cs_cfg = cfg.get("case_summary", {})
            thresholds = cs_cfg.get("thresholds", {})
            use_llm = (not args.no_llm) and cs_cfg.get("use_llm", True)
            try:
                build_case_summary(
                    mv_id=mv_id,
                    output_root=output_root,
                    use_llm=use_llm,
                    fast_threshold=thresholds.get("fast_cut_seconds", 1.0),
                    medium_threshold=thresholds.get("medium_cut_seconds", 2.5),
                    max_captions=cs_cfg.get("llm", {}).get("max_representative_captions", 30),
                )
            except Exception as e:
                print(f"\n  [Step 7] 失败，跳过\n  原因: {e}")
        else:
            print("\n── Step 7: 跳过案例级总结 ──")


def main():
    parser = argparse.ArgumentParser(description="MV 资产拆解 — 批量处理")
    parser.add_argument("--raw-dir", default="data/raw", help="原始视频目录")
    parser.add_argument("--config", default="configs/pipeline.yaml")
    parser.add_argument("--prefix", default="MV", help="MV ID 前缀，默认 MV")
    parser.add_argument("--start-index", type=int, default=1, help="编号起始值，默认 1")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--max-shots", type=int, default=10)
    parser.add_argument("--skip-demix", action="store_true")
    parser.add_argument("--skip-music", action="store_true")
    parser.add_argument("--skip-caption", action="store_true")
    parser.add_argument("--skip-summary", action="store_true")
    parser.add_argument("--no-llm", action="store_true", help="Step 7 只生成规则统计版")
    parser.add_argument("--start-from", type=int, default=1, help="从第几步开始（1-7）")
    args = parser.parse_args()

    cfg = load_config(args.config)
    raw_dir = Path(args.raw_dir)

    videos = sorted(raw_dir.glob("*.mp4")) + sorted(raw_dir.glob("*.mov")) + sorted(raw_dir.glob("*.avi"))
    if not videos:
        print(f"[batch] {raw_dir} 下没有找到视频文件")
        return

    print(f"[batch] 找到 {len(videos)} 个视频，开始批量处理\n")

    failed = []
    for i, video_path in enumerate(videos):
        mv_id = f"{args.prefix}_{args.start_index + i:03d}"
        try:
            run_one(mv_id=mv_id, input_path=video_path, cfg=cfg, args=args)
        except Exception as e:
            print(f"\n  [batch] {mv_id} 处理失败，跳过\n  原因: {e}")
            failed.append((mv_id, str(e)))

    print(f"\n{'='*50}")
    print(f"  批量完成，共 {len(videos)} 个，失败 {len(failed)} 个")
    if failed:
        for mv_id, reason in failed:
            print(f"  ✗ {mv_id}: {reason}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
