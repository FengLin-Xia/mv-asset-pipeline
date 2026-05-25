def seconds_to_tc(seconds: float) -> str:
    """Convert float seconds to MM:SS.mmm string."""
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:06.3f}"


def tc_to_seconds(tc: str) -> float:
    """Parse MM:SS.mmm or HH:MM:SS.mmm to float seconds."""
    parts = tc.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    raise ValueError(f"Unrecognized timecode format: {tc}")
