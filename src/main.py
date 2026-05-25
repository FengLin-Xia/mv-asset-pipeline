"""
一键运行全流程：
  python src/main.py --input data/raw/MV_001.mp4 --mv-id MV_001
  python src/main.py --input data/raw/MV_001.mp4 --mv-id MV_001 --debug --max-shots 10
  python src/main.py --input data/raw/MV_001.mp4 --mv-id MV_001 --skip-caption
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
from src.modules.schema_builder import build_schema
from src.modules.reviewer_export import export_review_csv


def main():
    parser = argparse.ArgumentParser(description="MV 资产拆解 Pipeline")
    parser.add_argument("--input", required=True, help="输入 MV 视频路径")
    parser.add_argument("--mv-id", required=True, help="MV ID，如 MV_001")
    parser.add_argument("--config", default="configs/pipeline.yaml")
    parser.add_argument("--debug", action="store_true", help="Debug 模式：只处理前 N 个 shot")
    parser.add_argument("--max-shots", type=int, default=10, help="Debug 模式的 shot 数量上限")
    parser.add_argument("--skip-music", action="store_true", help="跳过音乐结构分析（SongFormer/WSL 未配置时使用）")
    parser.add_argument("--skip-caption", action="store_true", help="跳过 VLM caption")
    parser.add_argument("--start-from", type=int, default=1, help="从第几步开始（1-6）")
    args = parser.parse_args()

    cfg = load_config(args.config)
    output_root = cfg["project"]["output_root"]
    mv_id = args.mv_id
    max_shots = args.max_shots if args.debug else None

    print(f"\n{'='*50}")
    print(f"  MV 资产拆解 Pipeline")
    print(f"  MV ID   : {mv_id}")
    print(f"  输入    : {args.input}")
    print(f"  Debug   : {args.debug}{f' (前 {max_shots} 个 shot)' if args.debug else ''}")
    print(f"{'='*50}\n")

    if args.start_from <= 1:
        print("── Step 1: 视频标准化 ──")
        standardize(
            input_path=args.input,
            mv_id=mv_id,
            output_root=output_root,
            target_height=cfg["video"]["target_height"],
            target_fps=cfg["video"]["target_fps"],
            audio_sample_rate=cfg["video"]["audio_sample_rate"],
        )

    if args.start_from <= 2:
        print("\n── Step 2: 镜头切分 ──")
        sd_cfg = cfg["shot_detection"]["pyscenedetect"]
        detect_shots(
            mv_id=mv_id,
            output_root=output_root,
            threshold=sd_cfg["threshold"],
            min_scene_len=sd_cfg["min_scene_len"],
        )

    if args.start_from <= 3:
        print("\n── Step 3: 关键帧抽取 ──")
        extract_keyframes(mv_id=mv_id, output_root=output_root)

    if args.start_from <= 4:
        if not args.skip_music:
            print("\n── Step 4: 音乐结构分析 (SongFormer) ──")
            try:
                analyze_music(mv_id=mv_id, output_root=output_root)
            except Exception as e:
                print('\n  [Step 4] 失败，跳过音乐分析（后续步骤中 music_section 字段将为"不确定"）')
                print(f"  原因: {e}")
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

    print(f"\n{'='*50}")
    print(f"  全流程完成！输出目录：{output_root}/{mv_id}/")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
