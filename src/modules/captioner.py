"""
Step 5: 视觉 Caption（API VLM）
- 对每个 shot 的 3 张关键帧发送 VLM API 请求
- 输出 captions_raw.json

支持 OpenAI-compatible API（含 GPT-4o、Qwen-VL-Plus 等）
"""
import base64
import json
import os
import time
from pathlib import Path
from tqdm import tqdm

import requests
from dotenv import load_dotenv

from src.utils.json_utils import save_json, load_json
from src.utils.path_utils import get_frames_dir, get_analysis_dir

load_dotenv()

CAPTION_PROMPT = """你是一个 MV 视觉分析助手。请根据这组关键帧（同一镜头的开始、中间、结束帧），描述该镜头中可见的视觉事实。

要求：
1. 只描述你能看到的内容，不要脑补剧情。
2. 输出中文。
3. 优先关注：人物数量、表演形式、场景、灯光色彩、服装、景别、可能的镜头运动。
4. 如果无法判断某字段，请写"不确定"。
5. 严格输出 JSON，不要有多余文字。

JSON 格式：
{
  "caption": "...",
  "performer_count_type": "单人 / 双人 / 多人团体 / 大量人群 / 不确定",
  "performance_type": "群舞 / 单人表演 / 走位 / 摆pose / 剧情表演 / 混合 / 不确定",
  "scene_type": "室内舞台 / 城市街景 / 学校场景 / 摄影棚 / 幻想空间 / 豪华房间 / 街头空间 / 不确定",
  "shot_size": "远景 / 中景 / 近景 / 特写 / 大特写 / 不确定",
  "lighting_color": [],
  "costume_style": [],
  "visual_elements": [],
  "camera_movement_guess": "静止 / 推进 / 拉远 / 横摇 / 环绕 / 手持 / 快速变焦 / 不确定",
  "confidence_notes": ""
}"""


def _image_to_b64(image_path: Path) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _call_vlm_api(image_paths: list[Path], api_key: str, api_base: str, model: str) -> dict:
    content = []
    for img_path in image_paths:
        if img_path.exists():
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{_image_to_b64(img_path)}",
                    "detail": "low",
                },
            })
    content.append({"type": "text", "text": CAPTION_PROMPT})

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 800,
        "temperature": 0.2,
    }

    resp = requests.post(
        f"{api_base.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=60,
        proxies={"http": None, "https": None},
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"].strip()

    # 尝试提取 JSON
    if "```" in text:
        text = text.split("```json")[-1].split("```")[0].strip()
    return json.loads(text)


def caption_shots(
    mv_id: str,
    output_root: str = "data/processed",
    max_shots: int | None = None,
    request_interval: float = 3.0,
) -> list[dict]:
    api_key = os.getenv("VLM_API_KEY", "")
    api_base = os.getenv("VLM_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("VLM_MODEL", "gpt-4o")

    if not api_key:
        raise ValueError("VLM_API_KEY 未设置，请检查 .env 文件")

    analysis_dir = get_analysis_dir(output_root, mv_id)

    keyframes_data = load_json(analysis_dir / "keyframes_raw.json")
    if max_shots:
        keyframes_data = keyframes_data[:max_shots]

    out_path = analysis_dir / "captions_raw.json"

    # 断点续跑：读取已有结果，跳过已完成的 shot
    if out_path.exists():
        existing = load_json(out_path)
        done_ids = {item["shot_id"] for item in existing}
        results = existing
        skip_count = len(done_ids)
        print(f"[Step 5] 发现已有 {skip_count} 个 shot 的结果，断点续跑")
    else:
        done_ids = set()
        results = []

    pending = [s for s in keyframes_data if s["shot_id"] not in done_ids]
    if not pending:
        print(f"[Step 5] 全部 shot 已完成，无需重跑")
        return results

    for shot_kf in tqdm(pending, desc="[Step 5] Caption"):
        shot_id = shot_kf["shot_id"]
        image_paths = [
            Path(output_root) / mv_id / kf["image_path"]
            for kf in shot_kf["keyframes"]
        ]

        try:
            caption = _call_vlm_api(image_paths, api_key, api_base, model)
            caption["source"] = "api_vlm"
            caption["model"] = model
        except Exception as e:
            print(f"  {shot_id} caption 失败: {e}")
            caption = {"error": str(e), "source": "api_vlm", "model": model}

        results.append({"shot_id": shot_id, "caption_result": caption})

        # 每完成一个 shot 立即写盘
        save_json(results, out_path)

        time.sleep(request_interval)

    print(f"[Step 5] 完成，输出 -> {out_path}")
    return results
