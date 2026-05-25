from pathlib import Path


def get_mv_dir(output_root: str, mv_id: str) -> Path:
    return Path(output_root) / mv_id


def get_source_dir(output_root: str, mv_id: str) -> Path:
    return get_mv_dir(output_root, mv_id) / "source"


def get_clips_dir(output_root: str, mv_id: str) -> Path:
    return get_mv_dir(output_root, mv_id) / "clips"


def get_frames_dir(output_root: str, mv_id: str) -> Path:
    return get_mv_dir(output_root, mv_id) / "frames"


def get_analysis_dir(output_root: str, mv_id: str) -> Path:
    return get_mv_dir(output_root, mv_id) / "analysis"


def ensure_dirs(output_root: str, mv_id: str) -> None:
    for d in [
        get_source_dir(output_root, mv_id),
        get_clips_dir(output_root, mv_id),
        get_frames_dir(output_root, mv_id),
        get_analysis_dir(output_root, mv_id),
    ]:
        d.mkdir(parents=True, exist_ok=True)
